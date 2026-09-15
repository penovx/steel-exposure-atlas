# EU sanctions matchability results — 2026-09-15

## Scope

This review records the observed structure and matchability characteristics of the pinned local snapshot of the European Commission `Consolidated Financial Sanctions File 1.1` before any company-level matching is published.

Snapshot provenance:

- retrieved at: `2026-09-15T21:53:03+00:00`
- source file SHA-256: `049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015`
- raw size: `25,166,172` bytes
- source rows: `43,851`
- columns: `118`
- file generation date reported on every row: `05/08/2026`

The raw file remains local under ignored `tmp/` paths and is not a repository publication asset.

## Subject population

The current snapshot contains only two observed subject types:

- `enterprise`: 17,812 flattened rows
- `person`: 26,039 flattened rows

Person rows are excluded before enterprise profiling and are outside the first public sanctions layer.

The 17,812 enterprise rows collapse to **1,772 unique enterprises** using `Entity_LogicalId` as the grouping key.

## Flattening and names

The EU CSV is strongly denormalized:

- rows per enterprise: min 1, median 7, p95 26, max 112
- distinct source names per enterprise: min 1, median 5, p95 24, max 107
- enterprises with multiple names: 1,564 of 1,772

Therefore one CSV row must never be treated as one company.

The source exposes many `NameAlias_*` columns, including `NameAlias_WholeName`, language and regulation metadata. The profile found no reviewed field that establishes one universal primary company name for this project. The first derived entity subset therefore preserves the set of source names without inventing a primary name.

Name-key collision profile:

| Normalisation | Distinct keys | Unique to one enterprise | Shared across enterprises | Max enterprises per key |
| --- | ---: | ---: | ---: | ---: |
| Raw source name | 14,145 | 14,067 | 78 | 3 |
| Conservative normalisation | 14,033 | 13,932 | 101 | 3 |
| Legal-form-relaxed | 13,975 | 13,869 | 106 | 3 |

Exact names are therefore usually distinctive within the sanctions source, but not always. Shared-name collisions exist and must remain review cases.

## Identifier coverage

Observed identifier types on enterprise records:

| Type | Description | Enterprises | Coverage | Shared values |
| --- | --- | ---: | ---: | ---: |
| `regnumber` | Registration Number | 676 | 38.1% | 6 |
| `other` | Other identification number | 248 | 14.0% | 11 |
| `fiscalcode` | National Fiscal Code | 244 | 13.8% | 0 |
| `taxid` | Tax identification number | 230 | 13.0% | 1 |
| `imo` | IMO vessel identification | 41 | 2.3% | 0 |
| `swiftbic` | SWIFT BIC | 7 | 0.4% | 0 |
| `id` | National identification card | 4 | 0.2% | 0 |
| `euvat` | EU-standardized VAT number | 2 | 0.1% | 0 |
| `unssn` | UN Social Security Number | 2 | 0.1% | 0 |
| `tradelic` | Trade license | 1 | 0.1% | 0 |

Overall `Identification_Number` coverage is 916 of 1,772 enterprises (51.7%). Identifier values are not automatically globally unique: `regnumber`, `other` and `taxid` contain some values shared across multiple sanctions enterprises.

An identifier may therefore be used as hard evidence only when the identifier type is compatible on both sides and the normalized value is not ambiguous for the relevant source context.

## GIST matching boundary

The current GIST public plant extract exposes an immediate owner/operator name and a GEM entity ID. The GEM entity ID is a source identity, **not a legal-registry identifier that can be compared directly with EU sanctions registration, tax or other identifiers**.

For the first GIST → EU sanctions screening pass:

- exact conservative name equality is a **review candidate**, not a published sanctions finding;
- legal-form-relaxed equality is also review-only;
- fuzzy similarity is not run in the first batch pass;
- plant country must not be used as if it were the legal domicile of the owner company;
- a `direct_list_match` requires separate corroborating legal-entity evidence or explicit human review.

This source-specific rule is intentionally stricter than the generic sanctions matcher because the company identity quality on the GIST side is not yet equivalent to a legal-entity registry record.

## Product consequence

The next step is a local candidate profile between the 1,772 EU sanctions enterprises and unique GIST owner identities. It will report aggregate counts and keep row-level candidate details under ignored `tmp/` review output.

No candidate is shown in the public UI until candidate evidence has been reviewed. A no-candidate result remains only `no direct list match in this snapshot`, never a clearance statement.
