# GIST plant data contract v0.1

Status: **draft pending full profiling**

This contract defines how the reviewed Global Iron and Steel Tracker June 2026 (V1) plant-level workbook may be transformed for the first atlas layer. It does not authorize publication by itself; source approval and release controls still apply.

## Source identity

- Source: Global Energy Monitor — Global Iron and Steel Tracker
- Release: June 2026 (V1)
- Reviewed workbook SHA-256: `A5768B59CD7E6CEC217692AE45EDA80EA70AAB1666AEF74332CC1B41DD5338EB`
- Licence: CC BY 4.0
- Source key: `GEM plant ID`

## Source tables

### Plant

Source worksheet: `Plant data`

Expected grain: one row per GEM plant ID.

Candidate source fields for the first atlas release:

| Public field | Source field | Rule |
| --- | --- | --- |
| `plant_id` | `GEM plant ID` | required stable identifier; no project-generated replacement |
| `plant_name` | `Plant name (English)` | source fact |
| `owner_name` | `Owner` | source fact; immediate owner/operator only |
| `owner_gem_entity_id` | `Owner GEM entity ID` | preserve as string |
| `parent_display` | `Parent (English)` | preserve source meaning; may contain multiple parents/shares |
| `parent_gem_entity_ids` | `Parent GEM entity ID` | parse only after multi-value syntax is profiled |
| `municipality` | `Municipality` | source fact |
| `subnational_unit` | `Subnational unit` | source fact |
| `country_area` | `Country/area` | source terminology retained; country-code mapping is a separate derived field |
| `region` | `Region` | WEO region as supplied by GEM |
| `latitude` | `Coordinates` | derived by parsing source coordinate pair |
| `longitude` | `Coordinates` | derived by parsing source coordinate pair |
| `coordinate_accuracy` | `Coordinate accuracy` | preserve `exact` / `approximate` distinction |
| `product_category` | `Category steel product` | preserve source categories |
| `steel_products` | `Steel products` | source list; explicitly not comprehensive |
| `end_user_sectors` | `Steel sector end users` | source categories where present |
| `main_production_equipment` | `Main production equipment` | source summary only; capacity/status table remains authoritative for status-specific equipment |
| `plant_start_date` | `Start date` | decode Excel date semantics; serialize as ISO 8601 calendar date or documented year precision |
| `wiki_url` | `GEM wiki page` | link only; linked content is outside this data licence review |

Fields not selected for the first public layer remain excluded by default. Exclusion is not a claim that the fields are unusable; it limits scope and public-data volume.

### Capacity and status

Source worksheet: `Plant capacities and status`

Expected grain: one row per plant/status/equipment grouping, subject to profiling.

Fields retained internally for transformation:

- `GEM plant ID`
- `Main production equipment`
- `Status`
- `Start date`
- `Nominal crude steel capacity (ttpa)`
- `Nominal BOF steel capacity (ttpa)`
- `Nominal EAF steel capacity (ttpa)`
- `Nominal IF steel capacity (ttpa)`
- `Other/unspecified steel capacity (ttpa)`
- `Nominal iron capacity (ttpa)`
- `Nominal BF capacity (ttpa)`
- `Nominal DRI capacity (ttpa)`
- `Other/unspecified iron capacity (ttpa)`

Allowed source status values according to metadata:

- `announced`
- `construction`
- `operating`
- `operating pre-retirement`
- `mothballed`
- `mothballed pre-retirement`
- `cancelled`
- `retired`

No single `plant_status` field will be published until a deterministic rule is defined for plants with multiple simultaneous status rows.

No capacity total will be published until profiling confirms how rows combine and a tested aggregation avoids double counting across status and technology groupings.

### Production

Source worksheet: `Plant production`

Expected grain: one row per plant and production type, with yearly columns 2019–2025.

Source metadata distinguishes total categories from technology-route categories. Therefore, total crude-steel production must not be summed together with EAF/BOF/IF route production for the same plant-year.

Production is not required for the first map layer. It can be added after capacity/status logic is validated.

## Value-state semantics

The ingestion model must preserve source meaning before any UI simplification.

| Source value | Internal interpretation |
| --- | --- |
| numeric value | observed/reported source value |
| `unknown` | applicable or possible, but value not found |
| `N/A` | source says not applicable |
| `>0` | positive amount known without a precise value |
| blank | missing cell; do not automatically equate to `unknown` or `N/A` |

For numeric public fields, a companion state may be required where collapsing these source states would materially change interpretation.

## Coordinates

`Coordinates` must parse into valid decimal latitude/longitude pairs.

Validation rules:

- latitude: -90 to 90
- longitude: -180 to 180
- malformed pairs fail transformation rather than being silently dropped
- `coordinate_accuracy` stays attached to the point
- approximate coordinates must remain distinguishable in the UI or methodology

No point proximity may be described as a sourcing relationship or dependency.

## Dates

Source metadata describes date fields as `YYYY-MM-DD`, but XLSX cells can store dates as serial numbers with date styles.

The transformer must:

1. inspect cell style/number format;
2. decode Excel serial dates only where the cell is date-formatted;
3. preserve textual `unknown` values;
4. avoid inventing day/month precision when the source only provides a year;
5. serialize normalized full dates using ISO 8601.

## Ownership

`Owner` means immediate owner/operator according to GEM metadata.

`Parent (English)` and related ID fields can encode multiple parents and ownership shares. Until the syntax is fully profiled:

- preserve the source string;
- do not select one parent as an ultimate parent;
- do not infer operational control from share alone;
- do not treat absence of a parent record as evidence that no parent exists.

GLEIF enrichment, if introduced, is a separate derived entity-resolution layer and must expose match evidence/confidence.

## Provenance in public output

Each generated public dataset must carry or be accompanied by:

- source dataset name and release
- retrieval date
- reviewed source SHA-256
- transformation version or commit
- attribution text
- statement that the public extract is transformed by the Steel Exposure Atlas project

## Required profiling before v1.0

The draft contract cannot become v1.0 until a reproducible profile confirms at minimum:

- unique and duplicate plant-ID counts
- missingness for candidate plant fields
- coordinate parse success and accuracy distribution
- country/region cardinality
- status value distribution
- rows per plant in capacity/status data
- plants with multiple simultaneous status rows
- capacity value-state distributions (`numeric`, `unknown`, `N/A`, `>0`, blank)
- date storage patterns and conversion rules
- parent-field multi-value patterns

Any profiling result that contradicts an assumption above changes the contract before ingestion code is approved.
