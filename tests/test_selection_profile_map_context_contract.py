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

    def test_company_rail_is_bounded_and_never_delayed_backfilled(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")
        rail = (ROOT / "src" / "connections-rail-polish.js").read_text(encoding="utf-8")
        procurement = (ROOT / "src" / "connections-procurement-ui.js").read_text(encoding="utf-8")
        bootstrap = (ROOT / "src" / "connections-bootstrap.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-rail-polish.js?v=20260916-6', index)
        self.assertIn('./src/connections-procurement-ui.js?v=20260916-7', index)
        self.assertIn('./src/connections-bootstrap.js?v=20260916-3', index)
        self.assertIn("import('./connections-core.js?v=20260916-3')", bootstrap)
        self.assertIn("ownerList=[...availableOwners]", core)
        owner_block = core.split("const availableOwners=owners(base)", 1)[1].split("$('#company-total')", 1)[0]
        self.assertIn(".slice(0,5)", owner_block)
        self.assertNotIn("appendScrollableOwners", rail)
        self.assertNotIn("bridge-extra-owner", rail)
        self.assertIn("input.readOnly = true", procurement)
        self.assertIn("openCompanyPicker", procurement)

    def test_first_paint_builds_only_world_and_europe_maps(self) -> None:
        bootstrap = (ROOT / "src" / "connections-bootstrap.js").read_text(encoding="utf-8")

        self.assertIn("ensureMap('Europe')", bootstrap)
        self.assertIn("ensureMap('World')", bootstrap)
        self.assertIn("const maps=new Proxy(mapCache", bootstrap)
        self.assertIn("requestIdleCallback(warmNext", bootstrap)
        self.assertNotIn("for(const region of REGIONS){const scoped", bootstrap)

    def test_company_click_restores_page_and_rail_viewport(self) -> None:
        rail = (ROOT / "src" / "connections-rail-polish.js").read_text(encoding="utf-8")

        self.assertIn("function installCompanyViewportGuard(companyNodes)", rail)
        self.assertIn("const pageY = window.scrollY", rail)
        self.assertIn("const railScrollTop = companyNodes.scrollTop", rail)
        self.assertIn("companyNodes.scrollTop = railScrollTop", rail)
        self.assertIn("window.scrollTo({left: pageX, top: pageY, behavior: 'auto'})", rail)


if __name__ == "__main__":
    unittest.main()
