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
        self.assertIn('./src/connections.css', index)
        self.assertIn('./src/connections-runtime-bridge.js', index)
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

    def test_focused_non_product_selection_links_related_products(self) -> None:
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(encoding="utf-8")
        self.assertIn("var selectedProducts", bridge)
        self.assertIn("products.length", bridge)
        self.assertIn("state.filters?.owner", bridge)
        self.assertIn("state.filters?.route", bridge)
        self.assertIn("return Boolean(state.site", bridge)

    def test_steelmaking_values_expose_mtpa_unit(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")
        self.assertIn("* Mtpa = million tonnes per year.", index)
        self.assertIn("<small> Mtpa*</small>", core)

    def test_homepage_does_not_embed_the_full_dataset(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertLess(len(index.encode("utf-8")), 50_000)
        self.assertNotIn('\"plants\":[{', index)


if __name__ == "__main__":
    unittest.main()
