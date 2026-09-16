from __future__ import annotations

import unittest

from pipeline.profile_gist_eu_steel_measure import build_profile


def plant(plant_id: str, country: str, products: list[str]) -> dict[str, object]:
    return {
        "plant_id": plant_id,
        "plant_name": f"Plant {plant_id}",
        "country_area": country,
        "steel_products": {"state": "text", "values": products},
    }


def gist() -> dict[str, object]:
    return {
        "meta": {"schema": "steel-exposure-atlas/gist-plant-v1.0"},
        "plants": [
            plant("P-EU", "Germany", ["rebar"]),
            plant("P-EEA", "Norway", ["rebar"]),
            plant("P-TR", "Turkey", ["rebar"]),
            plant("P-CA", "Canada", ["rebar"]),
            plant("P-US", "United States", ["billet"]),
        ],
    }


def measure() -> dict[str, object]:
    return {
        "meta": {
            "schema": "steel-exposure-atlas/eu-steel-measure-2026-1457-v1.0",
            "raw_sha256": "A" * 64,
        },
        "products": [
            {
                "product_number": "13",
                "product_category": "Rebars",
                "cn_codes": ["72142000", "72149910"],
                "taric_codes": ["7228306911"],
            }
        ],
        "allocations": [
            {
                "product_number": "13",
                "allocation": "Türkiye",
                "total_yearly_volume_tonnes": 239676.09,
                "quarterly_volume_tonnes": [59919.02] * 4,
                "additional_duty_rate_pct": 50.0,
                "order_number": "09.9884",
            },
            {
                "product_number": "13",
                "allocation": "Other countries",
                "total_yearly_volume_tonnes": 63322.34,
                "quarterly_volume_tonnes": [15830.59] * 4,
                "additional_duty_rate_pct": 50.0,
                "order_number": "09.9614",
            },
        ],
    }


def bilateral() -> dict[str, object]:
    return {
        "meta": {
            "schema": "steel-exposure-atlas/eu-steel-bilateral-2026-1930-v1.0",
            "raw_sha256": "B" * 64,
        },
        "countries": [
            "Albania", "Israel", "Jordan", "Morocco", "North Macedonia",
            "Serbia", "Switzerland", "Tunisia", "Türkiye",
        ],
        "additional_duty_rate_pct": 50.0,
    }


def mapping() -> dict[str, object]:
    return {
        "schema": "steel-exposure-atlas/eu-steel-measure-product-map-v1.0",
        "mappings": {
            "rebar": {
                "state": "family_candidate",
                "product_numbers": ["13"],
                "family": "Rebars",
                "note": "classification required",
            },
            "billet": {
                "state": "no_supported_mapping",
                "product_numbers": [],
                "note": "not mapped",
            },
        },
    }


class GistEuSteelMeasureProfileTests(unittest.TestCase):
    def test_separates_eu_eea_named_quota_residual_and_unmapped_states(self) -> None:
        payload = build_profile(gist(), measure(), mapping(), bilateral())
        counts = payload["counts"]
        self.assertEqual(counts["gist_plants"], 5)
        self.assertEqual(counts["not_applicable_intra_eu_origin"], 1)
        self.assertEqual(counts["quota_duty_exempt_eea_origin"], 1)
        self.assertEqual(counts["candidate_with_named_origin_quota_row"], 1)
        self.assertEqual(counts["candidate_requires_residual_quota_review"], 1)
        self.assertEqual(counts["no_supported_product_family_candidate"], 1)
        self.assertEqual(counts["plants_with_any_trade_measure_candidate"], 2)
        self.assertEqual(counts["plants_from_bilateral_safeguard_origins"], 1)
        self.assertEqual(counts["candidate_plants_from_bilateral_safeguard_origins"], 1)

    def test_country_alias_connects_turkey_to_turkiye_quota_and_bilateral_route(self) -> None:
        payload = build_profile(gist(), measure(), mapping(), bilateral())
        rows = {item["plant_id"]: item for item in payload["plants"]}
        turkey = rows["P-TR"]
        self.assertEqual(turkey["measure_country"], "Türkiye")
        self.assertEqual(turkey["legal_route"], "bilateral_safeguard_2026_1930")
        self.assertEqual(turkey["scenario_state"], "candidate_with_named_origin_quota_row")
        candidate = turkey["measure_candidates"][0]
        self.assertEqual(candidate["product_number"], "13")
        self.assertEqual(candidate["product_category"], "Rebars")
        self.assertEqual(candidate["legal_route"], "bilateral_safeguard_2026_1930")
        self.assertEqual(candidate["named_origin_quota_rows"][0]["additional_duty_rate_pct"], 50.0)

    def test_non_bilateral_origin_keeps_steel_regulation_route(self) -> None:
        payload = build_profile(gist(), measure(), mapping(), bilateral())
        rows = {item["plant_id"]: item for item in payload["plants"]}
        self.assertEqual(rows["P-CA"]["legal_route"], "steel_regulation_2026_1384")

    def test_profile_keeps_scenario_and_evidence_boundary(self) -> None:
        payload = build_profile(gist(), measure(), mapping(), bilateral())
        self.assertIn("hypothetical import", payload["meta"]["scenario"])
        self.assertIn("review evidence", payload["meta"]["interpretation"])
        self.assertIn("bilateral safeguards", payload["meta"]["interpretation"])
        self.assertEqual(payload["meta"]["bilateral_snapshot_sha256"], "B" * 64)

    def test_rejects_mapping_to_unknown_measure_product_number(self) -> None:
        bad_mapping = mapping()
        bad_mapping["mappings"]["rebar"]["product_numbers"] = ["999"]  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "unknown product numbers"):
            build_profile(gist(), measure(), bad_mapping, bilateral())


if __name__ == "__main__":
    unittest.main()
