from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_GIST = Path("public/data/gist-plants.v1.json")
DEFAULT_SANCTIONS = Path("tmp/source-packages/ofac/derived/ofac-sanctions-entities.v1.json")
DEFAULT_REGISTRY = Path("config/reviewed-entity-links.v1.json")
DEFAULT_OUTPUT = Path(
    "tmp/source-packages/ofac/derived/gist-owner-ofac-reviewed-matches.v1.json"
)
SCHEMA = "steel-exposure-atlas/gist-owner-ofac-reviewed-matches-v1.0"


def _clean(value: object) -> str:
    return str(value or "").strip()


def _snapshot_hashes(meta: dict[str, object]) -> dict[str, str]:
    files = meta.get("files")
    if not isinstance(files, dict):
        raise ValueError("OFAC sanctions subset has no files metadata.")

    result: dict[str, str] = {}
    mapping = {
        "SDN": "sdn",
        "Consolidated Non-SDN": "consolidated_non_sdn",
    }
    for source_list, key in mapping.items():
        item = files.get(key)
        if not isinstance(item, dict):
            raise ValueError(f"OFAC sanctions subset has no metadata for {source_list}.")
        source_hash = _clean(item.get("raw_sha256"))
        if not source_hash:
            raise ValueError(f"OFAC sanctions subset has no SHA-256 for {source_list}.")
        result[source_list] = source_hash
    return result


def build_reviewed_matches(
    gist: dict[str, object],
    sanctions: dict[str, object],
    registry: dict[str, object],
) -> dict[str, object]:
    plants = gist.get("plants")
    entities = sanctions.get("entities")
    links = registry.get("links")
    if not isinstance(plants, list):
        raise ValueError("GIST payload has no plants list.")
    if not isinstance(entities, list):
        raise ValueError("OFAC sanctions subset has no entities list.")
    if not isinstance(links, list):
        raise ValueError("Reviewed entity-link registry has no links list.")

    owner_ids = {
        _clean(plant.get("owner_gem_entity_id"))
        for plant in plants
        if isinstance(plant, dict) and _clean(plant.get("owner_gem_entity_id"))
    }
    entity_map = {
        _clean(entity.get("entity_id")): entity
        for entity in entities
        if isinstance(entity, dict) and _clean(entity.get("entity_id"))
    }

    sanctions_meta = sanctions.get("meta")
    if not isinstance(sanctions_meta, dict):
        raise ValueError("OFAC sanctions subset has no meta object.")
    snapshot_hashes = _snapshot_hashes(sanctions_meta)

    matches: list[dict[str, object]] = []
    seen_resolution_ids: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()

    for link in links:
        if not isinstance(link, dict):
            raise ValueError("Reviewed entity-link entry must be an object.")

        resolution_id = _clean(link.get("resolution_id"))
        if not resolution_id:
            raise ValueError("Reviewed entity link has no resolution_id.")
        if resolution_id in seen_resolution_ids:
            raise ValueError(f"Duplicate resolution_id: {resolution_id}")
        seen_resolution_ids.add(resolution_id)

        left = link.get("left")
        right = link.get("right")
        if not isinstance(left, dict) or not isinstance(right, dict):
            raise ValueError(f"Resolution {resolution_id} has invalid source sides.")

        if right.get("source") != "ofac":
            continue
        if link.get("decision") != "same_legal_entity":
            continue
        if link.get("downstream_state") != "direct_list_match":
            raise ValueError(
                f"Same-entity OFAC resolution {resolution_id} must downstream to direct_list_match."
            )
        if left.get("source") != "gem":
            raise ValueError(f"Resolution {resolution_id} left source is not gem.")

        owner_id = _clean(left.get("entity_id"))
        entity_id = _clean(right.get("entity_id"))
        if owner_id not in owner_ids:
            raise ValueError(
                f"Resolution {resolution_id} references unknown GEM owner {owner_id!r}."
            )
        entity = entity_map.get(entity_id)
        if entity is None:
            raise ValueError(
                f"Resolution {resolution_id} references unknown OFAC entity {entity_id!r}."
            )

        source_list = _clean(entity.get("source_list"))
        if source_list not in snapshot_hashes:
            raise ValueError(
                f"OFAC entity {entity_id} has unexpected source list {source_list!r}."
            )
        if _clean(right.get("source_list")) != source_list:
            raise ValueError(
                f"Resolution {resolution_id} source list does not match OFAC entity."
            )
        if _clean(right.get("ofac_uid")) != _clean(entity.get("ofac_uid")):
            raise ValueError(
                f"Resolution {resolution_id} OFAC UID does not match source entity."
            )
        if _clean(right.get("snapshot_sha256")) != snapshot_hashes[source_list]:
            raise ValueError(
                f"Resolution {resolution_id} snapshot hash does not match local {source_list} subset."
            )

        pair = (owner_id, entity_id)
        if pair in seen_pairs:
            raise ValueError(f"Duplicate reviewed GEM/OFAC pair: {owner_id} / {entity_id}")
        seen_pairs.add(pair)

        programmes = entity.get("programmes")
        if not isinstance(programmes, list):
            programmes = []

        matches.append(
            {
                "company_source": "gem",
                "company_id": owner_id,
                "source": "ofac",
                "state": "direct_list_match",
                "matched_entity_id": entity_id,
                "source_list": source_list,
                "ofac_uid": _clean(entity.get("ofac_uid")),
                "programmes": sorted({_clean(value) for value in programmes if _clean(value)}),
                "resolution_id": resolution_id,
                "reviewed_at": _clean(link.get("reviewed_at")),
                "resolution_method": _clean(link.get("resolution_method")),
            }
        )

    matches.sort(key=lambda item: (str(item["company_id"]), str(item["matched_entity_id"])))

    return {
        "meta": {
            "schema": SCHEMA,
            "source": "ofac",
            "source_snapshot_sha256": snapshot_hashes,
            "review_registry_schema": registry.get("schema"),
            "direct_company_matches": len(matches),
            "scope": (
                "Reviewed company-identity direct-list matches only. Negative screening "
                "results and unresolved candidates are intentionally not exported."
            ),
            "interpretation": (
                "A match attaches to the resolved GIST company identity. It is not a "
                "separate plant-level sanctions finding. SDN and Consolidated Non-SDN "
                "records retain their source-list/program context."
            ),
        },
        "matches": matches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a local minimal package of reviewed GIST-owner to OFAC direct-list matches."
    )
    parser.add_argument("--gist", type=Path, default=DEFAULT_GIST)
    parser.add_argument("--sanctions", type=Path, default=DEFAULT_SANCTIONS)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    gist = json.loads(args.gist.read_text(encoding="utf-8"))
    sanctions = json.loads(args.sanctions.read_text(encoding="utf-8"))
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    payload = build_reviewed_matches(gist, sanctions, registry)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"OFAC snapshot SHA-256: {payload['meta']['source_snapshot_sha256']}")
    print(f"reviewed direct company matches: {payload['meta']['direct_company_matches']}")
    for item in payload["matches"]:
        print(
            f"  {item['company_id']} -> {item['matched_entity_id']} "
            f"[{item['source_list']}] via {item['resolution_id']}"
        )
    print("negative results exported: 0")
    print("plant-level sanctions findings exported: 0")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
