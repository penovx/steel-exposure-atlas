from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

DEFAULT_INPUT = Path(
    "tmp/source-packages/eu-sanctions/raw/eu-financial-sanctions-1.1.csv"
)
DEFAULT_OUTPUT = Path(
    "tmp/source-packages/eu-sanctions/review/"
    "eu-financial-sanctions-1.1.enterprise-profile.json"
)
PROFILE_SCHEMA = "steel-exposure-atlas/eu-sanctions-enterprise-profile-v1.0"

REQUIRED_COLUMNS = (
    "fileGenerationDate",
    "Entity_LogicalId",
    "Entity_SubjectType_ClassificationCode",
    "NameAlias_WholeName",
)

COVERAGE_FIELDS = (
    "Entity_EU_ReferenceNumber",
    "Entity_UnitedNationId",
    "Entity_DesignationDate",
    "Entity_Regulation_Programme",
    "Address_CountryIso2Code",
    "Address_CountryDescription",
    "Identification_Number",
    "Identification_TypeCode",
    "Identification_TypeDescription",
)


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _percentile_nearest_rank(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    rank = max(1, int((percentile * len(ordered)) + 0.999999999))
    return ordered[min(rank - 1, len(ordered) - 1)]


def _distribution(values: list[int]) -> dict[str, int | float]:
    if not values:
        return {"min": 0, "median": 0, "p95": 0, "max": 0}
    med = median(values)
    return {
        "min": min(values),
        "median": int(med) if float(med).is_integer() else med,
        "p95": _percentile_nearest_rank(values, 0.95),
        "max": max(values),
    }


def profile_enterprises(raw_bytes: bytes) -> dict[str, object]:
    """Profile enterprise-only records without emitting row-level sanctions content."""
    text = raw_bytes.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines(), delimiter=";")
    if not reader.fieldnames:
        raise ValueError("EU sanctions CSV has no header row.")

    columns = [_clean(name) for name in reader.fieldnames]
    missing = [name for name in REQUIRED_COLUMNS if name not in columns]
    if missing:
        raise ValueError(
            "EU sanctions CSV is missing required columns: " + ", ".join(missing)
        )

    present_coverage_fields = [name for name in COVERAGE_FIELDS if name in columns]

    all_rows = 0
    enterprise_rows = 0
    person_rows = 0
    other_rows = 0
    generation_dates: Counter[str] = Counter()
    rows_by_entity: Counter[str] = Counter()
    names_by_entity: dict[str, set[str]] = defaultdict(set)
    name_logical_ids_by_entity: dict[str, set[str]] = defaultdict(set)
    coverage_entities: dict[str, set[str]] = {
        field: set() for field in present_coverage_fields
    }

    for row in reader:
        all_rows += 1
        subject_type = _clean(row.get("Entity_SubjectType_ClassificationCode"))
        if subject_type == "person":
            person_rows += 1
            continue
        if subject_type != "enterprise":
            other_rows += 1
            continue

        enterprise_rows += 1
        entity_id = _clean(row.get("Entity_LogicalId"))
        if not entity_id:
            raise ValueError(f"Enterprise row {all_rows} has no Entity_LogicalId.")

        rows_by_entity[entity_id] += 1

        generated = _clean(row.get("fileGenerationDate"))
        if generated:
            generation_dates[generated] += 1

        whole_name = _clean(row.get("NameAlias_WholeName"))
        if whole_name:
            names_by_entity[entity_id].add(whole_name)

        name_logical_id = _clean(row.get("NameAlias_LogicalId"))
        if name_logical_id:
            name_logical_ids_by_entity[entity_id].add(name_logical_id)

        for field in present_coverage_fields:
            if _clean(row.get(field)):
                coverage_entities[field].add(entity_id)

    if enterprise_rows == 0:
        raise ValueError("EU sanctions CSV contains no enterprise rows.")

    entity_ids = set(rows_by_entity)
    row_counts = list(rows_by_entity.values())
    name_counts = [len(names_by_entity.get(entity_id, set())) for entity_id in entity_ids]
    name_id_counts = [
        len(name_logical_ids_by_entity.get(entity_id, set())) for entity_id in entity_ids
    ]

    return {
        "schema": PROFILE_SCHEMA,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest().upper(),
        "source_counts": {
            "all_rows": all_rows,
            "enterprise_rows": enterprise_rows,
            "person_rows_excluded": person_rows,
            "other_subject_rows_excluded": other_rows,
            "unique_enterprises": len(entity_ids),
        },
        "file_generation_dates_on_enterprise_rows": dict(
            sorted(generation_dates.items())
        ),
        "flattening": {
            "rows_per_enterprise": _distribution(row_counts),
            "distinct_names_per_enterprise": _distribution(name_counts),
            "distinct_name_logical_ids_per_enterprise": _distribution(name_id_counts),
            "enterprises_with_at_least_one_name": sum(1 for value in name_counts if value),
            "enterprises_with_multiple_names": sum(1 for value in name_counts if value > 1),
        },
        "entity_field_coverage": {
            field: {
                "enterprises": len(ids),
                "of_unique_enterprises": round(len(ids) / len(entity_ids), 6),
            }
            for field, ids in coverage_entities.items()
        },
        "missing_expected_coverage_fields": [
            field for field in COVERAGE_FIELDS if field not in columns
        ],
        "interpretation": {
            "subject_filter": "enterprise",
            "grouping_key": "Entity_LogicalId",
            "names": (
                "NameAlias_WholeName values are profiled as source names. This step does "
                "not infer which name is primary."
            ),
            "privacy": (
                "Person rows are excluded before enterprise coverage or name statistics "
                "are accumulated. No row-level names or identifiers are emitted."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Profile enterprise records in a local EU sanctions 1.1 snapshot without "
            "emitting row-level sanctions content."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    raw = args.input.read_bytes()
    profile = profile_enterprises(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    counts = profile["source_counts"]
    flattening = profile["flattening"]
    print(f"sha256: {profile['raw_sha256']}")
    print(f"source rows: {counts['all_rows']}")
    print(f"enterprise rows: {counts['enterprise_rows']}")
    print(f"person rows excluded: {counts['person_rows_excluded']}")
    print(f"other subject rows excluded: {counts['other_subject_rows_excluded']}")
    print(f"unique enterprises: {counts['unique_enterprises']}")
    print(f"rows per enterprise: {flattening['rows_per_enterprise']}")
    print(
        "distinct names per enterprise: "
        f"{flattening['distinct_names_per_enterprise']}"
    )
    print(
        "enterprises with multiple names: "
        f"{flattening['enterprises_with_multiple_names']}"
    )
    print("entity field coverage:")
    for field, values in profile["entity_field_coverage"].items():
        print(
            f"  {field}: {values['enterprises']} "
            f"({values['of_unique_enterprises']:.1%})"
        )
    if profile["missing_expected_coverage_fields"]:
        print(
            "missing expected coverage fields: "
            + ", ".join(profile["missing_expected_coverage_fields"])
        )
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
