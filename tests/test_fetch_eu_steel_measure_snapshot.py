from __future__ import annotations

import unittest

from pipeline.fetch_eu_steel_measure_snapshot import build_payload, parse_annex_i


PRODUCT_NUMBERS = [
    "1.A", "1.B", "2", "3.A", "3.B", "4.A", "4.B", "5", "6", "7",
    "8", "9", "10", "12", "13", "14", "15", "16", "17", "18",
    "19", "20", "21", "22", "24", "25.A", "25.B", "26", "27", "28",
]


def html_fixture() -> str:
    rows = []
    for index, product_number in enumerate(PRODUCT_NUMBERS):
        category = "Rebars" if product_number == "13" else f"Category {product_number}"
        codes = (
            "7214 20 00, 7214 99 10 TARIC code: 7228 30 69 11"
            if product_number == "13"
            else f"72{index:02d} 10 00"
        )
        rows.append(
            "<tr>"
            f"<td>{product_number}</td><td>{category}</td><td>{codes}</td>"
            "<td>Türkiye</td><td>1 000,50</td><td>500,25</td><td>500,25</td>"
            "<td>250,13</td><td>250,13</td><td>250,13</td><td>250,13</td>"
            "<td>50 %</td><td>09.9801</td>"
            "</tr>"
        )
        if product_number == "13":
            rows.append(
                "<tr><td>Other countries</td><td>100,00</td><td>100,00</td><td>0,00</td>"
                "<td>25,00</td><td>25,00</td><td>25,00</td><td>25,00</td>"
                "<td>50 %</td><td>09.9600</td></tr>"
            )

    return (
        "<html><body><table><tr><td>irrelevant</td></tr></table>"
        "<table>"
        "<tr><th>Product Number</th><th>Product category</th><th>CN Codes</th>"
        "<th>Allocation by country (Where Applicable)</th><th>Total yearly volume in tonnes</th>"
        "<th>MFN Part in tonnes</th><th>FTA Part in tonnes</th>"
        "<th>From 1.7. to 30.9.</th><th>From 1.10. to 31.12.</th>"
        "<th>From 1.1. to 31.3.</th><th>From 1.4. to 30.6.</th>"
        "<th>Additional duty rate</th><th>Order numbers</th></tr>"
        + "".join(rows)
        + "</table></body></html>"
    )


class EuSteelMeasureSnapshotTests(unittest.TestCase):
    def test_parses_product_numbers_codes_and_continuation_rows(self) -> None:
        payload = parse_annex_i(html_fixture())
        self.assertEqual(len(payload["products"]), 30)
        self.assertEqual(len(payload["allocations"]), 31)

        rebar = next(item for item in payload["products"] if item["product_number"] == "13")
        self.assertEqual(rebar["product_category"], "Rebars")
        self.assertEqual(rebar["cn_codes"], ["72142000", "72149910"])
        self.assertEqual(rebar["taric_codes"], ["7228306911"])

        rows = [item for item in payload["allocations"] if item["product_number"] == "13"]
        self.assertEqual([item["allocation"] for item in rows], ["Türkiye", "Other countries"])
        self.assertEqual(rows[0]["additional_duty_rate_pct"], 50.0)
        self.assertAlmostEqual(rows[0]["total_yearly_volume_tonnes"], 1000.5)

    def test_build_payload_fingerprints_raw_source_and_keeps_boundary(self) -> None:
        raw = html_fixture().encode("utf-8")
        payload = build_payload(raw, retrieved_at="2026-09-16T17:00:00+00:00")
        self.assertEqual(payload["meta"]["legal_product_categories"], 26)
        self.assertEqual(payload["meta"]["annex_product_numbers"], 30)
        self.assertEqual(payload["meta"]["additional_duty_rate_pct"], 50.0)
        self.assertEqual(payload["meta"]["valid_from"], "2026-07-01")
        self.assertEqual(payload["meta"]["valid_to"], "2026-12-31")
        self.assertEqual(len(payload["meta"]["raw_sha256"]), 64)
        self.assertIn("does not establish that a GIST plant exports", payload["meta"]["interpretation"])

    def test_rejects_incomplete_annex(self) -> None:
        broken = html_fixture().replace("<td>28</td>", "<td>not-28</td>")
        with self.assertRaisesRegex(ValueError, "Expected 30 Annex-I product numbers"):
            parse_annex_i(broken)


if __name__ == "__main__":
    unittest.main()
