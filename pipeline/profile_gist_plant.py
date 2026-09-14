#!/usr/bin/env python3
"""Profile the reviewed GIST plant-level workbook without transforming it.

The profiler is a source-review tool. It verifies the pinned workbook identity,
reads only the three data worksheets needed for the draft contract and emits
quality/shape statistics. It does not write GEM records to the repository or
produce a publication dataset.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from pipeline.inspect_xlsx import read_sheet_records, sha256_file

EXPECTED_SHA256 = "A5768B59CD7E6CEC217692AE45EDA80EA70AAB1666AEF74332CC1B41DD5338EB"

PLANT_SHEET = "Plant data"
CAPACITY_SHEET = "Plant capacities and status"
PRODUCTION_SHEET = "Plant production"

PLANT_REQUIRED = [
    "GEM plant ID",
    "Plant name (English)",
    "Owner",
    "Owner GEM entity ID",
    "Parent (English)",
    "Parent GEM entity ID",
    "Country/area",
    "Region",
    "Coordinates",
    "Coordinate accuracy",
    "Main production equipment",
]

PLANT_CANDIDATE_FIELDS = [
    "Plant name (English)",
    "Owner",
    "Owner GEM entity ID",
    "Parent (English)",
    "Parent GEM entity ID",
    "Municipality",
    "Subnational unit",
    "Country/area",
    "Region",
    "Coordinates",
    "Coordinate accuracy",
    "Category steel product",
    "Steel products",
    "Steel sector end users",
    "Main production equipment",
    "GEM wiki page",
]

PLANT_DATE_FIELDS = [
    "Announced date",
    "Construction date",
    "Start date",
    "Pre-retirement announcement date",
    "Idled date",
    "Retired date",
]

CAPACITY_REQUIRED = [
    "GEM plant ID",
    "Main production equipment",
    "Status",
    "Start date",
    "Nominal crude steel capacity (ttpa)",
    "Nominal iron capacity (ttpa)",
]

CAPACITY_FIELDS = [
    "Nominal crude steel capacity (ttpa)",
    "Nominal BOF steel capacity (ttpa)",
    "Nominal EAF steel capacity (ttpa)",
    "Nominal IF steel capacity (ttpa)",
    "Other/unspecified steel capacity (ttpa)",
    "Nominal iron capacity (ttpa)",
    "Nominal BF capacity (ttpa)",
    "Nominal DRI capacity (ttpa)",
    "Other/unspecified iron capacity (ttpa)",
]

PRODUCTION_REQUIRED = ["GEM plant ID", "Type of production"]
PRODUCTION_YEARS = [str(year) for year in range(2019, 2026)]

PERCENT_TOKEN = re.compile(r"\[(\d+(?:\.\d+)?)%\]")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
YEAR_TEXT = re.compile(r"^\d{4}$")


def classify_source_value(value: Any) -> str:
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


def raw_date_pattern(value: Any) -> str:
    state = classify_source_value(value)
    if state in {"blank", "unknown", "N/A"}:
        return state
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        if float(value).is_integer() and 1800 <= int(value) <= 2200:
            return "numeric_year"
        if 20000 <= float(value) <= 80000:
            return "excel_serial_candidate"
        return "numeric_other"
    text = str(value).strip()
    if ISO_DATE.fullmatch(text):
        return "iso_date_text"
    if YEAR_TEXT.fullmatch(text):
        return "year_text"
    return "text_other"


def parse_coordinate_pair(value: Any) -> tuple[float, float] | None:
    if value is None:
        return None
    parts = [part.strip() for part in str(value).split(",")]
    if len(parts) != 2:
        return None
    try:
        latitude, longitude = float(parts[0]), float(parts[1])
    except ValueError:
        return None
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None
    return latitude, longitude


def source_state_counts(records: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    counter = Counter(classify_source_value(record.get(field)) for record in records)
    return dict(sorted(counter.items()))


def date_pattern_counts(records: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    counter = Counter(raw_date_pattern(record.get(field)) for record in records)
    return dict(sorted(counter.items()))


def top_counts(values: Iterable[Any], limit: int = 20) -> dict[str, int]:
    counter = Counter(str(value) for value in values if value is not None and str(value).strip())
    return dict(counter.most_common(limit))


def required_columns(records: list[dict[str, Any]], required: list[str]) -> dict[str, Any]:
    observed: set[str] = set()
    for record in records[: min(len(records), 100)]:
        observed.update(key for key in record if not key.startswith("__"))
    missing = [column for column in required if column not in observed]
    return {"missing": missing, "ok": not missing}


def key_profile(records: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [record.get(key) for record in records]
    non_blank = [value for value in values if value is not None and str(value).strip()]
    counts = Counter(str(value) for value in non_blank)
    duplicate_keys = sorted(key_value for key_value, count in counts.items() if count > 1)
    return {
        "rows": len(records),
        "non_blank_keys": len(non_blank),
        "unique_keys": len(counts),
        "duplicate_key_count": len(duplicate_keys),
        "duplicate_key_examples": duplicate_keys[:20],
    }


def rows_per_key_profile(records: list[dict[str, Any]], key: str) -> dict[str, Any]:
    counts = Counter(
        str(record.get(key))
        for record in records
        if record.get(key) is not None and str(record.get(key)).strip()
    )
    distribution = Counter(counts.values())
    return {
        "unique_keys": len(counts),
        "keys_with_multiple_rows": sum(1 for count in counts.values() if count > 1),
        "max_rows_per_key": max(counts.values(), default=0),
        "row_count_distribution": {str(k): v for k, v in sorted(distribution.items())},
    }


def profile_plant(records: list[dict[str, Any]]) -> dict[str, Any]:
    ids = key_profile(records, "GEM plant ID")

    coord_present = 0
    coord_parseable = 0
    coord_invalid_examples: list[dict[str, Any]] = []
    for record in records:
        value = record.get("Coordinates")
        if value is None or not str(value).strip():
            continue
        coord_present += 1
        if parse_coordinate_pair(value) is not None:
            coord_parseable += 1
        elif len(coord_invalid_examples) < 20:
            coord_invalid_examples.append(
                {"row": record.get("__row__"), "plant_id": record.get("GEM plant ID"), "value": value}
            )

    parent_rows = 0
    multi_share_rows = 0
    semicolon_parent_rows = 0
    for record in records:
        value = record.get("Parent (English)")
        if value is None or not str(value).strip():
            continue
        parent_rows += 1
        text = str(value)
        if len(PERCENT_TOKEN.findall(text)) > 1:
            multi_share_rows += 1
        if ";" in text:
            semicolon_parent_rows += 1

    return {
        "key": ids,
        "required_columns": required_columns(records, PLANT_REQUIRED),
        "field_states": {
            field: source_state_counts(records, field) for field in PLANT_CANDIDATE_FIELDS
        },
        "countries_areas": {
            "unique": len({str(r.get("Country/area")) for r in records if r.get("Country/area")}),
            "top": top_counts((r.get("Country/area") for r in records)),
        },
        "regions": top_counts((r.get("Region") for r in records), limit=50),
        "coordinates": {
            "present": coord_present,
            "parseable": coord_parseable,
            "invalid": coord_present - coord_parseable,
            "invalid_examples": coord_invalid_examples,
            "accuracy_values": top_counts((r.get("Coordinate accuracy") for r in records), limit=20),
        },
        "date_storage_patterns": {
            field: date_pattern_counts(records, field) for field in PLANT_DATE_FIELDS
        },
        "parent_field_patterns": {
            "rows_with_parent_value": parent_rows,
            "rows_with_multiple_percentage_tokens": multi_share_rows,
            "rows_with_semicolon": semicolon_parent_rows,
        },
    }


def profile_capacity(records: list[dict[str, Any]]) -> dict[str, Any]:
    statuses_by_plant: dict[str, set[str]] = defaultdict(set)
    signature_counts: Counter[tuple[Any, ...]] = Counter()
    for record in records:
        plant_id = record.get("GEM plant ID")
        status = record.get("Status")
        if plant_id is not None and status is not None:
            statuses_by_plant[str(plant_id)].add(str(status))
        signature = (
            plant_id,
            record.get("Main production equipment"),
            status,
            record.get("Start date"),
            *(record.get(field) for field in CAPACITY_FIELDS),
        )
        signature_counts[signature] += 1

    exact_duplicate_rows = sum(count - 1 for count in signature_counts.values() if count > 1)

    return {
        "rows": len(records),
        "required_columns": required_columns(records, CAPACITY_REQUIRED),
        "rows_per_plant": rows_per_key_profile(records, "GEM plant ID"),
        "status_values": top_counts((r.get("Status") for r in records), limit=50),
        "equipment_values": top_counts((r.get("Main production equipment") for r in records), limit=50),
        "plants_with_multiple_status_values": sum(
            1 for statuses in statuses_by_plant.values() if len(statuses) > 1
        ),
        "exact_duplicate_rows_beyond_first": exact_duplicate_rows,
        "capacity_value_states": {
            field: source_state_counts(records, field) for field in CAPACITY_FIELDS
        },
        "start_date_storage_patterns": date_pattern_counts(records, "Start date"),
    }


def profile_production(records: list[dict[str, Any]]) -> dict[str, Any]:
    types_by_plant: dict[str, set[str]] = defaultdict(set)
    pair_counts: Counter[tuple[str, str]] = Counter()
    for record in records:
        plant_id = record.get("GEM plant ID")
        production_type = record.get("Type of production")
        if plant_id is None or production_type is None:
            continue
        plant_id_text = str(plant_id)
        production_type_text = str(production_type)
        types_by_plant[plant_id_text].add(production_type_text)
        pair_counts[(plant_id_text, production_type_text)] += 1

    steel_routes = {
        "EAF steel production (ttpa)",
        "BOF steel production (ttpa)",
        "IF steel production (ttpa)",
        "Other/Unknown steel production (ttpa)",
    }
    iron_routes = {
        "BF iron production (ttpa)",
        "DRI iron production (ttpa)",
        "Other/Unknown iron production (ttpa)",
    }

    total_plus_route_steel = 0
    total_plus_route_iron = 0
    for types in types_by_plant.values():
        if "Crude steel production (ttpa)" in types and types.intersection(steel_routes):
            total_plus_route_steel += 1
        if "Iron production (ttpa)" in types and types.intersection(iron_routes):
            total_plus_route_iron += 1

    return {
        "rows": len(records),
        "required_columns": required_columns(records, PRODUCTION_REQUIRED + PRODUCTION_YEARS),
        "unique_plants": len(types_by_plant),
        "production_types": top_counts((r.get("Type of production") for r in records), limit=50),
        "duplicate_plant_type_rows_beyond_first": sum(
            count - 1 for count in pair_counts.values() if count > 1
        ),
        "plants_with_total_and_route_steel_rows": total_plus_route_steel,
        "plants_with_total_and_route_iron_rows": total_plus_route_iron,
        "year_value_states": {
            year: source_state_counts(records, year) for year in PRODUCTION_YEARS
        },
    }


def profile_workbook(path: Path) -> dict[str, Any]:
    actual_sha = sha256_file(path)
    if actual_sha != EXPECTED_SHA256:
        raise ValueError(
            "GIST plant workbook identity mismatch: "
            f"expected {EXPECTED_SHA256}, got {actual_sha}."
        )

    plant = read_sheet_records(path, PLANT_SHEET)
    capacity = read_sheet_records(path, CAPACITY_SHEET)
    production = read_sheet_records(path, PRODUCTION_SHEET)

    return {
        "file_name": path.name,
        "sha256": actual_sha,
        "plant": profile_plant(plant),
        "capacity_status": profile_capacity(capacity),
        "production": profile_production(production),
    }


def _print_section(title: str) -> None:
    print()
    print(title)
    print("=" * len(title))


def _print_json_block(label: str, value: Any) -> None:
    print(f"{label}: {json.dumps(value, ensure_ascii=False, sort_keys=True)}")


def print_text(report: dict[str, Any]) -> None:
    print(f"WORKBOOK: {report['file_name']}")
    print(f"SHA256: {report['sha256']}")

    plant = report["plant"]
    _print_section("PLANT DATA")
    _print_json_block("KEY", plant["key"])
    _print_json_block("REQUIRED_COLUMNS", plant["required_columns"])
    _print_json_block("COUNTRIES_AREAS", plant["countries_areas"])
    _print_json_block("REGIONS", plant["regions"])
    _print_json_block("COORDINATES", plant["coordinates"])
    _print_json_block("PARENT_FIELD_PATTERNS", plant["parent_field_patterns"])
    _print_json_block("DATE_STORAGE_PATTERNS", plant["date_storage_patterns"])
    print("FIELD_STATES:")
    for field, counts in plant["field_states"].items():
        _print_json_block(f"  {field}", counts)

    capacity = report["capacity_status"]
    _print_section("CAPACITY AND STATUS")
    print(f"ROWS: {capacity['rows']}")
    _print_json_block("REQUIRED_COLUMNS", capacity["required_columns"])
    _print_json_block("ROWS_PER_PLANT", capacity["rows_per_plant"])
    _print_json_block("STATUS_VALUES", capacity["status_values"])
    _print_json_block("EQUIPMENT_VALUES", capacity["equipment_values"])
    print(f"PLANTS_WITH_MULTIPLE_STATUS_VALUES: {capacity['plants_with_multiple_status_values']}")
    print(f"EXACT_DUPLICATE_ROWS_BEYOND_FIRST: {capacity['exact_duplicate_rows_beyond_first']}")
    _print_json_block("START_DATE_STORAGE_PATTERNS", capacity["start_date_storage_patterns"])
    print("CAPACITY_VALUE_STATES:")
    for field, counts in capacity["capacity_value_states"].items():
        _print_json_block(f"  {field}", counts)

    production = report["production"]
    _print_section("PRODUCTION")
    print(f"ROWS: {production['rows']}")
    _print_json_block("REQUIRED_COLUMNS", production["required_columns"])
    print(f"UNIQUE_PLANTS: {production['unique_plants']}")
    _print_json_block("PRODUCTION_TYPES", production["production_types"])
    print(
        "DUPLICATE_PLANT_TYPE_ROWS_BEYOND_FIRST: "
        f"{production['duplicate_plant_type_rows_beyond_first']}"
    )
    print(
        "PLANTS_WITH_TOTAL_AND_ROUTE_STEEL_ROWS: "
        f"{production['plants_with_total_and_route_steel_rows']}"
    )
    print(
        "PLANTS_WITH_TOTAL_AND_ROUTE_IRON_ROWS: "
        f"{production['plants_with_total_and_route_iron_rows']}"
    )
    _print_json_block("YEAR_VALUE_STATES", production["year_value_states"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile the pinned GIST plant-level workbook.")
    parser.add_argument("path", type=Path, help="Path to the reviewed GIST plant-level XLSX.")
    parser.add_argument("--json", action="store_true", help="Emit the full profile as JSON.")
    args = parser.parse_args()

    report = profile_workbook(args.path)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print_text(report)


if __name__ == "__main__":
    main()
