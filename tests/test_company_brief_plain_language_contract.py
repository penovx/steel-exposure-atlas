from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SelectionProfilePlainLanguageContractTests(unittest.TestCase):
    def test_profile_updates_from_first_selection_without_affordance_click(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8")

        self.assertIn('./src/connections-selection-profile.js?v=20260917-2', index)
        self.assertIn("new MutationObserver(reconcile).observe(path", script)
        self.assertIn("renderProfile(review", script)
        self.assertNotIn("View company brief", script)
        self.assertNotIn("Company brief open", script)

    def test_profile_names_relationships_instead_of_using_shorthand(self) -> None:
        script = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8")

        self.assertIn("Immediate owner or operator named by GEM", script)
        self.assertIn("GIST-listed products", script)
        self.assertIn("Known operating crude-steel capacity", script)
        self.assertIn("Known operating method capacity", script)
        self.assertNotIn("connected sites", script.lower())
        self.assertNotIn("1/4 sites", script)
        self.assertNotIn("procurement follow-up", script.lower())

    def test_regulatory_copy_stays_factual(self) -> None:
        script = (ROOT / "src" / "connections-selection-profile.js").read_text(encoding="utf-8")

        self.assertIn("EU sanctions list", script)
        self.assertIn("U.S. sanctions list", script)
        self.assertIn("EU tariff-quota framework in force", script)
        self.assertIn("50% out-of-quota duty after applicable quota exhaustion", script)
        self.assertNotIn("route it for", script.lower())
        self.assertNotIn("before contracting", script.lower())
        self.assertNotIn("no direct eu or u.s. listing found", script.lower())


if __name__ == "__main__":
    unittest.main()
