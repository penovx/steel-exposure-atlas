from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ConnectionVisualContractTests(unittest.TestCase):
    def test_visual_polish_layer_is_loaded(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('./src/connections-visual-polish.css', index)

    def test_logo_uses_connected_node_grammar(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        self.assertIn('d="M7 7 25 15 9 26 7 7"', index)
        self.assertEqual(index.count("<circle"), 3)
        self.assertIn(".brandsvgpath{fill:none", css)
        self.assertIn(".brandsvgcircle{fill:var(--paper)", css)

    def test_visible_ports_share_active_edge_anchors(self) -> None:
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")

        self.assertIn("function syncProductPorts()", bridge)
        self.assertIn("dividerRect.top + dividerRect.height / 2 - stageRect.top", bridge)
        self.assertIn("edge.dataset.productTarget = target.id", bridge)
        self.assertIn(".product-axis-port{fill:var(--night);stroke:#9fb7c4", css)

        self.assertIn("function syncMethodPorts()", bridge)
        self.assertIn("marker.getBoundingClientRect()", bridge)
        self.assertIn("edge.dataset.routeTarget = routeId", bridge)
        self.assertIn(".method-port{position:absolute", css)

    def test_disconnected_product_keeps_scope_description_not_zero(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )

        self.assertIn(".product-node.dim>span{visibility:visible", css)
        self.assertIn("scopeProductCount", bridge)
        self.assertIn("connected > 0", bridge)
        self.assertIn("`${value} listed sites`", bridge)

    def test_product_descriptions_are_moved_to_picker(self) -> None:
        polish_script = (ROOT / "src" / "connections-rail-polish.js").read_text(
            encoding="utf-8"
        )
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")

        self.assertIn("PRODUCT_DESCRIPTIONS", polish_script)
        self.assertIn("Semi-finished long steel", polish_script)
        self.assertIn("Reinforcing bar", polish_script)
        self.assertIn("GIST-listed steel product category", polish_script)
        self.assertIn("function decorateProductPickerDescriptions()", polish_script)
        self.assertIn('#browse-result .browse-item[data-browse-kind="product"]', polish_script)
        self.assertIn("function removeInlineProductDescriptions()", polish_script)
        self.assertIn("#product-nodes .product-description", polish_script)
        self.assertIn(".product-description{display:none!important}", css)


if __name__ == "__main__":
    unittest.main()
