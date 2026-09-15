# Sanctions matching contract v1.0

## Purpose

This contract defines how the atlas may connect a company identity to an official sanctions-list **entity** record without turning name similarity into a legal conclusion.

The first implementation is source-agnostic. It can support the UK Sanctions List first and later additional reviewed sources, but a source may be used publicly only when its own publication gate is open.

## Core rule

A sanctions result is evidence about a reviewed source snapshot. It is not a compliance decision.

The UI and exported data must never use `sanctions clear`, `compliant`, `safe`, a red/green supplier verdict, or equivalent language.

Allowed top-level states:

- `direct_list_match` — direct deterministic evidence links the company identity to one sanctions entity record.
- `review_required` — there is relevant but insufficient or ambiguous evidence; human review is required.
- `no_direct_list_match_in_snapshot` — no direct deterministic match was found in the reviewed snapshot. This is not evidence that the company is unaffected by sanctions.

## Input: company identity

A company identity may contain:

- `company_id` — stable atlas identity.
- `name` — company name used by the atlas.
- `aliases` — optional reviewed alternate names.
- `country` — optional country context.
- `identifiers` — optional reviewed identifiers such as LEI or company-registration identifiers.

Plant names are not company identities and must not be matched as if they were legal entities.

## Input: sanctions entity record

Only records whose source type is `entity` are eligible for this v1 contract.

Each source record may contain:

- `source` — source identifier, for example `uk_sanctions_list`.
- `snapshot_id` — pinned source snapshot or release identifier.
- `entity_id` — stable source record identifier.
- `primary_name` — official listed name.
- `aliases` — source-provided alternate names.
- `countries` — optional source country context.
- `identifiers` — source-provided entity identifiers.

Person records and personal identifiers are outside the first public sanctions layer.

## Match evidence

### Direct evidence

The following may produce `direct_list_match` when they point to exactly one entity record:

1. `identifier_exact`
   - the same reviewed identifier type and normalized value occurs on both sides;
   - this is stronger than a name match.

2. `primary_name_exact`
   - company name equals the sanctions primary name after conservative normalization.

3. `alias_exact`
   - company name or a reviewed company alias equals a sanctions primary name or source alias after conservative normalization.

Conservative normalization may standardize Unicode form, case, punctuation and whitespace. It must not silently remove material legal-name tokens or translate names in a way that turns a fuzzy candidate into a direct match.

### Review-only evidence

The following must remain `review_required`:

- a match that becomes equal only after removing legal-form tokens such as `Ltd`, `Limited`, `GmbH`, `S.A.` or equivalents;
- high string similarity without exact normalized identity;
- conflicting country or identifier evidence;
- more than one sanctions entity record matching the same company identity;
- ownership/control implications inferred from a listed parent or related company without a separately reviewed ownership/control rule.

A similarity score may be stored as diagnostic evidence, but it is never a sanctions finding by itself.

## Output record

Each company receives one result per sanctions source snapshot:

```json
{
  "company_id": "...",
  "source": "uk_sanctions_list",
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

> no direct deterministic match was found against the entity records present in this pinned source snapshot.

It does **not** establish that:

- the company is sanctions-clear;
- the company is compliant;
- no owner, controller, parent, subsidiary or related party is sanctioned;
- the company is unaffected by sectoral or ownership/control restrictions;
- another jurisdiction has no relevant designation.

## Source and publication requirements

Every published sanctions result must retain:

- source publisher and dataset name;
- pinned snapshot/retrieval date;
- source file hash;
- publication/redistribution decision from source governance;
- required attribution;
- matcher version.

No sanctions source file enters `public/data/` until its source record is `approved_for_publication` for the exact intended output.

## Human review

The atlas may expose a `review_required` state and the evidence that caused it. It must not automatically promote that state to `direct_list_match`.

Any future ownership/control logic must be a separate evidence layer with its own rules and provenance.