from __future__ import annotations

import unittest

from pipeline.profile_gist_eu_sanctions_candidates import build_profile


class GistEuSanctionsCandidateProfileTests(unittest.TestCase):
    def test_exact_names_remain_review_candidates(self) -> None:
        gist = {
            "meta": {"schema": "steel-exposure-atlas/gist-plant-v1.0"},
            "plants": [
                {
                    "plant_id": "P1",
                    "owner_gem_entity_id": "E1",
                    "owner_name": "Acme Steel GmbH",
                },
                {
                    "plant_id": "P2",
                    "owner_gem_entity_id": "E1",
                    "owner_name": "ACME Steel GmbH",
                },
            ],
        }
        sanctions = {
            "meta": {"raw_sha256": "ABC"},
            "entities": [
                {"entity_id": "10", "names": ["Acme Steel GmbH"]},
            ],
        }

        payload = build_profile(gist, sanctions)
        self.assertEqual(payload["counts"]["review_required_exact_name"], 1)
        self.assertEqual(payload["counts"]["plants_under_candidate_owners"], 2)
        candidate = payload["candidates"][0]
        self.assertEqual(candidate["state"], "review_required_exact_name")
        self.assertEqual(candidate["candidate_eu_entity_ids"], ["10"])

    def test_same_exact_name_on_multiple_sanctions_entities_is_ambiguous(self) -> None:
        gist = {
            "plants": [
                {
                    "plant_id": "P1",
                    "owner_gem_entity_id": "E1",
                    "owner_name": "Shared Holdings",
                }
            ]
        }
        sanctions = {
            "entities": [
                {"entity_id": "10", "names": ["Shared Holdings"]},
                {"entity_id": "20", "names": ["SHARED HOLDINGS"]},
            ]
        }

        payload = build_profile(gist, sanctions)
        self.assertEqual(
            payload["counts"]["review_required_ambiguous_exact_name"], 1
        )
        self.assertEqual(
            payload["candidates"][0]["candidate_eu_entity_ids"], ["10", "20"]
        )

    def test_legal_form_equivalence_is_review_only(self) -> None:
        gist = {
            "plants": [
                {
                    "plant_id": "P1",
                    "owner_gem_entity_id": "E1",
                    "owner_name": "North Star Metals Limited",
                }
            ]
        }
        sanctions = {
            "entities": [
                {"entity_id": "10", "names": ["North Star Metals Ltd"]},
            ]
        }

        payload = build_profile(gist, sanctions)
        self.assertEqual(payload["counts"]["review_required_legal_form"], 1)
        self.assertEqual(payload["counts"]["review_required_exact_name"], 0)

    def test_plant_country_is_not_used_for_matching(self) -> None:
        gist = {
            "plants": [
                {
                    "plant_id": "P1",
                    "owner_gem_entity_id": "E1",
                    "owner_name": "Acme Steel",
                    "country_area": "Germany",
                }
            ]
        }
        sanctions = {
            "entities": [
                {
                    "entity_id": "10",
                    "names": ["Acme Steel"],
                    "countries_iso2": ["FR"],
                }
            ]
        }
        payload = build_profile(gist, sanctions)
        self.assertEqual(payload["counts"]["review_required_exact_name"], 1)
        self.assertIn("Plant country is not used", payload["meta"]["interpretation"])

    def test_unknown_owner_is_not_a_company_identity(self) -> None:
        gist = {
            "plants": [
                {
                    "plant_id": "P1",
                    "owner_gem_entity_id": "",
                    "owner_name": "unknown",
                }
            ]
        }
        sanctions = {"entities": [{"entity_id": "10", "names": ["unknown"]}]}
        payload = build_profile(gist, sanctions)
        self.assertEqual(payload["counts"]["usable_unique_owner_identities"], 0)
        self.assertEqual(payload["counts"]["owner_identities_with_any_candidate"], 0)


if __name__ == "__main__":
    unittest.main()
