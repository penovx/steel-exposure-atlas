from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

SOURCE_URL = "https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.csv"
SCHEMA = "steel-exposure-atlas/uk-sanctions-entity-v1.0"
OGL_ATTRIBUTION = (
    "Contains public sector information licensed under the Open Government Licence v3.0. "
    "Source: UK Sanctions List, Foreign, Commonwealth & Development Office."
)


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").strip().lower())


def _header_map(fieldnames: Iterable[str]) -> dict[str, str]:
    return {_key(name): name for name in fieldnames if name}


def _get(row: dict[str, str], headers: dict[str, str], *logical_names: str) -> str:
    for name in logical_names:
        actual = headers.get(_key(name))
        if actual is not None:
            return (row.get(actual) or "").strip()
    return ""


def _add(values: set[str], value: str) -> None:
    if value:
        values.add(value.strip())


def parse_entity_subset(raw_bytes: bytes, *, retrieved_at: str | None = None) -> dict[str, object]:
    """Parse the official UK Sanctions List CSV into a minimal entity-only review subset.

    Individual and ship rows are discarded before any output object is created. Personal
    fields are intentionally not copied into the derived subset.
    """
    text = raw_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("UK Sanctions List CSV has no header row.")

    headers = _header_map(reader.fieldnames)
    required = ["Unique ID", "Individual, Entity, Ship", "Name 6", "Name type"]
    missing = [name for name in required if _key(name) not in headers]
    if missing:
        raise ValueError(
            "UK Sanctions List CSV is missing required columns: " + ", ".join(missing)
        )

    records: dict[str, dict[str, object]] = {}
    total_rows = 0
    entity_rows = 0
    skipped_person_rows = 0
    skipped_ship_rows = 0

    for row in reader:
        total_rows += 1
        kind = _get(row, headers, "Individual, Entity, Ship").casefold()
        if kind != "entity":
            if kind == "individual":
                skipped_person_rows += 1
            elif kind == "ship":
                skipped_ship_rows += 1
            continue

        entity_rows += 1
        uid = _get(row, headers, "Unique ID")
        if not uid:
            raise ValueError(f"Entity row {total_rows} has no Unique ID.")

        item = records.setdefault(
            uid,
            {
                "entity_id": uid,
                "ofsi_group_ids": set(),
                "un_reference_numbers": set(),
                "primary_names": set(),
                "aliases": set(),
                "name_variations": set(),
                "regimes": set(),
                "designation_sources": set(),
                "sanctions_imposed": set(),
                "countries": set(),
                "business_registration_numbers": set(),
                "entity_types": set(),
                "parent_companies": set(),
                "subsidiaries": set(),
                "dates_designated": set(),
                "last_updated": set(),
            },
        )

        name = _get(row, headers, "Name 6")
        name_type = _get(row, headers, "Name type").casefold()
        if name:
            if name_type == "primary name":
                _add(item["primary_names"], name)
            elif name_type == "primary name variation":
                _add(item["name_variations"], name)
            else:
                _add(item["aliases"], name)

        for key, names in [
            ("ofsi_group_ids", ("OFSI Group ID",)),
            ("un_reference_numbers", ("UN Reference Number",)),
            ("regimes", ("Regime Name",)),
            ("designation_sources", ("Designation source",)),
            ("sanctions_imposed", ("Sanctions Imposed",)),
            ("countries", ("Address Country",)),
            (
                "business_registration_numbers",
                ("Business registration number (s)", "Business registration number(s)"),
            ),
            ("entity_types", ("Type of entity",)),
            ("parent_companies", ("Parent Company", "Parent company")),
            ("subsidiaries", ("Subsidiaries",)),
            ("dates_designated", ("Date Designated",)),
            ("last_updated", ("Last Updated",)),
        ]:
            _add(item[key], _get(row, headers, *names))

    output_records: list[dict[str, object]] = []
    for uid in sorted(records):
        item = records[uid]
        primary_names = sorted(item["primary_names"])
        if not primary_names:
            fallback = sorted(item["name_variations"] | item["aliases"])
            if not fallback:
                raise ValueError(f"Entity {uid} has no usable name.")
            primary_names = [fallback[0]]

        output_records.append(
            {
                "source": "uk_sanctions_list",
                "entity_id": uid,
                "primary_name": primary_names[0],
                "primary_names": primary_names,
                "aliases": sorted(item["aliases"]),
                "name_variations": sorted(item["name_variations"]),
                "regimes": sorted(item["regimes"]),
                "designation_sources": sorted(item["designation_sources"]),
                "sanctions_imposed": sorted(item["sanctions_imposed"]),
                "countries": sorted(item["countries"]),
                "identifiers": {
                    "ofsi_group_id": sorted(item["ofsi_group_ids"]),
                    "un_reference_number": sorted(item["un_reference_numbers"]),
                    "business_registration_number": sorted(
                        item["business_registration_numbers"]
                    ),
                },
                "entity_types": sorted(item["entity_types"]),
                "parent_companies_source_text": sorted(item["parent_companies"]),
                "subsidiaries_source_text": sorted(item["subsidiaries"]),
                "dates_designated": sorted(item["dates_designated"]),
                "last_updated": sorted(item["last_updated"]),
            }
        )

    retrieved = retrieved_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    digest = hashlib.sha256(raw_bytes).hexdigest().upper()
    return {
        "meta": {
            "schema": SCHEMA,
            "publisher": "Foreign, Commonwealth & Development Office",
            "dataset": "UK Sanctions List",
            "source_url": SOURCE_URL,
            "retrieved_at": retrieved,
            "raw_sha256": digest,
            "licence": "Open Government Licence v3.0",
            "attribution": OGL_ATTRIBUTION,
            "scope": "entity-only derived subset; individual and ship rows excluded",
            "publication_state": "snapshot review required before public/data inclusion",
        },
        "counts": {
            "source_rows": total_rows,
            "entity_rows": entity_rows,
            "entity_records": len(output_records),
            "skipped_individual_rows": skipped_person_rows,
            "skipped_ship_rows": skipped_ship_rows,
        },
        "entities": output_records,
    }


def download_source(url: str = SOURCE_URL) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "steel-exposure-atlas/1.0 "
                "(+https://github.com/penovx/steel-exposure-atlas)"
            ),
            "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def write_snapshot(raw_bytes: bytes, output: Path) -> dict[str, object]:
    payload = parse_entity_subset(raw_bytes)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch and derive an entity-only UK Sanctions List snapshot for local review."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tmp/uk-sanctions-entities.snapshot.json"),
        help=(
            "Local review output. Do not point this at public/data before the snapshot "
            "review gate is closed."
        ),
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Optional local CSV instead of downloading the official source.",
    )
    args = parser.parse_args()

    raw = args.input.read_bytes() if args.input else download_source()
    payload = write_snapshot(raw, args.output)
    meta = payload["meta"]
    counts = payload["counts"]
    print(f"source: {meta['source_url']}")
    print(f"sha256: {meta['raw_sha256']}")
    print(f"rows: {counts['source_rows']}")
    print(f"entity rows: {counts['entity_rows']}")
    print(f"entity records: {counts['entity_records']}")
    print(f"excluded individual rows: {counts['skipped_individual_rows']}")
    print(f"excluded ship rows: {counts['skipped_ship_rows']}")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
