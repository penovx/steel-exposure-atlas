# Sanctions matching contract v1.0

## Purpose

This contract defines how the atlas may connect a company identity to an official sanctions-list **entity** record without turning name similarity into a legal conclusion.

The matching layer remains source-agnostic, but the current product scope is limited to the **EU consolidated financial sanctions list**.

## Core rule

A sanctions result is evidence about a reviewed source snapshot. It is not a compliance decision.

The UI and exported data must never use `sanctions clear`, `compliant`, `safe`, a red/green supplier verdict, or equivalent language.

Allowed top-level states:

- `direct_list_match` — direct deterministic evidence links a sufficiently resolved company identity to one sanctions entity record.
- `review_required` — there is relevant but insufficient or ambiguous evidence; human review is required.
- `no_direct_list_match_in_snapshot` — no direct deterministic match was found in the reviewed snapshot. This is not evidence that the company is unaffected by sanctions.

## Input: company identity

A company identity may contain:

- `company_id` — stable atlas identity.
- `name` — company name used by the atlas.
- `aliases` — optional reviewed alternate names.
- `country` — optional company-level country or jurisdiction context from a suitable entity source.
- `identifiers` — optional reviewed identifiers such as LEI or company-registration identifiers.

Plant names are not company identities and must not be matched as if they were legal entities. Plant country must not be substituted for company domicile or incorporation jurisdiction.

## Input: sanctions entity record

Only records whose source type is `entity` are eligible for this v1 contract.

Each source record may contain:

- `source` — source identifier, currently `eu_financial_sanctions`.
- `snapshot_id` — pinned source snapshot or release identifier.
- `entity_id` — stable source record identifier.
- `primary_name` — official listed name when the source explicitly establishes one.
- `aliases` — source-provided alternate or additional names.
- `countries` — optional source country context.
- `identifiers` — source-provided entity identifiers.

The current EU 1.1 adapter does **not** infer a primary company name from `NameAlias_WholeName`. All observed source names are preserved without inventing primary-name semantics.

Person records and personal identifiers are outside the first public sanctions layer.

## Match evidence

### Potential direct evidence

The strongest direct evidence is:

1. `identifier_exact`
   - the same reviewed identifier type and normalized value occurs on both sides;
   - identifier-type compatibility must be established explicitly;
   - a source value known to be shared or ambiguous must not be promoted automatically.

Exact source-name equality can be strong evidence when the company identity on the other side is itself a reviewed legal-entity identity. Conservative normalization may standardize Unicode form, case, punctuation and whitespace. It must not silently remove material legal-name tokens or translate names in a way that turns a fuzzy candidate into a fact.

### Review-only evidence

The following must remain `review_required` unless a separate reviewed identity-resolution step supplies stronger evidence:

- name equality where the company-side identity is only a source owner/operator label rather than a legal-registry identity;
- a match that becomes equal only after removing legal-form tokens such as `Ltd`, `Limited`, `GmbH`, `S.A.` or equivalents;
- high string similarity without exact normalized identity;
- conflicting country or identifier evidence;
- more than one sanctions entity record matching the same company identity;
- ownership/control implications inferred from a listed parent or related company without a separately reviewed ownership/control rule.

A similarity score may be stored as diagnostic evidence, but it is never a sanctions finding by itself.

## GIST owner identity boundary

For the first GIST → EU sanctions pass, `owner_name` and `owner_gem_entity_id` are treated as **source identities**, not as legal-registry identities.

Therefore:

- exact conservative equality between a GIST owner name and an EU sanctions source name is `review_required`, not `direct_list_match`;
- legal-form-relaxed equality is `review_required`;
- fuzzy matching is not part of the first batch pass;
- the country of a steel plant is not used as the domicile or incorporation country of its owner;
- GEM entity IDs must never be compared directly with EU registration, tax or other legal identifiers;
- a public `direct_list_match` requires additional reviewed legal-entity evidence or explicit human resolution.

This stricter source-specific rule prevents a shared or coincidentally equal company name from becoming a sanctions finding merely because two public datasets use the same text.

## Output record

Each company receives one result for the pinned EU sanctions source snapshot:

```json
{
  "company_id": "...",
  "source": "eu_financial_sanctions",
  "snapshot_id": "...",
  "state": "direct_list_match | review_required | no_direct_list_match_in_snapshot",
  "matched_entity_ids": ["..."],
  "evidence": [
    {
      "type": "identifier_exact | primary_name_exact | alias_exact | legal_form_candidate | similar_name_candidate | ambiguous_direct_match",
      "company_value": "...",
      "source_value": "...",
      "similarity": null
    }
  ]
}
```

`matched_entity_ids` may be empty. More than one direct candidate must not be collapsed automatically.

## Negative-result boundary

`no_direct_list_match_in_snapshot` means only:

> no direct deterministic match was found against the entity records present in this pinned EU source snapshot.

It does **not** establish that:

- the company is sanctions-clear;
- the company is compliant;
- no owner, controller, parent, subsidiary or related party is sanctioned;
- the company is unaffected by ownership/control or other sanctions restrictions;
- another jurisdiction has no relevant designation.

## Source and publication requirements

Every published sanctions result must retain:

- jurisdiction;
- source publisher and dataset name;
- pinned snapshot/retrieval date;
- source file hash;
- publication/redistribution decision from source governance;
- required attribution;
- matcher version.

The current approved publication path is a **derived entity-only subset** from the EU Consolidated Financial Sanctions File 1.1 under the conditions documented in `docs/source-reviews/2026-09-15-procurement-source-gate.md`.

The raw source file is not automatically a public-site asset. Publication should use the minimum transformed fields required by the atlas.

## Human review

The atlas may expose a `review_required` state and the evidence that caused it. It must not automatically promote that state to `direct_list_match`.

Any future ownership/control logic must be a separate evidence layer with its own rules and provenance.
