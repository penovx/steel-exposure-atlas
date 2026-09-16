from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

SOURCE_URL = "https://eur-lex.europa.eu/eli/reg_impl/2026/1930/oj/eng"
DEFAULT_RAW = Path("tmp/source-packages/eu-steel-measure/raw/2026-1930.html")
DEFAULT_META = Path("tmp/source-packages/eu-steel-measure/review/2026-1930.meta.json")
DEFAULT_DERIVED = Path(
    "tmp/source-packages/eu-steel-measure/derived/eu-steel-bilateral-2026-1930.v1.json"
)
SCHEMA = "steel-exposure-atlas/eu-steel-bilateral-2026-1930-v1.0"
EXPECTED_COUNTRIES = [
    "Albania",
    "Israel",
    "Jordan",
    "Morocco",
    "North Macedonia",
    "Serbia",
    "Switzerland",
    "Tunisia",
    "Türkiye",
]


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.replace("\xa0", " ").replace("\u202f", " ").split())
        if text:
            self.parts.append(text)


def _plain_text(html: str) -> str:
    parser = _TextParser()
    parser.feed(html)
    return " ".join(parser.parts)


def parse_article_1(html: str) -> dict[str, object]:
    text = _plain_text(html)
    match = re.search(r"Article\s+1\s+(.*?)\s+Article\s+2", text, flags=re.IGNORECASE)
    if not match:
        raise ValueError("Could not locate Article 1 in Regulation (EU) 2026/1930.")
    article = match.group(1)

    countries = [country for country in EXPECTED_COUNTRIES if country in article]
    if countries != EXPECTED_COUNTRIES:
        missing = [country for country in EXPECTED_COUNTRIES if country not in countries]
        raise ValueError(f"Article 1 country set is incomplete: missing {missing}")

    if not re.search(r"50\s*%\s*ad\s*valorem", article, flags=re.IGNORECASE):
        raise ValueError("Could not confirm the 50% ad valorem out-of-quota duty in Article 1.")
    if not re.search(r"once\s+the\s+tariff\s+quota.*?has\s+been\s+exhausted", article, flags=re.IGNORECASE):
        raise ValueError("Could not confirm the quota-exhaustion trigger in Article 1.")

    return {
        "countries": countries,
        "additional_duty_rate_pct": 50.0,
        "trigger": "applicable tariff quota exhausted",
    }


def build_payload(raw: bytes, *, retrieved_at: str) -> dict[str, object]:
    html = raw.decode("utf-8", errors="strict")
    parsed = parse_article_1(html)
    return {
        "meta": {
            "schema": SCHEMA,
            "publisher": "European Commission",
            "source": "EUR-Lex",
            "regulation": "Commission Implementing Regulation (EU) 2026/1930",
            "source_url": SOURCE_URL,
            "retrieved_at": retrieved_at,
            "raw_sha256": hashlib.sha256(raw).hexdigest().upper(),
            "valid_from": "2026-08-06",
            "legal_route": "bilateral safeguard measure",
            "publication_state": "local derived review output; public publication requires snapshot review",
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
        description="Fetch and validate the official EUR-Lex bilateral steel safeguard Regulation (EU) 2026/1930."
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
    print(f"bilateral safeguard origins: {len(payload['countries'])}")
    print(f"additional duty rate: {payload['additional_duty_rate_pct']:.0f}%")
    print(f"valid from: {payload['meta']['valid_from']}")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
