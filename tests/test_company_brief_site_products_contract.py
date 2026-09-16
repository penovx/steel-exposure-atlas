from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CompanyBriefSiteProductsContractTests(unittest.TestCase):
    def test_site_product_view_is_loaded(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn(
            './src/connections-company-brief-sites.css?v=20260916-1',
            index,
        )
        self.assertIn(
            './src/connections-company-brief-sites.js?v=20260916-1',
            index,
        )

    def test_brief_groups_country_and_products_by_site(self) -> None:
        script = (ROOT / "src" / "connections-company-brief-sites.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("SITES & PRODUCTS", script)
        self.assertIn("GIST-listed products", script)
        self.assertIn("plant.country", script)
        self.assertIn("plant.products?.values", script)
        self.assertIn("productSection?.remove()", script)
        self.assertIn("company-context-metrics-capacity-only", script)
        self.assertNotIn("Countries represented", script)
        self.assertNotIn("Sites in this view", script)

    def test_many_sites_expand_progressively(self) -> None:
        script = (ROOT / "src" / "connections-company-brief-sites.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("INITIAL_SITE_LIMIT = 4", script)
        self.assertIn("Show ${remaining} more sites ↓", script)
        self.assertIn("Show fewer sites ↑", script)
        self.assertIn("aria-expanded", script)
        self.assertIn("row.hidden = expanded", script)


if __name__ == "__main__":
    unittest.main()
