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

    def test_visible_ports_share_the_active_edge_anchors(self) -> None:
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")

        self.assertIn("b.right-stage.left+4", core)
        self.assertIn("kind==='route'?{x:b.left-stage.left-5,y:b.top-stage.top+13}", core)
        self.assertIn("left:calc(100%+4px)", css)
        self.assertIn(".method-node::before{width:9px;height:9px;left:-5px;top:13px", css)

        self.assertIn("function syncProductPorts()", bridge)
        self.assertIn("const axisY = areaRect.top - stageRect.top", bridge)
        self.assertIn("port.setAttribute('cy', axisY.toFixed(2))", bridge)
        self.assertIn("const to = {x: target.x, y: axisY}", bridge)
        self.assertIn("edge.dataset.productTarget = target.id", bridge)
        self.assertIn(".product-axis-port{fill:var(--night);stroke:#9fb7c4", css)

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


if __name__ == "__main__":
    unittest.main()
