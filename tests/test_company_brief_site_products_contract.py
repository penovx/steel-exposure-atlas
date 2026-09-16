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
            './src/connections-company-brief-sites.js?v=20260916-4',
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

    def test_company_brief_uses_company_geographic_scope_not_cross_filter_intersection(self) -> None:
        script = (ROOT / "src" / "connections-company-brief-sites.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("function plantsAttributedToOwnerInGeography", script)
        self.assertIn("region === 'World' || plant.region === region", script)
        self.assertNotIn("selectedIds", script)
        self.assertIn("current geographic scope", script)
        self.assertIn("capacityFor(review, plants)", script)

    def test_production_method_grammar_is_dynamic_and_scope_is_rebuilt(self) -> None:
        script = (ROOT / "src" / "connections-company-brief-sites.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("routes.length === 1 ? 'method' : 'methods'", script)
        self.assertIn("function patchProductionProfile", script)
        self.assertIn("review.model?.hasRoute", script)
        self.assertIn("summarizedPlaces(route.plants)", script)

    def test_many_sites_expand_progressively(self) -> None:
        script = (ROOT / "src" / "connections-company-brief-sites.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("INITIAL_SITE_LIMIT = 4", script)
        self.assertIn("Show ${remaining} more sites ↓", script)
        self.assertIn("Show fewer sites ↑", script)
        self.assertIn("aria-expanded", script)
        self.assertIn("site.hidden = expanded", script)

    def test_trade_signal_shows_decision_relevant_consequence_only(self) -> None:
        script = (ROOT / "src" / "connections-company-brief-sites.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("function patchTradeSignal(card)", script)
        self.assertIn("50% additional duty after quota exhaustion", script)
        self.assertIn("an additional duty of 50% applies once the applicable quota is exhausted", script)
        self.assertIn("consequence?.remove()", script)
        self.assertNotIn("Origin used for the measure:", script)
        self.assertNotIn("GIST product labels map to:", script)
        self.assertNotIn("Sites: ${trade.sites}", script)
        self.assertNotIn("trade.mappingLabel", script)


if __name__ == "__main__":
    unittest.main()
