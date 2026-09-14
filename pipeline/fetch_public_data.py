#!/usr/bin/env python3
"""Fetch reviewed public inputs with pinned source identity.

This script intentionally handles only sources that are already approved for the
specific publication use recorded in data/source-registry.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

NATURAL_EARTH_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "v5.1.1/geojson/ne_110m_admin_0_countries.geojson"
)
NATURAL_EARTH_GIT_BLOB_SHA1 = "1e6ab74c7042f97013be69ceec798be8e1aff27d"
OUTPUT_PATH = Path("public/data/ne_110m_admin_0_countries.v5.1.1.geojson")


def git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def validate_geojson(payload: bytes) -> dict:
    data = json.loads(payload)
    if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
        raise ValueError("Expected a GeoJSON FeatureCollection with a features array.")
    if not data["features"]:
        raise ValueError("GeoJSON FeatureCollection contains no features.")
    return data


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "steel-exposure-atlas/0"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def fetch_natural_earth(output: Path = OUTPUT_PATH) -> Path:
    payload = fetch(NATURAL_EARTH_URL)
    actual_sha = git_blob_sha1(payload)
    if actual_sha != NATURAL_EARTH_GIT_BLOB_SHA1:
        raise ValueError(
            "Natural Earth source identity mismatch: "
            f"expected {NATURAL_EARTH_GIT_BLOB_SHA1}, got {actual_sha}."
        )
    data = validate_geojson(payload)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch approved public atlas data.")
    parser.add_argument(
        "source",
        choices=["natural-earth"],
        help="Reviewed source to fetch.",
    )
    args = parser.parse_args()

    if args.source == "natural-earth":
        path = fetch_natural_earth()
        print(f"Wrote reviewed Natural Earth basemap to {path}")


if __name__ == "__main__":
    main()
