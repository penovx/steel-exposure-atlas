from __future__ import annotations

import unittest

from pipeline.build_ofac_entity_subset import build_subset
from pipeline.profile_gist_ofac_candidates import build_profile


SDN_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<sdnList xmlns="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML">
  <publshInformation><Publish_Date>09/16/2026</Publish_Date><Record_Count>2</Record_Count></publshInformation>
  <sdnEntry>
    <uid>100</uid><lastName>Example Steel Holdings</lastName><sdnType>Entity</sdnType>
    <programList><program>EXAMPLE</program></programList>
    <akaList><aka><uid>1001</uid><category>strong</category><lastName>Example Steel</lastName></aka></akaList>
    <addressList><address><uid>2001</uid><city>Example City</city><country>Exampleland</country></address></addressList>
    <idList><id><uid>3001</uid><idType>Registration ID</idType><idNumber>ABC123</idNumber></id></idList>
  </sdnEntry>
  <sdnEntry>
    <uid>101</uid><firstName>Jane</firstName><lastName>Example</lastName><sdnType>Individual</sdnType>
  </sdnEntry>
</sdnList>
"""

CONSOLIDATED_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<sdnList xmlns="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML">
  <publshInformation><Publish_Date>09/14/2026</Publish_Date><Record_Count>1</Record_Count></publshInformation>
  <sdnEntry>
    <uid>500</uid><lastName>Acme Metals LLC</lastName><sdnType>Entity</sdnType>
    <programList><program>SSI</program></programList>
    <akaList><aka><uid>5001</uid><category>weak</category><lastName>Acme Metals Group</lastName></aka></akaList>
  </sdnEntry>
</sdnList>
"""


def gist_payload() -> dict[str, object]:
    return {
        "meta": {"schema": "steel-exposure-atlas/gist-public-v1.0"},
        "plants": [
            {
                "plant_id": "P1",
                "owner_gem_entity_id": "E1",
                "owner_name": "Example Steel",
            },
            {
                "plant_id": "P2",
                "owner_gem_entity_id": "E2",
                "owner_name": "Acme Metals GmbH",
            },
            {
                "plant_id": "P3",
                "owner_gem_entity_id": "E3",
                "owner_name": "Unrelated Corp",
            },
        ],
    }


class OfacEntitySubsetAndCandidateTests(unittest.TestCase):
    def test_subset_keeps_entities_only_and_preserves_list_context(self) -> None:
        payload = build_subset(SDN_XML, CONSOLIDATED_XML)
        entities = payload["entities"]
        self.assertEqual(len(entities), 2)
        self.assertEqual(payload["meta"]["counts"]["sdn_entities"], 1)
        self.assertEqual(payload["meta"]["counts"]["consolidated_non_sdn_entities"], 1)

        sdn = next(item for item in entities if item["source_list"] == "SDN")
        self.assertEqual(sdn["entity_id"], "ofac-sdn:100")
        self.assertEqual(sdn["primary_name"], "Example Steel Holdings")
        self.assertIn("Example Steel", sdn["names"])
        self.assertEqual(sdn["programmes"], ["EXAMPLE"])
        self.assertEqual(sdn["countries"], ["Exampleland"])
        self.assertEqual(
            sdn["identifiers"],
            [{"type": "Registration ID", "value": "ABC123"}],
        )

    def test_candidate_profile_is_conservative_and_keeps_source_lists(self) -> None:
        ofac = build_subset(SDN_XML, CONSOLIDATED_XML)
        profile = build_profile(gist_payload(), ofac)
        counts = profile["counts"]

        self.assertEqual(counts["gist_plants"], 3)
        self.assertEqual(counts["usable_unique_owner_identities"], 3)
        self.assertEqual(counts["ofac_entities"], 2)
        self.assertEqual(counts["review_required_exact_name"], 1)
        self.assertEqual(counts["review_required_legal_form"], 1)
        self.assertEqual(counts["no_name_candidate"], 1)
        self.assertEqual(counts["owner_identities_with_any_candidate"], 2)
        self.assertEqual(counts["plants_under_candidate_owners"], 2)

        by_owner = {item["owner_gem_entity_id"]: item for item in profile["candidates"]}
        self.assertEqual(by_owner["E1"]["state"], "review_required_exact_name")
        self.assertEqual(by_owner["E1"]["candidate_source_lists"], ["SDN"])
        self.assertEqual(by_owner["E2"]["state"], "review_required_legal_form")
        self.assertEqual(
            by_owner["E2"]["candidate_source_lists"],
            ["Consolidated Non-SDN"],
        )
        self.assertEqual(by_owner["E3"]["state"], "no_name_candidate")
        self.assertIn("not sanctions clearance", profile["meta"]["interpretation"])
        self.assertIn("No fuzzy matching", profile["meta"]["interpretation"])

    def test_subset_uses_prefixed_ids_so_lists_cannot_collide(self) -> None:
        overlapping_consolidated = CONSOLIDATED_XML.replace(b"<uid>500</uid>", b"<uid>100</uid>", 1)
        payload = build_subset(SDN_XML, overlapping_consolidated)
        ids = {item["entity_id"] for item in payload["entities"]}
        self.assertEqual(ids, {"ofac-sdn:100", "ofac-consolidated-non-sdn:100"})


if __name__ == "__main__":
    unittest.main()
