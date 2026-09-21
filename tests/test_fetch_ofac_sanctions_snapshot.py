from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from pipeline.fetch_ofac_sanctions_snapshot import (
    CONSOLIDATED_URL,
    LICENCE,
    META_SCHEMA,
    PUBLISHER,
    SDN_URL,
    build_metadata,
    profile_xml,
    write_snapshot,
)


SDN_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<sdnList xmlns="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML">
  <publshInformation>
    <Publish_Date>09/16/2026</Publish_Date>
    <Record_Count>3</Record_Count>
  </publshInformation>
  <sdnEntry>
    <uid>100</uid>
    <lastName>Example Steel Holdings</lastName>
    <sdnType>Entity</sdnType>
    <programList><program>EXAMPLE</program></programList>
    <akaList>
      <aka><uid>1001</uid><category>strong</category><lastName>Example Steel</lastName></aka>
    </akaList>
    <addressList><address><uid>2001</uid><country>Exampleland</country></address></addressList>
    <idList><id><uid>3001</uid><idType>Registration ID</idType><idNumber>ABC123</idNumber></id></idList>
  </sdnEntry>
  <sdnEntry>
    <uid>101</uid>
    <firstName>Jane</firstName><lastName>Example</lastName>
    <sdnType>Individual</sdnType>
    <programList><program>EXAMPLE</program></programList>
  </sdnEntry>
  <sdnEntry>
    <uid>102</uid>
    <lastName>Example Vessel</lastName>
    <sdnType>Vessel</sdnType>
    <programList><program>MARITIME</program></programList>
  </sdnEntry>
</sdnList>
"""

CONSOLIDATED_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<sdnList xmlns="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML">
  <publshInformation>
    <Publish_Date>09/15/2026</Publish_Date>
    <Record_Count>2</Record_Count>
  </publshInformation>
  <sdnEntry>
    <uid>500</uid>
    <lastName>Example Non-SDN Metals</lastName>
    <sdnType>Entity</sdnType>
    <programList><program>SSI</program></programList>
    <akaList>
      <aka><uid>5001</uid><category>strong</category><lastName>ENSM</lastName></aka>
      <aka><uid>5002</uid><category>weak</category><lastName>Example Metals</lastName></aka>
    </akaList>
  </sdnEntry>
  <sdnEntry>
    <uid>501</uid>
    <lastName>Example Aircraft</lastName>
    <sdnType>Aircraft</sdnType>
    <programList><program>CAPTA</program></programList>
  </sdnEntry>
</sdnList>
"""


class OfacSanctionsSnapshotTests(unittest.TestCase):
    def test_profile_counts_entries_types_programs_and_context(self) -> None:
        profile = profile_xml(SDN_XML)

        self.assertEqual(profile["root_element"], "sdnList")
        self.assertEqual(
            profile["namespace"],
            "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML",
        )
        self.assertEqual(profile["publish_date"], "09/16/2026")
        self.assertEqual(profile["declared_record_count"], 3)
        self.assertEqual(profile["entry_count"], 3)
        self.assertEqual(profile["unique_uid_count"], 3)
        self.assertEqual(
            profile["sdn_type_counts"],
            {"Entity": 1, "Individual": 1, "Vessel": 1},
        )
        self.assertEqual(
            profile["program_occurrence_counts"],
            {"EXAMPLE": 2, "MARITIME": 1},
        )
        self.assertEqual(profile["alias_count"], 1)
        self.assertEqual(profile["address_count"], 1)
        self.assertEqual(profile["identifier_count"], 1)
        self.assertTrue(profile["declared_count_matches_entries"])

    def test_consolidated_profile_uses_same_basic_xml_contract(self) -> None:
        profile = profile_xml(CONSOLIDATED_XML)
        self.assertEqual(profile["entry_count"], 2)
        self.assertEqual(profile["sdn_type_counts"], {"Aircraft": 1, "Entity": 1})
        self.assertEqual(profile["alias_count"], 2)
        self.assertEqual(profile["publish_date"], "09/15/2026")

    def test_metadata_keeps_both_files_and_interpretation_boundary(self) -> None:
        metadata = build_metadata(
            SDN_XML,
            CONSOLIDATED_XML,
            retrieved_at="2026-09-16T16:00:00+00:00",
            sdn_transport={"final_url": SDN_URL, "content_type": "text/xml"},
            consolidated_transport={
                "final_url": CONSOLIDATED_URL,
                "content_type": "text/xml",
            },
        )

        self.assertEqual(metadata["schema"], META_SCHEMA)
        self.assertEqual(metadata["publisher"], PUBLISHER)
        self.assertEqual(metadata["licence"], LICENCE)
        self.assertIn("not sanctions clearance", metadata["interpretation_boundary"])

        files = metadata["files"]
        self.assertEqual(files["sdn"]["source_url"], SDN_URL)
        self.assertEqual(
            files["sdn"]["raw_sha256"],
            hashlib.sha256(SDN_XML).hexdigest().upper(),
        )
        self.assertEqual(
            files["consolidated_non_sdn"]["raw_sha256"],
            hashlib.sha256(CONSOLIDATED_XML).hexdigest().upper(),
        )
        self.assertIn("local-only", metadata["raw_publication_state"])
        self.assertIn("minimal derived", metadata["derived_publication_state"])

    def test_write_snapshot_keeps_raw_sources_and_review_metadata_local(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sdn_path = root / "raw" / "sdn.xml"
            consolidated_path = root / "raw" / "consolidated.xml"
            meta_path = root / "review" / "ofac.meta.json"

            metadata = write_snapshot(
                SDN_XML,
                CONSOLIDATED_XML,
                sdn_output=sdn_path,
                consolidated_output=consolidated_path,
                meta_output=meta_path,
                retrieved_at="2026-09-16T16:00:00+00:00",
            )

            self.assertEqual(sdn_path.read_bytes(), SDN_XML)
            self.assertEqual(consolidated_path.read_bytes(), CONSOLIDATED_XML)
            persisted = json.loads(meta_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["schema"], metadata["schema"])
            self.assertEqual(persisted["files"]["sdn"]["profile"]["entry_count"], 3)
            self.assertEqual(
                persisted["files"]["consolidated_non_sdn"]["profile"]["entry_count"],
                2,
            )

    def test_invalid_xml_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "not valid XML"):
            profile_xml(b"<sdnList>")

    def test_xml_without_sdn_entries_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "no sdnEntry"):
            profile_xml(b"<sdnList><publshInformation/></sdnList>")


if __name__ == "__main__":
    unittest.main()
