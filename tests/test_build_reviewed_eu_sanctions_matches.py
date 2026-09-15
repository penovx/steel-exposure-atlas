from __future__ import annotations

import unittest

from pipeline.build_reviewed_eu_sanctions_matches import build_reviewed_matches


class ReviewedEuSanctionsMatchesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gist = {
            "plants": [
                {
                    "plant_id": "P1",
                    "owner_gem_entity_id": "E1",
                    "owner_name": "Acme Steel",
                },
                {
                    "plant_id": "P2",
                    "owner_gem_entity_id": "E2",
                    "owner_name": "Other Steel",
                },
            ]
        }
        self.sanctions = {
            "meta": {"raw_sha256": "ABC"},
            "entities": [
                {
                    "entity_id": "10",
                    "eu_reference_numbers": ["EU.10"],
                    "names": ["Acme Steel Limited"],
                }
            ],
        }
        self.registry = {
            "schema": "steel-exposure-atlas/reviewed-entity-links-v1.0",
            "links": [
                {
                    "resolution_id": "R1",
                    "left": {"source": "gem", "entity_id": "E1"},
                    "right": {
                        "source": "eu_financial_sanctions",
                        "entity_id": "10",
                        "eu_reference": "EU.10",
                        "snapshot_sha256": "ABC",
                    },
                    "decision": "same_legal_entity",
                    "resolution_method": "human_review_corroborated",
                    "reviewed_at": "2026-09-16",
                    "downstream_state": "direct_list_match",
                    "evidence": [],
                    "review_note": "Company identity only; no plant-level finding.",
                }
            ],
        }

    def test_exports_only_reviewed_positive_company_matches(self) -> None:
        payload = build_reviewed_matches(self.gist, self.sanctions, self.registry)
        self.assertEqual(payload["meta"]["direct_company_matches"], 1)
        self.assertEqual(len(payload["matches"]), 1)
        match = payload["matches"][0]
        self.assertEqual(match["company_id"], "E1")
        self.assertEqual(match["state"], "direct_list_match")
        self.assertEqual(match["matched_entity_id"], "10")
        serialized = repr(payload)
        self.assertNotIn("no_direct_list_match_in_snapshot", serialized)
        self.assertNotIn("plant_id", serialized)

    def test_unresolved_and_not_same_links_are_not_exported(self) -> None:
        for decision in ("unresolved", "not_same_entity"):
            registry = {**self.registry, "links": [{**self.registry["links"][0], "decision": decision}]}
            payload = build_reviewed_matches(self.gist, self.sanctions, registry)
            self.assertEqual(payload["matches"], [])

    def test_snapshot_hash_mismatch_fails(self) -> None:
        registry = {
            **self.registry,
            "links": [
                {
                    **self.registry["links"][0],
                    "right": {
                        **self.registry["links"][0]["right"],
                        "snapshot_sha256": "DIFFERENT",
                    },
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "snapshot hash"):
            build_reviewed_matches(self.gist, self.sanctions, registry)

    def test_unknown_gem_owner_fails(self) -> None:
        registry = {
            **self.registry,
            "links": [
                {
                    **self.registry["links"][0],
                    "left": {"source": "gem", "entity_id": "MISSING"},
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "unknown GEM owner"):
            build_reviewed_matches(self.gist, self.sanctions, registry)

    def test_wrong_eu_reference_fails(self) -> None:
        registry = {
            **self.registry,
            "links": [
                {
                    **self.registry["links"][0],
                    "right": {
                        **self.registry["links"][0]["right"],
                        "eu_reference": "EU.WRONG",
                    },
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "EU reference"):
            build_reviewed_matches(self.gist, self.sanctions, registry)


if __name__ == "__main__":
    unittest.main()
