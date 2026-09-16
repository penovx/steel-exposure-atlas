from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CompanyBriefPlainLanguageContractTests(unittest.TestCase):
    def test_first_click_affordance_is_loaded_and_explicit(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "src" / "connections-company-brief-affordance.js").read_text(encoding="utf-8")

        self.assertIn(
            './src/connections-company-brief-affordance.js?v=20260916-1',
            index,
        )
        self.assertIn("Open company brief →", script)
        self.assertIn("Click again to", script)
        self.assertIn("requestAnimationFrame(sync)", script)

    def test_company_brief_uses_plain_location_and_product_coverage_copy(self) -> None:
        script = (ROOT / "src" / "connections-company-brief-affordance.js").read_text(encoding="utf-8")

        self.assertIn("SITES & COUNTRIES", script)
        self.assertIn("Where the connected plants are located", script)
        self.assertIn("site' : 'sites'} in ${country}", script)
        self.assertIn("Listed at ${listed} of ${total} connected", script)
        self.assertIn("· ${plain}", script)
        self.assertIn("trade context at $1 of $2 connected sites", script)
        self.assertNotIn("1/4 sites", script)


if __name__ == "__main__":
    unittest.main()
