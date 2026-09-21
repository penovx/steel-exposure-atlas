from __future__ import annotations

import hashlib
import unittest

from pipeline.profile_eu_sanctions_matchability import profile_matchability


CSV = """Entity_LogicalId;Entity_SubjectType_ClassificationCode;NameAlias_WholeName;NameAlias_LogicalId;NameAlias_Strong;NameAlias_NameLanguage;Identification_Number;Identification_TypeCode;Identification_TypeDescription
10;enterprise;Acme Steel Ltd;100;true;EN;HRB123;REG;Registration
10;enterprise;ACME Steel;101;true;EN;HRB123;REG;Registration
20;enterprise;Acme Steel;200;false;EN;HRB999;REG;Registration
30;enterprise;Beta Metals GmbH;300;true;DE;LEI-1;LEI;Legal Entity Identifier
40;enterprise;Beta Metals Limited;400;true;EN;LEI-2;LEI;Legal Entity Identifier
50;person;Jane Example;500;true;EN;P123;PASS;Passport
"""


class EuSanctionsMatchabilityProfileTests(unittest.TestCase):
    def test_profiles_only_enterprises_and_keeps_output_aggregate(self) -> None:
        raw = CSV.encode("utf-8")
        profile = profile_matchability(raw)

        self.assertEqual(profile["raw_sha256"], hashlib.sha256(raw).hexdigest().upper())
        self.assertEqual(
            profile["population"],
            {"enterprise_rows": 5, "unique_enterprises": 4},
        )
        serialized = repr(profile)
        self.assertNotIn("Acme Steel", serialized)
        self.assertNotIn("HRB123", serialized)
        self.assertNotIn("Jane Example", serialized)
        self.assertNotIn("P123", serialized)

    def test_exact_normalized_name_collisions_are_measured(self) -> None:
        profile = profile_matchability(CSV.encode("utf-8"))
        names = profile["name_matchability"]["conservative_normalized_names"]
        self.assertEqual(names["keys_shared_across_enterprises"], 1)
        self.assertEqual(names["max_enterprises_per_key"], 2)

    def test_legal_form_relaxation_can_create_additional_collisions(self) -> None:
        profile = profile_matchability(CSV.encode("utf-8"))
        conservative = profile["name_matchability"]["conservative_normalized_names"]
        relaxed = profile["name_matchability"]["legal_form_relaxed_names"]
        self.assertGreaterEqual(
            relaxed["keys_shared_across_enterprises"],
            conservative["keys_shared_across_enterprises"],
        )

    def test_identifier_types_are_kept_separate_and_collision_checked(self) -> None:
        profile = profile_matchability(CSV.encode("utf-8"))
        types = {
            item["type_code"]: item
            for item in profile["identification_matchability"]["types"]
        }
        self.assertEqual(types["REG"]["enterprises"], 2)
        self.assertEqual(types["REG"]["distinct_normalized_values"], 2)
        self.assertEqual(types["REG"]["values_shared_across_enterprises"], 0)
        self.assertEqual(types["LEI"]["enterprises"], 2)

    def test_name_metadata_columns_are_discovered_without_row_values(self) -> None:
        profile = profile_matchability(CSV.encode("utf-8"))
        schema = profile["source_schema"]
        self.assertIn("NameAlias_Strong", schema["name_alias_columns"])
        self.assertIn("NameAlias_NameLanguage", schema["name_alias_columns"])
        self.assertEqual(
            schema["name_metadata_value_counts"]["NameAlias_Strong"],
            {"false": 1, "true": 4},
        )
        self.assertEqual(
            schema["name_metadata_value_counts"]["NameAlias_NameLanguage"],
            {"DE": 1, "EN": 4},
        )

    def test_missing_required_column_fails_loudly(self) -> None:
        malformed = (
            "Entity_LogicalId;Entity_SubjectType_ClassificationCode\n"
            "10;enterprise\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "NameAlias_WholeName"):
            profile_matchability(malformed)


if __name__ == "__main__":
    unittest.main()
