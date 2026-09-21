from __future__ import annotations

import json
import unittest
from pathlib import Path

from pipeline.build_eu_steel_trade_context import (
    DEFAULT_OUTPUT,
    EXPECTED_BILATERAL_SHA256,
    EXPECTED_MEASURE_SHA256,
)

ROOT = Path(__file__).resolve().parents[1]


class EuSteelTradePublicationContractTests(unittest.TestCase):
    def test_public_builder_targets_reviewed_public_data_path(self) -> None:
        self.assertEqual(DEFAULT_OUTPUT, Path("public/data/eu-steel-trade-context.v1.json"))

    def test_source_registry_pins_both_reviewed_legal_snapshots(self) -> None:
        registry = json.loads((ROOT / "data" / "source-registry.json").read_text(encoding="utf-8"))
        source = next(
            item for item in registry["sources"] if item["id"] == "eu-steel-import-measures-2026"
        )
        self.assertEqual(source["status"], "approved_for_publication")
        self.assertEqual(source["publication_status"], "approved_for_publication")
        artifacts = {item["file"]: item for item in source["source_artifacts"]}
        self.assertEqual(artifacts["2026-1457.html"]["sha256"], EXPECTED_MEASURE_SHA256)
        self.assertEqual(artifacts["2026-1930.html"]["sha256"], EXPECTED_BILATERAL_SHA256)
        self.assertEqual(artifacts["2026-1457.html"]["repository_policy"], "do_not_commit")
        self.assertEqual(artifacts["2026-1930.html"]["repository_policy"], "do_not_commit")

    def test_review_records_publication_approval(self) -> None:
        review = (ROOT / "docs" / "source-reviews" / "2026-09-16-eu-steel-import-measure-snapshot-review.md").read_text(encoding="utf-8")
        self.assertIn("Approved for publication of a minimal derived EU steel import-context layer", review)
        self.assertIn(EXPECTED_MEASURE_SHA256, review)
        self.assertIn(EXPECTED_BILATERAL_SHA256, review)
        self.assertIn("764", review)
        self.assertIn("482", review)
        self.assertIn("282", review)


if __name__ == "__main__":
    unittest.main()
