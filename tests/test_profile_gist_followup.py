from __future__ import annotations

import unittest

from pipeline.profile_gist_followup import (
    IRON_PRODUCTION_ROUTES,
    STEEL_PRODUCTION_ROUTES,
    _number_or_zero,
    _reconcile_row_total,
    production_followup,
)


class GistFollowupTests(unittest.TestCase):
    def test_number_or_zero_preserves_uncertainty(self) -> None:
        self.assertEqual(_number_or_zero(10), 10.0)
        self.assertEqual(_number_or_zero("N/A"), 0.0)
        self.assertIsNone(_number_or_zero("unknown"))
        self.assertIsNone(_number_or_zero(">0"))
        self.assertIsNone(_number_or_zero(None))

    def test_capacity_total_reconciliation(self) -> None:
        record = {"total": 100, "a": 60, "b": 40, "c": "N/A"}
        result, total, route_sum = _reconcile_row_total(record, "total", ["a", "b", "c"])
        self.assertEqual(result, "match")
        self.assertEqual(total, 100.0)
        self.assertEqual(route_sum, 100.0)

        record["b"] = ">0"
        result, _, _ = _reconcile_row_total(record, "total", ["a", "b", "c"])
        self.assertEqual(result, "not_comparable")

    def test_actual_iron_labels_are_recognised(self) -> None:
        self.assertIn("BF production (ttpa)", IRON_PRODUCTION_ROUTES)
        self.assertIn("DRI production (ttpa)", IRON_PRODUCTION_ROUTES)
        self.assertIn("OHF steel production (ttpa)", STEEL_PRODUCTION_ROUTES)

    def test_production_followup_counts_total_plus_routes(self) -> None:
        records = [
            {
                "GEM plant ID": "P1",
                "Type of production": "Iron production (ttpa)",
                "2019": 10,
            },
            {
                "GEM plant ID": "P1",
                "Type of production": "BF production (ttpa)",
                "2019": 10,
            },
            {
                "GEM plant ID": "P2",
                "Type of production": "Crude steel production (ttpa)",
                "2019": 20,
            },
            {
                "GEM plant ID": "P2",
                "Type of production": "OHF steel production (ttpa)",
                "2019": 20,
            },
        ]
        report = production_followup(records)
        self.assertEqual(report["plants_with_total_and_route_iron_rows"], 1)
        self.assertEqual(report["plants_with_total_and_route_steel_rows"], 1)
        self.assertEqual(report["iron_total_vs_routes"]["counts"]["match"], 1)
        self.assertEqual(report["steel_total_vs_routes"]["counts"]["match"], 1)


if __name__ == "__main__":
    unittest.main()
