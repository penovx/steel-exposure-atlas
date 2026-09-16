from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ConnectionPortsContractTests(unittest.TestCase):
    def test_product_ports_use_dedicated_structural_axis(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("function ensureProductAxis()", bridge)
        self.assertIn("axis.className = 'product-axis'", bridge)
        self.assertIn(".product-axis{position:absolute;left:0;right:0;top:0", css)
        self.assertIn(".product-axis-port{position:absolute;top:0;width:9px;height:9px", css)
        self.assertIn(".product-port{visibility:hidden}", css)

    def test_connection_layer_can_enter_products_area_and_nodes_stay_above_it(self) -> None:
        base_css = (ROOT / "src" / "connections.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        polish = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")

        self.assertIn("#connection-lines{", base_css)
        self.assertIn("z-index:3", base_css)
        self.assertIn(".products-area{z-index:auto!important;border-top:0", polish)
        self.assertIn(".product-node{z-index:4", polish)
        self.assertIn(".product-axis{", polish)

    def test_product_axis_is_grid_boundary_not_measured_offset(self) -> None:
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )
        polish = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")

        self.assertNotIn("alignProductBaseline", bridge)
        self.assertNotIn("--product-baseline-y", bridge)
        self.assertIn("const axisY = areaRect.top - stageRect.top", bridge)
        self.assertIn(".products-area::before{display:none}", polish)
        self.assertIn(".product-nodes{padding-top:20px", polish)
        self.assertNotIn("top:-6px", polish)
        self.assertNotIn("top:-12px", polish)

    def test_method_ports_remain_visible_at_the_route_endpoint(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")

        self.assertIn(".method-rail,.method-nodes,.method-node{overflow:visible}", css)
        self.assertIn(".method-node::before{width:9px;height:9px;left:-5px;top:13px", css)
        self.assertIn("kind==='route'?{x:b.left-stage.left-5,y:b.top-stage.top+13}", core)

    def test_product_edges_are_reanchored_to_axis_ports(self) -> None:
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("function syncProductAxis()", bridge)
        self.assertIn("productTargets(stageRect)", bridge)
        self.assertIn("const to = {x: target.x, y: axisY}", bridge)
        self.assertIn("edge.dataset.productTarget = target.id", bridge)
        self.assertIn("#edge-layer .connection-edge.product", bridge)


if __name__ == "__main__":
    unittest.main()
