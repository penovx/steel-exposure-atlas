from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_CANDIDATES = Path(
    "tmp/source-packages/ofac/review/gist-owner-ofac-candidates.json"
)
DEFAULT_OFAC = Path(
    "tmp/source-packages/ofac/derived/ofac-sanctions-entities.v1.json"
)
DEFAULT_GIST = Path("public/data/gist-plants.v1.json")
DEFAULT_OUTPUT = Path(
    "tmp/source-packages/ofac/review/gist-owner-ofac-candidate-detail.json"
)
SCHEMA = "steel-exposure-atlas/gist-ofac-candidate-review-v1.0"


def _clean(value: object) -> str:
    return str(value or "").strip()


def build_review(
    candidate_payload: dict[str, object],
    ofac_payload: dict[str, object],
    gist_payload: dict[str, object],
) -> dict[str, object]:
    candidates = candidate_payload.get("candidates")
    entities = ofac_payload.get("entities")
    plants = gist_payload.get("plants")
    if not isinstance(candidates, list):
        raise ValueError("Candidate payload has no candidates list.")
    if not isinstance(entities, list):
        raise ValueError("OFAC payload has no entities list.")
    if not isinstance(plants, list):
        raise ValueError("GIST payload has no plants list.")

    entity_index = {
        _clean(entity.get("entity_id")): entity
        for entity in entities
        if isinstance(entity, dict) and _clean(entity.get("entity_id"))
    }

    active = [
        item
        for item in candidates
        if isinstance(item, dict) and item.get("candidate_ofac_entity_ids")
    ]

    reviews: list[dict[str, object]] = []
    for candidate in active:
        owner_id = _clean(candidate.get("owner_gem_entity_id"))
        entity_ids = [
            _clean(value)
            for value in candidate.get("candidate_ofac_entity_ids", [])
            if _clean(value)
        ]

        selected_plants = [
            plant
            for plant in plants
            if isinstance(plant, dict)
            and _clean(plant.get("owner_gem_entity_id")) == owner_id
        ]
        if not selected_plants:
            raise ValueError(f"Candidate owner {owner_id!r} has no plants in GIST.")

        review_entities: list[dict[str, object]] = []
        for entity_id in entity_ids:
            entity = entity_index.get(entity_id)
            if entity is None:
                raise ValueError(
                    f"Candidate references OFAC entity {entity_id!r} missing from subset."
                )
            review_entities.append(
                {
                    "entity_id": entity_id,
                    "source_list": entity.get("source_list"),
                    "ofac_uid": entity.get("ofac_uid"),
                    "primary_name": entity.get("primary_name"),
                    "names": entity.get("names", []),
                    "aliases": entity.get("aliases", []),
                    "programmes": entity.get("programmes", []),
                    "countries": entity.get("countries", []),
                    "addresses": entity.get("addresses", []),
                    "identifiers": entity.get("identifiers", []),
                }
            )

        reviews.append(
            {
                "owner_gem_entity_id": owner_id,
                "owner_names": candidate.get("owner_names", []),
                "plant_count": len(selected_plants),
                "plants": [
                    {
                        "plant_id": plant.get("plant_id"),
                        "plant_name": plant.get("plant_name"),
                        "country_area": plant.get("country_area"),
                    }
                    for plant in selected_plants
                ],
                "candidate_state": candidate.get("state"),
                "evidence_name_pairs": candidate.get("evidence_name_pairs", []),
                "ofac_entities": review_entities,
                "conclusion": "review_required",
            }
        )

    reviews.sort(
        key=lambda item: (
            _clean(item.get("candidate_state")),
            _clean((item.get("owner_names") or [""])[0] if isinstance(item.get("owner_names"), list) else ""),
            _clean(item.get("owner_gem_entity_id")),
        )
    )

    return {
        "meta": {
            "schema": SCHEMA,
            "state": "review_required",
            "candidate_count": len(reviews),
            "interpretation": (
                "Identity-review detail only. Exact or legal-form name agreement does not "
                "by itself establish that a GEM owner and an OFAC list record are the same "
                "legal entity. No direct-list finding is produced by this step."
            ),
            "publication_state": "local review only; do not publish candidate detail yet",
        },
        "reviews": reviews,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Print all GIST-owner to OFAC review candidates with list/program/context "
            "evidence. This is identity review, not a sanctions finding."
        )
    )
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--ofac", type=Path, default=DEFAULT_OFAC)
    parser.add_argument("--gist", type=Path, default=DEFAULT_GIST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    candidate_payload = json.loads(args.candidates.read_text(encoding="utf-8"))
    ofac_payload = json.loads(args.ofac.read_text(encoding="utf-8"))
    gist_payload = json.loads(args.gist.read_text(encoding="utf-8"))

    review = build_review(candidate_payload, ofac_payload, gist_payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(review, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    reviews = review["reviews"]
    print(f"review candidates: {len(reviews)}")
    for index, item in enumerate(reviews, start=1):
        print()
        print(f"[{index}] GEM owner ID: {item['owner_gem_entity_id']}")
        print(f"    GEM owner names: {item['owner_names']}")
        print(f"    GIST plants: {item['plant_count']}")
        for plant in item["plants"]:
            print(
                "      - "
                f"{plant.get('plant_name')} | {plant.get('country_area')} | "
                f"{plant.get('plant_id')}"
            )
        print(f"    candidate type: {item['candidate_state']}")
        print("    evidence name pairs:")
        for pair in item["evidence_name_pairs"]:
            print(f"      {pair['owner_name']}  <->  {pair['source_name']}")
        print("    OFAC candidate entities:")
        for entity in item["ofac_entities"]:
            print(
                f"      {entity['entity_id']} | {entity['source_list']} | "
                f"UID {entity['ofac_uid']}"
            )
            print(f"        primary name: {entity['primary_name']}")
            print(f"        programmes: {entity['programmes']}")
            print(f"        countries: {entity['countries']}")
            print(f"        identifiers: {entity['identifiers']}")
            if entity["aliases"]:
                print(f"        aliases: {entity['aliases']}")
            if entity["addresses"]:
                print(f"        addresses: {entity['addresses']}")
        print("    conclusion: review_required")

    print()
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
