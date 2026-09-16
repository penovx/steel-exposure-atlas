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

        self.assertIn('./src/connections-hero.css?v=20260916-3', index)
        self.assertIn('Steel Exposure <b>Atlas</b>', index)
        self.assertIn('STEEL PRODUCTION, IN CONTEXT', index)
        self.assertIn(
            'Trace steel companies across their plants, products and production methods, with sanctions and trade measures brought into the same view through public evidence.',
            index,
        )
        self.assertNotIn('Explore the connections.', index)
        self.assertNotIn('Know who makes what, where.', index)
        self.assertNotIn('Steel production, ownership and sourcing exposure', index)
        self.assertIn('.masthead{position:absolute!important', css)
        self.assertIn('.intro{position:absolute!important', css)
        self.assertIn('.atlas{min-height:100svh;padding-top:98px', css)
        self.assertIn('.connections-stage{height:calc(100svh-180px)!important', css)


if __name__ == "__main__":
    unittest.main()
