from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RUNTIME_FILES = (
    "gist-plants.v1.json",
    "ne_110m_admin_0_countries.v5.1.1.geojson",
    "eu-sanctions-owner-status.v1.json",
    "ofac-sanctions-owner-status.v1.json",
    "eu-steel-trade-context.v1.json",
)


class PublicationGovernanceContractTests(unittest.TestCase):
    def test_bundled_runtime_data_is_documented(self) -> None:
        licences = (ROOT / "DATA_LICENSES.md").read_text(encoding="utf-8")
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        self.assertNotIn(
            "No third-party dataset is currently bundled or redistributed by this repository.",
            licences,
        )
        for filename in RUNTIME_FILES:
            self.assertTrue((ROOT / "public" / "data" / filename).exists(), filename)
            self.assertIn(f"public/data/{filename}", licences)

        self.assertIn("Global Energy Monitor", notices)
        self.assertIn("Natural Earth", notices)
        self.assertIn("European Commission / European Union", notices)
        self.assertIn("U.S. Department of the Treasury / OFAC", notices)

    def test_eu_sanctions_snapshot_is_registered(self) -> None:
        registry = json.loads(
            (ROOT / "data" / "source-registry.json").read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(registry["schema_version"], 5)

        source = next(
            item for item in registry["sources"] if item["id"] == "eu-financial-sanctions"
        )
        self.assertEqual(source["status"], "approved_for_publication")
        self.assertEqual(source["publication_status"], "approved_for_publication")
        self.assertEqual(source["retrieved_at"], "2026-09-15T21:53:03+00:00")
        artifact = source["source_artifacts"][0]
        self.assertEqual(
            artifact["sha256"],
            "049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015",
        )
        self.assertEqual(artifact["source_file_generation_date"], "05/08/2026")
        self.assertEqual(artifact["repository_policy"], "do_not_commit")

    def test_natural_earth_identity_is_pinned_without_invented_retrieval_date(self) -> None:
        registry = json.loads(
            (ROOT / "data" / "source-registry.json").read_text(encoding="utf-8")
        )
        source = next(
            item
            for item in registry["sources"]
            if item["id"] == "natural-earth-admin0-110m"
        )
        self.assertIsNone(source["retrieved_at"])
        artifact = source["source_artifacts"][0]
        self.assertEqual(
            artifact["git_blob_sha1"],
            "1e6ab74c7042f97013be69ceec798be8e1aff27d",
        )
        self.assertIn(
            "exact retrieval timestamp was not separately recorded",
            source["review_notes"],
        )


if __name__ == "__main__":
    unittest.main()
