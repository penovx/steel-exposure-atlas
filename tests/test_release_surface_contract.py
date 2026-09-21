from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseSurfaceContractTests(unittest.TestCase):
    def test_homepage_has_pre_release_share_metadata(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn('<meta name="robots" content="noindex,nofollow">', index)
        self.assertIn('<meta property="og:title" content="Steel Exposure Atlas">', index)
        self.assertIn('<meta property="og:type" content="website">', index)
        self.assertIn('<meta property="og:site_name" content="Steel Exposure Atlas">', index)
        self.assertIn('<meta name="twitter:card" content="summary">', index)
        self.assertIn('<meta name="twitter:title" content="Steel Exposure Atlas">', index)
        self.assertNotIn('property="og:url"', index)
        self.assertNotIn('property="og:image"', index)
        self.assertNotIn('rel="canonical"', index)

    def test_public_privacy_notice_is_linked_and_minimal(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        privacy = (ROOT / "privacy.html").read_text(encoding="utf-8")

        self.assertIn('href="./privacy.html">Privacy', index)
        self.assertIn("No user accounts, sign-in or profiles.", privacy)
        self.assertIn("No behavioural analytics or advertising pixels.", privacy)
        self.assertIn("No runtime AI service processing visitor prompts or identifiers.", privacy)
        self.assertIn("does not set tracking cookies or use browser storage for visitor profiling", privacy)
        self.assertIn("GitHub Pages", privacy)
        self.assertIn(
            "https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages",
            privacy,
        )
        self.assertIn(
            "https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement",
            privacy,
        )
        self.assertIn("connect-src 'none'", privacy)

    def test_homepage_runtime_policy_remains_same_origin(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn("connect-src 'self'", index)
        self.assertIn("font-src 'none'", index)
        self.assertIn("object-src 'none'", index)


if __name__ == "__main__":
    unittest.main()
