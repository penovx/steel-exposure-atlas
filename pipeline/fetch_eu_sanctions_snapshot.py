from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

SOURCE_URL = (
    "https://webgate.ec.europa.eu/fsd/fsf/public/files/"
    "csvFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw"
)
DATASET = "Consolidated Financial Sanctions File 1.1"
PUBLISHER = "European Commission"
LICENCE = "CC BY 4.0"
META_SCHEMA = "steel-exposure-atlas/eu-sanctions-snapshot-review-v1.0"

REQUIRED_COLUMNS = (
    "fileGenerationDate",
    "Entity_LogicalId",
    "Entity_SubjectType_ClassificationCode",
)

DEFAULT_RAW_OUTPUT = Path(
    "tmp/source-packages/eu-sanctions/raw/eu-financial-sanctions-1.1.csv"
)
DEFAULT_META_OUTPUT = Path(
    "tmp/source-packages/eu-sanctions/review/eu-financial-sanctions-1.1.meta.json"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clean(value: str | None) -> str:
    return (value or "").strip()


def profile_csv(raw_bytes: bytes) -> dict[str, object]:
    """Profile the official flattened EU sanctions CSV without deriving match records.

    This first step intentionally records structure and subject-type populations only.
    It does not publish, match, or copy row-level sanctions content into repository data.
    """
    text = raw_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    if not reader.fieldnames:
        raise ValueError("EU sanctions CSV has no header row.")

    columns = [_clean(name) for name in reader.fieldnames]
    missing = [name for name in REQUIRED_COLUMNS if name not in columns]
    if missing:
        raise ValueError(
            "EU sanctions CSV is missing required columns: " + ", ".join(missing)
        )

    rows = 0
    logical_ids: set[str] = set()
    subject_types: Counter[str] = Counter()
    generation_dates: Counter[str] = Counter()

    for row in reader:
        rows += 1
        logical_id = _clean(row.get("Entity_LogicalId"))
        if logical_id:
            logical_ids.add(logical_id)

        subject_type = _clean(row.get("Entity_SubjectType_ClassificationCode"))
        subject_types[subject_type or "<blank>"] += 1

        generated = _clean(row.get("fileGenerationDate"))
        if generated:
            generation_dates[generated] += 1

    if rows == 0:
        raise ValueError("EU sanctions CSV contains no data rows.")

    return {
        "row_count": rows,
        "unique_entity_logical_ids": len(logical_ids),
        "column_count": len(columns),
        "columns": columns,
        "subject_type_row_counts": dict(sorted(subject_types.items())),
        "file_generation_dates": dict(sorted(generation_dates.items())),
    }


def download_source(url: str = SOURCE_URL) -> tuple[bytes, Mapping[str, str | None]]:
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
    with urllib.request.urlopen(request, timeout=90) as response:
        raw = response.read()
        metadata = {
            "final_url": response.geturl(),
            "content_type": response.headers.get("Content-Type"),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
        }
    return raw, metadata


def build_metadata(
    raw_bytes: bytes,
    *,
    retrieved_at: str,
    transport: Mapping[str, str | None] | None = None,
) -> dict[str, object]:
    profile = profile_csv(raw_bytes)
    return {
        "schema": META_SCHEMA,
        "publisher": PUBLISHER,
        "dataset": DATASET,
        "source_url": SOURCE_URL,
        "retrieved_at": retrieved_at,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest().upper(),
        "raw_bytes": len(raw_bytes),
        "licence": LICENCE,
        "reuse_basis": (
            "European Commission reuse policy: EU-owned website content is CC BY 4.0 "
            "unless otherwise indicated. The downloaded snapshot must still be checked "
            "for any more-specific conflicting notice before derived public output."
        ),
        "raw_publication_state": "local-only; do not commit raw source to public/data",
        "derived_publication_state": (
            "allowed after snapshot notice check, entity-only transformation review, "
            "attribution, and provenance preservation"
        ),
        "transport": dict(transport or {}),
        "profile": profile,
    }


def write_snapshot(
    raw_bytes: bytes,
    *,
    raw_output: Path,
    meta_output: Path,
    retrieved_at: str | None = None,
    transport: Mapping[str, str | None] | None = None,
) -> dict[str, object]:
    retrieved = retrieved_at or _utc_now()
    metadata = build_metadata(
        raw_bytes,
        retrieved_at=retrieved,
        transport=transport,
    )

    raw_output.parent.mkdir(parents=True, exist_ok=True)
    meta_output.parent.mkdir(parents=True, exist_ok=True)
    raw_output.write_bytes(raw_bytes)
    meta_output.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download and profile the official EU Consolidated Financial Sanctions "
            "File 1.1 as a local, pre-publication snapshot."
        )
    )
    parser.add_argument(
        "--raw-output",
        type=Path,
        default=DEFAULT_RAW_OUTPUT,
        help="Local ignored raw CSV path. Never point this at public/data.",
    )
    parser.add_argument(
        "--meta-output",
        type=Path,
        default=DEFAULT_META_OUTPUT,
        help="Local ignored snapshot metadata/profile JSON path.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Optional local CSV instead of downloading the official source.",
    )
    args = parser.parse_args()

    if args.input:
        raw = args.input.read_bytes()
        transport: Mapping[str, str | None] = {
            "final_url": None,
            "content_type": None,
            "etag": None,
            "last_modified": None,
        }
    else:
        raw, transport = download_source()

    metadata = write_snapshot(
        raw,
        raw_output=args.raw_output,
        meta_output=args.meta_output,
        transport=transport,
    )
    profile = metadata["profile"]

    print(f"source: {metadata['source_url']}")
    print(f"retrieved_at: {metadata['retrieved_at']}")
    print(f"sha256: {metadata['raw_sha256']}")
    print(f"bytes: {metadata['raw_bytes']}")
    print(f"rows: {profile['row_count']}")
    print(f"unique logical entities: {profile['unique_entity_logical_ids']}")
    print(f"columns: {profile['column_count']}")
    print("subject type row counts:")
    for key, value in profile["subject_type_row_counts"].items():
        print(f"  {key}: {value}")
    print("file generation dates:")
    for key, value in profile["file_generation_dates"].items():
        print(f"  {key}: {value}")
    print(f"raw output: {args.raw_output}")
    print(f"metadata output: {args.meta_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
