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

        self.assertIn('./src/connections-hero.css?v=20260916-7', index)
        self.assertIn('class="brand-name">Steel Exposure <b>Atlas</b>', index)
        self.assertNotIn('brand-kicker', index)
        self.assertNotIn('STEEL PRODUCTION, IN CONTEXT', index)
        self.assertIn(
            'Trace steel companies across their plants, products and production methods,<br class="hero-break">with sanctions and trade measures brought into the same view through public evidence.',
            index,
        )
        self.assertIn('class="scope-action">· Select area</span>', index)
        self.assertNotIn('class="small-cross"', index)
        self.assertNotIn('Explore the connections.', index)
        self.assertNotIn('Know who makes what, where.', index)
        self.assertNotIn('Steel production, ownership and sourcing exposure', index)
        self.assertIn('.masthead{position:fixed!important', css)
        self.assertIn('background:var(--night)!important', css)
        self.assertIn('.brand-copy{display:flex;align-items:center', css)
        self.assertNotIn('.brand-kicker{', css)
        self.assertIn('.hero-break{display:block}', css)
        self.assertIn('#scope-meta{display:none!important}', css)
        self.assertIn('.atlas{min-height:100svh;padding-top:148px', css)
        self.assertIn('.connections-stage{height:calc(100svh-220px)!important', css)


if __name__ == "__main__":
    unittest.main()
