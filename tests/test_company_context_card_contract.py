from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SelectionProfileContractTests(unittest.TestCase):
    def test_company_detail_is_one_click_profile_not_second_click_card(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8")
        css = (ROOT / "src" / "connections-selection-profile.css").read_text(encoding="utf-8")

        self.assertIn('./src/connections-selection-profile.js?v=20260916-1', index)
        self.assertIn('./src/connections-selection-profile.css?v=20260916-3', index)
        self.assertNotIn('./src/connections-company-context.js', index)
        self.assertNotIn('./src/connections-company-brief-sites.js', index)
        self.assertIn('id="selection-profile"', index)
        self.assertIn("function selectionModel(review)", script)
        self.assertIn("if (filters.owner)", script)
        self.assertIn("renderProfile(review", script)
        self.assertNotIn("installSecondClickGate", script)
        self.assertNotIn("View company brief", script)
        self.assertIn(".selection-profile{", css)

    def test_profile_standardizes_identity_sites_production_regulatory_and_sources(self) -> None:
        script = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8")

        self.assertIn("Immediate owner or operator named by GEM", script)
        self.assertIn("SITES & PRODUCTS", script)
        self.assertIn("PRODUCTION", script)
        self.assertIn("SANCTIONS & TRADE", script)
        self.assertIn("EVIDENCE & SOURCES", script)
        self.assertIn("Company identity listed", (ROOT / "src" / "connections-sanctions-bridge.js").read_text(encoding="utf-8"))
        self.assertIn("50% out-of-quota duty after applicable quota exhaustion", script)
        self.assertIn("Sources & interpretation ↗", script)

    def test_profile_keeps_process_guidance_out_of_visible_facts(self) -> None:
        script = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8").lower()

        self.assertNotIn("procurement follow-up", script)
        self.assertNotIn("route to compliance", script)
        self.assertNotIn("before contracting", script)
        self.assertNotIn("confirm the customs code", script)
        self.assertNotIn("live quota availability not evaluated", script)
        self.assertNotIn("fuzzy matching not run", script)

    def test_trade_context_is_loaded_and_shown_as_factual_measure(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        loader = (ROOT / "src" / "connections-trade-loader.js").read_text(encoding="utf-8")
        profile = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-trade-loader.js?v=20260916-3', index)
        self.assertIn('eu-steel-trade-context.v1.json', loader)
        self.assertIn('eu-steel-trade-context-v1.1', loader)
        self.assertIn("async function safeLoad()", loader)
        self.assertIn("__ATLAS_TRADE_ERROR__", loader)
        self.assertIn("__ATLAS_TRADE_PROMISE__ = safeLoad()", loader)
        self.assertIn("EU tariff-quota framework in force", profile)
        self.assertIn("Regulation (EU) 2026/1384", profile)
        self.assertIn("Implementing Regulation (EU) 2026/1457", profile)
        self.assertIn("50% out-of-quota duty", profile)

    def test_product_ui_principle_documents_one_click_profile(self) -> None:
        principles = (ROOT / "docs" / "product-ui-principles.md").read_text(encoding="utf-8")
        self.assertIn("Evidence -> relationship -> meaning", principles)
        self.assertIn("One-click selection profile", principles)
        self.assertIn("does not require a second click", principles)
        self.assertIn("facts and relationships stay in the profile", principles)
        self.assertIn("Sources & interpretation", principles)


if __name__ == "__main__":
    unittest.main()
