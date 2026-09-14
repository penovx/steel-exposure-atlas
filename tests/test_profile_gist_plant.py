from __future__ import annotations

import unittest

from pipeline.profile_gist_plant import (
    classify_source_value,
    parse_coordinate_pair,
    profile_capacity,
    profile_production,
    raw_date_pattern,
)


class ProfileGistPlantTests(unittest.TestCase):
    def test_source_value_states_remain_distinct(self) -> None:
        self.assertEqual(classify_source_value(1200), "numeric")
        self.assertEqual(classify_source_value("unknown"), "unknown")
        self.assertEqual(classify_source_value("N/A"), "N/A")
        self.assertEqual(classify_source_value(">0"), ">0")
        self.assertEqual(classify_source_value(""), "blank")

    def test_coordinate_parser_validates_ranges(self) -> None:
        self.assertEqual(parse_coordinate_pair("45.1, 11.9"), (45.1, 11.9))
        self.assertIsNone(parse_coordinate_pair("91, 11"))
        self.assertIsNone(parse_coordinate_pair("not a coordinate"))

    def test_raw_date_patterns_distinguish_year_and_excel_serial(self) -> None:
        self.assertEqual(raw_date_pattern(1983), "numeric_year")
        self.assertEqual(raw_date_pattern(39988), "excel_serial_candidate")
        self.assertEqual(raw_date_pattern("2026-01-02"), "iso_date_text")
        self.assertEqual(raw_date_pattern("unknown"), "unknown")

    def test_capacity_profile_detects_multiple_statuses(self) -> None:
        rows = [
            {
                "GEM plant ID": "P1",
                "Main production equipment": "EAF",
                "Status": "operating",
                "Start date": 2000,
                "Nominal crude steel capacity (ttpa)": 1000,
                "Nominal iron capacity (ttpa)": "N/A",
            },
            {
                "GEM plant ID": "P1",
                "Main production equipment": "DRI; EAF",
                "Status": "announced",
                "Start date": "unknown",
                "Nominal crude steel capacity (ttpa)": 500,
                "Nominal iron capacity (ttpa)": 400,
            },
        ]
        report = profile_capacity(rows)
        self.assertEqual(report["rows_per_plant"]["keys_with_multiple_rows"], 1)
        self.assertEqual(report["plants_with_multiple_status_values"], 1)
        self.assertEqual(report["capacity_value_states"]["Nominal crude steel capacity (ttpa)"]["numeric"], 2)

    def test_production_profile_identifies_total_plus_route(self) -> None:
        rows = [
            {"GEM plant ID": "P1", "Type of production": "Crude steel production (ttpa)", "2019": 100},
            {"GEM plant ID": "P1", "Type of production": "EAF steel production (ttpa)", "2019": 100},
        ]
        report = profile_production(rows)
        self.assertEqual(report["plants_with_total_and_route_steel_rows"], 1)
        self.assertEqual(report["duplicate_plant_type_rows_beyond_first"], 0)


if __name__ == "__main__":
    unittest.main()
