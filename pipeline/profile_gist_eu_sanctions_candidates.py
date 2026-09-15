from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

try:
    from pipeline.sanctions_match import normalize_name, relaxed_legal_form_name
except ModuleNotFoundError:
    from sanctions_match import normalize_name, relaxed_legal_form_name  # type: ignore[no-redef]

DEFAULT_GIST = Path("public/data/gist-plants.v1.json")
DEFAULT_SANCTIONS = Path(
    "tmp/source-packages/eu-sanctions/derived/eu-sanctions-enterprises.v1.json"
)
DEFAULT_OUTPUT = Path(
    "tmp/source-packages/eu-sanctions/review/gist-owner-eu-sanctions-candidates.json"
)
SCHEMA = "steel-exposure-atlas/gist-eu-sanctions-candidate-profile-v1.0"


def _clean(value: object) -> str:
    return str(value or "").strip()


def _usable_owner(owner_id: object, owner_name: object) -> bool:
    oid = _clean(owner_id)
    name = _clean(owner_name)
    return bool(oid and name and name.casefold() not in {"unknown", "n/a"})


def build_profile(gist: dict[str, object], sanctions: dict[str, object]) -> dict[str, object]:
    plants = gist.get("plants")
    entities = sanctions.get("entities")
    if not isinstance(plants, list):
        raise ValueError("GIST payload has no plants list.")
    if not isinstance(entities, list):
        raise ValueError("EU sanctions subset has no entities list.")

    owners: dict[str, dict[str, object]] = {}
    for plant in plants:
        if not isinstance(plant, dict):
            continue
        owner_id = plant.get("owner_gem_entity_id")
        owner_name = plant.get("owner_name")
        if not _usable_owner(owner_id, owner_name):
            continue
        oid = _clean(owner_id)
        item = owners.setdefault(oid, {"names": set(), "plant_ids": set()})
        item["names"].add(_clean(owner_name))  # type: ignore[union-attr]
        item["plant_ids"].add(_clean(plant.get("plant_id")))  # type: ignore[union-attr]

    conservative_index: dict[str, set[str]] = defaultdict(set)
    relaxed_index: dict[str, set[str]] = defaultdict(set)
    sanction_names: dict[str, list[str]] = {}

    for entity in entities:
        if not isinstance(entity, dict):
            continue
        entity_id = _clean(entity.get("entity_id"))
        names = entity.get("names")
        if not entity_id or not isinstance(names, list):
            raise ValueError("EU sanctions entity is missing entity_id or names.")
        cleaned_names = sorted({_clean(name) for name in names if _clean(name)})
        if not cleaned_names:
            raise ValueError(f"EU sanctions entity {entity_id} has no usable names.")
        sanction_names[entity_id] = cleaned_names
        for name in cleaned_names:
            conservative = normalize_name(name)
            relaxed = relaxed_legal_form_name(name)
            if conservative:
                conservative_index[conservative].add(entity_id)
            if relaxed:
                relaxed_index[relaxed].add(entity_id)

    candidates: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    candidate_owner_ids: set[str] = set()
    candidate_plant_ids: set[str] = set()

    for owner_id in sorted(owners):
        owner = owners[owner_id]
        owner_names = sorted(owner["names"])  # type: ignore[arg-type]
        exact_hits: set[str] = set()
        relaxed_hits: set[str] = set()
        exact_pairs: list[dict[str, str]] = []
        relaxed_pairs: list[dict[str, str]] = []

        for owner_name in owner_names:
            conservative = normalize_name(owner_name)
            for entity_id in sorted(conservative_index.get(conservative, set())):
                exact_hits.add(entity_id)
                for source_name in sanction_names[entity_id]:
                    if normalize_name(source_name) == conservative:
                        exact_pairs.append(
                            {"owner_name": owner_name, "source_name": source_name}
                        )

        if exact_hits:
            if len(exact_hits) == 1:
                state = "review_required_exact_name"
            else:
                state = "review_required_ambiguous_exact_name"
            entity_ids = sorted(exact_hits)
            evidence_pairs = exact_pairs
        else:
            for owner_name in owner_names:
                relaxed = relaxed_legal_form_name(owner_name)
                if not relaxed:
                    continue
                for entity_id in sorted(relaxed_index.get(relaxed, set())):
                    relaxed_hits.add(entity_id)
                    for source_name in sanction_names[entity_id]:
                        if relaxed_legal_form_name(source_name) == relaxed:
                            relaxed_pairs.append(
                                {"owner_name": owner_name, "source_name": source_name}
                            )
            if relaxed_hits:
                state = "review_required_legal_form"
                entity_ids = sorted(relaxed_hits)
                evidence_pairs = relaxed_pairs
            else:
                state = "no_name_candidate"
                entity_ids = []
                evidence_pairs = []

        counts[state] += 1
        if entity_ids:
            candidate_owner_ids.add(owner_id)
            candidate_plant_ids.update(owner["plant_ids"])  # type: ignore[arg-type]

        candidates.append(
            {
                "owner_gem_entity_id": owner_id,
                "owner_names": owner_names,
                "plant_count": len(owner["plant_ids"]),  # type: ignore[arg-type]
                "state": state,
                "candidate_eu_entity_ids": entity_ids,
                "evidence_name_pairs": evidence_pairs,
            }
        )

    multi_name_owners = sum(
        1 for owner in owners.values() if len(owner["names"]) > 1  # type: ignore[arg-type]
    )

    return {
        "meta": {
            "schema": SCHEMA,
            "gist_schema": (gist.get("meta") or {}).get("schema")
            if isinstance(gist.get("meta"), dict)
            else None,
            "eu_source_sha256": (sanctions.get("meta") or {}).get("raw_sha256")
            if isinstance(sanctions.get("meta"), dict)
            else None,
            "interpretation": (
                "This is a candidate-screening profile only. GIST owner names and GEM entity "
                "IDs are not legal-registry identities. Exact and legal-form name candidates "
                "remain review_required; fuzzy matching is intentionally not run. Plant country "
                "is not used as owner domicile."
            ),
        },
        "counts": {
            "gist_plants": len(plants),
            "usable_unique_owner_identities": len(owners),
            "owner_identities_with_multiple_source_names": multi_name_owners,
            "eu_sanctions_enterprises": len(sanction_names),
            "review_required_exact_name": counts["review_required_exact_name"],
            "review_required_ambiguous_exact_name": counts[
                "review_required_ambiguous_exact_name"
            ],
            "review_required_legal_form": counts["review_required_legal_form"],
            "no_name_candidate": counts["no_name_candidate"],
            "owner_identities_with_any_candidate": len(candidate_owner_ids),
            "plants_under_candidate_owners": len(candidate_plant_ids),
        },
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Profile conservative GIST-owner to EU-sanctions name candidates locally. "
            "No candidate is a sanctions finding."
        )
    )
    parser.add_argument("--gist", type=Path, default=DEFAULT_GIST)
    parser.add_argument("--sanctions", type=Path, default=DEFAULT_SANCTIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    gist = json.loads(args.gist.read_text(encoding="utf-8"))
    sanctions = json.loads(args.sanctions.read_text(encoding="utf-8"))
    payload = build_profile(gist, sanctions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    counts = payload["counts"]
    print(f"GIST plants: {counts['gist_plants']}")
    print(f"usable unique owner identities: {counts['usable_unique_owner_identities']}")
    print(
        "owner identities with multiple source names: "
        f"{counts['owner_identities_with_multiple_source_names']}"
    )
    print(f"EU sanctions enterprises: {counts['eu_sanctions_enterprises']}")
    print(f"exact-name review candidates: {counts['review_required_exact_name']}")
    print(
        "ambiguous exact-name review candidates: "
        f"{counts['review_required_ambiguous_exact_name']}"
    )
    print(f"legal-form review candidates: {counts['review_required_legal_form']}")
    print(f"no name candidate: {counts['no_name_candidate']}")
    print(
        "owner identities with any candidate: "
        f"{counts['owner_identities_with_any_candidate']}"
    )
    print(f"plants under candidate owners: {counts['plants_under_candidate_owners']}")
    print("fuzzy matching: not run")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
