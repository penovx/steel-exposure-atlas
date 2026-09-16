from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class UiIntegrationContractTests(unittest.TestCase):
    def test_root_uses_relational_homepage(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="connections-stage"', index)
        self.assertIn('id="company-nodes"', index)
        self.assertIn('id="method-nodes"', index)
        self.assertIn('id="product-nodes"', index)
        self.assertIn('class="product-divider"', index)
        self.assertIn('./src/connections.css', index)
        self.assertIn('./src/connections-sanctions.css', index)
        self.assertIn('./src/connections-runtime-bridge.js', index)
        self.assertIn('./src/connections-sanctions-loader.js', index)
        self.assertIn('./src/connections-company-eligibility.js', index)
        self.assertIn('./src/connections-trade-loader.js', index)
        self.assertIn('./src/connections-company-context.js', index)
        self.assertIn('./src/connections-sanctions-bridge.js', index)
        self.assertIn('./src/connections-bootstrap.js', index)
        self.assertNotIn('type="application/json"', index)

    def test_explorer_remains_available_as_internal_secondary_route(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(encoding="utf-8")
        self.assertIn('./prototype/evidence.html', index)
        self.assertTrue((ROOT / "prototype" / "evidence.html").exists())
        self.assertIn('a[href="./prototype/evidence.html"]', bridge)
        self.assertIn('?.remove()', bridge)

    def test_runtime_reads_reviewed_local_artifacts_and_checks_gist_hash(self) -> None:
        bootstrap = (ROOT / "src" / "connections-bootstrap.js").read_text(encoding="utf-8")
        self.assertIn("gist-plants.v1.json", bootstrap)
        self.assertIn("ne_110m_admin_0_countries.v5.1.1.geojson", bootstrap)
        self.assertIn("EXPECTED_PLANTS = 1293", bootstrap)
        self.assertIn("6D9C2CBAC1DBC25068AF5DD69736FF7E44D6074E220BDB5880054487F28A3EC3", bootstrap)
        self.assertIn("crypto.subtle.digest('SHA-256'", bootstrap)

    def test_products_are_directly_scrollable_and_multi_selectable(self) -> None:
        css = (ROOT / "src" / "connections.css").read_text(encoding="utf-8").replace(" ", "")
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")
        self.assertIn("overflow-x:auto", css)
        self.assertIn("scrollbar-width:thin", css)
        self.assertIn("state.filters.products", core)
        self.assertIn("productMode", core)
        self.assertIn("selectedProducts.size", core)

    def test_homepage_starts_at_world_scope(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(encoding="utf-8")
        self.assertIn('id="region-title">World<', index)
        self.assertIn("review.setRegion('World')", bridge)

    def test_any_focused_selection_links_related_products(self) -> None:
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(encoding="utf-8")
        self.assertIn("var selectedProducts", bridge)
        self.assertIn("hasRelationalFocus", bridge)
        self.assertIn("state.filters?.owner", bridge)
        self.assertIn("state.filters?.route", bridge)
        self.assertIn("products.length", bridge)
        self.assertIn("has()", bridge)
        self.assertIn("return hasRelationalFocus(reviewState())", bridge)

    def test_product_counts_and_picker_descriptions_are_explicit(self) -> None:
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(encoding="utf-8")
        rail = (ROOT / "src" / "connections-rail-polish.js").read_text(encoding="utf-8")
        polish = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")

        self.assertIn("decorateProductLabels", bridge)
        self.assertIn("${value} listed sites", bridge)
        self.assertIn("${value} connected sites", bridge)
        self.assertIn(".product-node>span,.product-count{display:block", polish)

        self.assertIn("decorateProductPickerDescriptions", rail)
        self.assertIn("PRODUCT_DESCRIPTIONS", rail)
        self.assertIn("Semi-finished long steel", rail)
        self.assertIn("Reinforcing bar", rail)
        self.assertIn("#browse-result .browse-item", rail)
        self.assertIn("removeInlineProductDescriptions", rail)
        self.assertIn(".product-description{display:none!important}", polish)

    def test_steelmaking_values_expose_mtpa_unit(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")
        self.assertIn("* Mtpa = million tonnes per year.", index)
        self.assertIn("<small> Mtpa*</small>", core)

    def test_eu_and_ofac_sanctions_contexts_are_separate_factual_and_pinned(self) -> None:
        loader = (ROOT / "src" / "connections-sanctions-loader.js").read_text(encoding="utf-8")
        bridge = (ROOT / "src" / "connections-sanctions-bridge.js").read_text(encoding="utf-8")

        self.assertIn("eu-sanctions-owner-status.v1.json", loader)
        self.assertIn("ofac-sanctions-owner-status.v1.json", loader)
        self.assertIn("049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015", loader)
        self.assertIn("3D594ED7CDB5E0FD13F126A3815255146D730F791DCF672665C67416D03A7C1F", loader)
        self.assertIn("C59772F3EDD625812AC43C4AEC57513D08CDD180135A3B6368DBC086AB81DF7D", loader)
        self.assertIn("Company identity listed by OFAC", bridge)
        self.assertIn("Specially Designated Nationals and Blocked Persons (SDN) List", bridge)
        self.assertIn("Listed since", bridge)
        self.assertIn("Designation context", bridge)
        self.assertIn("reviewed GIST company identity", bridge)
        self.assertNotIn("Procurement implication", bridge)
        self.assertNotIn("No direct EU or U.S. listing found", bridge)
        self.assertNotIn("before contracting", bridge)
        self.assertNotIn("Identity resolution: Confirmed", bridge)
        self.assertNotIn("OFAC SDN", bridge)
        self.assertNotIn("85%", bridge)

    def test_trade_context_is_pinned_and_documented_in_sources(self) -> None:
        loader = (ROOT / "src" / "connections-trade-loader.js").read_text(encoding="utf-8")
        bridge = (ROOT / "src" / "connections-sanctions-bridge.js").read_text(encoding="utf-8")
        self.assertIn("eu-steel-trade-context.v1.json", loader)
        self.assertIn("eu-steel-trade-context-v1.1", loader)
        self.assertIn("B869A4BB8C4E4F7AE320B4CE4A117A33B05CADEEDF1C9DF106845EBCA9D9B21B", loader)
        self.assertIn("5F0214CD0FC9FC85A114B9EC485E2D6887F3F2137BD177EE357CC00FE2BB32BE", loader)
        self.assertIn("EU steel import scenario", bridge)
        self.assertIn("hypothetical import into the EU", bridge)
        self.assertNotIn("procurement follow-up", bridge.lower())
        self.assertNotIn("No water-stress, trade, emissions or buyer-supplier layer is present", bridge)

    def test_homepage_does_not_embed_the_full_dataset(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertLess(len(index.encode("utf-8")), 50_000)
        self.assertNotIn('\"plants\":[{', index)


if __name__ == "__main__":
    unittest.main()
