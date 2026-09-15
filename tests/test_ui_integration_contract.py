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

    def test_map_has_direct_navigation_controls(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        for element_id in ["zoom-in", "zoom-out", "zoom-reset", "zoom-level"]:
            self.assertIn(f'id="{element_id}"', index)

    def test_production_focus_has_region_and_country_controls(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="region-select"', index)
        self.assertIn('id="country-select"', index)
        self.assertIn('id="focus-stats"', index)

    def test_map_supports_wheel_pan_and_fit(self) -> None:
        app = (ROOT / "src" / "app.js").read_text(encoding="utf-8")
        self.assertIn("worldMap.addEventListener('wheel'", app)
        self.assertIn("worldMap.addEventListener('pointerdown'", app)
        self.assertIn("function fitPlants", app)
        self.assertIn("function setViewBox", app)

    def test_detail_actions_are_data_driven_and_parent_caveat_is_visible(self) -> None:
        app = (ROOT / "src" / "app.js").read_text(encoding="utf-8")
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("focusOwner", app)
        self.assertIn("focusParentLabel", app)
        self.assertIn("Matching parent text is a source-label match", index)

    def test_hover_tooltip_uses_country_and_plant_context(self) -> None:
        app = (ROOT / "src" / "app.js").read_text(encoding="utf-8")
        self.assertIn("showPlantTooltip", app)
        self.assertIn("showCountryTooltip", app)


if __name__ == "__main__":
    unittest.main()
