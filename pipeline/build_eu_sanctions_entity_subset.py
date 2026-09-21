from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

DEFAULT_INPUT = Path(
    "tmp/source-packages/eu-sanctions/raw/eu-financial-sanctions-1.1.csv"
)
DEFAULT_OUTPUT = Path(
    "tmp/source-packages/eu-sanctions/derived/eu-sanctions-enterprises.v1.json"
)
SCHEMA = "steel-exposure-atlas/eu-sanctions-enterprises-v1.0"
SOURCE = "eu_financial_sanctions"

REQUIRED_COLUMNS = (
    "fileGenerationDate",
    "Entity_LogicalId",
    "Entity_SubjectType_ClassificationCode",
    "NameAlias_WholeName",
    "Entity_EU_ReferenceNumber",
)


def _clean(value: str | None) -> str:
    return (value or "").strip()


def build_subset(raw_bytes: bytes) -> dict[str, object]:
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

    groups: dict[str, dict[str, object]] = {}
    enterprise_rows = 0
    person_rows = 0
    other_rows = 0
    generation_dates: set[str] = set()

    for row_number, row in enumerate(reader, start=2):
        subject = _clean(row.get("Entity_SubjectType_ClassificationCode"))
        if subject == "person":
            person_rows += 1
            continue
        if subject != "enterprise":
            other_rows += 1
            continue

        enterprise_rows += 1
        entity_id = _clean(row.get("Entity_LogicalId"))
        if not entity_id:
            raise ValueError(f"Enterprise row {row_number} has no Entity_LogicalId.")

        generated = _clean(row.get("fileGenerationDate"))
        if generated:
            generation_dates.add(generated)

        item = groups.setdefault(
            entity_id,
            {
                "entity_id": entity_id,
                "names": set(),
                "eu_reference_numbers": set(),
                "united_nations_ids": set(),
                "designation_dates": set(),
                "programmes": set(),
                "countries_iso2": set(),
                "countries": set(),
                "identifiers": set(),
            },
        )

        def add_set(key: str, value: str | None) -> None:
            cleaned = _clean(value)
            if cleaned:
                item[key].add(cleaned)  # type: ignore[index,union-attr]

        add_set("names", row.get("NameAlias_WholeName"))
        add_set("eu_reference_numbers", row.get("Entity_EU_ReferenceNumber"))
        add_set("united_nations_ids", row.get("Entity_UnitedNationId"))
        add_set("designation_dates", row.get("Entity_DesignationDate"))
        add_set("programmes", row.get("Entity_Regulation_Programme"))
        add_set("countries_iso2", row.get("Address_CountryIso2Code"))
        add_set("countries", row.get("Address_CountryDescription"))

        ident_value = _clean(row.get("Identification_Number"))
        ident_type = _clean(row.get("Identification_TypeCode"))
        ident_description = _clean(row.get("Identification_TypeDescription"))
        if ident_value:
            item["identifiers"].add(  # type: ignore[union-attr]
                (ident_type or "<blank>", ident_description, ident_value)
            )

    entities: list[dict[str, object]] = []
    for entity_id in sorted(groups):
        item = groups[entity_id]
        names = sorted(item["names"])  # type: ignore[arg-type]
        if not names:
            raise ValueError(f"Enterprise {entity_id} has no NameAlias_WholeName value.")

        identifiers = [
            {
                "type_code": type_code,
                "type_description": description,
                "value": value,
            }
            for type_code, description, value in sorted(item["identifiers"])  # type: ignore[arg-type]
        ]

        entities.append(
            {
                "source": SOURCE,
                "entity_type": "entity",
                "entity_id": entity_id,
                "names": names,
                "eu_reference_numbers": sorted(item["eu_reference_numbers"]),  # type: ignore[arg-type]
                "united_nations_ids": sorted(item["united_nations_ids"]),  # type: ignore[arg-type]
                "designation_dates": sorted(item["designation_dates"]),  # type: ignore[arg-type]
                "programmes": sorted(item["programmes"]),  # type: ignore[arg-type]
                "countries_iso2": sorted(item["countries_iso2"]),  # type: ignore[arg-type]
                "countries": sorted(item["countries"]),  # type: ignore[arg-type]
                "identifiers": identifiers,
            }
        )

    return {
        "meta": {
            "schema": SCHEMA,
            "source": SOURCE,
            "publisher": "European Commission",
            "dataset": "Consolidated Financial Sanctions File 1.1",
            "raw_sha256": hashlib.sha256(raw_bytes).hexdigest().upper(),
            "file_generation_dates": sorted(generation_dates),
            "licence": "CC BY 4.0",
            "scope": "enterprise-only derived local review subset; person rows excluded",
            "name_semantics": (
                "All NameAlias_WholeName values are preserved as source names. No primary "
                "name is inferred."
            ),
            "publication_state": (
                "local review output; publication requires candidate/evidence review and "
                "minimum-field transformation"
            ),
            "counts": {
                "enterprise_rows": enterprise_rows,
                "person_rows_excluded": person_rows,
                "other_subject_rows_excluded": other_rows,
                "unique_enterprises": len(entities),
            },
        },
        "entities": entities,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a local enterprise-only EU sanctions subset from the pinned 1.1 CSV."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    raw = args.input.read_bytes()
    payload = build_subset(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    meta = payload["meta"]
    counts = meta["counts"]
    print(f"sha256: {meta['raw_sha256']}")
    print(f"enterprise rows: {counts['enterprise_rows']}")
    print(f"person rows excluded: {counts['person_rows_excluded']}")
    print(f"unique enterprises: {counts['unique_enterprises']}")
    print(f"file generation dates: {meta['file_generation_dates']}")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
