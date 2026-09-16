from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SelectionProfileMapContextContractTests(unittest.TestCase):
    def test_company_selection_keeps_full_map_context_visible(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "src" / "connections-selection-profile.css").read_text(encoding="utf-8")
        script = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-selection-profile.css?v=20260916-3', index)
        self.assertLess(index.index('id="geography"'), index.index('id="selection-profile"'))
        self.assertIn('.plant-node.dim{opacity:.42!important}', css.replace(" ", ""))
        self.assertIn(
            '.connections-stage:has(#company-nodes .company-node.is-selected) .plant-node.dim{opacity:1!important}',
            css,
        )
        self.assertIn(
            '.connections-stage:has(#company-nodes .company-node.is-selected) .plant-node:not(.dim) .plant-disc',
            css,
        )
        self.assertIn('overflow-anchor:none', css.replace(" ", ""))
        self.assertNotIn("document.querySelector('#geography').hidden", script)
        self.assertNotIn("document.querySelector('#connections-stage').hidden", script)

    def test_company_click_does_not_rebuild_the_long_rail_twice_in_the_click_handler(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        rail = (ROOT / "src" / "connections-rail-polish.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-rail-polish.js?v=20260916-5', index)
        self.assertIn('document.createDocumentFragment()', rail)
        self.assertIn("companyNodes.dataset.restoreScrollTop = String(scrollTop)", rail)
        self.assertIn("api.choose('owner', button.dataset.owner)", rail)
        self.assertIn("window.scrollTo({left: pageX, top: pageY, behavior: 'auto'})", rail)
        click_block = rail.split("companyNodes.addEventListener('click'", 1)[1].split("function removeMisleadingSublines", 1)[0]
        self.assertNotIn("appendScrollableOwners();", click_block)
        self.assertNotIn("restoreStableOwnerOrder(companyNodes);", click_block)


if __name__ == "__main__":
    unittest.main()
