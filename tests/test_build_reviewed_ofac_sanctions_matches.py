from __future__ import annotations

import copy
import unittest

from pipeline.build_reviewed_ofac_sanctions_matches import build_reviewed_matches


SDN_HASH = "A" * 64
CONSOLIDATED_HASH = "B" * 64


def gist() -> dict[str, object]:
    return {
        "plants": [
            {"plant_id": "P1", "owner_gem_entity_id": "E1", "owner_name": "Alpha Steel"},
            {"plant_id": "P2", "owner_gem_entity_id": "E2", "owner_name": "Beta Metals"},
        ]
    }


def sanctions() -> dict[str, object]:
    return {
        "meta": {
            "files": {
                "sdn": {"raw_sha256": SDN_HASH, "publish_date": "09/16/2026"},
                "consolidated_non_sdn": {
                    "raw_sha256": CONSOLIDATED_HASH,
                    "publish_date": "09/14/2026",
                },
            }
        },
        "entities": [
            {
                "entity_id": "ofac-sdn:100",
                "source_list": "SDN",
                "ofac_uid": "100",
                "programmes": ["TEST-SDN"],
            },
            {
                "entity_id": "ofac-consolidated-non-sdn:200",
                "source_list": "Consolidated Non-SDN",
                "ofac_uid": "200",
                "programmes": ["TEST-CNS"],
            },
        ],
    }


def registry() -> dict[str, object]:
    return {
        "schema": "steel-exposure-atlas/reviewed-entity-links-v1.0",
        "links": [
            {
                "resolution_id": "REL-EU",
                "left": {"source": "gem", "entity_id": "E1"},
                "right": {"source": "eu_financial_sanctions", "entity_id": "EU1"},
                "decision": "same_legal_entity",
                "downstream_state": "direct_list_match",
            },
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
            },
            {
                "resolution_id": "REL-OFAC-2",
                "left": {"source": "gem", "entity_id": "E2"},
                "right": {
                    "source": "ofac",
                    "entity_id": "ofac-consolidated-non-sdn:200",
                    "ofac_uid": "200",
                    "source_list": "Consolidated Non-SDN",
                    "snapshot_sha256": CONSOLIDATED_HASH,
                },
                "decision": "same_legal_entity",
                "downstream_state": "direct_list_match",
                "reviewed_at": "2026-09-16",
                "resolution_method": "human_review_corroborated",
            },
        ],
    }


class ReviewedOfacMatchesTests(unittest.TestCase):
    def test_builds_reviewed_matches_and_ignores_other_sources(self) -> None:
        payload = build_reviewed_matches(gist(), sanctions(), registry())
        self.assertEqual(payload["meta"]["direct_company_matches"], 2)
        self.assertEqual(
            payload["meta"]["source_snapshot_sha256"],
            {"SDN": SDN_HASH, "Consolidated Non-SDN": CONSOLIDATED_HASH},
        )
        matches = payload["matches"]
        self.assertEqual(matches[0]["company_id"], "E1")
        self.assertEqual(matches[0]["source_list"], "SDN")
        self.assertEqual(matches[0]["programmes"], ["TEST-SDN"])
        self.assertEqual(matches[1]["source_list"], "Consolidated Non-SDN")

    def test_snapshot_hash_must_match_the_entity_source_list(self) -> None:
        bad = registry()
        bad["links"][1]["right"]["snapshot_sha256"] = "C" * 64  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "snapshot hash"):
            build_reviewed_matches(gist(), sanctions(), bad)

    def test_ofac_uid_must_match_source_entity(self) -> None:
        bad = registry()
        bad["links"][1]["right"]["ofac_uid"] = "999"  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "OFAC UID"):
            build_reviewed_matches(gist(), sanctions(), bad)

    def test_unknown_ofac_entity_is_rejected(self) -> None:
        bad = registry()
        bad["links"][1]["right"]["entity_id"] = "ofac-sdn:999"  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "unknown OFAC entity"):
            build_reviewed_matches(gist(), sanctions(), bad)

    def test_same_entity_resolution_must_downstream_to_direct_match(self) -> None:
        bad = registry()
        bad["links"][1]["downstream_state"] = "review_required"  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "must downstream"):
            build_reviewed_matches(gist(), sanctions(), bad)


if __name__ == "__main__":
    unittest.main()
