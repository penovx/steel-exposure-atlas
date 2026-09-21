from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "ofac-designation-context.v1.json"


class OfacDesignationContextTests(unittest.TestCase):
    def test_reviewed_designation_context_is_complete_for_current_matches(self) -> None:
        payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "steel-exposure-atlas/ofac-designation-context-v1.0")
        records = payload["records"]
        self.assertEqual(len(records), 8)
        entity_ids = [item["entity_id"] for item in records]
        self.assertEqual(len(entity_ids), len(set(entity_ids)))
        for item in records:
            self.assertRegex(item["entity_id"], r"^ofac-sdn:\d+$")
            self.assertRegex(item["listed_since"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertTrue(item["designation_summary"])
            self.assertTrue(item["designation_action"])
            self.assertTrue(item["source_url"].startswith("https://ofac.treasury.gov/recent-actions/"))

    def test_status_builder_attaches_designation_context_in_production_path(self) -> None:
        builder = (ROOT / "pipeline" / "build_ofac_sanctions_owner_status.py").read_text(encoding="utf-8")
        self.assertIn("DEFAULT_DESIGNATIONS", builder)
        self.assertIn("designation_context", builder)
        self.assertIn('"listed_since"', builder)
        self.assertIn('"designation_summary"', builder)
        self.assertIn('"designation_source_url"', builder)
        self.assertIn("Reviewed SDN match", builder)


if __name__ == "__main__":
    unittest.main()
