from __future__ import annotations

import unittest

from pipeline.build_gist_public_extract import _production_contains_year_key


class Gist2025GuardTests(unittest.TestCase):
    def test_checks_year_keys_not_numeric_values(self) -> None:
        legitimate = [{"production": {"crude_steel_ttpa": {"2024": {"state": "numeric", "value_ttpa": 2025}}}}]
        leaked = [{"production": {"crude_steel_ttpa": {"2025": {"state": "numeric", "value_ttpa": 1000}}}}]

        self.assertFalse(_production_contains_year_key(legitimate, "2025"))
        self.assertTrue(_production_contains_year_key(leaked, "2025"))


if __name__ == "__main__":
    unittest.main()
