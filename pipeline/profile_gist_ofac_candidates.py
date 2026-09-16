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
DEFAULT_OFAC = Path("tmp/source-packages/ofac/derived/ofac-sanctions-entities.v1.json")
DEFAULT_OUTPUT = Path("tmp/source-packages/ofac/review/gist-owner-ofac-candidates.json")
SCHEMA = "steel-exposure-atlas/gist-ofac-candidate-profile-v1.0"


def _clean(value: object) -> str:
    return str(value or "").strip()


def _usable_owner(owner_id: object, owner_name: object) -> bool:
    oid = _clean(owner_id)
    name = _clean(owner_name)
    return bool(oid and name and name.casefold() not in {"unknown", "n/a"})


def build_profile(gist: dict[str, object], ofac: dict[str, object]) -> dict[str, object]:
    plants = gist.get("plants")
    entities = ofac.get("entities")
    if not isinstance(plants, list):
        raise ValueError("GIST payload has no plants list.")
    if not isinstance(entities, list):
        raise ValueError("OFAC subset has no entities list.")

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
    entity_names: dict[str, list[str]] = {}
    entity_lists: dict[str, str] = {}
    entity_programmes: dict[str, list[str]] = {}

    for entity in entities:
        if not isinstance(entity, dict):
            continue
        entity_id = _clean(entity.get("entity_id"))
        names = entity.get("names")
        if not entity_id or not isinstance(names, list):
            raise ValueError("OFAC entity is missing entity_id or names.")
        cleaned_names = list(dict.fromkeys(_clean(name) for name in names if _clean(name)))
        if not cleaned_names:
            raise ValueError(f"OFAC entity {entity_id} has no usable names.")
        entity_names[entity_id] = cleaned_names
        entity_lists[entity_id] = _clean(entity.get("source_list"))
        programmes = entity.get("programmes")
        entity_programmes[entity_id] = (
            sorted({_clean(value) for value in programmes if _clean(value)})
            if isinstance(programmes, list)
            else []
        )
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
                for source_name in entity_names[entity_id]:
                    if normalize_name(source_name) == conservative:
                        exact_pairs.append(
                            {"owner_name": owner_name, "source_name": source_name}
                        )

        if exact_hits:
            state = (
                "review_required_exact_name"
                if len(exact_hits) == 1
                else "review_required_ambiguous_exact_name"
            )
            entity_ids = sorted(exact_hits)
            evidence_pairs = exact_pairs
        else:
            for owner_name in owner_names:
                relaxed = relaxed_legal_form_name(owner_name)
                if not relaxed:
                    continue
                for entity_id in sorted(relaxed_index.get(relaxed, set())):
                    relaxed_hits.add(entity_id)
                    for source_name in entity_names[entity_id]:
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
                "candidate_ofac_entity_ids": entity_ids,
                "candidate_source_lists": sorted(
                    {entity_lists[entity_id] for entity_id in entity_ids if entity_lists[entity_id]}
                ),
                "candidate_programmes": sorted(
                    {
                        programme
                        for entity_id in entity_ids
                        for programme in entity_programmes[entity_id]
                    }
                ),
                "evidence_name_pairs": evidence_pairs,
            }
        )

    multi_name_owners = sum(
        1 for owner in owners.values() if len(owner["names"]) > 1  # type: ignore[arg-type]
    )
    list_counts = Counter(entity_lists.values())

    return {
        "meta": {
            "schema": SCHEMA,
            "gist_schema": (gist.get("meta") or {}).get("schema")
            if isinstance(gist.get("meta"), dict)
            else None,
            "ofac_schema": (ofac.get("meta") or {}).get("schema")
            if isinstance(ofac.get("meta"), dict)
            else None,
            "interpretation": (
                "Candidate screening only. Exact and legal-form name candidates remain review_required. "
                "No fuzzy matching is run. A no-name-candidate result is not sanctions clearance, and "
                "SDN and Consolidated Non-SDN legal effects are not treated as equivalent."
            ),
        },
        "counts": {
            "gist_plants": len(plants),
            "usable_unique_owner_identities": len(owners),
            "owner_identities_with_multiple_source_names": multi_name_owners,
            "ofac_entities": len(entity_names),
            "ofac_sdn_entities": list_counts["SDN"],
            "ofac_consolidated_non_sdn_entities": list_counts["Consolidated Non-SDN"],
            "review_required_exact_name": counts["review_required_exact_name"],
            "review_required_ambiguous_exact_name": counts["review_required_ambiguous_exact_name"],
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
            "Profile conservative GIST-owner to OFAC Entity name candidates locally. "
            "No candidate is a sanctions finding."
        )
    )
    parser.add_argument("--gist", type=Path, default=DEFAULT_GIST)
    parser.add_argument("--ofac", type=Path, default=DEFAULT_OFAC)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    gist = json.loads(args.gist.read_text(encoding="utf-8"))
    ofac = json.loads(args.ofac.read_text(encoding="utf-8"))
    payload = build_profile(gist, ofac)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    counts = payload["counts"]
    print(f"GIST plants: {counts['gist_plants']}")
    print(f"usable unique owner identities: {counts['usable_unique_owner_identities']}")
    print(f"OFAC Entity records: {counts['ofac_entities']}")
    print(f"  SDN: {counts['ofac_sdn_entities']}")
    print(f"  Consolidated Non-SDN: {counts['ofac_consolidated_non_sdn_entities']}")
    print(f"exact-name review candidates: {counts['review_required_exact_name']}")
    print(f"ambiguous exact-name review candidates: {counts['review_required_ambiguous_exact_name']}")
    print(f"legal-form review candidates: {counts['review_required_legal_form']}")
    print(f"no name candidate: {counts['no_name_candidate']}")
    print(f"owner identities with any candidate: {counts['owner_identities_with_any_candidate']}")
    print(f"plants under candidate owners: {counts['plants_under_candidate_owners']}")
    print("fuzzy matching: not run")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
