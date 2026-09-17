from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HelpControlsContractTests(unittest.TestCase):
    def test_help_controls_are_static_and_aligned(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "src" / "connections-info-hints.js").read_text(encoding="utf-8")
        css = (ROOT / "src" / "connections-info-hints.css").read_text(encoding="utf-8")

        for key in ("company", "method", "product", "capacity"):
            self.assertIn(f'data-info-for="{key}"', index)
        self.assertIn('class="facet-title-actions"', index)
        self.assertIn('class="product-heading-title"', index)
        self.assertIn('class="product-heading-subtitle"', index)
        self.assertIn('aria-label="Help: Companies"', index)
        self.assertIn('aria-label="Help: Production methods"', index)
        self.assertIn('aria-label="Help: Products"', index)

        self.assertNotIn("createElement", script)
        self.assertNotIn("insertAdjacentElement", script)
        self.assertNotIn("HINTS=", script)
        self.assertIn("querySelectorAll('.info-hint')", script)

        self.assertIn(".rail-heading .info-hint-button", css)
        self.assertIn(".product-heading .info-hint-button", css)
        self.assertIn("min-width:14px", css)
        self.assertIn("padding:0", css)


if __name__ == "__main__":
    unittest.main()
