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

    def test_company_rail_is_complete_immediately_and_not_reconstructed_after_click(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        core = (ROOT / "src" / "connections-core.js").read_text(encoding="utf-8")
        rail = (ROOT / "src" / "connections-rail-polish.js").read_text(encoding="utf-8")
        bootstrap = (ROOT / "src" / "connections-bootstrap.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-rail-polish.js?v=20260916-5', index)
        self.assertIn('./src/connections-runtime-bridge.js?v=20260916-2', index)
        self.assertIn('./src/connections-bootstrap.js?v=20260916-2', index)
        self.assertIn("import('./connections-core.js?v=20260916-2')", bootstrap)
        self.assertIn("function syncCompanyRail(availableOwners,chosen)", core)
        self.assertIn("ownerList=availableOwners", core)
        self.assertIn("if(container.dataset.ownerSignature!==signature)", core)
        self.assertNotIn(".slice(0,5)", core)
        self.assertNotIn("appendScrollableOwners", rail)
        self.assertNotIn("restoreStableOwnerOrder", rail)
        self.assertNotIn("installOwnerSelectionBridge", rail)


if __name__ == "__main__":
    unittest.main()
