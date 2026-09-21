from __future__ import annotations

import unittest

from pipeline.build_ofac_sanctions_owner_status import build_status_layer


SDN_HASH = "A" * 64
CONSOLIDATED_HASH = "B" * 64


def gist() -> dict[str, object]:
    return {
        "meta": {"schema": "steel-exposure-atlas/gist-public-v1"},
        "plants": [
            {"plant_id": "P1", "owner_gem_entity_id": "E1", "owner_name": "Alpha Steel Co"},
            {"plant_id": "P2", "owner_gem_entity_id": "E2", "owner_name": "Beta Metals Co"},
            {"plant_id": "P3", "owner_gem_entity_id": "E3", "owner_name": "Gamma Works"},
        ],
    }


def sanctions() -> dict[str, object]:
    return {
        "meta": {
            "schema": "steel-exposure-atlas/ofac-sanctions-entities-v1.0",
            "files": {
                "sdn": {
                    "raw_sha256": SDN_HASH,
                    "publish_date": "09/16/2026",
                },
                "consolidated_non_sdn": {
                    "raw_sha256": CONSOLIDATED_HASH,
                    "publish_date": "09/14/2026",
                },
            },
        },
        "entities": [
            {
                "entity_id": "ofac-sdn:100",
                "source_list": "SDN",
                "ofac_uid": "100",
                "names": ["ALPHA STEEL CO"],
                "programmes": ["TEST-SDN"],
            },
            {
                "entity_id": "ofac-sdn:200",
                "source_list": "SDN",
                "ofac_uid": "200",
                "names": ["BETA METALS"],
                "programmes": ["TEST-SDN"],
            },
        ],
    }


def registry() -> dict[str, object]:
    return {
        "schema": "steel-exposure-atlas/reviewed-entity-links-v1.0",
        "links": [
            {
                "resolution_id": "REL-OFAC-1",
                "left": {"source": "gem", "entity_id": "E1"},
                "right": {
                    "source": "ofac",
                    "entity_id": "ofac-sdn:100",
                    "ofac_uid": "100",
                    "source_list": "SDN",
                    "snapshot_sha256": SDN_HASH,
                },
                "decision": "same_legal_entity",
                "downstream_state": "direct_list_match",
                "reviewed_at": "2026-09-16",
                "resolution_method": "human_review_corroborated",
            }
        ],
    }


class OfacOwnerStatusTests(unittest.TestCase):
    def test_builds_direct_review_and_no_match_states(self) -> None:
        payload = build_status_layer(gist(), sanctions(), registry())
        self.assertEqual(payload["meta"]["screened_owner_identities"], 3)
        self.assertEqual(
            payload["meta"]["counts"],
            {
                "direct_list_match": 1,
                "review_required": 1,
                "no_direct_list_match_in_snapshot": 1,
            },
        )
        statuses = {item["company_id"]: item for item in payload["statuses"]}
        self.assertEqual(statuses["E1"]["state"], "direct_list_match")
        self.assertEqual(statuses["E1"]["reviewed_matches"][0]["ofac_uid"], "100")
        self.assertEqual(statuses["E2"]["state"], "review_required")
        self.assertEqual(statuses["E2"]["candidate_basis"], "review_required_legal_form")
        self.assertEqual(statuses["E3"]["state"], "no_direct_list_match_in_snapshot")

    def test_preserves_source_publish_dates_and_hashes(self) -> None:
        payload = build_status_layer(gist(), sanctions(), registry())
        self.assertEqual(
            payload["meta"]["source_snapshot_sha256"],
            {"SDN": SDN_HASH, "Consolidated Non-SDN": CONSOLIDATED_HASH},
        )
        self.assertEqual(payload["meta"]["source_publish_dates"]["SDN"], "09/16/2026")
        self.assertEqual(
            payload["meta"]["source_publish_dates"]["Consolidated Non-SDN"],
            "09/14/2026",
        )

    def test_negative_boundary_is_explicit(self) -> None:
        payload = build_status_layer(gist(), sanctions(), registry())
        self.assertIn("not sanctions clearance", payload["meta"]["negative_result_boundary"])
        self.assertIn("No separate plant-level", payload["meta"]["scope"])


if __name__ == "__main__":
    unittest.main()
