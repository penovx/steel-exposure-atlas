from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourcesDialogContractTests(unittest.TestCase):
    def test_current_sources_dialog_is_loaded(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "src" / "connections-sources-dialog.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-sources-dialog.js?v=20260917-1', index)
        self.assertIn("SOURCE_BUTTON_IDS = ['open-sources', 'map-basis', 'footer-sources']", script)
        self.assertIn("document.documentElement.dataset.sourcesDialogInstalled", script)
        self.assertIn("The Company rail exposes the eligible company population", script)

    def test_sources_describe_current_relationship_boundaries(self) -> None:
        script = (ROOT / "src" / "connections-sources-dialog.js").read_text(encoding="utf-8")

        self.assertIn("immediate owner or operator recorded by GEM", script)
        self.assertIn("Plant product labels are descriptive source fields", script)
        self.assertIn("Operating capacity must not be read as supply available to a buyer", script)
        self.assertIn("Sanctions and EU steel trade context", script)
        self.assertIn("absence of a direct match is not promoted as clearance", script)
        self.assertIn("hypothetical import-into-the-EU relationship", script)

    def test_sources_do_not_repeat_retired_overview_copy(self) -> None:
        script = (ROOT / "src" / "connections-sources-dialog.js").read_text(encoding="utf-8").lower()

        self.assertNotIn("five company groups with the most sites", script)
        self.assertNotIn("no water-stress, trade, emissions or buyer-supplier layer is present", script)
        self.assertNotIn("explicit selections are shown below the graphic", script)

    def test_procurement_sources_expose_official_links_and_reuse_context(self) -> None:
        bridge = (ROOT / "src" / "connections-sanctions-bridge.js").read_text(encoding="utf-8")

        self.assertIn("https://webgate.ec.europa.eu/fsd/fsf#!/files", bridge)
        self.assertIn("https://commission.europa.eu/legal-notice_en", bridge)
        self.assertIn("https://creativecommons.org/licenses/by/4.0/", bridge)
        self.assertIn("https://ofac.treasury.gov/sanctions-list-service", bridge)
        self.assertIn("https://eur-lex.europa.eu/eli/reg_impl/2026/1457/oj/eng", bridge)
        self.assertIn("https://eur-lex.europa.eu/eli/reg_impl/2026/1930/oj/eng", bridge)
        self.assertIn("transformed enterprise-only evidence layer", bridge)
        self.assertIn("candidate product-family evidence rather than customs classification", bridge)
        self.assertIn("Cartography and provenance", bridge)


if __name__ == "__main__":
    unittest.main()
