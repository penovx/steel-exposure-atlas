from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

PUBLISHER = "U.S. Department of the Treasury, Office of Foreign Assets Control"
LICENCE = "CC0 1.0 Universal (official Data.gov catalogue metadata)"
META_SCHEMA = "steel-exposure-atlas/ofac-sanctions-snapshot-review-v1.0"

SDN_URL = (
    "https://sanctionslistservice.ofac.treas.gov/"
    "api/PublicationPreview/exports/SDN.XML"
)
CONSOLIDATED_URL = (
    "https://sanctionslistservice.ofac.treas.gov/"
    "api/PublicationPreview/exports/CONSOLIDATED.XML"
)

DEFAULT_SDN_OUTPUT = Path("tmp/source-packages/ofac/raw/sdn.xml")
DEFAULT_CONSOLIDATED_OUTPUT = Path(
    "tmp/source-packages/ofac/raw/consolidated.xml"
)
DEFAULT_META_OUTPUT = Path(
    "tmp/source-packages/ofac/review/ofac-sanctions.meta.json"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _namespace(tag: str) -> str | None:
    if tag.startswith("{") and "}" in tag:
        return tag[1:].split("}", 1)[0]
    return None


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


def _parse_declared_count(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value.replace(",", "").strip())
    except ValueError:
        return None


def profile_xml(raw_bytes: bytes) -> dict[str, object]:
    """Profile one official OFAC basic XML file without deriving match records."""
    try:
        root = ET.fromstring(raw_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"OFAC source is not valid XML: {exc}") from exc

    entries = [
        element for element in root.iter() if _local_name(element.tag) == "sdnEntry"
    ]
    if not entries:
        raise ValueError("OFAC XML contains no sdnEntry records.")

    type_counts: Counter[str] = Counter()
    program_counts: Counter[str] = Counter()
    unique_uids: set[str] = set()
    alias_count = 0
    address_count = 0
    identifier_count = 0

    for entry in entries:
        uid = _direct_child_text(entry, "uid")
        if uid:
            unique_uids.add(uid)

        sdn_type = _direct_child_text(entry, "sdnType")
        type_counts[sdn_type or "<blank>"] += 1

        for descendant in entry.iter():
            local = _local_name(descendant.tag)
            if local == "program":
                program = _clean(descendant.text)
                if program:
                    program_counts[program] += 1
            elif local == "aka":
                alias_count += 1
            elif local == "address":
                address_count += 1
            elif local == "id":
                identifier_count += 1

    publish_date = _first_text(root, "Publish_Date")
    if not publish_date:
        publish_date = _clean(root.attrib.get("dateGenerated")) or None

    declared_record_count_text = _first_text(root, "Record_Count")
    declared_record_count = _parse_declared_count(declared_record_count_text)

    return {
        "root_element": _local_name(root.tag),
        "namespace": _namespace(root.tag),
        "publish_date": publish_date,
        "declared_record_count": declared_record_count,
        "entry_count": len(entries),
        "unique_uid_count": len(unique_uids),
        "sdn_type_counts": dict(sorted(type_counts.items())),
        "program_occurrence_counts": dict(sorted(program_counts.items())),
        "alias_count": alias_count,
        "address_count": address_count,
        "identifier_count": identifier_count,
        "declared_count_matches_entries": (
            None
            if declared_record_count is None
            else declared_record_count == len(entries)
        ),
    }


def download_source(url: str) -> tuple[bytes, Mapping[str, str | None]]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "steel-exposure-atlas/1.0 "
                "(+https://github.com/penovx/steel-exposure-atlas)"
            ),
            "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read()
        metadata = {
            "final_url": response.geturl(),
            "content_type": response.headers.get("Content-Type"),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
        }
    return raw, metadata


def _file_metadata(
    *,
    source_id: str,
    dataset: str,
    source_url: str,
    raw_bytes: bytes,
    transport: Mapping[str, str | None] | None,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "dataset": dataset,
        "source_url": source_url,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest().upper(),
        "raw_bytes": len(raw_bytes),
        "transport": dict(transport or {}),
        "profile": profile_xml(raw_bytes),
    }


def build_metadata(
    sdn_bytes: bytes,
    consolidated_bytes: bytes,
    *,
    retrieved_at: str,
    sdn_transport: Mapping[str, str | None] | None = None,
    consolidated_transport: Mapping[str, str | None] | None = None,
) -> dict[str, object]:
    return {
        "schema": META_SCHEMA,
        "publisher": PUBLISHER,
        "retrieved_at": retrieved_at,
        "licence": LICENCE,
        "reuse_basis": (
            "Official Data.gov catalogue records for the OFAC SDN List and "
            "Consolidated Non-SDN Sanctions List specify CC0 1.0 Universal."
        ),
        "raw_publication_state": (
            "local-only by project policy; do not commit complete OFAC source files "
            "to public/data"
        ),
        "derived_publication_state": (
            "approved only for a reviewed minimal derived entity-evidence subset "
            "with source-list/program context and snapshot provenance"
        ),
        "interpretation_boundary": (
            "No direct list match is not sanctions clearance. OFAC ownership rules "
            "can affect entities that are not separately named on a list."
        ),
        "files": {
            "sdn": _file_metadata(
                source_id="ofac-sdn",
                dataset="Specially Designated Nationals and Blocked Persons List",
                source_url=SDN_URL,
                raw_bytes=sdn_bytes,
                transport=sdn_transport,
            ),
            "consolidated_non_sdn": _file_metadata(
                source_id="ofac-consolidated-non-sdn",
                dataset="Consolidated Non-SDN Sanctions List",
                source_url=CONSOLIDATED_URL,
                raw_bytes=consolidated_bytes,
                transport=consolidated_transport,
            ),
        },
    }


def write_snapshot(
    sdn_bytes: bytes,
    consolidated_bytes: bytes,
    *,
    sdn_output: Path,
    consolidated_output: Path,
    meta_output: Path,
    retrieved_at: str | None = None,
    sdn_transport: Mapping[str, str | None] | None = None,
    consolidated_transport: Mapping[str, str | None] | None = None,
) -> dict[str, object]:
    retrieved = retrieved_at or _utc_now()
    metadata = build_metadata(
        sdn_bytes,
        consolidated_bytes,
        retrieved_at=retrieved,
        sdn_transport=sdn_transport,
        consolidated_transport=consolidated_transport,
    )

    for path in (sdn_output, consolidated_output, meta_output):
        path.parent.mkdir(parents=True, exist_ok=True)

    sdn_output.write_bytes(sdn_bytes)
    consolidated_output.write_bytes(consolidated_bytes)
    meta_output.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata


def _local_transport() -> Mapping[str, str | None]:
    return {
        "final_url": None,
        "content_type": None,
        "etag": None,
        "last_modified": None,
    }


def _print_file_summary(label: str, metadata: Mapping[str, object]) -> None:
    profile = metadata["profile"]
    assert isinstance(profile, Mapping)
    print(label)
    print(f"  source: {metadata['source_url']}")
    print(f"  sha256: {metadata['raw_sha256']}")
    print(f"  bytes: {metadata['raw_bytes']}")
    print(f"  publish_date: {profile['publish_date']}")
    print(f"  entries: {profile['entry_count']}")
    print(f"  unique uids: {profile['unique_uid_count']}")
    print(f"  aliases: {profile['alias_count']}")
    print("  sdn types:")
    type_counts = profile["sdn_type_counts"]
    assert isinstance(type_counts, Mapping)
    for key, value in type_counts.items():
        print(f"    {key}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download, fingerprint and profile official OFAC SDN and Consolidated "
            "Non-SDN XML files as local pre-publication snapshots."
        )
    )
    parser.add_argument("--sdn-input", type=Path)
    parser.add_argument("--consolidated-input", type=Path)
    parser.add_argument("--sdn-output", type=Path, default=DEFAULT_SDN_OUTPUT)
    parser.add_argument(
        "--consolidated-output",
        type=Path,
        default=DEFAULT_CONSOLIDATED_OUTPUT,
    )
    parser.add_argument("--meta-output", type=Path, default=DEFAULT_META_OUTPUT)
    args = parser.parse_args()

    if bool(args.sdn_input) != bool(args.consolidated_input):
        parser.error(
            "Use both --sdn-input and --consolidated-input together, or neither."
        )

    if args.sdn_input:
        sdn_bytes = args.sdn_input.read_bytes()
        consolidated_bytes = args.consolidated_input.read_bytes()
        sdn_transport = _local_transport()
        consolidated_transport = _local_transport()
    else:
        sdn_bytes, sdn_transport = download_source(SDN_URL)
        consolidated_bytes, consolidated_transport = download_source(CONSOLIDATED_URL)

    metadata = write_snapshot(
        sdn_bytes,
        consolidated_bytes,
        sdn_output=args.sdn_output,
        consolidated_output=args.consolidated_output,
        meta_output=args.meta_output,
        sdn_transport=sdn_transport,
        consolidated_transport=consolidated_transport,
    )

    print(f"retrieved_at: {metadata['retrieved_at']}")
    files = metadata["files"]
    assert isinstance(files, Mapping)
    _print_file_summary("SDN", files["sdn"])
    _print_file_summary("Consolidated Non-SDN", files["consolidated_non_sdn"])
    print(f"sdn output: {args.sdn_output}")
    print(f"consolidated output: {args.consolidated_output}")
    print(f"metadata output: {args.meta_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
