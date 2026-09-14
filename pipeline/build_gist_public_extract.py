#!/usr/bin/env python3
"""Build the reviewed GIST v1.0 public extract deterministically.

The builder reads the pinned Global Iron and Steel Tracker June 2026 (V1)
plant-level workbook, applies the rules in docs/data-contracts/gist-plant-v1.0.md,
and writes a derived JSON file to a caller-selected path.

It never modifies the source workbook. The default output is under tmp/, which is
ignored by Git, so validation happens before any file is admitted to public/data/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.inspect_xlsx import read_sheet_records, sha256_file

EXPECTED_SHA256 = "A5768B59CD7E6CEC217692AE45EDA80EA70AAB1666AEF74332CC1B41DD5338EB"
EXPECTED_PLANT_COUNT = 1293
EXPECTED_CAPACITY_ROW_COUNT = 1845
SOURCE_RELEASE = "June 2026 (V1)"
RETRIEVED_AT = "2026-09-14"
CONTRACT = "docs/data-contracts/gist-plant-v1.0.md"

PLANT_SHEET = "Plant data"
CAPACITY_SHEET = "Plant capacities and status"
PRODUCTION_SHEET = "Plant production"
PRODUCTION_YEARS = [str(year) for year in range(2019, 2025)]

ALLOWED_STATUSES = {
    "announced",
    "construction",
    "operating",
    "operating pre-retirement",
    "mothballed",
    "mothballed pre-retirement",
    "cancelled",
    "retired",
}

STATUS_BUCKETS = {
    "operating": {"operating", "operating pre-retirement"},
    "development": {"announced", "construction"},
    "mothballed": {"mothballed", "mothballed pre-retirement"},
    "closed_or_cancelled": {"retired", "cancelled"},
}

CAPACITY_FIELDS = {
    "crude_steel": "Nominal crude steel capacity (ttpa)",
    "bof_steel": "Nominal BOF steel capacity (ttpa)",
    "eaf_steel": "Nominal EAF steel capacity (ttpa)",
    "if_steel": "Nominal IF steel capacity (ttpa)",
    "other_steel": "Other/unspecified steel capacity (ttpa)",
    "iron": "Nominal iron capacity (ttpa)",
    "bf_iron": "Nominal BF capacity (ttpa)",
    "dri_iron": "Nominal DRI capacity (ttpa)",
    "other_iron": "Other/unspecified iron capacity (ttpa)",
}

STEEL_ROUTE_FIELDS = ["bof_steel", "eaf_steel", "if_steel", "other_steel"]
IRON_ROUTE_FIELDS = ["bf_iron", "dri_iron", "other_iron"]

TOTAL_PRODUCTION_TYPES = {
    "crude_steel_ttpa": "Crude steel production (ttpa)",
    "iron_ttpa": "Iron production (ttpa)",
}


def source_state(value: Any) -> str:
    if value is None or value == "":
        return "blank"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "numeric"
    text = str(value).strip()
    if not text:
        return "blank"
    lowered = text.casefold()
    if lowered == "unknown":
        return "unknown"
    if lowered == "n/a":
        return "N/A"
    if text == ">0":
        return ">0"
    return "text"


def value_object(value: Any) -> dict[str, Any]:
    state = source_state(value)
    if state == "numeric":
        return {"state": "numeric", "value_ttpa": value}
    if state not in {"unknown", "N/A", ">0", "blank"}:
        raise ValueError(f"Unexpected numeric-field source state {state!r} for value {value!r}")
    return {"state": state, "value_ttpa": None}


def list_object(value: Any, delimiter: str) -> dict[str, Any]:
    state = source_state(value)
    if state in {"unknown", "N/A", "blank"}:
        return {"state": state, "values": []}
    if state != "text":
        raise ValueError(f"Unexpected list-field source state {state!r} for value {value!r}")
    values = [part.strip() for part in str(value).split(delimiter) if part.strip()]
    return {"state": "text", "values": values}


def parse_coordinates(value: Any) -> tuple[float, float]:
    parts = [part.strip() for part in str(value).split(",")]
    if len(parts) != 2:
        raise ValueError(f"Malformed coordinate pair: {value!r}")
    latitude, longitude = float(parts[0]), float(parts[1])
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError(f"Coordinate out of range: {value!r}")
    return latitude, longitude


def _capacity_tranche(record: dict[str, Any]) -> dict[str, Any]:
    status = str(record.get("Status", "")).strip()
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Unexpected capacity status {status!r} on row {record.get('__row__')}")
    equipment = list_object(record.get("Main production equipment"), ";")
    tranche: dict[str, Any] = {
        "status": status,
        "equipment": equipment,
    }
    for public_name, source_name in CAPACITY_FIELDS.items():
        tranche[f"{public_name}_capacity_ttpa"] = value_object(record.get(source_name))
    return tranche


def _numeric_sum(values: Iterable[dict[str, Any]]) -> dict[str, Any]:
    known_sum = 0.0
    has_positive = False
    has_unknown = False
    contributing_rows = 0
    numeric_rows = 0

    for item in values:
        state = item["state"]
        if state == "N/A":
            continue
        contributing_rows += 1
        if state == "numeric":
            known_sum += float(item["value_ttpa"])
            numeric_rows += 1
        elif state == ">0":
            has_positive = True
        elif state in {"unknown", "blank"}:
            has_unknown = True
        else:
            raise ValueError(f"Unexpected capacity state {state!r}")

    if known_sum.is_integer():
        normalized_sum: int | float = int(known_sum)
    else:
        normalized_sum = known_sum

    return {
        "known_numeric_sum_ttpa": normalized_sum,
        "has_unquantified_positive": has_positive,
        "has_unknown": has_unknown,
        "contributing_rows": contributing_rows,
        "numeric_rows": numeric_rows,
        "is_exact": not has_positive and not has_unknown,
    }


def _capacity_summary(tranches: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for bucket, statuses in STATUS_BUCKETS.items():
        bucket_rows = [row for row in tranches if row["status"] in statuses]
        summary[bucket] = {
            "source_statuses": sorted({row["status"] for row in bucket_rows}),
            "tranche_count": len(bucket_rows),
            "crude_steel_capacity": _numeric_sum(
                row["crude_steel_capacity_ttpa"] for row in bucket_rows
            ),
            "iron_capacity": _numeric_sum(row["iron_capacity_ttpa"] for row in bucket_rows),
        }
    return summary


def _check_capacity_total_routes(tranche: dict[str, Any], total_key: str, route_keys: list[str]) -> str:
    total = tranche[total_key]
    routes = [tranche[key] for key in route_keys]
    if total["state"] != "numeric":
        return "not_comparable"
    if any(route["state"] not in {"numeric", "N/A"} for route in routes):
        return "not_comparable"
    route_sum = sum(float(route["value_ttpa"]) for route in routes if route["state"] == "numeric")
    if route_sum != float(total["value_ttpa"]):
        raise ValueError(
            f"Capacity total/route mismatch for {total_key}: total={total['value_ttpa']}, route_sum={route_sum}"
        )
    return "match"


def _merge_duplicate_year_values(values: list[Any]) -> tuple[dict[str, Any], bool]:
    if not values:
        return {"state": "blank", "value_ttpa": None}, False

    normalized = [value_object(value) for value in values]
    signatures = {(item["state"], item["value_ttpa"]) for item in normalized}
    if len(signatures) == 1:
        return normalized[0], False

    numeric_values = {item["value_ttpa"] for item in normalized if item["state"] == "numeric"}
    non_numeric_states = {item["state"] for item in normalized if item["state"] != "numeric"}

    if len(numeric_values) == 1 and non_numeric_states.issubset({"unknown", "blank"}):
        return {"state": "numeric", "value_ttpa": next(iter(numeric_values))}, False

    if not numeric_values and {item["state"] for item in normalized}.issubset({"unknown", "blank"}):
        state = "unknown" if any(item["state"] == "unknown" for item in normalized) else "blank"
        return {"state": state, "value_ttpa": None}, False

    return {"state": "conflict", "value_ttpa": None}, True


def _production_series(records: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    total_type_values = set(TOTAL_PRODUCTION_TYPES.values())
    for record in records:
        plant_id = str(record.get("GEM plant ID", "")).strip()
        production_type = str(record.get("Type of production", "")).strip()
        if not plant_id or production_type not in total_type_values:
            continue
        grouped[(plant_id, production_type)].append(record)

    per_plant: dict[str, dict[str, Any]] = defaultdict(dict)
    conflicts: list[dict[str, Any]] = []
    reverse_type = {source: public for public, source in TOTAL_PRODUCTION_TYPES.items()}

    for (plant_id, production_type), group in sorted(grouped.items()):
        series: dict[str, Any] = {}
        for year in PRODUCTION_YEARS:
            values = [record.get(year) for record in group]
            merged, conflict = _merge_duplicate_year_values(values)
            series[year] = merged
            if conflict:
                conflicts.append(
                    {
                        "plant_id": plant_id,
                        "production_type": production_type,
                        "year": year,
                        "source_rows": [record.get("__row__") for record in group],
                    }
                )
        per_plant[plant_id][reverse_type[production_type]] = series

    return dict(per_plant), conflicts


def _coverage(production: dict[str, dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for public_type in TOTAL_PRODUCTION_TYPES:
        by_year: dict[str, Any] = {}
        plants_with_series = [plant_id for plant_id, payload in production.items() if public_type in payload]
        for year in PRODUCTION_YEARS:
            numeric = 0
            unknown = 0
            not_applicable = 0
            positive_unquantified = 0
            blank = 0
            conflict = 0
            for plant_id in plants_with_series:
                state = production[plant_id][public_type][year]["state"]
                if state == "numeric":
                    numeric += 1
                elif state == "unknown":
                    unknown += 1
                elif state == "N/A":
                    not_applicable += 1
                elif state == ">0":
                    positive_unquantified += 1
                elif state == "blank":
                    blank += 1
                elif state == "conflict":
                    conflict += 1
            by_year[year] = {
                "plants_with_total_series": len(plants_with_series),
                "numeric": numeric,
                "unknown": unknown,
                "N/A": not_applicable,
                ">0": positive_unquantified,
                "blank": blank,
                "conflict": conflict,
            }
        result[public_type] = by_year
    return result


def _plant_object(
    record: dict[str, Any],
    tranches: list[dict[str, Any]],
    production: dict[str, Any] | None,
) -> dict[str, Any]:
    plant_id = str(record["GEM plant ID"])
    latitude, longitude = parse_coordinates(record.get("Coordinates"))
    coordinate_accuracy = str(record.get("Coordinate accuracy", "")).strip()
    if coordinate_accuracy not in {"exact", "approximate"}:
        raise ValueError(f"Unexpected coordinate accuracy {coordinate_accuracy!r} for {plant_id}")

    equipment = list_object(record.get("Main production equipment"), ";")
    product_category = list_object(record.get("Category steel product"), ",")
    steel_products = list_object(record.get("Steel products"), ",")
    end_user_sectors = list_object(record.get("Steel sector end users"), ",")

    return {
        "plant_id": plant_id,
        "plant_name": record.get("Plant name (English)"),
        "owner_name": record.get("Owner"),
        "owner_gem_entity_id": record.get("Owner GEM entity ID"),
        "parent_display": record.get("Parent (English)"),
        "municipality": record.get("Municipality"),
        "subnational_unit": record.get("Subnational unit"),
        "country_area": record.get("Country/area"),
        "region": record.get("Region"),
        "latitude": latitude,
        "longitude": longitude,
        "coordinate_accuracy": coordinate_accuracy,
        "product_category": product_category,
        "steel_products": steel_products,
        "end_user_sectors": end_user_sectors,
        "main_production_equipment": equipment,
        "wiki_url": record.get("GEM wiki page"),
        "capacity": {
            "tranches": tranches,
            "summary": _capacity_summary(tranches),
        },
        "production": {
            "crude_steel_ttpa": (production or {}).get("crude_steel_ttpa"),
            "iron_ttpa": (production or {}).get("iron_ttpa"),
        },
    }



def _production_contains_year_key(
    plants: list[dict[str, Any]],
    year: str,
) -> bool:
    return any(
        year in series
        for plant in plants
        for series in (plant.get("production") or {}).values()
        if isinstance(series, dict)
    )


def build_extract(
    plant_records: list[dict[str, Any]],
    capacity_records: list[dict[str, Any]],
    production_records: list[dict[str, Any]],
    *,
    strict_release_assertions: bool = True,
) -> dict[str, Any]:
    plant_ids = [str(record.get("GEM plant ID", "")).strip() for record in plant_records]
    if any(not plant_id for plant_id in plant_ids):
        raise ValueError("Plant table contains a blank GEM plant ID.")
    if len(set(plant_ids)) != len(plant_ids):
        raise ValueError("Plant table contains duplicate GEM plant IDs.")

    if strict_release_assertions and len(plant_records) != EXPECTED_PLANT_COUNT:
        raise ValueError(f"Expected {EXPECTED_PLANT_COUNT} plant rows, found {len(plant_records)}.")
    if strict_release_assertions and len(capacity_records) != EXPECTED_CAPACITY_ROW_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_CAPACITY_ROW_COUNT} capacity rows, found {len(capacity_records)}."
        )

    capacity_by_plant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_plant_status: set[tuple[str, str]] = set()
    capacity_checks = {"steel_match": 0, "steel_not_comparable": 0, "iron_match": 0, "iron_not_comparable": 0}

    for record in capacity_records:
        plant_id = str(record.get("GEM plant ID", "")).strip()
        if plant_id not in set(plant_ids):
            raise ValueError(f"Capacity row references unknown plant ID {plant_id!r}")
        status = str(record.get("Status", "")).strip()
        key = (plant_id, status)
        if key in seen_plant_status:
            raise ValueError(f"Repeated plant/status pair: {plant_id} / {status}")
        seen_plant_status.add(key)

        tranche = _capacity_tranche(record)
        steel_check = _check_capacity_total_routes(
            tranche,
            "crude_steel_capacity_ttpa",
            [f"{name}_capacity_ttpa" for name in STEEL_ROUTE_FIELDS],
        )
        iron_check = _check_capacity_total_routes(
            tranche,
            "iron_capacity_ttpa",
            [f"{name}_capacity_ttpa" for name in IRON_ROUTE_FIELDS],
        )
        capacity_checks[f"steel_{steel_check}"] += 1
        capacity_checks[f"iron_{iron_check}"] += 1
        capacity_by_plant[plant_id].append(tranche)

    for plant_id in capacity_by_plant:
        capacity_by_plant[plant_id].sort(
            key=lambda item: (item["status"], tuple(item["equipment"]["values"]))
        )

    production_by_plant, production_conflicts = _production_series(production_records)
    if production_conflicts:
        raise ValueError(
            "Unresolved total-production duplicate conflicts remain: "
            + json.dumps(production_conflicts[:10], ensure_ascii=False, sort_keys=True)
        )

    plants = [
        _plant_object(
            record,
            capacity_by_plant[str(record["GEM plant ID"])],
            production_by_plant.get(str(record["GEM plant ID"])),
        )
        for record in sorted(plant_records, key=lambda row: str(row["GEM plant ID"]))
    ]

    if _production_contains_year_key(plants, "2025"):
        raise ValueError("2025 production leaked into the v1.0 public extract.")

    exact_coordinates = sum(1 for plant in plants if plant["coordinate_accuracy"] == "exact")
    approximate_coordinates = len(plants) - exact_coordinates

    return {
        "meta": {
            "schema": "steel-exposure-atlas/gist-plant-v1.0",
            "source": "Global Energy Monitor — Global Iron and Steel Tracker",
            "source_release": SOURCE_RELEASE,
            "source_sha256": EXPECTED_SHA256,
            "retrieved_at": RETRIEVED_AT,
            "contract": CONTRACT,
            "licence": "CC BY 4.0",
            "attribution": "Global Energy Monitor, Global Iron and Steel Tracker, June 2026 (V1) release.",
            "transformation_note": "Transformed extract produced by Steel Exposure Atlas; Global Energy Monitor does not endorse this project or its derived interpretations.",
            "production_years": PRODUCTION_YEARS,
            "counts": {
                "plants": len(plants),
                "capacity_status_tranches": len(capacity_records),
                "coordinate_exact": exact_coordinates,
                "coordinate_approximate": approximate_coordinates,
            },
            "validation": {
                "capacity_total_route_checks": capacity_checks,
                "unresolved_total_production_conflicts": len(production_conflicts),
                "production_coverage": _coverage(production_by_plant),
            },
        },
        "plants": plants,
    }


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return text.encode("utf-8")


def build_from_workbook(path: Path) -> dict[str, Any]:
    actual_sha = sha256_file(path)
    if actual_sha != EXPECTED_SHA256:
        raise ValueError(
            f"GIST workbook identity mismatch: expected {EXPECTED_SHA256}, got {actual_sha}."
        )
    plant = read_sheet_records(path, PLANT_SHEET)
    capacity = read_sheet_records(path, CAPACITY_SHEET)
    production = read_sheet_records(path, PRODUCTION_SHEET)
    return build_extract(plant, capacity, production, strict_release_assertions=True)


def write_extract(path: Path, output: Path) -> tuple[Path, str, int]:
    payload = build_from_workbook(path)
    encoded = canonical_json_bytes(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded)
    digest = hashlib.sha256(encoded).hexdigest().upper()
    return output, digest, len(encoded)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the reviewed GIST public extract.")
    parser.add_argument("path", type=Path, help="Path to the pinned GIST plant-level XLSX.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tmp/gist-plants.v1.json"),
        help="Output path. Defaults to ignored tmp/gist-plants.v1.json for validation.",
    )
    args = parser.parse_args()

    output, digest, size = write_extract(args.path, args.output)
    print(f"WROTE: {output}")
    print(f"SIZE_BYTES: {size}")
    print(f"SHA256: {digest}")
    print(f"PLANTS: {EXPECTED_PLANT_COUNT}")
    print(f"CAPACITY_STATUS_TRANCHES: {EXPECTED_CAPACITY_ROW_COUNT}")
    print("PUBLICATION_STATUS: local validation output only; do not publish until release gate is reviewed")


if __name__ == "__main__":
    main()
