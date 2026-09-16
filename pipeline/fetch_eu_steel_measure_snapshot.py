from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

SOURCE_URL = "https://eur-lex.europa.eu/eli/reg_impl/2026/1457/oj/eng"
DEFAULT_RAW = Path("tmp/source-packages/eu-steel-measure/raw/2026-1457.html")
DEFAULT_META = Path("tmp/source-packages/eu-steel-measure/review/2026-1457.meta.json")
DEFAULT_DERIVED = Path(
    "tmp/source-packages/eu-steel-measure/derived/eu-steel-measure-2026-1457.v1.json"
)
SCHEMA = "steel-exposure-atlas/eu-steel-measure-2026-1457-v1.0"
EXPECTED_PRODUCT_NUMBERS = 30


def _clean(value: object) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").replace("\u202f", " ").split())


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table" and self._table is None:
            self._table = []
        elif tag == "tr" and self._table is not None and self._row is None:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None and self._cell is None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(_clean(" ".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if any(self._row):
                self._table.append(self._row)
            self._row = None
            self._cell = None
        elif tag == "table" and self._table is not None:
            if self._table:
                self.tables.append(self._table)
            self._table = None
            self._row = None
            self._cell = None


def _number(value: str) -> float:
    text = _clean(value).replace(" ", "").replace("%", "").replace(",", ".")
    if not text:
        raise ValueError("Missing numeric value in EU steel-measure table.")
    return float(text)


def _codes(value: str) -> tuple[list[str], list[str]]:
    normal = _clean(value)
    found = re.findall(r"(?<!\d)(\d{4}\s*\d{2}\s*\d{2}(?:\s*\d{2})?)(?!\d)", normal)
    codes = [re.sub(r"\s+", "", item) for item in found]
    cn = list(dict.fromkeys(item for item in codes if len(item) == 8))
    taric = list(dict.fromkeys(item for item in codes if len(item) == 10))
    return cn, taric


def _annex_table(html: str) -> list[list[str]]:
    parser = _TableParser()
    parser.feed(html)
    for table in parser.tables:
        flattened = " | ".join(" | ".join(row) for row in table[:3])
        if (
            "Product Number" in flattened
            and "Product category" in flattened
            and "Additional duty rate" in flattened
            and "Order numbers" in flattened
        ):
            return table
    raise ValueError("Could not locate Annex I tariff-quota table in EUR-Lex HTML.")


def parse_annex_i(html: str) -> dict[str, object]:
    table = _annex_table(html)
    product_re = re.compile(r"^\d+(?:\.[AB])?$")
    current: dict[str, object] | None = None
    allocations: list[dict[str, object]] = []
    products: dict[str, dict[str, object]] = {}

    for row in table:
        if not row or row[0] == "Product Number" or row[0].startswith("Volume of tariff quota"):
            continue

        if product_re.fullmatch(_clean(row[0])) and len(row) >= 13:
            number = _clean(row[0])
            category = _clean(row[1])
            cn_codes, taric_codes = _codes(row[2])
            current = {
                "product_number": number,
                "product_category": category,
                "cn_codes": cn_codes,
                "taric_codes": taric_codes,
            }
            products[number] = dict(current)
            allocation_cells = row[3:13]
        elif current is not None and len(row) >= 10:
            allocation_cells = row[-10:]
        else:
            continue

        if len(allocation_cells) != 10:
            continue

        allocation = {
            **current,
            "allocation": _clean(allocation_cells[0]),
            "total_yearly_volume_tonnes": _number(allocation_cells[1]),
            "mfn_part_tonnes": _number(allocation_cells[2]),
            "fta_part_tonnes": _number(allocation_cells[3]),
            "quarterly_volume_tonnes": [
                _number(allocation_cells[4]),
                _number(allocation_cells[5]),
                _number(allocation_cells[6]),
                _number(allocation_cells[7]),
            ],
            "additional_duty_rate_pct": _number(allocation_cells[8]),
            "order_number": _clean(allocation_cells[9]),
        }
        allocations.append(allocation)

    if len(products) != EXPECTED_PRODUCT_NUMBERS:
        raise ValueError(
            f"Expected {EXPECTED_PRODUCT_NUMBERS} Annex-I product numbers, found {len(products)}."
        )
    if not allocations:
        raise ValueError("No EU steel-measure allocation rows parsed.")
    duty_rates = {row["additional_duty_rate_pct"] for row in allocations}
    if duty_rates != {50.0}:
        raise ValueError(f"Unexpected additional-duty rates in Annex I: {sorted(duty_rates)}")

    return {
        "products": [products[key] for key in sorted(products, key=lambda value: (int(value.split('.')[0]), value))],
        "allocations": allocations,
    }


def build_payload(raw: bytes, *, retrieved_at: str) -> dict[str, object]:
    html = raw.decode("utf-8", errors="strict")
    parsed = parse_annex_i(html)
    return {
        "meta": {
            "schema": SCHEMA,
            "publisher": "European Commission",
            "source": "EUR-Lex",
            "regulation": "Commission Implementing Regulation (EU) 2026/1457",
            "source_url": SOURCE_URL,
            "retrieved_at": retrieved_at,
            "raw_sha256": hashlib.sha256(raw).hexdigest().upper(),
            "valid_from": "2026-07-01",
            "valid_to": "2026-12-31",
            "legal_product_categories": 26,
            "annex_product_numbers": EXPECTED_PRODUCT_NUMBERS,
            "additional_duty_rate_pct": 50.0,
            "publication_state": "local derived review output; public publication requires snapshot review",
            "interpretation": (
                "Quota structure only. This dataset does not establish that a GIST plant exports "
                "to the EU, does not classify a plant product into CN/TARIC, and does not report "
                "live quota balances."
            ),
        },
        **parsed,
    }


def fetch(url: str = SOURCE_URL) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SteelExposureAtlas/1.0 (+https://github.com/penovx/steel-exposure-atlas)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - pinned HTTPS source
        if response.status != 200:
            raise RuntimeError(f"EUR-Lex returned HTTP {response.status}.")
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch and parse the official EUR-Lex Annex-I quota table for Regulation (EU) 2026/1457."
    )
    parser.add_argument("--url", default=SOURCE_URL)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--meta", type=Path, default=DEFAULT_META)
    parser.add_argument("--output", type=Path, default=DEFAULT_DERIVED)
    args = parser.parse_args()

    raw = fetch(args.url)
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = build_payload(raw, retrieved_at=retrieved_at)

    args.raw.parent.mkdir(parents=True, exist_ok=True)
    args.meta.parent.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.raw.write_bytes(raw)
    args.meta.write_text(
        json.dumps(
            {
                "source_url": args.url,
                "retrieved_at": retrieved_at,
                "sha256": payload["meta"]["raw_sha256"],
                "bytes": len(raw),
                "regulation": payload["meta"]["regulation"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"retrieved_at: {retrieved_at}")
    print(f"sha256: {payload['meta']['raw_sha256']}")
    print(f"bytes: {len(raw)}")
    print(f"legal product categories: {payload['meta']['legal_product_categories']}")
    print(f"Annex-I product numbers: {len(payload['products'])}")
    print(f"allocation rows: {len(payload['allocations'])}")
    print(f"additional duty rate: {payload['meta']['additional_duty_rate_pct']:.0f}%")
    print(f"validity: {payload['meta']['valid_from']} to {payload['meta']['valid_to']}")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
