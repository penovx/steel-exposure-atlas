from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
import re
import unicodedata
from typing import Iterable, Mapping, Sequence

DIRECT_LIST_MATCH = "direct_list_match"
REVIEW_REQUIRED = "review_required"
NO_DIRECT_LIST_MATCH = "no_direct_list_match_in_snapshot"

_DIRECT_EVIDENCE = {"identifier_exact", "primary_name_exact", "alias_exact"}
_LEGAL_FORM_TOKENS = {
    "ag", "as", "bv", "co", "corp", "corporation", "gmbh", "inc", "incorporated",
    "kg", "kgaa", "limited", "llc", "ltd", "nv", "oy", "plc", "sa", "sas", "spa",
    "srl", "sro", "pte", "pty",
}


@dataclass(frozen=True)
class CompanyIdentity:
    company_id: str
    name: str
    aliases: tuple[str, ...] = ()
    country: str | None = None
    identifiers: Mapping[str, str | Sequence[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class SanctionsEntity:
    source: str
    snapshot_id: str
    entity_id: str
    primary_name: str
    aliases: tuple[str, ...] = ()
    countries: tuple[str, ...] = ()
    identifiers: Mapping[str, str | Sequence[str]] = field(default_factory=dict)
    entity_type: str = "entity"


@dataclass(frozen=True)
class Evidence:
    type: str
    company_value: str
    source_value: str
    similarity: float | None = None
    entity_id: str | None = None


@dataclass(frozen=True)
class MatchResult:
    company_id: str
    source: str
    snapshot_id: str
    state: str
    matched_entity_ids: tuple[str, ...]
    evidence: tuple[Evidence, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "company_id": self.company_id,
            "source": self.source,
            "snapshot_id": self.snapshot_id,
            "state": self.state,
            "matched_entity_ids": list(self.matched_entity_ids),
            "evidence": [
                {
                    "type": item.type,
                    "company_value": item.company_value,
                    "source_value": item.source_value,
                    "similarity": item.similarity,
                    "entity_id": item.entity_id,
                }
                for item in self.evidence
            ],
        }


def normalize_name(value: str) -> str:
    """Conservative normalization suitable for direct name evidence."""
    text = unicodedata.normalize("NFKC", value or "").casefold()
    text = "".join(" " if unicodedata.category(ch)[0] in {"P", "Z"} else ch for ch in text)
    return " ".join(text.split())


def normalize_identifier(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "").casefold()
    return re.sub(r"[^0-9a-z]+", "", text)


def relaxed_legal_form_name(value: str) -> str:
    tokens = [token for token in normalize_name(value).split() if token not in _LEGAL_FORM_TOKENS]
    return " ".join(tokens)


def _values(mapping: Mapping[str, str | Sequence[str]]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for raw_key, raw_value in mapping.items():
        key = normalize_name(raw_key)
        values = (raw_value,) if isinstance(raw_value, str) else tuple(raw_value)
        cleaned = {normalize_identifier(value) for value in values if normalize_identifier(value)}
        if key and cleaned:
            result[key] = cleaned
    return result


def _company_names(company: CompanyIdentity) -> tuple[tuple[str, str], ...]:
    return tuple(("name" if index == 0 else "alias", value) for index, value in enumerate((company.name, *company.aliases)))


def _source_names(entity: SanctionsEntity) -> tuple[tuple[str, str], ...]:
    return tuple(("primary" if index == 0 else "alias", value) for index, value in enumerate((entity.primary_name, *entity.aliases)))


def _direct_name_evidence(company: CompanyIdentity, entity: SanctionsEntity) -> list[Evidence]:
    evidence: list[Evidence] = []
    for company_kind, company_value in _company_names(company):
        company_norm = normalize_name(company_value)
        if not company_norm:
            continue
        for source_kind, source_value in _source_names(entity):
            if company_norm != normalize_name(source_value):
                continue
            evidence_type = "primary_name_exact" if company_kind == "name" and source_kind == "primary" else "alias_exact"
            evidence.append(Evidence(evidence_type, company_value, source_value, entity_id=entity.entity_id))
    return evidence


def _identifier_evidence(company: CompanyIdentity, entity: SanctionsEntity) -> list[Evidence]:
    evidence: list[Evidence] = []
    company_ids = _values(company.identifiers)
    entity_ids = _values(entity.identifiers)
    for kind in sorted(company_ids.keys() & entity_ids.keys()):
        for value in sorted(company_ids[kind] & entity_ids[kind]):
            evidence.append(Evidence("identifier_exact", f"{kind}:{value}", f"{kind}:{value}", entity_id=entity.entity_id))
    return evidence


def _review_evidence(company: CompanyIdentity, entity: SanctionsEntity, similarity_threshold: float) -> list[Evidence]:
    evidence: list[Evidence] = []
    direct_pairs = {(normalize_name(c), normalize_name(s)) for _, c in _company_names(company) for _, s in _source_names(entity)}
    for _, company_value in _company_names(company):
        conservative_company = normalize_name(company_value)
        relaxed_company = relaxed_legal_form_name(company_value)
        if not conservative_company or not relaxed_company:
            continue
        for _, source_value in _source_names(entity):
            conservative_source = normalize_name(source_value)
            if (conservative_company, conservative_source) in direct_pairs and conservative_company == conservative_source:
                continue
            relaxed_source = relaxed_legal_form_name(source_value)
            if relaxed_source and relaxed_company == relaxed_source and conservative_company != conservative_source:
                evidence.append(Evidence("legal_form_candidate", company_value, source_value, entity_id=entity.entity_id))
                continue
            similarity = SequenceMatcher(None, conservative_company, conservative_source).ratio()
            if similarity >= similarity_threshold:
                evidence.append(Evidence("similar_name_candidate", company_value, source_value, round(similarity, 4), entity.entity_id))
    return evidence


def match_company_to_entities(
    company: CompanyIdentity,
    entities: Iterable[SanctionsEntity],
    *,
    source: str,
    snapshot_id: str,
    similarity_threshold: float = 0.94,
) -> MatchResult:
    """Return evidence state for one company against one reviewed source snapshot.

    Only source records explicitly typed as entities participate. Direct results require
    deterministic identifier/name evidence. Similarity can only create review candidates.
    """
    direct_by_entity: dict[str, list[Evidence]] = {}
    review_by_entity: dict[str, list[Evidence]] = {}

    for entity in entities:
        if entity.entity_type != "entity" or entity.source != source or entity.snapshot_id != snapshot_id:
            continue
        direct = _identifier_evidence(company, entity) + _direct_name_evidence(company, entity)
        if direct:
            direct_by_entity[entity.entity_id] = direct
            continue
        review = _review_evidence(company, entity, similarity_threshold)
        if review:
            review_by_entity[entity.entity_id] = review

    if len(direct_by_entity) == 1:
        entity_id = next(iter(direct_by_entity))
        evidence = tuple(direct_by_entity[entity_id])
        assert all(item.type in _DIRECT_EVIDENCE for item in evidence)
        return MatchResult(company.company_id, source, snapshot_id, DIRECT_LIST_MATCH, (entity_id,), evidence)

    if len(direct_by_entity) > 1:
        entity_ids = tuple(sorted(direct_by_entity))
        evidence = [item for entity_id in entity_ids for item in direct_by_entity[entity_id]]
        evidence.append(Evidence("ambiguous_direct_match", company.name, ", ".join(entity_ids)))
        return MatchResult(company.company_id, source, snapshot_id, REVIEW_REQUIRED, entity_ids, tuple(evidence))

    if review_by_entity:
        entity_ids = tuple(sorted(review_by_entity))
        evidence = tuple(item for entity_id in entity_ids for item in review_by_entity[entity_id])
        return MatchResult(company.company_id, source, snapshot_id, REVIEW_REQUIRED, entity_ids, evidence)

    return MatchResult(company.company_id, source, snapshot_id, NO_DIRECT_LIST_MATCH, (), ())
