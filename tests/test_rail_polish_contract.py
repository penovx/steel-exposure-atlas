from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RailPolishContractTests(unittest.TestCase):
    def test_polish_runtime_is_loaded(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('./src/connections-rail-polish.js?v=20260916-5', index)

    def test_ownership_list_is_scrollable_and_rendered_complete_by_core(self) -> None:
        css = (ROOT / "src" / "connections-visual-polish.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        rail = (ROOT / "src" / "connections-rail-polish.js").read_text(
            encoding="utf-8"
        )
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")

        self.assertIn("overflow-y:scroll", css)
        self.assertIn("scrollbar-gutter:stable", css)
        self.assertIn(".company-sub{display:none!important}", css)
        self.assertIn(".more-link{display:none!important}", css)
        self.assertIn("function syncCompanyRail(availableOwners,chosen)", core)
        self.assertIn("ownerList=availableOwners", core)
        self.assertIn("container.dataset.ownerSignature", core)
        self.assertIn("container.innerHTML=availableOwners.map", core)
        self.assertNotIn("ownerList=[...availableOwners]", core)
        self.assertNotIn("function appendScrollableOwners()", rail)
        self.assertNotIn("bridge-extra-owner", rail)
        self.assertIn("function removeMisleadingSublines()", rail)
        self.assertIn("#company-nodes .company-sub", rail)

    def test_selected_owner_keeps_stable_row_and_edge_anchor_without_rail_rebuild(self) -> None:
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")
        rail = (ROOT / "src" / "connections-rail-polish.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("if(container.dataset.ownerSignature!==signature)", core)
        self.assertIn("node.classList.toggle('is-selected',select)", core)
        self.assertIn("node.setAttribute('aria-pressed',String(select))", core)
        self.assertIn('data-port="owner:${esc(g.id)}"', core)
        self.assertNotIn("function installOwnerSelectionBridge", rail)
        self.assertNotIn("function restoreStableOwnerOrder", rail)
        self.assertNotIn("function appendScrollableOwners", rail)
        self.assertIn("function syncCompanyEdgeAnchors()", rail)
        self.assertIn("companyNodes.addEventListener('scroll', sync", rail)

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

    def test_masthead_stays_sticky_full_width_while_intro_scrolls_away(self) -> None:
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
        self.assertIn(".intro{position:static}", css)
        self.assertIn('connections-visual-polish.css?v=20260916-4', index)
        self.assertIn('class="masthead"', index)
        self.assertIn('class="intro"', index)


if __name__ == "__main__":
    unittest.main()
