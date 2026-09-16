from __future__ import annotations

import unittest

from pipeline.fetch_eu_steel_bilateral_safeguard_snapshot import (
    EXPECTED_COUNTRIES,
    build_payload,
    parse_article_1,
)


HTML = """
<html><body>
<h2>Article 1</h2>
<p>1. Imports into the Union of the product categories listed in Annex I and originating in
Albania, Israel, Jordan, Morocco, North Macedonia, Serbia, Switzerland, Tunisia and Türkiye
shall be subject, by way of bilateral safeguard measures, to an out-of-quota duty at the rate
of 50 % ad valorem.</p>
<p>2. The out-of-quota duty laid down in paragraph 1 shall apply once the tariff quota opened
under Regulation (EU) 2026/1384 distributed to each country concerned has been exhausted.</p>
<h2>Article 2</h2>
<p>Origin rules.</p>
</body></html>
"""


class EuSteelBilateralSafeguardTests(unittest.TestCase):
    def test_parses_country_scope_rate_and_trigger(self) -> None:
        payload = parse_article_1(HTML)
        self.assertEqual(payload["countries"], EXPECTED_COUNTRIES)
        self.assertEqual(payload["additional_duty_rate_pct"], 50.0)
        self.assertEqual(payload["trigger"], "applicable tariff quota exhausted")

    def test_payload_preserves_snapshot_provenance(self) -> None:
        payload = build_payload(HTML.encode("utf-8"), retrieved_at="2026-09-16T17:30:00+00:00")
        self.assertEqual(
            payload["meta"]["schema"],
            "steel-exposure-atlas/eu-steel-bilateral-2026-1930-v1.0",
        )
        self.assertEqual(payload["meta"]["valid_from"], "2026-08-06")
        self.assertEqual(payload["meta"]["legal_route"], "bilateral safeguard measure")
        self.assertEqual(len(payload["countries"]), 9)
        self.assertEqual(len(payload["meta"]["raw_sha256"]), 64)

    def test_missing_country_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "country set"):
            parse_article_1(HTML.replace("Switzerland, ", ""))

    def test_missing_duty_rate_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "50%"):
            parse_article_1(HTML.replace("50 % ad valorem", "40 % ad valorem"))


if __name__ == "__main__":
    unittest.main()
