from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class UiIntegrationContractTests(unittest.TestCase):
    def test_root_promotes_real_evidence_workspace(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="evidence-map"', index)
        self.assertIn('id="region"', index)
        self.assertIn('id="country"', index)
        self.assertIn('id="plant-search"', index)
        self.assertIn('id="zoom-in"', index)
        self.assertIn('id="zoom-out"', index)
        self.assertIn('./prototype/evidence.mjs', index)
        self.assertNotIn('./src/app.js', index)

    def test_root_keeps_publication_boundaries_visible(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('Sources &amp; boundaries', index)
        self.assertIn('Global Energy Monitor', index)
        self.assertIn('CC BY 4.0', index)
        self.assertIn('Parent text is displayed unchanged and is not a corporate network.', index)

    def test_data_urls_are_module_relative_for_subpath_deployment(self) -> None:
        module = (ROOT / "prototype" / "evidence.mjs").read_text(encoding="utf-8")
        self.assertIn("new URL('../public/data/gist-plants.v1.json', import.meta.url)", module)
        self.assertIn("new URL('../public/data/ne_110m_admin_0_countries.v5.1.1.geojson', import.meta.url)", module)


if __name__ == "__main__":
    unittest.main()
