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

    def test_visible_ports_share_the_edge_endpoint_coordinates(self) -> None:
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")

        self.assertIn("b.right-stage.left+4", core)
        self.assertIn("kind==='route'?{x:b.left-stage.left-5,y:b.top-stage.top+13}", core)
        self.assertIn("{x:b.left-stage.left+b.width/2,y:b.top-stage.top-15}", core)

        self.assertIn("left:calc(100%+4px)", css)
        self.assertIn(".method-node::before{width:9px;height:9px;left:-5px;top:13px", css)
        self.assertIn(".product-port{width:9px;height:9px;left:50%;top:-15px", css)
        self.assertIn("transform:translate(-50%,-50%)", css)

    def test_disconnected_product_does_not_show_zero_as_a_data_value(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        self.assertIn(".product-node.dim>span{visibility:hidden}", css)


if __name__ == "__main__":
    unittest.main()
