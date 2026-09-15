# GIST owner ↔ EU sanctions candidate screen — 2026-09-15

## Scope

This note records the first conservative cross-source candidate screen between:

- the 1,293 steel plants in the reviewed GIST June 2026 derived plant extract; and
- the 1,772 enterprise entities in the pinned EU Consolidated Financial Sanctions File 1.1 snapshot.

The screen is an identity-resolution diagnostic, not a sanctions finding.

EU snapshot provenance:

- retrieved at: `2026-09-15T21:53:03+00:00`
- source SHA-256: `049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015`
- file generation date reported by the source: `05/08/2026`
- enterprise population: 1,772 unique `Entity_LogicalId` values

## GIST identity population

The 1,293 plants contain **1,068 usable unique owner identities** when grouped by `owner_gem_entity_id` and excluding unusable owner labels.

Within this snapshot, none of those 1,068 GEM owner IDs is associated with more than one distinct GIST owner-name string.

This consistency is useful for source-internal grouping, but it does not turn a GEM entity ID into a legal-registry identifier.

## Candidate-screen result

The first batch pass intentionally used only:

1. conservative exact name equality after Unicode/case/punctuation/whitespace normalisation; and
2. legal-form-relaxed equality when no conservative exact candidate exists.

Fuzzy matching was not run.

Observed result:

| Result | GIST owner identities |
| --- | ---: |
| Exact-name review candidate | 0 |
| Ambiguous exact-name review candidate | 0 |
| Legal-form-only review candidate | 1 |
| No name candidate | 1,067 |
| **Any candidate** | **1** |

The single candidate is associated with one GIST plant.

Expressed only as candidate-screen coverage, not as a sanctions rate:

- 1 of 1,068 usable GIST owner identities produced a deterministic name candidate (about 0.09%);
- 1 of 1,293 GIST plants sits under an owner with such a candidate (about 0.08%).

These percentages describe the output of this matching method. They do **not** measure the prevalence of sanctions and must never be presented as a clearance rate.

## Interpretation

The result is useful precisely because it is sparse.

A simple cross-source text join between GIST owner labels and the EU sanctions list would create almost no deterministic overlap in this snapshot. That does not establish that the remaining companies are unaffected by sanctions. It shows that public-data integration quality depends heavily on entity identity resolution rather than on the mere availability of two datasets.

In particular:

- GIST provides a source-level owner/operator identity, not a reviewed legal-entity identity;
- GEM entity IDs are not comparable with EU registration, tax or other legal identifiers;
- plant country is not used as owner domicile or incorporation jurisdiction;
- exact name equality would still remain `review_required` for GIST in the current contract;
- legal-form-only equality is weaker and remains `review_required`;
- ownership/control and related-party sanctions effects remain outside this candidate screen;
- no candidate means only that this deterministic name screen found no candidate in the pinned snapshot.

## Next review step

Inspect the single legal-form candidate locally with its evidence pair and relevant EU entity context. Do not publish the candidate until the underlying company identity has been independently resolved.

The local review should compare, at minimum:

- GIST owner label and GEM entity ID;
- EU source names and EU reference number;
- EU entity address-country context, without treating it automatically as incorporation country;
- EU programme and designation-date context;
- available enterprise identifier types/values where useful for independent corroboration.

If the identity cannot be corroborated, the result stays `review_required`. If later legal-entity evidence is introduced (for example a reviewed LEI relationship or registry identifier), that evidence must retain its own provenance and matching rule.
