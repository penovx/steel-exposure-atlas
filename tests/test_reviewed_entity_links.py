from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "reviewed-entity-links.v1.json"
EXPECTED_SNAPSHOT = "049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015"


class ReviewedEntityLinksTests(unittest.TestCase):
    def test_registry_is_source_scoped_and_reviewed(self) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["schema"],
            "steel-exposure-atlas/reviewed-entity-links-v1.0",
        )
        self.assertGreaterEqual(len(payload["links"]), 1)

        resolution_ids: set[str] = set()
        for link in payload["links"]:
            resolution_id = link["resolution_id"]
            self.assertNotIn(resolution_id, resolution_ids)
            resolution_ids.add(resolution_id)

            self.assertIn(
                link["decision"],
                {"same_legal_entity", "not_same_entity", "unresolved"},
            )
            self.assertEqual(link["resolution_method"], "human_review_corroborated")
            self.assertEqual(link["left"]["source"], "gem")
            self.assertEqual(link["right"]["source"], "eu_financial_sanctions")
            self.assertEqual(link["right"]["snapshot_sha256"], EXPECTED_SNAPSHOT)
            self.assertGreaterEqual(len(link["evidence"]), 2)
            self.assertTrue(all(item.get("url", "").startswith("https://") for item in link["evidence"]))

    def test_same_entity_decisions_are_not_plant_level_findings(self) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        for link in payload["links"]:
            if link["decision"] != "same_legal_entity":
                continue
            self.assertEqual(link["downstream_state"], "direct_list_match")
            note = link["review_note"].lower()
            self.assertIn("does not create a plant-level sanctions finding", note)
            self.assertNotIn("sanctions clear", note)
            self.assertNotIn("compliant", note)


if __name__ == "__main__":
    unittest.main()
