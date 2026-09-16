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
        self.assertIn('./src/connections-procurement-ui.js?v=20260916-6', index)
        self.assertIn('./src/connections-procurement-ui.css?v=20260916-4', index)
        self.assertIn(".company-node[data-owner]", search)
        self.assertIn("companyName(node)", search)
        self.assertIn("companyIsEligible", search)
        self.assertIn("__ATLAS_COMPANY_ELIGIBILITY__", search)
        self.assertIn("syncCompanyEdges", search)
        self.assertIn("edge.hidden = !eligible || (hasQuery && !visibleOwnerIds.has(ownerId))", search)
        self.assertIn("atlas-company-eligibility-ready", search)
        self.assertIn("event.key === 'Escape'", search)
        self.assertIn("event.key === 'Enter'", search)

    def test_dynamic_reading_copy_names_the_actual_relationship(self) -> None:
        script = (ROOT / "src" / "connections-procurement-ui.js").read_text(encoding="utf-8")
        self.assertIn("function syncReadingCopy()", script)
        self.assertIn("GEM names ${owner} as the immediate owner or operator", script)
        self.assertIn("company attribution, listed products and production methods", script)
        self.assertIn("companies GEM names as owner or operator", script)
        self.assertIn("sites in the current selection", script)
        self.assertIn("not material flows", script)
        self.assertNotIn("procurement follow-ups", script)
        self.assertNotIn("These sites are linked to the same company", script)

    def test_reading_composition_gives_more_space_to_evidence_detail(self) -> None:
        css = (ROOT / "src" / "connections-procurement-ui.css").read_text(
            encoding="utf-8"
        ).replace(" ", "")
        self.assertIn(
            ".reading-grid{grid-template-columns:minmax(0,.9fr)minmax(380px,1.1fr)",
            css,
        )
        self.assertIn("@media(max-width:900px){.reading-grid{grid-template-columns:1fr", css)
        self.assertIn(".company-rail.rail-subtitle{margin-bottom:10px}", css)

    def test_sanctions_are_visible_as_evidence_not_process_advice(self) -> None:
        bridge = (ROOT / "src" / "connections-sanctions-bridge.js").read_text(encoding="utf-8")
        css = (ROOT / "src" / "connections-procurement-ui.css").read_text(encoding="utf-8")

        self.assertIn("U.S. sanctions list", bridge)
        self.assertIn("EU sanctions list", bridge)
        self.assertIn("company-sanctions-flags", bridge)
        self.assertIn("Company identity listed by OFAC", bridge)
        self.assertIn("Specially Designated Nationals and Blocked Persons (SDN) List", bridge)
        self.assertIn("Listed since", bridge)
        self.assertIn("Designation context", bridge)
        self.assertIn("reviewed GIST company identity", bridge)
        self.assertNotIn("Procurement implication", bridge)
        self.assertNotIn("before contracting, ordering or payment", bridge)
        self.assertNotIn("No direct EU or U.S. listing found", bridge)
        self.assertNotIn("Identity resolution: Confirmed", bridge)
        self.assertNotIn("OFAC SDN", bridge)
        self.assertIn(".company-sanctions-flag", css)


if __name__ == "__main__":
    unittest.main()
