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

    def test_single_structural_divider_separates_upper_field_from_products(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        polish = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")

        self.assertIn('class="product-divider"', index)
        self.assertIn(".product-divider{grid-column:1/-1;grid-row:2", polish)
        self.assertIn("height:1px;background:#2d4553", polish)
        self.assertIn(".more-link{border-top:0}", polish)
        self.assertIn(".products-area::before{display:none}", polish)

    def test_product_circle_and_edge_share_structural_divider_y_coordinate(self) -> None:
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("document.querySelector('.product-divider')", bridge)
        self.assertIn("dividerRect.top + dividerRect.height / 2 - stageRect.top", bridge)
        self.assertIn("port.setAttribute('cy', axisY.toFixed(2))", bridge)
        self.assertIn("const to = {x: target.x, y: axisY}", bridge)
        self.assertIn("edge.dataset.productTarget = target.id", bridge)

    def test_method_ports_are_real_elements_and_edges_are_reanchored_to_them(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("function ensureMethodPorts()", bridge)
        self.assertIn("port.className = 'method-port'", bridge)
        self.assertIn("function syncMethodPorts()", bridge)
        self.assertIn("edge.dataset.routeTarget = routeId", bridge)
        self.assertIn(".method-node::before{display:none}", css)
        self.assertIn(".method-port{position:absolute;left:-5px;top:13px;width:9px;height:9px", css)

    def test_company_edges_hide_when_target_row_is_outside_scroll_viewport(self) -> None:
        rail = (ROOT / "src" / "connections-rail-polish.js").read_text(encoding="utf-8")

        self.assertIn("const companyViewport = companyNodes.getBoundingClientRect()", rail)
        self.assertIn("targetCenter >= companyViewport.top", rail)
        self.assertIn("targetCenter <= companyViewport.bottom", rail)
        self.assertIn("edge.style.visibility = targetVisible ? '' : 'hidden'", rail)
        self.assertIn("ownerTargetVisibility", rail)
        self.assertIn("companyNodes.addEventListener('scroll', sync", rail)
        self.assertNotIn("scrollIntoView", rail)


if __name__ == "__main__":
    unittest.main()
