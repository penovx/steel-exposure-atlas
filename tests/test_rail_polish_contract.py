from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RailPolishContractTests(unittest.TestCase):
    def test_polish_runtime_is_loaded(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('./src/connections-rail-polish.js?v=20260916-6', index)

    def test_company_rail_is_scrollable_virtualized_and_not_backfilled(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        rail = (ROOT / "src" / "connections-rail-polish.js").read_text(
            encoding="utf-8"
        )
        virtual = (ROOT / "src" / "connections-company-virtual-rail.js").read_text(
            encoding="utf-8"
        )
        virtual_css = (ROOT / "src" / "connections-company-virtual-rail.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")

        self.assertIn("overflow-y:scroll", css)
        self.assertIn("scrollbar-gutter:stable", css)
        self.assertIn(".company-sub{display:none!important}", css)
        self.assertIn("ROW_STEP = 72", virtual)
        self.assertIn("BUFFER_ROWS = 6", virtual)
        self.assertIn("logicalGroups = groups", virtual)
        self.assertIn("container.replaceChildren(fragment)", virtual)
        self.assertIn("company-virtual-spacer", virtual)
        self.assertIn(".company-nodes.is-virtualized", virtual_css)
        self.assertNotIn("function appendScrollableOwners()", rail)
        self.assertNotIn("bridge-extra-owner", rail)
        self.assertIn("function removeMisleadingSublines()", rail)
        self.assertIn("#company-nodes .company-sub", rail)

    def test_selected_owner_keeps_page_and_virtual_rail_viewport_stable(self) -> None:
        virtual = (ROOT / "src" / "connections-company-virtual-rail.js").read_text(
            encoding="utf-8"
        )
        rail = (ROOT / "src" / "connections-rail-polish.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("const pageX = window.scrollX", virtual)
        self.assertIn("const pageY = window.scrollY", virtual)
        self.assertIn("lastScrollTop = container.scrollTop", virtual)
        self.assertIn("container.scrollTop = lastScrollTop", virtual)
        self.assertIn("window.scrollTo({left: pageX, top: pageY, behavior: 'auto'})", virtual)
        self.assertIn("container.dataset.viewportGuard = 'true'", virtual)
        self.assertIn("function syncCompanyEdgeAnchors()", rail)
        self.assertNotIn("appendScrollableOwners", rail)

    def test_other_method_subline_and_method_tracks_are_removed(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        script = (ROOT / "src" / "connections-rail-polish.js").read_text(
            encoding="utf-8"
        )
        self.assertIn(".method-track{display:none!important}", css)
        self.assertIn('.method-node[data-route="Other"].method-sub{display:none!important}', css)
        self.assertIn('#method-nodes .method-node[data-route="Other"] .method-sub', script)

    def test_selected_products_and_methods_share_company_selection_grammar(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        self.assertIn(
            ".method-node.is-selected,.product-node.is-selected{background:#152b38!important;color:var(--accent)!important}",
            css,
        )
        self.assertIn(".method-node.is-selected{box-shadow:9px00#152b38}", css)
        self.assertIn(
            ".method-node.is-selected.method-name{color:var(--accent)!important}",
            css,
        )
        self.assertIn(
            ".method-node.is-selected.method-value{color:var(--method-color)!important}",
            css,
        )
        self.assertIn(
            ".product-node.is-selected.product-count,.product-node.is-selected.product-remove{color:var(--accent)!important}",
            css,
        )

    def test_find_a_plant_results_scroll_vertically(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        self.assertIn(".browse-result{max-height:min(52vh,520px);overflow-y:auto", css)
        self.assertIn("overscroll-behavior-y:contain", css)

    def test_method_endpoint_dots_are_svg_ports_at_edge_endpoints(self) -> None:
        script = (ROOT / "src" / "connections-rail-polish.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function renderMethodEndpointDots()", script)
        self.assertIn("method-endpoint-layer", script)
        self.assertIn("pathEnd(edge)", script)
        self.assertIn("method-endpoint-port", script)

    def test_product_descriptions_live_in_picker_not_atlas_rail(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        script = (ROOT / "src" / "connections-rail-polish.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function removeInlineProductDescriptions()", script)
        self.assertIn("#product-nodes .product-description", script)
        self.assertIn("function decorateProductPickerDescriptions()", script)
        self.assertIn('#browse-result .browse-item[data-browse-kind="product"]', script)
        self.assertIn("Semi-finished long steel", script)
        self.assertIn("GIST-listed steel product category", script)
        self.assertIn(".product-description{display:none!important}", css)
        self.assertNotIn("function ensureProductDescriptions()", script)

    def test_product_picker_uses_fixed_text_column_and_sentence_case_labels(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        script = (ROOT / "src" / "connections-rail-polish.js").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            '.browse-item[data-browse-kind="product"]{display:grid;grid-template-columns:18pxminmax(0,1fr)auto',
            css,
        )
        self.assertIn("function sentenceCaseProductLabel(value)", script)
        self.assertIn("function sentenceCaseInlineProductLabels()", script)
        self.assertIn("text.charAt(0).toUpperCase() + text.slice(1)", script)
        self.assertIn("item.querySelector('span > strong')", script)

    def test_masthead_stays_full_width_without_intro_deck(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        index = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn(".masthead{position:sticky;top:0;left:0;right:0;z-index:50", css)
        self.assertIn("width:100%!important", css)
        self.assertIn("margin:0!important", css)
        self.assertIn("padding:0var(--margin)!important", css)
        self.assertIn(".mastheadnav{display:none!important}", css)
        self.assertIn(".masthead.edition{margin-left:auto}", css)
        self.assertIn('connections-visual-polish.css?v=20260916-4', index)
        self.assertIn('class="masthead"', index)
        self.assertNotIn('class="intro"', index)


if __name__ == "__main__":
    unittest.main()
