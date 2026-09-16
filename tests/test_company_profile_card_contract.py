from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CompanyProfileCardContractTests(unittest.TestCase):
    def test_company_profile_card_is_mounted_over_atlas(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "src" / "connections-company-profile-card.css").read_text(encoding="utf-8")

        self.assertIn('id="company-profile-card"', index)
        self.assertIn('./src/connections-company-profile-card.css?v=20260917-1', index)
        self.assertIn('grid-column:2', css.replace(" ", ""))
        self.assertIn('grid-row:1', css.replace(" ", ""))
        self.assertIn('z-index:18', css.replace(" ", ""))
        self.assertIn('max-height:calc(100%-30px)', css.replace(" ", ""))

    def test_company_profile_moves_standard_profile_without_second_click(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "src" / "connections-company-profile-card.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-company-profile-card.js?v=20260917-1', index)
        self.assertLess(
            index.index('./src/connections-selection-profile.js?v=20260916-1'),
            index.index('./src/connections-company-profile-card.js?v=20260917-1'),
        )
        self.assertIn("root.dataset.profileKind === 'company'", script)
        self.assertIn('while (root.firstChild) inner.append(root.firstChild)', script)
        self.assertIn('area.hidden = true', script)
        self.assertIn("review.choose?.('owner', ownerId)", script)
        self.assertNotIn('View company brief', script)


if __name__ == "__main__":
    unittest.main()
