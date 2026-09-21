from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EdgeReadabilityContractTests(unittest.TestCase):
    def test_connection_edges_use_a_readability_mask(self) -> None:
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("edge-readability-mask", bridge)
        self.assertIn("edges.setAttribute('mask', 'url(#edge-readability-mask)')", bridge)
        self.assertIn("mask.style.maskType = 'luminance'", bridge)

    def test_map_and_static_interface_labels_create_fade_zones_without_measuring_every_company_row(self) -> None:
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )
        for selector in (
            ".country-label",
            ".plant-name",
            ".map-toolset",
            ".map-key",
            ".company-search",
            ".method-name",
            ".product-node",
        ):
            self.assertIn(selector, bridge)
        self.assertNotIn("'.company-name'", bridge)
        self.assertNotIn("'.company-count'", bridge)
        self.assertNotIn("'.company-sub'", bridge)
        self.assertIn("fill: '#2f2f2f'", bridge)

    def test_mask_observer_does_not_watch_every_stage_attribute_mutation(self) -> None:
        bridge = (ROOT / "src" / "connections-runtime-bridge.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function installEdgeReadabilityObserver()", bridge)
        self.assertIn("new ResizeObserver(queueEdgeReadabilityMask)", bridge)
        self.assertNotIn(
            "mutationObserver.observe(stage, {childList: true, subtree: true, attributes: true})",
            bridge,
        )

    def test_dense_product_edges_are_softer_than_other_focused_edges(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        self.assertIn(".connection-edge.strong{opacity:.48}", css)
        self.assertIn(".connection-edge.product.strong{opacity:.3}", css)


if __name__ == "__main__":
    unittest.main()
