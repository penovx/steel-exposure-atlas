from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RailPolishContractTests(unittest.TestCase):
    def test_polish_runtime_is_loaded(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('./src/connections-rail-polish.js', index)

    def test_ownership_list_is_scrollable_and_subline_hidden(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        script = (ROOT / "src" / "connections-rail-polish.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("overflow-y:auto", css)
        self.assertIn(".company-sub{display:none!important}", css)
        self.assertIn(".more-link{display:none!important}", css)
        self.assertIn("function appendScrollableOwners()", script)
        self.assertIn("bridge-extra-owner", script)

    def test_other_method_subline_and_method_tracks_are_removed(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        self.assertIn(".method-track{display:none!important}", css)
        self.assertIn('.method-node[data-route="Other"].method-sub{display:none!important}', css)

    def test_method_endpoint_dots_are_svg_ports_at_edge_endpoints(self) -> None:
        script = (ROOT / "src" / "connections-rail-polish.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function renderMethodEndpointDots()", script)
        self.assertIn("method-endpoint-layer", script)
        self.assertIn("pathEnd(edge)", script)
        self.assertIn("method-endpoint-port", script)

    def test_every_product_receives_a_visible_description(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        script = (ROOT / "src" / "connections-rail-polish.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function ensureProductDescriptions()", script)
        self.assertIn("GIST-listed steel product category", script)
        self.assertIn(".product-description{display:block!important", css)
        self.assertIn("min-height:28px", css)


if __name__ == "__main__":
    unittest.main()
