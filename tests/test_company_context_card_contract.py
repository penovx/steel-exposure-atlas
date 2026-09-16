from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CompanyContextCardContractTests(unittest.TestCase):
    def test_company_brief_is_explicit_second_click_non_modal_and_atlas_styled(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "src" / "connections-company-context.js").read_text(encoding="utf-8")
        css = (ROOT / "src" / "connections-company-context.css").read_text(encoding="utf-8").replace(" ", "")

        self.assertIn('./src/connections-company-context.js?v=20260916-5', index)
        self.assertIn('./src/connections-company-context.css?v=20260916-2', index)
        self.assertIn("function installSecondClickGate()", script)
        self.assertIn("clicked !== selected", script)
        self.assertIn("contextOpenOwnerId = contextOpenOwnerId === clicked ? null : clicked", script)
        self.assertIn("event.stopImmediatePropagation()", script)
        self.assertIn("card.hidden = contextOpenOwnerId !== ownerId", script)
        self.assertIn("function syncCompanyBriefOffer()", script)
        self.assertIn("View company brief →", script)
        self.assertIn("Company brief open ↑", script)
        self.assertIn(".company-brief-offer{", css)
        self.assertIn(".company-context-card{", css)
        self.assertIn("grid-column:2", css)
        self.assertIn("justify-self:start", css)
        self.assertIn("background:#0f2029f7", css)
        self.assertIn("border:1pxsolid#496675", css)
        self.assertNotIn("position:fixed", css)

    def test_company_brief_uses_supported_relationships_and_interpretations(self) -> None:
        script = (ROOT / "src" / "connections-company-context.js").read_text(encoding="utf-8")

        self.assertIn("COMPANY BRIEF", script)
        self.assertIn("GEM names this company as the immediate owner or operator", script)
        self.assertIn("Sites in this view", script)
        self.assertIn("Countries represented", script)
        self.assertIn("Known operating crude-steel capacity", script)
        self.assertIn("SITES & COUNTRIES", script)
        self.assertIn("PRODUCT-TO-SITE RELATION", script)
        self.assertIn("PRODUCTION PROFILE", script)
        self.assertIn("REGULATORY CONTEXT", script)
        self.assertIn("Listed by OFAC", script)
        self.assertIn("View evidence ↓", script)
        self.assertIn("Public-data interpretation · no supplier ranking", script)
        self.assertNotIn("Procurement follow-up", script)
        self.assertNotIn("This is not sanctions clearance.", script)
        self.assertNotIn("No direct EU or U.S. listing found", script)

    def test_trade_context_is_loaded_and_expressed_as_factual_scenario(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        loader = (ROOT / "src" / "connections-trade-loader.js").read_text(encoding="utf-8")
        context = (ROOT / "src" / "connections-company-context.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-trade-loader.js?v=20260916-2', index)
        self.assertIn('eu-steel-trade-context.v1.json', loader)
        self.assertIn('eu-steel-trade-context-v1.1', loader)
        self.assertIn('B869A4BB8C4E4F7AE320B4CE4A117A33B05CADEEDF1C9DF106845EBCA9D9B21B', loader)
        self.assertIn('5F0214CD0FC9FC85A114B9EC485E2D6887F3F2137BD177EE357CC00FE2BB32BE', loader)
        self.assertIn("__ATLAS_TRADE_PROMISE__", context)
        self.assertIn("If steel from these sites were imported into the EU", context)
        self.assertIn("EU steel import measure", context)
        self.assertIn("additional duty is 50% after the applicable quota is exhausted", context)
        self.assertNotIn("confirm the customs code", context.lower())
        self.assertIn("trade-context", context)

    def test_primary_ui_does_not_list_absent_analyses_or_process_advice(self) -> None:
        context = (ROOT / "src" / "connections-company-context.js").read_text(encoding="utf-8")
        primary = context.lower()

        self.assertNotIn("customs classification not performed", primary)
        self.assertNotIn("live quota availability not evaluated", primary)
        self.assertNotIn("fuzzy matching not run", primary)
        self.assertNotIn("confirm the customs code", primary)
        self.assertNotIn("route it for", primary)
        self.assertNotIn("before contracting", primary)

    def test_product_ui_principle_is_documented(self) -> None:
        principles = (ROOT / "docs" / "product-ui-principles.md").read_text(encoding="utf-8")
        self.assertIn("Evidence -> relationship -> meaning", principles)
        self.assertIn("Stress test for every visible statement", principles)
        self.assertIn("Does it avoid process advice?", principles)
        self.assertIn("Avoid unexplained words such as `connected`", principles)
        self.assertIn("View company brief ->", principles)


if __name__ == "__main__":
    unittest.main()
