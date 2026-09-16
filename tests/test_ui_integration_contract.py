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

    def test_eu_sanctions_context_is_categorical_and_snapshot_pinned(self) -> None:
        loader = (ROOT / "src" / "connections-sanctions-loader.js").read_text(encoding="utf-8")
        bridge = (ROOT / "src" / "connections-sanctions-bridge.js").read_text(encoding="utf-8")

        self.assertIn("eu-sanctions-owner-status.v1.json", loader)
        self.assertIn("049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015", loader)
        self.assertIn("Direct list match", bridge)
        self.assertIn("Review required", bridge)
        self.assertIn("No direct list match in this snapshot", bridge)
        self.assertIn("Identity resolution: Confirmed", bridge)
        self.assertIn("not sanctions clearance", bridge)
        self.assertNotIn("85%", bridge)
        self.assertIn("No sanctions percentage or risk score is defined", bridge)

    def test_homepage_does_not_embed_the_full_dataset(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertLess(len(index.encode("utf-8")), 50_000)
        self.assertNotIn('\"plants\":[{', index)


if __name__ == "__main__":
    unittest.main()
