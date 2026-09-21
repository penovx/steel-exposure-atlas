from __future__ import annotations

import hashlib
import unittest

from pipeline.profile_eu_sanctions_enterprises import profile_enterprises


CSV = """fileGenerationDate;Entity_LogicalId;Entity_SubjectType_ClassificationCode;NameAlias_WholeName;NameAlias_LogicalId;Entity_EU_ReferenceNumber;Entity_UnitedNationId;Entity_DesignationDate;Entity_Regulation_Programme;Address_CountryIso2Code;Address_CountryDescription;Identification_Number;Identification_TypeCode;Identification_TypeDescription
05/08/2026;10;enterprise;Acme Steel Ltd;100;EU.1;;01/01/2025;TEST;DE;Germany;HRB123;REG;Registration
05/08/2026;10;enterprise;ACME Steel;101;EU.1;;01/01/2025;TEST;DE;Germany;HRB123;REG;Registration
05/08/2026;10;enterprise;Acme Steel Ltd;100;EU.1;;01/01/2025;TEST;FR;France;HRB123;REG;Registration
05/08/2026;20;enterprise;Beta Metals;200;EU.2;UN2;02/02/2025;TEST;;;;;
05/08/2026;30;person;Jane Example;300;EU.3;UN3;03/03/2025;TEST;IT;Italy;P123;PASS;Passport
"""


class EuSanctionsEnterpriseProfileTests(unittest.TestCase):
    def test_profiles_unique_enterprises_not_flattened_rows(self) -> None:
        raw = CSV.encode("utf-8")
        profile = profile_enterprises(raw)

        self.assertEqual(profile["raw_sha256"], hashlib.sha256(raw).hexdigest().upper())
        self.assertEqual(
            profile["source_counts"],
            {
                "all_rows": 5,
                "enterprise_rows": 4,
                "person_rows_excluded": 1,
                "other_subject_rows_excluded": 0,
                "unique_enterprises": 2,
            },
        )
        self.assertEqual(profile["flattening"]["rows_per_enterprise"]["max"], 3)
        self.assertEqual(
            profile["flattening"]["distinct_names_per_enterprise"],
            {"min": 1, "median": 1.5, "p95": 2, "max": 2},
        )
        self.assertEqual(profile["flattening"]["enterprises_with_multiple_names"], 1)

    def test_person_rows_do_not_contribute_to_coverage(self) -> None:
        profile = profile_enterprises(CSV.encode("utf-8"))
        coverage = profile["entity_field_coverage"]

        self.assertEqual(coverage["Identification_Number"]["enterprises"], 1)
        self.assertEqual(coverage["Address_CountryIso2Code"]["enterprises"], 1)
        self.assertEqual(coverage["Entity_UnitedNationId"]["enterprises"], 1)

    def test_source_names_are_not_promoted_to_primary_name(self) -> None:
        profile = profile_enterprises(CSV.encode("utf-8"))
        self.assertIn(
            "does not infer which name is primary",
            profile["interpretation"]["names"],
        )
        serialized = repr(profile)
        self.assertNotIn("Acme Steel Ltd", serialized)
        self.assertNotIn("Jane Example", serialized)
        self.assertNotIn("P123", serialized)

    def test_missing_required_name_column_is_rejected(self) -> None:
        malformed = (
            "fileGenerationDate;Entity_LogicalId;Entity_SubjectType_ClassificationCode\n"
            "05/08/2026;10;enterprise\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "NameAlias_WholeName"):
            profile_enterprises(malformed)

    def test_enterprise_without_logical_id_is_rejected(self) -> None:
        malformed = (
            "fileGenerationDate;Entity_LogicalId;Entity_SubjectType_ClassificationCode;NameAlias_WholeName\n"
            "05/08/2026;;enterprise;Acme\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "no Entity_LogicalId"):
            profile_enterprises(malformed)


if __name__ == "__main__":
    unittest.main()
