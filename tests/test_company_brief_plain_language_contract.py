from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CompanyBriefPlainLanguageContractTests(unittest.TestCase):
    def test_first_click_affordance_is_integrated_and_immediate(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "src" / "connections-company-context.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-company-context.js?v=20260916-5', index)
        self.assertNotIn('connections-company-brief-affordance.js', index)
        self.assertIn("View company brief →", script)
        self.assertIn("function queueCompanyBriefOfferSync()", script)
        self.assertIn("requestAnimationFrame(() => requestAnimationFrame", script)
        self.assertIn("queueCompanyBriefOfferSync();\n        return;", script)

    def test_company_brief_names_relationships_instead_of_using_shorthand(self) -> None:
        script = (ROOT / "src" / "connections-company-context.js").read_text(encoding="utf-8")

        self.assertIn("SITES & COUNTRIES", script)
        self.assertIn("GEM names ${companyName} as the immediate owner or operator", script)
        self.assertIn("site' : 'sites'} in ${country}", script)
        self.assertIn("PRODUCT-TO-SITE RELATION", script)
        self.assertIn("Listed at ${summarizedPlaces(product.plants)}", script)
        self.assertIn("PRODUCTION PROFILE", script)
        self.assertIn("known operating capacity", script)
        self.assertNotIn("${row.count}/${totalSites} sites", script)
        self.assertNotIn("current connected scope", script)
        self.assertNotIn("Procurement follow-up", script)
        self.assertNotIn("confirm the customs code", script.lower())

    def test_regulatory_copy_stays_factual(self) -> None:
        script = (ROOT / "src" / "connections-company-context.js").read_text(encoding="utf-8")

        self.assertIn("REGULATORY CONTEXT", script)
        self.assertIn("Listed by OFAC", script)
        self.assertIn("If imported into the EU, the additional duty is 50%", script)
        self.assertNotIn("route it for", script.lower())
        self.assertNotIn("before contracting", script.lower())
        self.assertNotIn("no direct eu or u.s. listing found", script.lower())


if __name__ == "__main__":
    unittest.main()
