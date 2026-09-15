from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ConnectionPortsContractTests(unittest.TestCase):
    def test_product_ports_are_visible_inside_scroll_strip(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")

        self.assertIn(".product-nodes{padding-top:20px", css)
        self.assertIn(".product-port{width:9px;height:9px", css)
        self.assertIn("top:-15px", css)
        self.assertIn(".product-node::after{display:none}", css)

    def test_connection_layer_can_enter_products_area_and_nodes_stay_above_it(self) -> None:
        base_css = (ROOT / "src" / "connections.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        polish = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")

        self.assertIn("#connection-lines{", base_css)
        self.assertIn("z-index:3", base_css)
        self.assertIn(".products-area{z-index:auto!important}", polish)
        self.assertIn(".product-node{z-index:4", polish)

    def test_method_ports_remain_visible_at_the_route_endpoint(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")

        self.assertIn(".method-rail,.method-nodes,.method-node{overflow:visible}", css)
        self.assertIn(".method-node::before{width:9px;height:9px;left:-5px;top:13px", css)
        self.assertIn("kind==='route'?{x:b.left-stage.left-5,y:b.top-stage.top+13}", core)

    def test_product_edge_endpoint_matches_the_visible_port_center(self) -> None:
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")

        self.assertIn("{x:b.left-stage.left+b.width/2,y:b.top-stage.top-15}", core)
        self.assertIn(".product-port{width:9px;height:9px;left:50%;top:-15px", css)


if __name__ == "__main__":
    unittest.main()
