from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_CANDIDATES = Path(
    "tmp/source-packages/eu-sanctions/review/gist-owner-eu-sanctions-candidates.json"
)
DEFAULT_SANCTIONS = Path(
    "tmp/source-packages/eu-sanctions/derived/eu-sanctions-enterprises.v1.json"
)
DEFAULT_GIST = Path("public/data/gist-plants.v1.json")
DEFAULT_OUTPUT = Path(
    "tmp/source-packages/eu-sanctions/review/gist-owner-eu-sanctions-candidate-detail.json"
)
SCHEMA = "steel-exposure-atlas/gist-eu-sanctions-candidate-review-v1.0"


def _clean(value: object) -> str:
    return str(value or "").strip()


def build_review(
    candidate_payload: dict[str, object],
    sanctions_payload: dict[str, object],
    gist_payload: dict[str, object],
    *,
    owner_id: str | None = None,
) -> dict[str, object]:
    candidates = candidate_payload.get("candidates")
    entities = sanctions_payload.get("entities")
    plants = gist_payload.get("plants")
    if not isinstance(candidates, list):
        raise ValueError("Candidate payload has no candidates list.")
    if not isinstance(entities, list):
        raise ValueError("Sanctions payload has no entities list.")
    if not isinstance(plants, list):
        raise ValueError("GIST payload has no plants list.")

    active = [
        item
        for item in candidates
        if isinstance(item, dict) and item.get("candidate_eu_entity_ids")
    ]
    if owner_id is not None:
        active = [item for item in active if _clean(item.get("owner_gem_entity_id")) == owner_id]

    if len(active) != 1:
        if owner_id is None:
            raise ValueError(
                f"Expected exactly one active candidate, found {len(active)}. "
                "Pass --owner-id when multiple candidates exist."
            )
        raise ValueError(f"Expected one candidate for owner {owner_id!r}, found {len(active)}.")

    candidate = active[0]
    selected_owner_id = _clean(candidate.get("owner_gem_entity_id"))
    eu_ids = {
        _clean(value)
        for value in candidate.get("candidate_eu_entity_ids", [])
        if _clean(value)
    }

    selected_entities: list[dict[str, object]] = []
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        if _clean(entity.get("entity_id")) in eu_ids:
            selected_entities.append(entity)

    if len(selected_entities) != len(eu_ids):
        raise ValueError("Candidate references an EU entity that is missing from the subset.")

    selected_plants = [
        plant
        for plant in plants
        if isinstance(plant, dict)
        and _clean(plant.get("owner_gem_entity_id")) == selected_owner_id
    ]

    if not selected_plants:
        raise ValueError("Candidate owner has no plants in the GIST payload.")

    review_entities = []
    for entity in sorted(selected_entities, key=lambda item: _clean(item.get("entity_id"))):
        identifiers = entity.get("identifiers")
        if not isinstance(identifiers, list):
            identifiers = []
        review_entities.append(
            {
                "entity_id": _clean(entity.get("entity_id")),
                "names": entity.get("names", []),
                "eu_reference_numbers": entity.get("eu_reference_numbers", []),
                "designation_dates": entity.get("designation_dates", []),
                "programmes": entity.get("programmes", []),
                "countries_iso2": entity.get("countries_iso2", []),
                "countries": entity.get("countries", []),
                "identifiers": identifiers,
            }
        )

    return {
        "meta": {
            "schema": SCHEMA,
            "state": "review_required",
            "interpretation": (
                "Local identity review only. The candidate is not a sanctions finding. "
                "GIST owner labels are not legal-registry identities; plant country is not "
                "owner domicile."
            ),
            "publication_state": "local review only; do not publish candidate detail yet",
        },
        "gist_owner": {
            "owner_gem_entity_id": selected_owner_id,
            "owner_names": candidate.get("owner_names", []),
            "plants": [
                {
                    "plant_id": plant.get("plant_id"),
                    "plant_name": plant.get("plant_name"),
                    "country_area": plant.get("country_area"),
                }
                for plant in selected_plants
            ],
        },
        "candidate": {
            "state": candidate.get("state"),
            "evidence_name_pairs": candidate.get("evidence_name_pairs", []),
            "eu_entities": review_entities,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect one GIST-owner to EU-sanctions review candidate locally. "
            "This produces identity-review evidence, not a sanctions finding."
        )
    )
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--sanctions", type=Path, default=DEFAULT_SANCTIONS)
    parser.add_argument("--gist", type=Path, default=DEFAULT_GIST)
    parser.add_argument("--owner-id")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    candidate_payload = json.loads(args.candidates.read_text(encoding="utf-8"))
    sanctions_payload = json.loads(args.sanctions.read_text(encoding="utf-8"))
    gist_payload = json.loads(args.gist.read_text(encoding="utf-8"))

    review = build_review(
        candidate_payload,
        sanctions_payload,
        gist_payload,
        owner_id=args.owner_id,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    owner = review["gist_owner"]
    candidate = review["candidate"]
    print("state: review_required")
    print(f"GEM owner ID: {owner['owner_gem_entity_id']}")
    print(f"GIST owner names: {owner['owner_names']}")
    print(f"GIST plants: {len(owner['plants'])}")
    print(f"candidate type: {candidate['state']}")
    print("evidence name pairs:")
    for pair in candidate["evidence_name_pairs"]:
        print(f"  {pair['owner_name']}  <->  {pair['source_name']}")
    print("EU candidate entities:")
    for entity in candidate["eu_entities"]:
        print(f"  entity_id: {entity['entity_id']}")
        print(f"  EU references: {entity['eu_reference_numbers']}")
        print(f"  names: {entity['names']}")
        print(f"  programmes: {entity['programmes']}")
        print(f"  designation dates: {entity['designation_dates']}")
        print(f"  country context: {entity['countries_iso2']} | {entity['countries']}")
        print(f"  identifiers: {entity['identifiers']}")
    print("conclusion: none; candidate remains review_required")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
