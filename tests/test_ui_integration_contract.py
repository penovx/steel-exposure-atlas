from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UiIntegrationContractTests(unittest.TestCase):
    def test_header_no_longer_shows_demonstrator_eyebrow(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("OPEN-DATA DEMONSTRATOR", index)

    def test_svg_plant_layer_visibility_is_attribute_driven(self) -> None:
        app = (ROOT / "src" / "app.js").read_text(encoding="utf-8")
        self.assertIn("plantLayer.removeAttribute('hidden')", app)
        self.assertIn("plantLayer.setAttribute('hidden', '')", app)
        self.assertNotIn("plantLayer.hidden =", app)

    def test_desktop_shell_is_bound_to_viewport(self) -> None:
        css = (ROOT / "src" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("height: 100dvh", css)
        self.assertIn("body { overflow: hidden; }", css)


if __name__ == "__main__":
    unittest.main()
