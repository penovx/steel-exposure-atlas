from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "reviewed-entity-links.v1.json"
EU_SNAPSHOT = "049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015"
OFAC_SDN_SNAPSHOT = "3D594ED7CDB5E0FD13F126A3815255146D730F791DCF672665C67416D03A7C1F"
OFAC_CONSOLIDATED_SNAPSHOT = "C59772F3EDD625812AC43C4AEC57513D08CDD180135A3B6368DBC086AB81DF7D"


class ReviewedEntityLinksTests(unittest.TestCase):
    def test_registry_is_source_scoped_and_reviewed(self) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["schema"],
            "steel-exposure-atlas/reviewed-entity-links-v1.0",
        )
        self.assertGreaterEqual(len(payload["links"]), 1)

        resolution_ids: set[str] = set()
        seen_sources: set[str] = set()
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

            right = link["right"]
            source = right["source"]
            seen_sources.add(source)
            self.assertIn(source, {"eu_financial_sanctions", "ofac"})
            if source == "eu_financial_sanctions":
                self.assertEqual(right["snapshot_sha256"], EU_SNAPSHOT)
                self.assertTrue(right["eu_reference"])
            else:
                self.assertIn(right["source_list"], {"SDN", "Consolidated Non-SDN"})
                expected = (
                    OFAC_SDN_SNAPSHOT
                    if right["source_list"] == "SDN"
                    else OFAC_CONSOLIDATED_SNAPSHOT
                )
                self.assertEqual(right["snapshot_sha256"], expected)
                self.assertTrue(right["ofac_uid"])

            self.assertGreaterEqual(len(link["evidence"]), 2)
            self.assertTrue(
                all(item.get("url", "").startswith("https://") for item in link["evidence"])
            )

        self.assertIn("eu_financial_sanctions", seen_sources)
        self.assertIn("ofac", seen_sources)

    def test_same_entity_decisions_are_not_plant_level_findings(self) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        for link in payload["links"]:
            if link["decision"] != "same_legal_entity":
                continue
            self.assertEqual(link["downstream_state"], "direct_list_match")
            note = link["review_note"].lower()
            self.assertTrue("plant-level" in note or "company identity only" in note)
            self.assertNotIn("sanctions clear", note)
            self.assertNotIn("compliant", note)


if __name__ == "__main__":
    unittest.main()
