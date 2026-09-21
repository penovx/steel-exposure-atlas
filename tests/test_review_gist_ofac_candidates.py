from __future__ import annotations

import unittest

from pipeline.review_gist_ofac_candidates import SCHEMA, build_review


class OfacCandidateReviewTests(unittest.TestCase):
    def test_build_review_keeps_candidate_context_without_promoting_match(self) -> None:
        candidates = {
            "candidates": [
                {
                    "owner_gem_entity_id": "E100",
                    "owner_names": ["Example Steel Holdings"],
                    "plant_count": 1,
                    "state": "review_required_exact_name",
                    "candidate_ofac_entity_ids": ["ofac-sdn:100"],
                    "candidate_source_lists": ["SDN"],
                    "candidate_programmes": ["EXAMPLE"],
                    "evidence_name_pairs": [
                        {
                            "owner_name": "Example Steel Holdings",
                            "source_name": "Example Steel Holdings",
                        }
                    ],
                },
                {
                    "owner_gem_entity_id": "E200",
                    "owner_names": ["No Candidate Metals"],
                    "plant_count": 1,
                    "state": "no_name_candidate",
                    "candidate_ofac_entity_ids": [],
                    "candidate_source_lists": [],
                    "candidate_programmes": [],
                    "evidence_name_pairs": [],
                },
            ]
        }
        ofac = {
            "entities": [
                {
                    "entity_id": "ofac-sdn:100",
                    "source_list": "SDN",
                    "ofac_uid": "100",
                    "primary_name": "Example Steel Holdings",
                    "names": ["Example Steel Holdings", "Example Steel"],
                    "aliases": [{"name": "Example Steel", "category": "strong"}],
                    "programmes": ["EXAMPLE"],
                    "countries": ["Exampleland"],
                    "addresses": [{"city": "Example City", "country": "Exampleland"}],
                    "identifiers": [{"type": "Registration ID", "value": "ABC123"}],
                }
            ]
        }
        gist = {
            "plants": [
                {
                    "plant_id": "P1",
                    "plant_name": "Example Steel Plant",
                    "country_area": "Exampleland",
                    "owner_gem_entity_id": "E100",
                    "owner_name": "Example Steel Holdings",
                },
                {
                    "plant_id": "P2",
                    "plant_name": "Other Plant",
                    "country_area": "Otherland",
                    "owner_gem_entity_id": "E200",
                    "owner_name": "No Candidate Metals",
                },
            ]
        }

        review = build_review(candidates, ofac, gist)

        self.assertEqual(review["meta"]["schema"], SCHEMA)
        self.assertEqual(review["meta"]["candidate_count"], 1)
        self.assertEqual(review["meta"]["state"], "review_required")
        self.assertIn("does not", review["meta"]["interpretation"])

        item = review["reviews"][0]
        self.assertEqual(item["owner_gem_entity_id"], "E100")
        self.assertEqual(item["plant_count"], 1)
        self.assertEqual(item["candidate_state"], "review_required_exact_name")
        self.assertEqual(item["conclusion"], "review_required")
        self.assertEqual(item["ofac_entities"][0]["source_list"], "SDN")
        self.assertEqual(item["ofac_entities"][0]["ofac_uid"], "100")
        self.assertEqual(item["ofac_entities"][0]["programmes"], ["EXAMPLE"])

    def test_missing_referenced_entity_is_rejected(self) -> None:
        candidates = {
            "candidates": [
                {
                    "owner_gem_entity_id": "E100",
                    "owner_names": ["Example Steel Holdings"],
                    "candidate_ofac_entity_ids": ["ofac-sdn:missing"],
                    "evidence_name_pairs": [],
                }
            ]
        }
        gist = {
            "plants": [
                {
                    "plant_id": "P1",
                    "plant_name": "Example Steel Plant",
                    "country_area": "Exampleland",
                    "owner_gem_entity_id": "E100",
                    "owner_name": "Example Steel Holdings",
                }
            ]
        }

        with self.assertRaisesRegex(ValueError, "missing from subset"):
            build_review(candidates, {"entities": []}, gist)


if __name__ == "__main__":
    unittest.main()
