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

    def test_company_selection_requires_explicit_open_profile_action(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        card = (ROOT / "src" / "connections-company-profile-card.js").read_text(encoding="utf-8")
        rail = (ROOT / "src" / "connections-company-virtual-rail.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-company-profile-card.js?v=20260917-2', index)
        self.assertIn('./src/connections-company-virtual-rail.js?v=20260917-2', index)
        self.assertIn("button.textContent = 'Open company profile →'", rail)
        self.assertIn("atlas-open-company-profile", rail)
        self.assertIn("window.addEventListener('atlas-open-company-profile'", card)
        self.assertIn("openOwnerId !== ownerId", card)
        self.assertIn("area.hidden = true", card)
        self.assertNotIn("review.choose?.('owner', ownerId)", card)

    def test_clicking_selected_company_again_can_deselect_without_opening_profile(self) -> None:
        rail = (ROOT / "src" / "connections-company-virtual-rail.js").read_text(encoding="utf-8")
        card = (ROOT / "src" / "connections-company-profile-card.js").read_text(encoding="utf-8")

        self.assertIn("review.choose('owner', button.dataset.virtualOwner)", rail)
        self.assertIn("if (!ownerId) {", card)
        self.assertIn("card.hidden = true", card)
        self.assertIn("closeProfileOnly", card)
        self.assertIn("returnCardContentToRoot", card)


if __name__ == "__main__":
    unittest.main()
