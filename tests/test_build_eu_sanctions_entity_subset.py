from __future__ import annotations

import hashlib
import unittest

from pipeline.build_eu_sanctions_entity_subset import build_subset


CSV = """fileGenerationDate;Entity_LogicalId;Entity_SubjectType_ClassificationCode;NameAlias_WholeName;Entity_EU_ReferenceNumber;Entity_UnitedNationId;Entity_DesignationDate;Entity_Regulation_Programme;Address_CountryIso2Code;Address_CountryDescription;Identification_Number;Identification_TypeCode;Identification_TypeDescription
05/08/2026;10;enterprise;Acme Steel Ltd;EU.1;;01/01/2025;TEST;DE;Germany;HRB123;regnumber;Registration Number
05/08/2026;10;enterprise;ACME Steel;EU.1;;01/01/2025;TEST;DE;Germany;HRB123;regnumber;Registration Number
05/08/2026;20;enterprise;Beta Metals;EU.2;UN2;02/02/2025;TEST;FR;France;FR-22;taxid;Tax identification number
05/08/2026;30;person;Jane Example;EU.3;UN3;03/03/2025;TEST;IT;Italy;P123;id;National identification card
"""


class EuSanctionsEntitySubsetTests(unittest.TestCase):
    def test_groups_flattened_enterprise_rows(self) -> None:
        raw = CSV.encode("utf-8")
        payload = build_subset(raw)

        self.assertEqual(payload["meta"]["raw_sha256"], hashlib.sha256(raw).hexdigest().upper())
        self.assertEqual(payload["meta"]["counts"]["enterprise_rows"], 3)
        self.assertEqual(payload["meta"]["counts"]["person_rows_excluded"], 1)
        self.assertEqual(payload["meta"]["counts"]["unique_enterprises"], 2)
        self.assertEqual(len(payload["entities"]), 2)

        acme = next(item for item in payload["entities"] if item["entity_id"] == "10")
        self.assertEqual(acme["names"], ["ACME Steel", "Acme Steel Ltd"])
        self.assertEqual(acme["eu_reference_numbers"], ["EU.1"])
        self.assertEqual(
            acme["identifiers"],
            [
                {
                    "type_code": "regnumber",
                    "type_description": "Registration Number",
                    "value": "HRB123",
                }
            ],
        )

    def test_person_content_is_excluded(self) -> None:
        payload = build_subset(CSV.encode("utf-8"))
        serialized = repr(payload)
        self.assertNotIn("Jane Example", serialized)
        self.assertNotIn("P123", serialized)

    def test_no_primary_name_is_inferred(self) -> None:
        payload = build_subset(CSV.encode("utf-8"))
        serialized = repr(payload)
        self.assertNotIn("primary_name", serialized)
        self.assertIn("No primary name is inferred", payload["meta"]["name_semantics"])

    def test_enterprise_without_name_fails(self) -> None:
        malformed = """fileGenerationDate;Entity_LogicalId;Entity_SubjectType_ClassificationCode;NameAlias_WholeName;Entity_EU_ReferenceNumber
05/08/2026;10;enterprise;;EU.1
""".encode("utf-8")
        with self.assertRaisesRegex(ValueError, "has no NameAlias_WholeName"):
            build_subset(malformed)


if __name__ == "__main__":
    unittest.main()
