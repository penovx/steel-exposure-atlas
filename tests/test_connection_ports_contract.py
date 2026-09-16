from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ConnectionPortsContractTests(unittest.TestCase):
    def test_product_ports_render_in_connection_svg(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("function ensureProductPortLayer()", bridge)
        self.assertIn("id: 'product-port-layer'", bridge)
        self.assertIn("svgNode('circle'", bridge)
        self.assertIn("port.setAttribute('cx'", bridge)
        self.assertIn("port.setAttribute('cy'", bridge)
        self.assertIn("#product-port-layer{pointer-events:none}", css)
        self.assertIn(".product-axis-port{fill:var(--night);stroke:#9fb7c4", css)
        self.assertIn(".product-port{display:none}", css)

    def test_products_area_has_no_independent_horizontal_baseline(self) -> None:
        polish = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )

        self.assertIn(".products-area{z-index:auto!important;border-top:0", polish)
        self.assertIn(".products-area::before{display:none}", polish)
        self.assertNotIn(".product-axis{", polish)
        self.assertNotIn("alignProductBaseline", bridge)
        self.assertNotIn("--product-baseline-y", bridge)

    def test_product_circle_and_edge_share_exact_svg_y_coordinate(self) -> None:
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("const axisY = areaRect.top - stageRect.top", bridge)
        self.assertIn("port.setAttribute('cy', axisY.toFixed(2))", bridge)
        self.assertIn("const to = {x: target.x, y: axisY}", bridge)
        self.assertIn("edge.dataset.productTarget = target.id", bridge)
        self.assertIn("#edge-layer .connection-edge.product", bridge)

    def test_method_ports_remain_visible_at_the_route_endpoint(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")

        self.assertIn(".method-rail,.method-nodes,.method-node{overflow:visible}", css)
        self.assertIn(".method-node::before{width:9px;height:9px;left:-5px;top:13px", css)
        self.assertIn("kind==='route'?{x:b.left-stage.left-5,y:b.top-stage.top+13}", core)


if __name__ == "__main__":
    unittest.main()
