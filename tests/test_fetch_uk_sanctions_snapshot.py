from __future__ import annotations

import hashlib
import unittest

from pipeline.fetch_uk_sanctions_snapshot import (
    OGL_ATTRIBUTION,
    SCHEMA,
    SOURCE_URL,
    parse_entity_subset,
)


CSV = '''"Unique ID","Individual, Entity, Ship","Name 6","Name type","Regime Name","Address Country","Business registration number (s)","Parent Company","Subsidiaries","Last Updated","Date Designated","OFSI Group ID","UN Reference Number","Designation source","Sanctions Imposed","Type of entity","D.O.B","Passport number"
"UK001","Entity","Acme Holdings Ltd","Primary Name","Test regime","GB","BR123","Parent Plc","Sub A","01/09/2026","01/01/2025","G1","","UK","Asset freeze","Limited company","",""
"UK001","Entity","ACME Holdings","Alias","Test regime","GB","BR123","Parent Plc","Sub A","01/09/2026","01/01/2025","G1","","UK","Asset freeze","Limited company","",""
"UK001","Entity","Acme Holdings Limited","Primary Name Variation","Test regime","GB","BR123","Parent Plc","Sub A","01/09/2026","01/01/2025","G1","","UK","Asset freeze","Limited company","",""
"UK002","Individual","John Example","Primary Name","Test regime","GB","","","","01/09/2026","01/01/2025","G2","","UK","Asset freeze","","1970-01-01","P123"
"UK003","Ship","Vessel Example","Primary Name","Test regime","","","","","01/09/2026","01/01/2025","","","UK","Transport sanctions","","",""
'''


class UkSanctionsSnapshotTests(unittest.TestCase):
    def test_entity_only_subset_groups_repeated_name_rows(self) -> None:
        raw = CSV.encode("utf-8")
        payload = parse_entity_subset(raw, retrieved_at="2026-09-15T20:50:00+00:00")

        self.assertEqual(payload["meta"]["schema"], SCHEMA)
        self.assertEqual(payload["meta"]["source_url"], SOURCE_URL)
        self.assertEqual(payload["meta"]["attribution"], OGL_ATTRIBUTION)
        self.assertEqual(
            payload["meta"]["raw_sha256"], hashlib.sha256(raw).hexdigest().upper()
        )
        self.assertEqual(
            payload["counts"],
            {
                "source_rows": 5,
                "entity_rows": 3,
                "entity_records": 1,
                "skipped_individual_rows": 1,
                "skipped_ship_rows": 1,
            },
        )

        entity = payload["entities"][0]
        self.assertEqual(entity["entity_id"], "UK001")
        self.assertEqual(entity["primary_name"], "Acme Holdings Ltd")
        self.assertEqual(entity["aliases"], ["ACME Holdings"])
        self.assertEqual(entity["name_variations"], ["Acme Holdings Limited"])
        self.assertEqual(
            entity["identifiers"]["business_registration_number"], ["BR123"]
        )
        self.assertEqual(entity["parent_companies_source_text"], ["Parent Plc"])
        self.assertEqual(entity["subsidiaries_source_text"], ["Sub A"])

    def test_personal_fields_are_not_copied_to_output(self) -> None:
        payload = parse_entity_subset(CSV.encode("utf-8"))
        serialized = repr(payload)
        self.assertNotIn("John Example", serialized)
        self.assertNotIn("1970-01-01", serialized)
        self.assertNotIn("P123", serialized)
        self.assertNotIn("D.O.B", serialized)
        self.assertNotIn("Passport number", serialized)

    def test_required_headers_are_enforced(self) -> None:
        malformed = b'"Unique ID","Name 6","Name type"\n"UK001","Acme","Primary Name"\n'
        with self.assertRaisesRegex(ValueError, "Individual, Entity, Ship"):
            parse_entity_subset(malformed)

    def test_entity_without_unique_id_is_rejected(self) -> None:
        malformed = (
            '"Unique ID","Individual, Entity, Ship","Name 6","Name type"\n'
            '"","Entity","Acme","Primary Name"\n'
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "no Unique ID"):
            parse_entity_subset(malformed)

    def test_output_is_marked_prepublication(self) -> None:
        payload = parse_entity_subset(CSV.encode("utf-8"))
        self.assertEqual(
            payload["meta"]["publication_state"],
            "snapshot review required before public/data inclusion",
        )
        self.assertIn("entity-only", payload["meta"]["scope"])


if __name__ == "__main__":
    unittest.main()
