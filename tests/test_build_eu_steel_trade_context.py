from __future__ import annotations

import copy
import unittest

from pipeline.build_eu_steel_trade_context import (
    EXPECTED_BILATERAL_SHA256,
    EXPECTED_MEASURE_SHA256,
    SCHEMA,
    build_context,
)


def profile() -> dict[str, object]:
    return {
        "meta": {
            "schema": "steel-exposure-atlas/gist-eu-steel-measure-profile-v1.1",
            "measure_snapshot_sha256": EXPECTED_MEASURE_SHA256,
            "bilateral_snapshot_sha256": EXPECTED_BILATERAL_SHA256,
        },
        "plants": [
            {
                "plant_id": "P1",
                "plant_name": "Alpha",
                "country_area": "Turkey",
                "measure_country": "Türkiye",
                "legal_route": "bilateral_safeguard_2026_1930",
                "scenario_state": "candidate_with_named_origin_quota_row",
                "measure_candidates": [
                    {
                        "mapping_state": "family_candidate",
                        "product_number": "13",
                        "product_category": "Rebars",
                        "named_origin_quota_rows": [
                            {
                                "additional_duty_rate_pct": 50.0,
                                "order_number": "09.9884",
                            }
                        ],
                    }
                ],
            },
            {
                "plant_id": "P2",
                "plant_name": "Beta",
                "country_area": "Canada",
                "measure_country": "Canada",
                "legal_route": "steel_regulation_2026_1384",
                "scenario_state": "candidate_requires_residual_quota_review",
                "measure_candidates": [
                    {
                        "mapping_state": "ambiguous_family_candidate",
                        "product_number": "1.A",
                        "product_category": "Non-alloy and other alloy hot rolled sheets and strips",
                        "named_origin_quota_rows": [],
                    }
                ],
            },
            {
                "plant_id": "P3",
                "plant_name": "Gamma",
                "country_area": "Germany",
                "measure_country": "Germany",
                "legal_route": "intra_eu_origin",
                "scenario_state": "not_applicable_intra_eu_origin",
                "measure_candidates": [],
            },
        ],
    }


class EuSteelTradeContextTests(unittest.TestCase):
    def test_emits_only_useful_trade_context_rows(self) -> None:
        payload = build_context(profile())
        self.assertEqual(payload["meta"]["schema"], SCHEMA)
        self.assertEqual(payload["meta"]["counts"]["plants_with_context"], 2)
        self.assertEqual(payload["meta"]["counts"]["origin_specific_quota_context"], 1)
        self.assertEqual(payload["meta"]["counts"]["pooled_or_residual_quota_context"], 1)
        self.assertEqual([row["plant_id"] for row in payload["plants"]], ["P1", "P2"])
        self.assertEqual(payload["meta"]["publication_state"], "approved minimal derived public context")
        self.assertEqual(payload["meta"]["ui_principle"], "evidence -> relationship -> meaning")

    def test_named_origin_row_stays_factual(self) -> None:
        payload = build_context(profile())
        row = payload["plants"][0]
        self.assertEqual(row["scenario"], "if imported into the EU")
        self.assertEqual(row["quota_route"], "origin_specific")
        self.assertEqual(row["additional_duty_if_quota_exhausted_pct"], 50.0)
        self.assertEqual(row["customs_order_numbers"], ["09.9884"])
        self.assertNotIn("procurement_follow_up", row)
        self.assertNotIn("confirm", str(row).lower())

    def test_ambiguous_family_preserves_mapping_state_without_process_advice(self) -> None:
        payload = build_context(profile())
        row = payload["plants"][1]
        self.assertEqual(row["product_family_state"], "family_requires_confirmation")
        self.assertEqual(row["quota_route"], "pooled_or_residual")
        self.assertNotIn("procurement_follow_up", row)

    def test_rejects_unreviewed_source_snapshot(self) -> None:
        bad = copy.deepcopy(profile())
        bad["meta"]["measure_snapshot_sha256"] = "A" * 64  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "snapshot mismatch"):
            build_context(bad)


if __name__ == "__main__":
    unittest.main()
