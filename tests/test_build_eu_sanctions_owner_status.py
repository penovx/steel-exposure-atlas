from __future__ import annotations

import unittest

from pipeline.build_eu_sanctions_owner_status import build_status_layer


class EuSanctionsOwnerStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gist = {
            "plants": [
                {"plant_id": "P1", "owner_gem_entity_id": "E1", "owner_name": "Acme Steel GmbH"},
                {"plant_id": "P2", "owner_gem_entity_id": "E2", "owner_name": "Beta Metals Ltd"},
                {"plant_id": "P3", "owner_gem_entity_id": "E3", "owner_name": "Gamma Steel"},
            ]
        }
        self.sanctions = {
            "meta": {
                "raw_sha256": "ABC123",
                "file_generation_dates": ["05/08/2026"],
            },
            "entities": [
                {
                    "entity_id": "10",
                    "names": ["Acme Steel GmbH"],
                    "eu_reference_numbers": ["EU.10"],
                },
                {
                    "entity_id": "20",
                    "names": ["Beta Metals Limited"],
                    "eu_reference_numbers": ["EU.20"],
                },
            ],
        }
        self.registry = {
            "schema": "steel-exposure-atlas/reviewed-entity-links-v1.0",
            "links": [
                {
                    "resolution_id": "REL-1",
                    "left": {"source": "gem", "entity_id": "E1"},
                    "right": {
                        "source": "eu_financial_sanctions",
                        "entity_id": "10",
                        "eu_reference": "EU.10",
                        "snapshot_sha256": "ABC123",
                    },
                    "decision": "same_legal_entity",
                    "resolution_method": "human_review_corroborated",
                    "reviewed_at": "2026-09-16",
                    "downstream_state": "direct_list_match",
                }
            ],
        }

    def test_builds_three_categorical_states_without_percentages(self) -> None:
        payload = build_status_layer(self.gist, self.sanctions, self.registry)
        by_company = {item["company_id"]: item for item in payload["statuses"]}

        self.assertEqual(by_company["E1"]["state"], "direct_list_match")
        self.assertEqual(by_company["E1"]["identity_resolution"], "confirmed")
        self.assertEqual(by_company["E2"]["state"], "review_required")
        self.assertEqual(
            by_company["E3"]["state"], "no_direct_list_match_in_snapshot"
        )

        self.assertEqual(
            payload["meta"]["counts"],
            {
                "direct_list_match": 1,
                "review_required": 1,
                "no_direct_list_match_in_snapshot": 1,
            },
        )
        serialized = repr(payload).lower()
        self.assertNotIn("85%", serialized)
        self.assertNotIn("risk score", repr(payload["statuses"]).lower())
        self.assertIn("no sanctions percentage", payload["meta"]["display_semantics"].lower())

    def test_no_direct_match_is_explicitly_not_clearance(self) -> None:
        payload = build_status_layer(self.gist, self.sanctions, self.registry)
        boundary = payload["meta"]["negative_result_boundary"].lower()
        self.assertIn("not sanctions clearance", boundary)

    def test_output_is_company_level_not_plant_level(self) -> None:
        payload = build_status_layer(self.gist, self.sanctions, self.registry)
        serialized = repr(payload["statuses"])
        self.assertNotIn("P1", serialized)
        self.assertNotIn("plant_id", serialized)


if __name__ == "__main__":
    unittest.main()
