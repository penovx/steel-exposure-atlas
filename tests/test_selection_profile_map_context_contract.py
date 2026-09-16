from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SelectionProfileMapContextContractTests(unittest.TestCase):
    def test_selection_profile_keeps_map_context_visible(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "src" / "connections-selection-profile.css").read_text(encoding="utf-8").replace(" ", "")
        script = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-selection-profile.css?v=20260916-2', index)
        self.assertLess(index.index('id="geography"'), index.index('id="selection-profile"'))
        self.assertIn('.plant-node.dim{opacity:.42!important}', css)
        self.assertNotIn("document.querySelector('#geography').hidden", script)
        self.assertNotIn("document.querySelector('#connections-stage').hidden", script)


if __name__ == "__main__":
    unittest.main()
