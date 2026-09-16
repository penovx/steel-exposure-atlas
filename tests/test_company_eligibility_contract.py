from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CompanyEligibilityContractTests(unittest.TestCase):
    def test_primary_company_browse_uses_region_scoped_production_evidence_with_direct_listing_override(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "src" / "connections-company-eligibility.js").read_text(
            encoding="utf-8"
        )

        self.assertIn('./src/connections-company-eligibility.js?v=20260916-2', index)
        self.assertLess(
            index.index('./src/connections-sanctions-loader.js'),
            index.index('./src/connections-company-eligibility.js'),
        )
        self.assertIn("review.model?.hasRoute?.(plant, route)", script)
        self.assertIn("review.model?.total?.([plant])", script)
        self.assertIn("status?.state !== 'direct_list_match'", script)
        self.assertIn("productionEligibleRegionsByOwner", script)
        self.assertIn("currentRegion(review = reviewApi())", script)
        self.assertIn("if (region === 'World') return productionEligibleOwners.has(id)", script)
        self.assertIn("productionEligibleRegionsByOwner.get(id)?.has(region)", script)
        self.assertIn("directListedOwners.has(id)", script)
        self.assertIn("selectedOwnerId() === id", script)
        self.assertIn("data-browse-kind=\"owner\"", script)

    def test_eligibility_layer_does_not_replace_or_filter_the_underlying_plant_population(self) -> None:
        script = (ROOT / "src" / "connections-company-eligibility.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("for (const plant of review?.all ?? [])", script)
        self.assertNotIn("review.all =", script)
        self.assertNotIn("review.all.filter", script)
        self.assertNotIn("splice(", script)
        self.assertNotIn("delete review", script)


if __name__ == "__main__":
    unittest.main()
