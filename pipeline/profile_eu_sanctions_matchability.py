from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from pipeline.sanctions_match import normalize_identifier, normalize_name, relaxed_legal_form_name

DEFAULT_INPUT = Path(
    "tmp/source-packages/eu-sanctions/raw/eu-financial-sanctions-1.1.csv"
)
DEFAULT_OUTPUT = Path(
    "tmp/source-packages/eu-sanctions/review/"
    "eu-financial-sanctions-1.1.matchability-profile.json"
)
PROFILE_SCHEMA = "steel-exposure-atlas/eu-sanctions-matchability-profile-v1.0"

REQUIRED_COLUMNS = (
    "Entity_LogicalId",
    "Entity_SubjectType_ClassificationCode",
    "NameAlias_WholeName",
)


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _aggregate_value_counts(
    reader_rows: list[dict[str, str]],
    *,
    candidate_columns: list[str],
) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for column in candidate_columns:
        counts: Counter[str] = Counter()
        for row in reader_rows:
            value = _clean(row.get(column))
            if value:
                counts[value] += 1
        if counts:
            result[column] = dict(sorted(counts.items()))
    return result


def profile_matchability(raw_bytes: bytes) -> dict[str, object]:
    """Measure enterprise matching characteristics without emitting row-level values."""
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

    enterprise_rows: list[dict[str, str]] = []
    entity_ids: set[str] = set()
    raw_name_entities: dict[str, set[str]] = defaultdict(set)
    normalized_name_entities: dict[str, set[str]] = defaultdict(set)
    relaxed_name_entities: dict[str, set[str]] = defaultdict(set)
    identification_entities_by_type: dict[tuple[str, str], set[str]] = defaultdict(set)
    identification_values_by_type: dict[tuple[str, str], set[str]] = defaultdict(set)
    identification_value_entities: dict[
        tuple[str, str], dict[str, set[str]]
    ] = defaultdict(lambda: defaultdict(set))

    for row in reader:
        if _clean(row.get("Entity_SubjectType_ClassificationCode")) != "enterprise":
            continue

        entity_id = _clean(row.get("Entity_LogicalId"))
        if not entity_id:
            raise ValueError("Enterprise row has no Entity_LogicalId.")
        entity_ids.add(entity_id)
        enterprise_rows.append(row)

        whole_name = _clean(row.get("NameAlias_WholeName"))
        if whole_name:
            raw_name_entities[whole_name].add(entity_id)
            normalized = normalize_name(whole_name)
            if normalized:
                normalized_name_entities[normalized].add(entity_id)
            relaxed = relaxed_legal_form_name(whole_name)
            if relaxed:
                relaxed_name_entities[relaxed].add(entity_id)

        identification_number = _clean(row.get("Identification_Number"))
        if identification_number:
            type_code = _clean(row.get("Identification_TypeCode")) or "<blank>"
            type_description = (
                _clean(row.get("Identification_TypeDescription")) or "<blank>"
            )
            type_key = (type_code, type_description)
            normalized_id = normalize_identifier(identification_number)
            if normalized_id:
                identification_entities_by_type[type_key].add(entity_id)
                identification_values_by_type[type_key].add(normalized_id)
                identification_value_entities[type_key][normalized_id].add(entity_id)

    if not entity_ids:
        raise ValueError("EU sanctions CSV contains no enterprise records.")

    def collision_summary(mapping: dict[str, set[str]]) -> dict[str, int]:
        memberships = [len(ids) for ids in mapping.values()]
        return {
            "distinct_keys": len(mapping),
            "keys_unique_to_one_enterprise": sum(value == 1 for value in memberships),
            "keys_shared_across_enterprises": sum(value > 1 for value in memberships),
            "max_enterprises_per_key": max(memberships, default=0),
        }

    identification_types: list[dict[str, object]] = []
    for type_key in sorted(identification_entities_by_type):
        entity_members = identification_entities_by_type[type_key]
        value_members = identification_value_entities[type_key]
        collision_values = sum(len(ids) > 1 for ids in value_members.values())
        identification_types.append(
            {
                "type_code": type_key[0],
                "type_description": type_key[1],
                "enterprises": len(entity_members),
                "of_unique_enterprises": round(len(entity_members) / len(entity_ids), 6),
                "distinct_normalized_values": len(
                    identification_values_by_type[type_key]
                ),
                "values_shared_across_enterprises": collision_values,
                "max_enterprises_per_value": max(
                    (len(ids) for ids in value_members.values()), default=0
                ),
            }
        )

    name_alias_columns = sorted(
        column for column in columns if column.startswith("NameAlias_")
    )
    identification_columns = sorted(
        column for column in columns if column.startswith("Identification_")
    )
    name_metadata_candidates = [
        column
        for column in name_alias_columns
        if "strong" in column.casefold() or "language" in column.casefold()
    ]

    return {
        "schema": PROFILE_SCHEMA,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest().upper(),
        "population": {
            "enterprise_rows": len(enterprise_rows),
            "unique_enterprises": len(entity_ids),
        },
        "source_schema": {
            "name_alias_columns": name_alias_columns,
            "identification_columns": identification_columns,
            "name_metadata_value_counts": _aggregate_value_counts(
                enterprise_rows,
                candidate_columns=name_metadata_candidates,
            ),
        },
        "name_matchability": {
            "raw_source_names": collision_summary(raw_name_entities),
            "conservative_normalized_names": collision_summary(
                normalized_name_entities
            ),
            "legal_form_relaxed_names": collision_summary(relaxed_name_entities),
        },
        "identification_matchability": {
            "types": identification_types,
            "interpretation": (
                "Identification values are grouped within their source type. "
                "No type is automatically treated as a company-registration number, "
                "LEI or other comparable identifier until reviewed."
            ),
        },
        "privacy": (
            "Aggregate profile only. Person rows are excluded and no enterprise name "
            "or identification value is emitted."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Profile EU sanctions enterprise name and identifier matchability without "
            "emitting row-level sanctions values."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    raw = args.input.read_bytes()
    profile = profile_matchability(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"sha256: {profile['raw_sha256']}")
    print(f"enterprise rows: {profile['population']['enterprise_rows']}")
    print(f"unique enterprises: {profile['population']['unique_enterprises']}")
    print("name alias columns:")
    for column in profile["source_schema"]["name_alias_columns"]:
        print(f"  {column}")
    metadata_counts = profile["source_schema"]["name_metadata_value_counts"]
    if metadata_counts:
        print("name metadata value counts:")
        for column, values in metadata_counts.items():
            print(f"  {column}: {values}")
    print("name matchability:")
    for label, values in profile["name_matchability"].items():
        print(f"  {label}: {values}")
    print("identification types:")
    for item in profile["identification_matchability"]["types"]:
        print(
            "  "
            f"{item['type_code']} | {item['type_description']}: "
            f"{item['enterprises']} enterprises ({item['of_unique_enterprises']:.1%}), "
            f"{item['distinct_normalized_values']} values, "
            f"{item['values_shared_across_enterprises']} shared values, "
            f"max {item['max_enterprises_per_value']} enterprises/value"
        )
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
