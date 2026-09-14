# GIST plant data contract v1.0

Status: **approved for first public-layer implementation**

This contract defines the reviewed transformation rules for the Global Energy Monitor Global Iron and Steel Tracker June 2026 (V1) plant-level workbook used by Steel Exposure Atlas.

It authorizes implementation of a derived public subset only. The original workbook remains outside Git. Release controls, attribution and source provenance remain mandatory.

## Source identity

- Source: Global Energy Monitor — Global Iron and Steel Tracker
- Release: June 2026 (V1)
- Reviewed workbook SHA-256: `A5768B59CD7E6CEC217692AE45EDA80EA70AAB1666AEF74332CC1B41DD5338EB`
- Licence: CC BY 4.0
- Stable source key: `GEM plant ID`
- Retrieval date: 2026-09-14

## Public plant object

One public plant object is produced for each of the 1,293 unique GEM plant IDs.

Required fields:

| Public field | Source | Rule |
| --- | --- | --- |
| `plant_id` | `GEM plant ID` | required; preserve source ID |
| `plant_name` | `Plant name (English)` | source fact |
| `owner_name` | `Owner` | immediate owner/operator only; preserve `unknown` |
| `owner_gem_entity_id` | `Owner GEM entity ID` | preserve as string |
| `parent_display` | `Parent (English)` | source display text only; may contain multiple parents/shares |
| `municipality` | `Municipality` | preserve source value/state |
| `subnational_unit` | `Subnational unit` | preserve source value/state |
| `country_area` | `Country/area` | preserve GEM terminology |
| `region` | `Region` | WEO region as supplied by GEM |
| `latitude` | `Coordinates` | parse first coordinate component |
| `longitude` | `Coordinates` | parse second coordinate component |
| `coordinate_accuracy` | `Coordinate accuracy` | preserve `exact` / `approximate` |
| `product_category` | `Category steel product` | preserve source categories |
| `steel_products` | `Steel products` | source list; not comprehensive |
| `end_user_sectors` | `Steel sector end users` | preserve source categories |
| `main_production_equipment` | `Main production equipment` | plant-level source summary |
| `wiki_url` | `GEM wiki page` | link only; linked content is not incorporated into the dataset |

Excluded from v1.0 public output:

- plant date fields
- workforce and certification fields
- power source
- iron ore source
- metallurgical coal source
- raw PermIDs
- normalized parent relationship arrays

These exclusions are scope and assurance decisions, not statements that the source fields are invalid.

## Coordinates

All 1,293 source coordinate pairs parsed successfully in the reviewed release.

Validation remains mandatory:

- latitude must be between -90 and 90;
- longitude must be between -180 and 180;
- malformed coordinates fail the build;
- `coordinate_accuracy` must be present;
- `approximate` coordinates remain distinguishable in the UI or methodology.

Point proximity must never be presented as evidence of a supplier, ownership or logistics relationship.

## Capacity/status representation

Source worksheet: `Plant capacities and status`

Observed grain in the reviewed workbook is one row per `GEM plant ID` + `Status`. There are 1,845 rows, 1,293 plants and no repeated plant/status pair.

A public plant may therefore contain multiple status tranches.

Each tranche keeps:

- `status`
- `main_production_equipment`
- crude-steel total capacity
- BOF capacity
- EAF capacity
- IF capacity
- other/unspecified steel capacity
- iron total capacity
- BF capacity
- DRI capacity
- other/unspecified iron capacity

### Capacity value object

A capacity field is represented as:

```json
{
  "value_ttpa": 1200,
  "state": "numeric"
}
```

or, when no precise number exists:

```json
{
  "value_ttpa": null,
  "state": ">0"
}
```

Allowed states are:

- `numeric`
- `N/A`
- `>0`
- `unknown`
- `blank`

No transformation may silently turn `>0`, `unknown`, `N/A` or blank into zero.

### Total versus route capacity

The reviewed profile found that every directly comparable row matched:

- crude-steel total capacity = sum of steel-route capacities;
- iron total capacity = sum of iron-route capacities.

Therefore:

- source total fields are authoritative for total-capacity values;
- technology-route fields are breakdowns;
- route values must never be added on top of the source total.

### Status buckets

The source status is always retained. Optional derived buckets may be used for UI summaries:

| Derived bucket | Source statuses |
| --- | --- |
| `operating` | `operating`, `operating pre-retirement` |
| `development` | `announced`, `construction` |
| `mothballed` | `mothballed`, `mothballed pre-retirement` |
| `closed_or_cancelled` | `retired`, `cancelled` |

The application must not publish a single synthetic `plant_status` when multiple source status tranches exist.

### Derived capacity sums

Capacity may be summed only within an explicitly named status bucket.

For each sum publish or retain internally:

- `known_numeric_sum_ttpa`
- `has_unquantified_positive`
- contributing row count

If any contributing row is `>0`, the result is a lower-bound-like known numeric component plus an unquantified positive component. It must not be displayed as an exact total.

Operating and development capacity are separate measures and must not be combined into a value labelled current or operating capacity.

## Production representation

Source worksheet: `Plant production`

Production is available for 488 plants in the reviewed workbook and is incomplete by year. It is therefore a reported-production layer, not a complete market-production dataset.

### Authoritative totals

For total production use only:

- `Crude steel production (ttpa)`
- `Iron production (ttpa)`

Technology-route production rows are breakdowns and must not be added to the total rows.

Observed route labels are taken from the workbook values, including:

- `EAF steel production (ttpa)`
- `BOF steel production (ttpa)`
- `OHF steel production (ttpa)`
- `Other/Unknown steel production (ttpa)`
- `BF production (ttpa)`
- `DRI production (ttpa)`
- `Other/Unknown iron production (ttpa)`

### Duplicate production rows

Duplicate plant + production-type rows are handled deterministically:

1. identical duplicate year series collapse to one logical series;
2. for non-identical duplicates, a numeric value may replace another duplicate's `unknown` or blank value for the same plant/type/year;
3. `N/A` versus numeric is a semantic conflict and must not be auto-resolved;
4. differing numeric values must not be averaged or guessed;
5. unresolved conflicting cells are excluded from the derived public value and reported by validation.

### Years used in the first public view

The default production trend covers 2019–2024.

The 2025 field is excluded from the first public trend because only 5 crude-steel total rows and 1 iron total row contain numeric values in the reviewed release.

A production aggregate over a filtered selection must be described as reported production and must expose coverage, for example:

- plants in selection;
- plants with a numeric reported total for the selected year;
- reported production sum.

It must not be labelled as total production of the selection when coverage is incomplete.

## Ownership boundary

`owner_name` is the immediate owner/operator according to GEM metadata and may be used as a source fact.

`parent_display` may be shown as source text. It must not yet drive `same parent` grouping or entity navigation because 292 plant rows contain multiple percentage tokens and 353 contain semicolon-separated parent structures.

A separate reviewed ownership relationship parser is required before parent IDs, shares or parent-based navigation become part of the public interaction model.

GLEIF enrichment, if added later, remains a separate derived entity-resolution layer with its own provenance and match evidence.

## Dates

Date fields are explicitly excluded from v1.0 public output.

The workbook mixes plain years, Excel date serials and anomalous numeric values. A future date transformer must use cell number formats and plausibility validation, preserve year-only precision and reject ambiguous values rather than infer dates from numeric magnitude alone.

## Source-state semantics

The following meanings are preserved throughout transformation:

| Source state | Meaning in the atlas pipeline |
| --- | --- |
| numeric | precise source value |
| `unknown` | source indicates the field applies or may apply, but value was not found |
| `N/A` | source marks the field as not applicable |
| `>0` | a positive amount exists but the exact value is not supplied |
| blank | empty source cell; not automatically equivalent to another state |

## Provenance requirements

Every generated GIST public-data file must be accompanied by or linked to:

- dataset name and release;
- retrieval date;
- reviewed workbook SHA-256;
- transformation code version/commit;
- Global Energy Monitor attribution;
- statement that the output is a transformed extract produced by Steel Exposure Atlas.

Recommended source citation from the reviewed workbook:

> Global Energy Monitor, Global Iron and Steel Tracker, June 2026 (V1) release.

The project must not imply that Global Energy Monitor endorses the atlas or its derived interpretations.

## Build gates

The first GIST public extract may be generated only if automated validation confirms:

- exactly 1,293 unique plant IDs for this pinned release;
- no duplicate plant IDs;
- all coordinates parse and remain in range;
- coordinate accuracy is present for every plant;
- no unknown source status value is silently accepted;
- no repeated plant/status pair is silently accepted;
- capacity total-versus-route checks remain consistent with documented rules;
- production duplicate handling produces no unresolved value without a validation report;
- 2025 is not promoted to the default production year without a new source review;
- attribution/provenance metadata is emitted with the public extract.

A future source release must be re-profiled. Counts in this contract are release-specific assertions, not permanent assumptions.