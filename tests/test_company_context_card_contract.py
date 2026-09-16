from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CompanyContextCardContractTests(unittest.TestCase):
    def test_context_card_is_loaded_and_non_modal(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "src" / "connections-company-context.js").read_text(encoding="utf-8")
        css = (ROOT / "src" / "connections-procurement-ui.css").read_text(encoding="utf-8")

        self.assertIn('./src/connections-company-context.js?v=20260916-1', index)
        self.assertIn("company-context-card", script)
        self.assertIn("COMPANY CONTEXT", script)
        self.assertIn("connected ${siteCount === 1 ? 'site' : 'sites'}", script)
        self.assertIn("View evidence ↓", script)
        self.assertIn("Procurement follow-up", script)
        self.assertIn("Listed by OFAC", script)
        self.assertIn("This is not sanctions clearance.", script)
        self.assertIn(".company-context-card{grid-column:2;grid-row:1", css)
        self.assertIn("max-height:calc(100% - 44px)", css)
        self.assertIn("max-height:min(60vh,480px)", css)
        self.assertNotIn("position:fixed", css)

    def test_primary_ui_does_not_list_absent_trade_analyses(self) -> None:
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
