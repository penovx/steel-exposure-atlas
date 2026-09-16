from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CompanyContextCardContractTests(unittest.TestCase):
    def test_context_card_is_second_click_non_modal_and_atlas_styled(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "src" / "connections-company-context.js").read_text(encoding="utf-8")
        css = (ROOT / "src" / "connections-company-context.css").read_text(encoding="utf-8").replace(" ", "")

        self.assertIn('./src/connections-company-context.js?v=20260916-4', index)
        self.assertIn('./src/connections-company-context.css?v=20260916-1', index)
        self.assertIn("function installSecondClickGate()", script)
        self.assertIn("clicked !== selected", script)
        self.assertIn("contextOpenOwnerId = contextOpenOwnerId === clicked ? null : clicked", script)
        self.assertIn("event.stopImmediatePropagation()", script)
        self.assertIn("card.hidden = contextOpenOwnerId !== ownerId", script)
        self.assertIn("COMPANY CONTEXT", script)
        self.assertIn("Immediate owner or operator named by GEM", script)
        self.assertIn("Connected sites", script)
        self.assertIn("Countries", script)
        self.assertIn("Known operating capacity", script)
        self.assertIn("View evidence ↓", script)
        self.assertIn("Procurement follow-up", script)
        self.assertIn("Listed by OFAC", script)
        self.assertIn("This is not sanctions clearance.", script)
        self.assertIn(".company-context-card{", css)
        self.assertIn("grid-column:2", css)
        self.assertIn("justify-self:start", css)
        self.assertIn("background:#10212af5", css)
        self.assertIn("border:1pxsolid#496675", css)
        self.assertNotIn("position:fixed", css)

    def test_trade_context_is_loaded_and_expressed_as_scenario(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        loader = (ROOT / "src" / "connections-trade-loader.js").read_text(encoding="utf-8")
        context = (ROOT / "src" / "connections-company-context.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-trade-loader.js?v=20260916-1', index)
        self.assertIn('eu-steel-trade-context.v1.json', loader)
        self.assertIn('B869A4BB8C4E4F7AE320B4CE4A117A33B05CADEEDF1C9DF106845EBCA9D9B21B', loader)
        self.assertIn('5F0214CD0FC9FC85A114B9EC485E2D6887F3F2137BD177EE357CC00FE2BB32BE', loader)
        self.assertIn("__ATLAS_TRADE_PROMISE__", context)
        self.assertIn("If imported into the EU", context)
        self.assertIn("EU steel import measure", context)
        self.assertIn("50% additional duty after the applicable quota is exhausted.", context)
        self.assertIn("confirm the customs code", context.lower())
        self.assertIn("trade-context", context)

    def test_primary_ui_does_not_list_absent_analyses(self) -> None:
        context = (ROOT / "src" / "connections-company-context.js").read_text(encoding="utf-8")
        sanctions = (ROOT / "src" / "connections-sanctions-bridge.js").read_text(encoding="utf-8")
        primary = context + sanctions

        self.assertNotIn("customs classification not performed", primary.lower())
        self.assertNotIn("live quota availability not evaluated", primary.lower())
        self.assertNotIn("fuzzy matching not run", primary.lower())

    def test_product_ui_principle_is_documented(self) -> None:
        principles = (ROOT / "docs" / "product-ui-principles.md").read_text(encoding="utf-8")
        self.assertIn("Evidence -> meaning -> action", principles)
        self.assertIn("must not become a list of analyses the project did not perform", principles)
        self.assertIn("only when omitting it would create a materially false inference", principles)


if __name__ == "__main__":
    unittest.main()
