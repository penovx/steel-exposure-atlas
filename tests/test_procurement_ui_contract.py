from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProcurementUiContractTests(unittest.TestCase):
    def test_facets_use_plain_language_and_company_search(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        search = (ROOT / "src" / "connections-procurement-ui.js").read_text(encoding="utf-8")

        self.assertIn('id="company-title">Companies<', index)
        self.assertIn('id="method-title">Production methods<', index)
        self.assertIn('placeholder="Search companies"', index)
        self.assertIn('./src/connections-procurement-ui.js?v=20260916-1', index)
        self.assertIn(".company-node[data-owner]", search)
        self.assertIn("companyName(node)", search)
        self.assertIn("event.key === 'Escape'", search)
        self.assertIn("event.key === 'Enter'", search)

    def test_sanctions_are_visible_at_company_row_and_explained_for_procurement(self) -> None:
        bridge = (ROOT / "src" / "connections-sanctions-bridge.js").read_text(encoding="utf-8")
        css = (ROOT / "src" / "connections-procurement-ui.css").read_text(encoding="utf-8")

        self.assertIn("U.S. sanctions list", bridge)
        self.assertIn("EU sanctions list", bridge)
        self.assertIn("company-sanctions-flags", bridge)
        self.assertIn("Listed by OFAC", bridge)
        self.assertIn("Specially Designated Nationals and Blocked Persons (SDN) List", bridge)
        self.assertIn("Listed since", bridge)
        self.assertIn("Designation context", bridge)
        self.assertIn("Procurement implication", bridge)
        self.assertIn("before contracting, ordering or payment", bridge)
        self.assertIn("No direct EU or U.S. listing found", bridge)
        self.assertIn("This does not mean sanctions-cleared", bridge)
        self.assertNotIn("Identity resolution: Confirmed", bridge)
        self.assertNotIn("OFAC SDN", bridge)
        self.assertIn(".company-sanctions-flag", css)
        self.assertIn(".sanctions-impact", css)


if __name__ == "__main__":
    unittest.main()
