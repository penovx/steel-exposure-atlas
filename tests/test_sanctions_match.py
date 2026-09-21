from __future__ import annotations

import unittest

from pipeline.sanctions_match import (
    DIRECT_LIST_MATCH,
    NO_DIRECT_LIST_MATCH,
    REVIEW_REQUIRED,
    CompanyIdentity,
    SanctionsEntity,
    match_company_to_entities,
    normalize_name,
)


SOURCE = "eu_financial_sanctions"
SNAPSHOT = "synthetic-2026-09-15"


def entity(
    entity_id: str,
    name: str,
    *,
    aliases: tuple[str, ...] = (),
    identifiers: dict[str, str] | None = None,
    entity_type: str = "entity",
) -> SanctionsEntity:
    return SanctionsEntity(
        source=SOURCE,
        snapshot_id=SNAPSHOT,
        entity_id=entity_id,
        primary_name=name,
        aliases=aliases,
        identifiers=identifiers or {},
        entity_type=entity_type,
    )


class SanctionsMatchTests(unittest.TestCase):
    def test_conservative_normalization_handles_case_punctuation_and_space(self) -> None:
        self.assertEqual(normalize_name("  North-Star, Metals GmbH "), "north star metals gmbh")

    def test_exact_primary_name_is_direct_list_match(self) -> None:
        company = CompanyIdentity("c1", "North Star Metals GmbH")
        result = match_company_to_entities(company, [entity("s1", "NORTH STAR METALS GMBH")], source=SOURCE, snapshot_id=SNAPSHOT)
        self.assertEqual(result.state, DIRECT_LIST_MATCH)
        self.assertEqual(result.matched_entity_ids, ("s1",))
        self.assertIn("primary_name_exact", {item.type for item in result.evidence})

    def test_exact_source_alias_is_direct_list_match(self) -> None:
        company = CompanyIdentity("c1", "North Star Trading")
        result = match_company_to_entities(
            company,
            [entity("s1", "North Star Metals GmbH", aliases=("North Star Trading",))],
            source=SOURCE,
            snapshot_id=SNAPSHOT,
        )
        self.assertEqual(result.state, DIRECT_LIST_MATCH)
        self.assertIn("alias_exact", {item.type for item in result.evidence})

    def test_exact_identifier_is_direct_even_when_names_differ(self) -> None:
        company = CompanyIdentity("c1", "Atlas Steel Holdings", identifiers={"lei": "ABC 123-XY"})
        result = match_company_to_entities(
            company,
            [entity("s1", "Different Published Name", identifiers={"lei": "ABC123XY"})],
            source=SOURCE,
            snapshot_id=SNAPSHOT,
        )
        self.assertEqual(result.state, DIRECT_LIST_MATCH)
        self.assertIn("identifier_exact", {item.type for item in result.evidence})

    def test_legal_form_equivalence_is_review_only(self) -> None:
        company = CompanyIdentity("c1", "North Star Metals Limited")
        result = match_company_to_entities(
            company,
            [entity("s1", "North Star Metals Ltd")],
            source=SOURCE,
            snapshot_id=SNAPSHOT,
        )
        self.assertEqual(result.state, REVIEW_REQUIRED)
        self.assertIn("legal_form_candidate", {item.type for item in result.evidence})

    def test_high_similarity_is_review_only(self) -> None:
        company = CompanyIdentity("c1", "North Star Metal Holdings")
        result = match_company_to_entities(
            company,
            [entity("s1", "North Star Metals Holdings")],
            source=SOURCE,
            snapshot_id=SNAPSHOT,
            similarity_threshold=0.90,
        )
        self.assertEqual(result.state, REVIEW_REQUIRED)
        self.assertIn("similar_name_candidate", {item.type for item in result.evidence})

    def test_multiple_direct_matches_are_not_collapsed(self) -> None:
        company = CompanyIdentity("c1", "North Star Metals")
        result = match_company_to_entities(
            company,
            [entity("s1", "North Star Metals"), entity("s2", "North Star Metals")],
            source=SOURCE,
            snapshot_id=SNAPSHOT,
        )
        self.assertEqual(result.state, REVIEW_REQUIRED)
        self.assertEqual(result.matched_entity_ids, ("s1", "s2"))
        self.assertIn("ambiguous_direct_match", {item.type for item in result.evidence})

    def test_person_records_are_excluded_from_entity_only_layer(self) -> None:
        company = CompanyIdentity("c1", "Alex Example")
        result = match_company_to_entities(
            company,
            [entity("p1", "Alex Example", entity_type="person")],
            source=SOURCE,
            snapshot_id=SNAPSHOT,
        )
        self.assertEqual(result.state, NO_DIRECT_LIST_MATCH)
        self.assertEqual(result.matched_entity_ids, ())

    def test_no_direct_match_is_snapshot_scoped_not_clearance(self) -> None:
        company = CompanyIdentity("c1", "Unrelated Steel Co")
        result = match_company_to_entities(company, [entity("s1", "North Star Metals")], source=SOURCE, snapshot_id=SNAPSHOT)
        self.assertEqual(result.state, NO_DIRECT_LIST_MATCH)
        serialized = str(result.to_dict()).lower()
        self.assertNotIn("sanctions clear", serialized)
        self.assertNotIn("compliant", serialized)
        self.assertNotIn("safe", serialized)

    def test_wrong_source_or_snapshot_cannot_match(self) -> None:
        company = CompanyIdentity("c1", "North Star Metals")
        other_source = SanctionsEntity("other", SNAPSHOT, "s1", "North Star Metals")
        other_snapshot = SanctionsEntity(SOURCE, "different", "s2", "North Star Metals")
        result = match_company_to_entities(
            company,
            [other_source, other_snapshot],
            source=SOURCE,
            snapshot_id=SNAPSHOT,
        )
        self.assertEqual(result.state, NO_DIRECT_LIST_MATCH)


if __name__ == "__main__":
    unittest.main()
