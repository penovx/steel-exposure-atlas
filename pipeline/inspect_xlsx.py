#!/usr/bin/env python3
"""Inspect an XLSX workbook without modifying it or requiring third-party packages.

The utility is intended for source-package review before a workbook is admitted to
an ingestion pipeline. It reports the file fingerprint, workbook sheet metadata,
worksheet dimensions and a bounded preview of non-empty rows. The module also
exposes read-only helpers for downstream profiling code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CELL_REF_RE = re.compile(r"^([A-Z]+)[0-9]+$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _read_xml(archive: ZipFile, member: str) -> ET.Element:
    with archive.open(member) as handle:
        return ET.parse(handle).getroot()


def _shared_strings(archive: ZipFile) -> list[str]:
    member = "xl/sharedStrings.xml"
    if member not in archive.namelist():
        return []
    root = _read_xml(archive, member)
    values: list[str] = []
    for item in root.findall(f"{{{MAIN_NS}}}si"):
        text = "".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t"))
        values.append(text)
    return values


def _relationship_targets(archive: ZipFile) -> dict[str, str]:
    root = _read_xml(archive, "xl/_rels/workbook.xml.rels")
    targets: dict[str, str] = {}
    for rel in root.findall(f"{{{PKG_REL_NS}}}Relationship"):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        if rel_id and target:
            normalized = target.lstrip("/")
            if not normalized.startswith("xl/"):
                normalized = f"xl/{normalized}"
            targets[rel_id] = normalized
    return targets


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> Any:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        inline = cell.find(f"{{{MAIN_NS}}}is")
        if inline is None:
            return None
        return "".join(node.text or "" for node in inline.iter(f"{{{MAIN_NS}}}t"))

    value = cell.find(f"{{{MAIN_NS}}}v")
    if value is None or value.text is None:
        return None
    raw = value.text

    if cell_type == "s":
        try:
            return shared_strings[int(raw)]
        except (ValueError, IndexError):
            return raw
    if cell_type == "b":
        return raw == "1"
    if cell_type in {"str", "e"}:
        return raw

    try:
        number = float(raw)
    except ValueError:
        return raw
    return int(number) if number.is_integer() else number


def _workbook_sheet_members(archive: ZipFile) -> list[dict[str, str | None]]:
    targets = _relationship_targets(archive)
    workbook = _read_xml(archive, "xl/workbook.xml")
    sheets_node = workbook.find(f"{{{MAIN_NS}}}sheets")
    sheets: list[dict[str, str | None]] = []
    if sheets_node is None:
        return sheets
    for sheet in sheets_node.findall(f"{{{MAIN_NS}}}sheet"):
        rel_id = sheet.attrib.get(f"{{{DOC_REL_NS}}}id")
        sheets.append(
            {
                "name": sheet.attrib.get("name"),
                "sheet_id": sheet.attrib.get("sheetId"),
                "state": sheet.attrib.get("state", "visible"),
                "relationship_id": rel_id,
                "member": targets.get(rel_id or ""),
            }
        )
    return sheets


def _validate_xlsx_path(path: Path) -> None:
    if path.suffix.lower() != ".xlsx":
        raise ValueError("Expected an .xlsx file.")
    if not path.is_file():
        raise FileNotFoundError(path)


def _column_from_ref(ref: str | None) -> str | None:
    if not ref:
        return None
    match = CELL_REF_RE.match(ref)
    return match.group(1) if match else None


def read_sheet_rows(path: Path, sheet_name: str) -> list[dict[str, Any]]:
    """Return all worksheet rows as column-letter keyed values and style IDs.

    The function reads the XLSX ZIP/XML representation directly and never writes
    to the workbook. Cell values are decoded consistently with the inspector, but
    date serials intentionally remain raw numeric values; date interpretation is a
    separate ingestion concern because it depends on workbook number formats.
    """

    _validate_xlsx_path(path)
    with ZipFile(path) as archive:
        required = {"xl/workbook.xml", "xl/_rels/workbook.xml.rels"}
        missing = required.difference(archive.namelist())
        if missing:
            raise ValueError(f"Workbook is missing required XLSX members: {sorted(missing)}")

        sheet_defs = _workbook_sheet_members(archive)
        sheet_def = next((item for item in sheet_defs if item.get("name") == sheet_name), None)
        if sheet_def is None:
            names = [item.get("name") for item in sheet_defs]
            raise ValueError(f"Worksheet {sheet_name!r} not found. Available sheets: {names}")

        member = sheet_def.get("member")
        if not member or member not in archive.namelist():
            raise ValueError(f"Worksheet member for {sheet_name!r} was not found in the archive.")

        shared_strings = _shared_strings(archive)
        root = _read_xml(archive, member)
        sheet_data = root.find(f"{{{MAIN_NS}}}sheetData")
        rows: list[dict[str, Any]] = []
        if sheet_data is None:
            return rows

        for row in sheet_data.findall(f"{{{MAIN_NS}}}row"):
            values: dict[str, Any] = {}
            styles: dict[str, int] = {}
            for cell in row.findall(f"{{{MAIN_NS}}}c"):
                column = _column_from_ref(cell.attrib.get("r"))
                if column is None:
                    continue
                value = _cell_value(cell, shared_strings)
                if value is not None and value != "":
                    values[column] = value
                style = cell.attrib.get("s")
                if style is not None:
                    try:
                        styles[column] = int(style)
                    except ValueError:
                        pass
            rows.append(
                {
                    "row": int(row.attrib.get("r", len(rows) + 1)),
                    "values": values,
                    "styles": styles,
                }
            )
        return rows


def read_sheet_records(
    path: Path,
    sheet_name: str,
    header_row: int = 1,
) -> list[dict[str, Any]]:
    """Return non-empty worksheet records keyed by header text.

    Two reserved keys are added to each record: `__row__` for the source row
    number and `__styles__` for a header-keyed mapping of cell style IDs.
    """

    rows = read_sheet_rows(path, sheet_name)
    header = next((row for row in rows if row["row"] == header_row), None)
    if header is None:
        raise ValueError(f"Header row {header_row} not found in worksheet {sheet_name!r}.")

    headers = {
        column: str(value).strip()
        for column, value in header["values"].items()
        if value is not None and str(value).strip()
    }
    if not headers:
        raise ValueError(f"Header row {header_row} in worksheet {sheet_name!r} is empty.")

    records: list[dict[str, Any]] = []
    for row in rows:
        if row["row"] <= header_row:
            continue
        record: dict[str, Any] = {"__row__": row["row"]}
        style_map: dict[str, int] = {}
        populated = False
        for column, header_name in headers.items():
            value = row["values"].get(column)
            if value is not None and value != "":
                record[header_name] = value
                populated = True
            if column in row["styles"]:
                style_map[header_name] = row["styles"][column]
        if populated:
            record["__styles__"] = style_map
            records.append(record)
    return records


def _sheet_preview(
    archive: ZipFile,
    member: str,
    shared_strings: list[str],
    preview_rows: int,
) -> dict[str, Any]:
    root = _read_xml(archive, member)
    dimension = root.find(f"{{{MAIN_NS}}}dimension")
    dimension_ref = dimension.attrib.get("ref") if dimension is not None else None

    rows: list[list[dict[str, Any]]] = []
    row_count = 0
    non_empty_row_count = 0
    sheet_data = root.find(f"{{{MAIN_NS}}}sheetData")
    if sheet_data is not None:
        for row in sheet_data.findall(f"{{{MAIN_NS}}}row"):
            row_count += 1
            cells: list[dict[str, Any]] = []
            for cell in row.findall(f"{{{MAIN_NS}}}c"):
                value = _cell_value(cell, shared_strings)
                if value is not None and value != "":
                    cells.append({"ref": cell.attrib.get("r"), "value": value})
            if cells:
                non_empty_row_count += 1
                if len(rows) < preview_rows:
                    rows.append(cells)

    return {
        "member": member,
        "dimension": dimension_ref,
        "xml_row_count": row_count,
        "non_empty_row_count": non_empty_row_count,
        "preview_rows": rows,
    }


def inspect_workbook(
    path: Path,
    preview_rows: int = 8,
    sheet_name: str | None = None,
) -> dict[str, Any]:
    _validate_xlsx_path(path)

    with ZipFile(path) as archive:
        required = {"xl/workbook.xml", "xl/_rels/workbook.xml.rels"}
        missing = required.difference(archive.namelist())
        if missing:
            raise ValueError(f"Workbook is missing required XLSX members: {sorted(missing)}")

        shared_strings = _shared_strings(archive)
        sheet_defs = _workbook_sheet_members(archive)
        available_names = [item.get("name", "") or "" for item in sheet_defs]
        sheets: list[dict[str, Any]] = []

        for sheet in sheet_defs:
            name = sheet.get("name")
            if sheet_name is not None and name != sheet_name:
                continue
            member = sheet.get("member")
            item: dict[str, Any] = {
                "name": name,
                "sheet_id": sheet.get("sheet_id"),
                "state": sheet.get("state", "visible"),
                "relationship_id": sheet.get("relationship_id"),
            }
            if member and member in archive.namelist():
                item.update(_sheet_preview(archive, member, shared_strings, preview_rows))
            else:
                item["member"] = member
                item["error"] = "Worksheet member not found in archive."
            sheets.append(item)

    if sheet_name is not None and not sheets:
        raise ValueError(
            f"Worksheet {sheet_name!r} not found. Available sheets: {available_names}"
        )

    return {
        "file_name": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "sheet_count": len(sheets),
        "selected_sheet": sheet_name,
        "sheets": sheets,
    }


def _print_text(report: dict[str, Any]) -> None:
    print(f"WORKBOOK: {report['file_name']}")
    print(f"SIZE_BYTES: {report['size_bytes']}")
    print(f"SHA256: {report['sha256']}")
    print(f"SHEETS: {report['sheet_count']}")
    if report.get("selected_sheet"):
        print(f"SELECTED_SHEET: {report['selected_sheet']}")
    print()

    for sheet in report["sheets"]:
        print(f"SHEET: {sheet.get('name')}")
        print(f"STATE: {sheet.get('state')}")
        print(f"DIMENSION: {sheet.get('dimension')}")
        print(f"XML_ROWS: {sheet.get('xml_row_count')}")
        print(f"NON_EMPTY_ROWS: {sheet.get('non_empty_row_count')}")
        if sheet.get("error"):
            print(f"ERROR: {sheet['error']}")
        for row in sheet.get("preview_rows", []):
            formatted = " | ".join(f"{cell['ref']}={cell['value']!r}" for cell in row)
            print(formatted)
        print("-" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only XLSX source-package inspector.")
    parser.add_argument("path", type=Path, help="Path to the XLSX workbook to inspect.")
    parser.add_argument("--rows", type=int, default=8, help="Non-empty rows to preview per sheet.")
    parser.add_argument("--sheet", help="Inspect only the worksheet with this exact name.")
    parser.add_argument(
        "--expected-sha256",
        help="Fail if the workbook SHA-256 does not match this value.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    if args.rows < 0 or args.rows > 200:
        parser.error("--rows must be between 0 and 200")

    report = inspect_workbook(args.path, args.rows, args.sheet)
    if args.expected_sha256:
        expected = args.expected_sha256.upper()
        if report["sha256"] != expected:
            raise SystemExit(
                "SHA-256 mismatch: "
                f"expected {expected}, got {report['sha256']}. Refusing to inspect as the reviewed file."
            )

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        _print_text(report)


if __name__ == "__main__":
    main()
