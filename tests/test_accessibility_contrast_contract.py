from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rgb(value: str) -> tuple[float, float, float]:
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) / 255 for index in (0, 2, 4))


def luminance(value: str) -> float:
    channels = []
    for channel in rgb(value):
        channels.append(
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
        )
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(foreground: str, background: str) -> float:
    high, low = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def selector_color(css: str, selector: str) -> str:
    match = re.search(
        re.escape(selector) + r"\{[^}]*?color:(#[0-9a-fA-F]{6})",
        css,
    )
    if not match:
        raise AssertionError(f"Could not find explicit color for {selector}")
    return match.group(1)


class AccessibilityContrastContractTests(unittest.TestCase):
    def test_small_text_on_paper_meets_wcag_aa_contrast(self) -> None:
        css = (ROOT / "src" / "connections.css").read_text(encoding="utf-8")
        paper = "#f2f0e9"
        selectors = (
            ".edition",
            ".eyebrow",
            ".opening-hint",
            ".path-token small",
            ".path-base",
            ".reading-copy>p:not(.eyebrow)",
            ".summary-note",
            ".detail-rows>div>span:first-child",
            ".production-column",
            ".footer",
            "dialog>p,#browse-note",
            ".browse-item small",
            ".product-picker-tools>div:first-child",
            ".dialog-foot",
            ".source-section p",
            ".empty",
        )

        for selector in selectors:
            color = selector_color(css, selector)
            self.assertGreaterEqual(
                contrast(color, paper),
                4.5,
                f"{selector} uses {color} at {contrast(color, paper):.2f}:1",
            )

    def test_small_text_on_night_meets_wcag_aa_contrast(self) -> None:
        css = (ROOT / "src" / "connections.css").read_text(encoding="utf-8")
        night = "#0c1821"
        selectors = (
            ".rail-subtitle",
            ".company-sub",
            ".method-sub",
            ".method-note",
            ".map-key",
            ".product-heading>span",
            ".product-node",
            ".atlas-bottom",
        )

        for selector in selectors:
            color = selector_color(css, selector)
            self.assertGreaterEqual(
                contrast(color, night),
                4.5,
                f"{selector} uses {color} at {contrast(color, night):.2f}:1",
            )

    def test_privacy_muted_palette_meets_wcag_aa_contrast(self) -> None:
        css = (ROOT / "src" / "privacy.css").read_text(encoding="utf-8")
        muted = re.search(r"--muted:(#[0-9a-fA-F]{6})", css)
        paper = re.search(r"--paper:(#[0-9a-fA-F]{6})", css)
        self.assertIsNotNone(muted)
        self.assertIsNotNone(paper)
        self.assertGreaterEqual(contrast(muted.group(1), paper.group(1)), 4.5)
        self.assertIn(".note{font-size:12px;color:var(--muted)}", css)


if __name__ == "__main__":
    unittest.main()
