from __future__ import annotations

import unittest

from pipeline.review_gist_eu_sanctions_candidate import build_review


class ReviewGistEuSanctionsCandidateTests(unittest.TestCase):
    def test_builds_local_review_for_single_candidate(self) -> None:
        candidates = {
            "candidates": [
                {
                    "owner_gem_entity_id": "E1",
                    "owner_names": ["Acme Steel Limited"],
                    "plant_count": 1,
                    "state": "review_required_legal_form",
                    "candidate_eu_entity_ids": ["10"],
                    "evidence_name_pairs": [
                        {
                            "owner_name": "Acme Steel Limited",
                            "source_name": "Acme Steel Ltd",
                        }
                    ],
                },
                {
                    "owner_gem_entity_id": "E2",
                    "owner_names": ["Other Steel"],
                    "plant_count": 1,
                    "state": "no_name_candidate",
                    "candidate_eu_entity_ids": [],
                    "evidence_name_pairs": [],
                },
            ]
        }
        sanctions = {
            "entities": [
                {
                    "entity_id": "10",
                    "names": ["Acme Steel Ltd"],
                    "eu_reference_numbers": ["EU.10"],
                    "designation_dates": ["01/01/2025"],
                    "programmes": ["TEST"],
                    "countries_iso2": ["DE"],
                    "countries": ["Germany"],
                    "identifiers": [
                        {
                            "type_code": "regnumber",
                            "type_description": "Registration Number",
                            "value": "HRB123",
                        }
                    ],
                }
            ]
        }
        gist = {
            "plants": [
                {
                    "plant_id": "P1",
                    "plant_name": "Acme Works",
                    "owner_gem_entity_id": "E1",
                    "owner_name": "Acme Steel Limited",
                    "country_area": "France",
                }
            ]
        }

        review = build_review(candidates, sanctions, gist)
        self.assertEqual(review["meta"]["state"], "review_required")
        self.assertEqual(review["gist_owner"]["owner_gem_entity_id"], "E1")
        self.assertEqual(review["candidate"]["state"], "review_required_legal_form")
        self.assertEqual(review["candidate"]["eu_entities"][0]["entity_id"], "10")
        self.assertIn("not a sanctions finding", review["meta"]["interpretation"])

    def test_multiple_candidates_require_owner_id(self) -> None:
        candidates = {
            "candidates": [
                {
                    "owner_gem_entity_id": "E1",
                    "candidate_eu_entity_ids": ["10"],
                },
                {
                    "owner_gem_entity_id": "E2",
                    "candidate_eu_entity_ids": ["20"],
                },
            ]
        }
        sanctions = {
            "entities": [
                {"entity_id": "10", "names": ["A"]},
                {"entity_id": "20", "names": ["B"]},
            ]
        }
        gist = {
            "plants": [
                {"plant_id": "P1", "owner_gem_entity_id": "E1"},
                {"plant_id": "P2", "owner_gem_entity_id": "E2"},
            ]
        }
        with self.assertRaisesRegex(ValueError, "Pass --owner-id"):
            build_review(candidates, sanctions, gist)

    def test_plant_country_is_retained_only_as_plant_context(self) -> None:
        candidates = {
            "candidates": [
                {
                    "owner_gem_entity_id": "E1",
                    "owner_names": ["Acme"],
                    "state": "review_required_exact_name",
                    "candidate_eu_entity_ids": ["10"],
                    "evidence_name_pairs": [],
                }
            ]
        }
        sanctions = {
            "entities": [
                {
                    "entity_id": "10",
                    "names": ["Acme"],
                    "countries_iso2": ["DE"],
                    "countries": ["Germany"],
                }
            ]
        }
        gist = {
            "plants": [
                {
                    "plant_id": "P1",
                    "owner_gem_entity_id": "E1",
                    "country_area": "France",
                }
            ]
        }
        review = build_review(candidates, sanctions, gist)
        self.assertEqual(review["gist_owner"]["plants"][0]["country_area"], "France")
        self.assertEqual(
            review["candidate"]["eu_entities"][0]["countries_iso2"], ["DE"]
        )
        self.assertIn("plant country is not owner domicile", review["meta"]["interpretation"])


if __name__ == "__main__":
    unittest.main()
