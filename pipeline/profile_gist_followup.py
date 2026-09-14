#!/usr/bin/env python3
"""Run focused follow-up checks on the pinned GIST plant workbook.

This script exists because the first full profile exposed modelling questions that
must be resolved before ingestion: repeated plant/status rows, total-vs-route
capacity semantics, duplicate plant/production-type rows, observed production type
labels that differ from the metadata wording, and mixed raw date representations.
It is read-only and does not emit a publication dataset.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pipeline.inspect_xlsx import read_sheet_records, sha256_file
from pipeline.profile_gist_plant import classify_source_value, raw_date_pattern

EXPECTED_SHA256 = "A5768B59CD7E6CEC217692AE45EDA80EA70AAB1666AEF74332CC1B41DD5338EB"

PLANT_SHEET = "Plant data"
CAPACITY_SHEET = "Plant capacities and status"
PRODUCTION_SHEET = "Plant production"
YEARS = [str(year) for year in range(2019, 2026)]

STEEL_CAPACITY_ROUTES = [
    "Nominal BOF steel capacity (ttpa)",
    "Nominal EAF steel capacity (ttpa)",
    "Nominal IF steel capacity (ttpa)",
    "Other/unspecified steel capacity (ttpa)",
]
IRON_CAPACITY_ROUTES = [
    "Nominal BF capacity (ttpa)",
    "Nominal DRI capacity (ttpa)",
    "Other/unspecified iron capacity (ttpa)",
]

# Actual labels observed in the June 2026 V1 workbook. Keep metadata aliases too so
# future releases do not silently change the semantics of this check.
STEEL_PRODUCTION_ROUTES = {
    "EAF steel production (ttpa)",
    "BOF steel production (ttpa)",
    "IF steel production (ttpa)",
    "OHF steel production (ttpa)",
    "Other/Unknown steel production (ttpa)",
}
IRON_PRODUCTION_ROUTES = {
    "BF production (ttpa)",
    "DRI production (ttpa)",
    "BF iron production (ttpa)",
    "DRI iron production (ttpa)",
    "Other/Unknown iron production (ttpa)",
}

PLANT_DATE_FIELDS = [
    "Announced date",
    "Construction date",
    "Start date",
    "Pre-retirement announcement date",
    "Idled date",
    "Retired date",
]


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _number_or_zero(value: Any) -> float | None:
    """Return numeric values, treat explicit N/A as zero, reject uncertainty states."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip().casefold() == "n/a":
        return 0.0
    return None


def _reconcile_row_total(
    record: dict[str, Any], total_field: str, route_fields: list[str]
) -> tuple[str, float | None, float | None]:
    total = _number_or_zero(record.get(total_field))
    if total is None:
        return "not_comparable", None, None
    route_values = [_number_or_zero(record.get(field)) for field in route_fields]
    if any(value is None for value in route_values):
        return "not_comparable", total, None
    route_sum = sum(value or 0.0 for value in route_values)
    if abs(total - route_sum) <= 1e-9:
        return "match", total, route_sum
    return "mismatch", total, route_sum


def capacity_followup(records: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        plant = str(record.get("GEM plant ID", ""))
        status = str(record.get("Status", ""))
        groups[(plant, status)].append(record)

    repeated_groups = [
        (key, rows) for key, rows in groups.items() if key[0] and key[1] and len(rows) > 1
    ]
    repeated_groups.sort(key=lambda item: (-len(item[1]), item[0]))

    repeated_examples = []
    for (plant, status), rows in repeated_groups[:20]:
        repeated_examples.append(
            {
                "plant_id": plant,
                "status": status,
                "rows": [
                    {
                        "source_row": row.get("__row__"),
                        "equipment": row.get("Main production equipment"),
                        "start_date": row.get("Start date"),
                        "crude_capacity": row.get("Nominal crude steel capacity (ttpa)"),
                        "iron_capacity": row.get("Nominal iron capacity (ttpa)"),
                    }
                    for row in rows
                ],
            }
        )

    def reconciliation(total_field: str, route_fields: list[str]) -> dict[str, Any]:
        counts = Counter()
        mismatches = []
        for record in records:
            result, total, route_sum = _reconcile_row_total(record, total_field, route_fields)
            counts[result] += 1
            if result == "mismatch" and len(mismatches) < 20:
                mismatches.append(
                    {
                        "source_row": record.get("__row__"),
                        "plant_id": record.get("GEM plant ID"),
                        "status": record.get("Status"),
                        "equipment": record.get("Main production equipment"),
                        "total": total,
                        "route_sum": route_sum,
                    }
                )
        return {"counts": dict(sorted(counts.items())), "mismatch_examples": mismatches}

    current_statuses = {"operating", "operating pre-retirement"}
    current_rows_by_plant: Counter[str] = Counter(
        str(record.get("GEM plant ID"))
        for record in records
        if record.get("Status") in current_statuses and record.get("GEM plant ID")
    )

    return {
        "plant_status_group_count": len(groups),
        "repeated_plant_status_groups": len(repeated_groups),
        "max_rows_in_one_plant_status_group": max((len(rows) for _, rows in repeated_groups), default=1),
        "repeated_plant_status_examples": repeated_examples,
        "plants_with_multiple_current_status_rows": sum(
            1 for count in current_rows_by_plant.values() if count > 1
        ),
        "steel_total_vs_routes": reconciliation(
            "Nominal crude steel capacity (ttpa)", STEEL_CAPACITY_ROUTES
        ),
        "iron_total_vs_routes": reconciliation(
            "Nominal iron capacity (ttpa)", IRON_CAPACITY_ROUTES
        ),
    }


def _series_signature(record: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(record.get(year) for year in YEARS)


def _production_total_route_reconciliation(
    records: list[dict[str, Any]], total_type: str, route_types: set[str]
) -> dict[str, Any]:
    by_plant_type: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        plant = record.get("GEM plant ID")
        kind = record.get("Type of production")
        if plant is not None and kind is not None:
            by_plant_type[(str(plant), str(kind))].append(record)

    plants = sorted({plant for plant, _ in by_plant_type})
    counts = Counter()
    mismatches = []
    for plant in plants:
        total_rows = by_plant_type.get((plant, total_type), [])
        if len(total_rows) != 1:
            continue
        route_rows = [
            rows[0]
            for route in route_types
            if len((rows := by_plant_type.get((plant, route), []))) == 1
        ]
        if not route_rows:
            continue
        for year in YEARS:
            total = _number_or_zero(total_rows[0].get(year))
            if total is None:
                counts["not_comparable"] += 1
                continue
            route_values = [_number_or_zero(row.get(year)) for row in route_rows]
            if any(value is None for value in route_values):
                counts["not_comparable"] += 1
                continue
            route_sum = sum(value or 0.0 for value in route_values)
            if abs(total - route_sum) <= 1e-9:
                counts["match"] += 1
            else:
                counts["mismatch"] += 1
                if len(mismatches) < 20:
                    mismatches.append(
                        {
                            "plant_id": plant,
                            "year": year,
                            "total": total,
                            "route_sum": route_sum,
                        }
                    )
    return {"counts": dict(sorted(counts.items())), "mismatch_examples": mismatches}


def production_followup(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    types_by_plant: dict[str, set[str]] = defaultdict(set)
    observed_types = Counter()
    for record in records:
        plant = record.get("GEM plant ID")
        kind = record.get("Type of production")
        if plant is None or kind is None:
            continue
        plant_text, kind_text = str(plant), str(kind)
        by_pair[(plant_text, kind_text)].append(record)
        types_by_plant[plant_text].add(kind_text)
        observed_types[kind_text] += 1

    duplicate_groups = [(key, rows) for key, rows in by_pair.items() if len(rows) > 1]
    duplicate_groups.sort(key=lambda item: (-len(item[1]), item[0]))
    duplicate_examples = []
    identical_duplicate_groups = 0
    differing_duplicate_groups = 0
    for (plant, kind), rows in duplicate_groups:
        signatures = {_series_signature(row) for row in rows}
        if len(signatures) == 1:
            identical_duplicate_groups += 1
        else:
            differing_duplicate_groups += 1
        if len(duplicate_examples) < 20:
            duplicate_examples.append(
                {
                    "plant_id": plant,
                    "type": kind,
                    "rows": [row.get("__row__") for row in rows],
                    "identical_year_series": len(signatures) == 1,
                    "series": [list(_series_signature(row)) for row in rows],
                }
            )

    total_plus_steel = sum(
        1
        for types in types_by_plant.values()
        if "Crude steel production (ttpa)" in types and types.intersection(STEEL_PRODUCTION_ROUTES)
    )
    total_plus_iron = sum(
        1
        for types in types_by_plant.values()
        if "Iron production (ttpa)" in types and types.intersection(IRON_PRODUCTION_ROUTES)
    )

    def total_coverage(total_type: str) -> dict[str, dict[str, int]]:
        rows = [r for r in records if r.get("Type of production") == total_type]
        return {
            year: dict(
                sorted(Counter(classify_source_value(row.get(year)) for row in rows).items())
            )
            for year in YEARS
        }

    return {
        "observed_types": dict(observed_types.most_common()),
        "plants_with_total_and_route_steel_rows": total_plus_steel,
        "plants_with_total_and_route_iron_rows": total_plus_iron,
        "duplicate_plant_type_groups": len(duplicate_groups),
        "identical_duplicate_groups": identical_duplicate_groups,
        "differing_duplicate_groups": differing_duplicate_groups,
        "duplicate_examples": duplicate_examples,
        "crude_total_coverage": total_coverage("Crude steel production (ttpa)"),
        "iron_total_coverage": total_coverage("Iron production (ttpa)"),
        "steel_total_vs_routes": _production_total_route_reconciliation(
            records, "Crude steel production (ttpa)", STEEL_PRODUCTION_ROUTES
        ),
        "iron_total_vs_routes": _production_total_route_reconciliation(
            records, "Iron production (ttpa)", IRON_PRODUCTION_ROUTES
        ),
    }


def date_followup(
    plant_records: list[dict[str, Any]], capacity_records: list[dict[str, Any]]
) -> dict[str, Any]:
    def inspect(records: list[dict[str, Any]], fields: list[str]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for field in fields:
            pattern_styles: dict[str, Counter[int | str]] = defaultdict(Counter)
            numeric_other_examples = []
            for record in records:
                pattern = raw_date_pattern(record.get(field))
                style = record.get("__styles__", {}).get(field, "none")
                pattern_styles[pattern][style] += 1
                if pattern == "numeric_other" and len(numeric_other_examples) < 20:
                    numeric_other_examples.append(
                        {
                            "source_row": record.get("__row__"),
                            "plant_id": record.get("GEM plant ID"),
                            "value": record.get(field),
                            "style_id": style,
                        }
                    )
            result[field] = {
                "style_ids_by_pattern": {
                    pattern: {str(k): v for k, v in sorted(counter.items(), key=lambda item: str(item[0]))}
                    for pattern, counter in sorted(pattern_styles.items())
                },
                "numeric_other_examples": numeric_other_examples,
            }
        return result

    return {
        "plant_dates": inspect(plant_records, PLANT_DATE_FIELDS),
        "capacity_start_date": inspect(capacity_records, ["Start date"])["Start date"],
    }


def profile_followup(path: Path) -> dict[str, Any]:
    actual_sha = sha256_file(path)
    if actual_sha != EXPECTED_SHA256:
        raise ValueError(
            f"GIST plant workbook identity mismatch: expected {EXPECTED_SHA256}, got {actual_sha}."
        )
    plant = read_sheet_records(path, PLANT_SHEET)
    capacity = read_sheet_records(path, CAPACITY_SHEET)
    production = read_sheet_records(path, PRODUCTION_SHEET)
    return {
        "file_name": path.name,
        "sha256": actual_sha,
        "capacity": capacity_followup(capacity),
        "production": production_followup(production),
        "dates": date_followup(plant, capacity),
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"WORKBOOK: {report['file_name']}")
    print(f"SHA256: {report['sha256']}")
    print()
    print("CAPACITY FOLLOW-UP")
    print("==================")
    for key, value in report["capacity"].items():
        print(f"{key.upper()}: {_json(value)}")
    print()
    print("PRODUCTION FOLLOW-UP")
    print("====================")
    for key, value in report["production"].items():
        print(f"{key.upper()}: {_json(value)}")
    print()
    print("DATE FOLLOW-UP")
    print("==============")
    print(_json(report["dates"]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run focused follow-up checks on the pinned GIST workbook.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = profile_followup(args.path)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print_text(report)


if __name__ == "__main__":
    main()
