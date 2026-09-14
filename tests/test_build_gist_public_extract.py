from __future__ import annotations

import unittest

from pipeline.build_gist_public_extract import (
    _capacity_summary,
    _merge_duplicate_year_values,
    canonical_json_bytes,
    list_object,
    value_object,
)


class GistPublicExtractTests(unittest.TestCase):
    def test_capacity_value_states_remain_distinct(self) -> None:
        self.assertEqual(value_object(1200), {"state": "numeric", "value_ttpa": 1200})
        self.assertEqual(value_object(">0"), {"state": ">0", "value_ttpa": None})
        self.assertEqual(value_object("N/A"), {"state": "N/A", "value_ttpa": None})
        self.assertEqual(value_object("unknown"), {"state": "unknown", "value_ttpa": None})
        self.assertEqual(value_object(None), {"state": "blank", "value_ttpa": None})

    def test_list_object_preserves_unknown(self) -> None:
        self.assertEqual(list_object("BF; BOF; EAF", ";")["values"], ["BF", "BOF", "EAF"])
        self.assertEqual(list_object("unknown", ","), {"state": "unknown", "values": []})

    def test_capacity_summary_keeps_unquantified_positive(self) -> None:
        tranches = [
            {
                "status": "operating",
                "crude_steel_capacity_ttpa": {"state": "numeric", "value_ttpa": 1000},
                "iron_capacity_ttpa": {"state": "numeric", "value_ttpa": 500},
            },
            {
                "status": "operating pre-retirement",
                "crude_steel_capacity_ttpa": {"state": ">0", "value_ttpa": None},
                "iron_capacity_ttpa": {"state": "N/A", "value_ttpa": None},
            },
        ]
        summary = _capacity_summary(tranches)["operating"]
        self.assertEqual(summary["crude_steel_capacity"]["known_numeric_sum_ttpa"], 1000)
        self.assertTrue(summary["crude_steel_capacity"]["has_unquantified_positive"])
        self.assertFalse(summary["crude_steel_capacity"]["is_exact"])
        self.assertEqual(summary["iron_capacity"]["known_numeric_sum_ttpa"], 500)

    def test_duplicate_production_numeric_can_replace_unknown(self) -> None:
        merged, conflict = _merge_duplicate_year_values(["unknown", 3800])
        self.assertFalse(conflict)
        self.assertEqual(merged, {"state": "numeric", "value_ttpa": 3800})

    def test_duplicate_production_na_numeric_is_conflict(self) -> None:
        merged, conflict = _merge_duplicate_year_values(["N/A", 3800])
        self.assertTrue(conflict)
        self.assertEqual(merged, {"state": "conflict", "value_ttpa": None})

    def test_duplicate_production_different_numeric_is_conflict(self) -> None:
        _, conflict = _merge_duplicate_year_values([100, 101])
        self.assertTrue(conflict)

    def test_canonical_json_is_deterministic(self) -> None:
        first = canonical_json_bytes({"b": 2, "a": 1})
        second = canonical_json_bytes({"a": 1, "b": 2})
        self.assertEqual(first, second)
        self.assertEqual(first, b'{"a":1,"b":2}\n')


if __name__ == "__main__":
    unittest.main()
