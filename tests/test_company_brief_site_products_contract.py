from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SelectionProfileSiteProductsContractTests(unittest.TestCase):
    def test_selection_profile_assets_are_loaded(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('./src/connections-selection-profile.css?v=20260916-3', index)
        self.assertIn('./src/connections-selection-profile.js?v=20260916-1', index)
        self.assertNotIn('./src/connections-company-brief-sites.css', index)
        self.assertNotIn('./src/connections-company-brief-sites.js', index)

    def test_profile_groups_status_country_and_products_by_site(self) -> None:
        script = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8")
        self.assertIn("SITES & PRODUCTS", script)
        self.assertIn("GIST-listed products", script)
        self.assertIn("plant.country", script)
        self.assertIn("plant.products?.values", script)
        self.assertIn("function plantStatuses(plant)", script)
        self.assertIn("plant.tranches", script)
        self.assertIn("construction", script)
        self.assertIn("operating pre-retirement", script)

    def test_company_profile_uses_company_geographic_scope_not_cross_filter_intersection(self) -> None:
        script = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8")
        self.assertIn("function scopedCompanyPlants(review, ownerId)", script)
        self.assertIn("region === 'World' || plant.region === region", script)
        self.assertIn("plants = scopedCompanyPlants(review, filters.owner)", script)

    def test_production_profile_is_operating_capacity_only(self) -> None:
        script = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8")
        self.assertIn("review.model?.hasRoute?.(plant, route.id)", script)
        self.assertIn("known operating capacity", script)
        self.assertIn("Known operating crude-steel capacity", script)

    def test_many_sites_expand_progressively(self) -> None:
        script = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8")
        self.assertIn("SITE_LIMIT = 6", script)
        self.assertIn("Show ${remaining} more sites ↓", script)
        self.assertIn("Show fewer sites ↑", script)
        self.assertIn("aria-expanded", script)

    def test_trade_signal_explains_quota_before_duty_effect(self) -> None:
        script = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8")
        self.assertIn("EU tariff-quota framework in force", script)
        self.assertIn("Regulation (EU) 2026/1384", script)
        self.assertIn("annual quota period 1 Jul–30 Jun", script)
        self.assertIn("Implementing Regulation (EU) 2026/1457 applies 1 Jul–31 Dec 2026", script)
        self.assertIn("50% out-of-quota duty after applicable quota exhaustion", script)
        self.assertNotIn("Origin used for the measure:", script)
        self.assertNotIn("GIST product labels map to:", script)


if __name__ == "__main__":
    unittest.main()
