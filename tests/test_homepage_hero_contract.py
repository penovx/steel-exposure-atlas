from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HomepageHeroContractTests(unittest.TestCase):
    def test_atlas_is_the_opening_hero(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        css = "".join(
            (ROOT / "src" / "connections-hero.css").read_text(encoding="utf-8").split()
        )

        self.assertIn('./src/connections-hero.css?v=20260916-1', index)
        self.assertIn('STEEL PRODUCTION, IN CONTEXT', index)
        self.assertIn('Explore the connections.', index)
        self.assertIn(
            'See who operates which steel plants, what they produce, how they make steel, and where sanctions or EU import measures can affect sourcing.',
            index,
        )
        self.assertNotIn('overlap across the same industrial footprint', index)
        self.assertIn('.masthead{position:absolute!important', css)
        self.assertIn('.intro{position:absolute!important', css)
        self.assertIn('.atlas{min-height:100svh;padding-top:170px', css)


if __name__ == "__main__":
    unittest.main()
