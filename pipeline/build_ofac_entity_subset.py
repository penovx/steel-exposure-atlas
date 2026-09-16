from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

DEFAULT_SDN = Path("tmp/source-packages/ofac/raw/sdn.xml")
DEFAULT_CONSOLIDATED = Path("tmp/source-packages/ofac/raw/consolidated.xml")
DEFAULT_OUTPUT = Path("tmp/source-packages/ofac/derived/ofac-sanctions-entities.v1.json")
SCHEMA = "steel-exposure-atlas/ofac-sanctions-entities-v1.0"
SOURCE = "ofac"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _direct_child_text(element: ET.Element, local_name: str) -> str:
    for child in element:
        if _local_name(child.tag) == local_name:
            return _clean(child.text)
    return ""


def _first_text(root: ET.Element, local_name: str) -> str | None:
    for element in root.iter():
        if _local_name(element.tag) == local_name:
            value = _clean(element.text)
            if value:
                return value
    return None


def _person_or_entity_name(element: ET.Element) -> str:
    first = _direct_child_text(element, "firstName")
    last = _direct_child_text(element, "lastName")
    return " ".join(part for part in (first, last) if part).strip()


def _iter_children(element: ET.Element, local_name: str):
    for child in element:
        if _local_name(child.tag) == local_name:
            yield child


def _parse_one(raw_bytes: bytes, *, source_list: str, source_id: str) -> dict[str, object]:
    try:
        root = ET.fromstring(raw_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"OFAC {source_list} source is not valid XML: {exc}") from exc

    publish_date = _first_text(root, "Publish_Date")
    type_counts: Counter[str] = Counter()
    entities: list[dict[str, object]] = []

    for entry in root.iter():
        if _local_name(entry.tag) != "sdnEntry":
            continue

        sdn_type = _direct_child_text(entry, "sdnType") or "<blank>"
        type_counts[sdn_type] += 1
        if sdn_type != "Entity":
            continue

        uid = _direct_child_text(entry, "uid")
        if not uid:
            raise ValueError(f"OFAC {source_list} Entity entry has no uid.")

        primary_name = _person_or_entity_name(entry)
        if not primary_name:
            raise ValueError(f"OFAC {source_list} Entity {uid} has no usable name.")

        aliases: list[dict[str, str]] = []
        names: list[str] = [primary_name]
        programs: set[str] = set()
        countries: set[str] = set()
        addresses: list[dict[str, str]] = []
        identifiers: list[dict[str, str]] = []

        for descendant in entry.iter():
            local = _local_name(descendant.tag)
            if local == "program":
                value = _clean(descendant.text)
                if value:
                    programs.add(value)
            elif local == "aka":
                alias_name = _person_or_entity_name(descendant)
                if alias_name:
                    aliases.append(
                        {
                            "name": alias_name,
                            "category": _direct_child_text(descendant, "category"),
                        }
                    )
                    names.append(alias_name)
            elif local == "address":
                address = {
                    key: _direct_child_text(descendant, key)
                    for key in ("address1", "address2", "address3", "city", "stateOrProvince", "postalCode", "country")
                }
                if address["country"]:
                    countries.add(address["country"])
                if any(address.values()):
                    addresses.append(address)
            elif local == "id":
                id_type = _direct_child_text(descendant, "idType")
                id_number = _direct_child_text(descendant, "idNumber")
                if id_number:
                    identifiers.append({"type": id_type, "value": id_number})

        ordered_names = list(dict.fromkeys(name for name in names if name))
        alias_keyed = {
            (item["name"], item["category"]): item
            for item in aliases
        }
        address_keyed = {
            tuple(sorted(item.items())): item
            for item in addresses
        }
        identifier_keyed = {
            (item["type"], item["value"]): item
            for item in identifiers
        }

        entities.append(
            {
                "source": SOURCE,
                "source_list": source_list,
                "source_id": source_id,
                "entity_type": "entity",
                "entity_id": f"{source_id}:{uid}",
                "ofac_uid": uid,
                "primary_name": primary_name,
                "names": ordered_names,
                "aliases": [alias_keyed[key] for key in sorted(alias_keyed)],
                "programmes": sorted(programs),
                "countries": sorted(countries),
                "addresses": [address_keyed[key] for key in sorted(address_keyed)],
                "identifiers": [identifier_keyed[key] for key in sorted(identifier_keyed)],
            }
        )

    return {
        "source_list": source_list,
        "source_id": source_id,
        "publish_date": publish_date,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest().upper(),
        "type_counts": dict(sorted(type_counts.items())),
        "entities": entities,
    }


def build_subset(sdn_bytes: bytes, consolidated_bytes: bytes) -> dict[str, object]:
    sdn = _parse_one(sdn_bytes, source_list="SDN", source_id="ofac-sdn")
    consolidated = _parse_one(
        consolidated_bytes,
        source_list="Consolidated Non-SDN",
        source_id="ofac-consolidated-non-sdn",
    )

    entities = [*sdn["entities"], *consolidated["entities"]]  # type: ignore[list-item]
    ids = [entity["entity_id"] for entity in entities if isinstance(entity, dict)]
    if len(ids) != len(set(ids)):
        raise ValueError("OFAC derived entity IDs are not unique.")

    return {
        "meta": {
            "schema": SCHEMA,
            "source": SOURCE,
            "publisher": "U.S. Department of the Treasury, Office of Foreign Assets Control",
            "licence": "CC0 1.0 Universal (official Data.gov catalogue metadata)",
            "scope": "Entity-only local derived subset; Individual, Vessel and Aircraft entries excluded from company candidate generation",
            "publication_state": "local review output; publication requires reviewed identity-resolution evidence and minimum-field transformation",
            "files": {
                "sdn": {
                    key: sdn[key]
                    for key in ("source_id", "source_list", "publish_date", "raw_sha256", "type_counts")
                },
                "consolidated_non_sdn": {
                    key: consolidated[key]
                    for key in ("source_id", "source_list", "publish_date", "raw_sha256", "type_counts")
                },
            },
            "counts": {
                "sdn_entities": len(sdn["entities"]),  # type: ignore[arg-type]
                "consolidated_non_sdn_entities": len(consolidated["entities"]),  # type: ignore[arg-type]
                "total_entities": len(entities),
            },
            "interpretation": "A direct list identity match is list evidence only. No direct match is not sanctions clearance, and Consolidated Non-SDN restrictions are not equivalent to SDN blocking.",
        },
        "entities": entities,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a local Entity-only OFAC subset from pinned SDN and Consolidated basic XML snapshots."
    )
    parser.add_argument("--sdn", type=Path, default=DEFAULT_SDN)
    parser.add_argument("--consolidated", type=Path, default=DEFAULT_CONSOLIDATED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    payload = build_subset(args.sdn.read_bytes(), args.consolidated.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    meta = payload["meta"]
    counts = meta["counts"]
    files = meta["files"]
    print(f"SDN publish date: {files['sdn']['publish_date']}")
    print(f"SDN sha256: {files['sdn']['raw_sha256']}")
    print(f"SDN Entity entries: {counts['sdn_entities']}")
    print(f"Consolidated publish date: {files['consolidated_non_sdn']['publish_date']}")
    print(f"Consolidated sha256: {files['consolidated_non_sdn']['raw_sha256']}")
    print(f"Consolidated Entity entries: {counts['consolidated_non_sdn_entities']}")
    print(f"total Entity entries: {counts['total_entities']}")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
