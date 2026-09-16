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

    def test_company_rail_exposes_full_population_through_virtual_window(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        virtual = (ROOT / "src" / "connections-company-virtual-rail.js").read_text(encoding="utf-8")
        virtual_css = (ROOT / "src" / "connections-company-virtual-rail.css").read_text(encoding="utf-8")
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-company-virtual-rail.js?v=20260916-1', index)
        self.assertIn('./src/connections-company-virtual-rail.css?v=20260916-1', index)
        self.assertLess(
            index.index('./src/connections-company-virtual-rail.js?v=20260916-1'),
            index.index('./src/connections-rail-polish.js?v=20260916-6'),
        )
        self.assertIn('review.model.owners(scoped)', virtual)
        self.assertIn('logicalGroups = groups', virtual)
        self.assertIn('filteredGroups = needle', virtual)
        self.assertIn("node.className = 'company-virtual-spacer'", virtual)
        self.assertIn('container.replaceChildren(fragment)', virtual)
        self.assertIn('BUFFER_ROWS', virtual)
        self.assertIn('.company-nodes.is-virtualized', virtual_css)
        # Core keeps a small owner list only as relationship-line LOD; it is no
        # longer the user-facing company population.
        self.assertIn('.slice(0,5)', core)

    def test_first_paint_builds_only_world_and_europe_maps(self) -> None:
        bootstrap = (ROOT / "src" / "connections-bootstrap.js").read_text(encoding="utf-8")

        self.assertIn("ensureMap('Europe')", bootstrap)
        self.assertIn("ensureMap('World')", bootstrap)
        self.assertIn("const maps=new Proxy(mapCache", bootstrap)
        self.assertIn("requestIdleCallback(warmNext", bootstrap)
        self.assertNotIn("for(const region of REGIONS){const scoped", bootstrap)

    def test_virtual_company_click_preserves_page_and_rail_viewport(self) -> None:
        virtual = (ROOT / "src" / "connections-company-virtual-rail.js").read_text(encoding="utf-8")

        self.assertIn('lastScrollTop = container.scrollTop', virtual)
        self.assertIn('const pageY = window.scrollY', virtual)
        self.assertIn("review.choose('owner', button.dataset.virtualOwner)", virtual)
        self.assertIn("window.scrollTo({left: pageX, top: pageY, behavior: 'auto'})", virtual)
        self.assertIn("container.dataset.viewportGuard = 'true'", virtual)


if __name__ == "__main__":
    unittest.main()
