# GIST plant workbook profiling results — 2026-09-14

Status: **review complete for first-layer transformation rules**

This note records the reproducible profile of the reviewed Global Energy Monitor Global Iron and Steel Tracker June 2026 (V1) plant-level workbook.

Reviewed workbook SHA-256:

`A5768B59CD7E6CEC217692AE45EDA80EA70AAB1666AEF74332CC1B41DD5338EB`

The profiling tools are read-only. No GEM records were written to the repository while producing these results.

## Plant table

- Rows: 1,293
- Non-blank GEM plant IDs: 1,293
- Unique GEM plant IDs: 1,293
- Duplicate GEM plant IDs: 0
- Countries/areas: 91
- Coordinates present: 1,293
- Coordinates parseable and within latitude/longitude bounds: 1,293
- Coordinate accuracy: 1,141 `exact`, 152 `approximate`
- Immediate owner values: 1,291 text values, 2 `unknown`
- Parent field present: 1,293 rows
- Parent strings with multiple percentage tokens: 292
- Parent strings containing semicolon-separated structure: 353

Conclusion: `GEM plant ID` is suitable as the public plant key. The plant table is one row per plant in this release. Coordinates are complete, but coordinate accuracy must stay attached to every point. Parent ownership cannot be reduced to a single parent without a separate relationship parser.

## Capacity and status table

- Rows: 1,845
- Unique plants: 1,293
- Plants with more than one row: 390
- Maximum rows for one plant: 5
- Exact duplicate capacity/status rows: 0
- Plant + status groups: 1,845
- Repeated plant + status groups: 0
- Plants with more than one current-status row: 62

Observed status rows:

| Status | Rows |
| --- | ---: |
| operating | 935 |
| announced | 287 |
| retired | 232 |
| construction | 140 |
| operating pre-retirement | 97 |
| cancelled | 76 |
| mothballed | 72 |
| mothballed pre-retirement | 6 |

### Capacity total versus technology routes

For crude-steel capacity, 1,828 rows were directly comparable and every comparable row matched the sum of its route fields. Seventeen rows were not exactly comparable because at least one contributing value was non-numeric such as `>0`.

For iron capacity, 1,809 rows were directly comparable and every comparable row matched the sum of its route fields. Thirty-six rows were not exactly comparable because at least one contributing value was non-numeric.

This supports two rules:

1. the source total columns are authoritative for total-capacity display and aggregation;
2. route fields are breakdowns and must never be added on top of the total columns.

A plant can have separate rows for operating, construction, announced, mothballed or other status tranches. Therefore a single scalar `plant_status` is not valid. Capacity must be grouped by source status or by an explicitly documented status bucket.

### Value-state observations

`>0` occurs in capacity fields and means a positive but unquantified amount. It is not zero and must not be silently converted to a numeric value. `N/A` remains distinct from missing or unknown.

For any derived capacity sum, the transformer must retain both the known numeric sum and whether an unquantified positive component is present.

## Production table

- Rows: 1,393
- Plants represented: 488
- Duplicate plant + production-type groups: 28
- Identical duplicate groups: 26
- Differing duplicate groups: 2

Observed production types differ slightly from the prose metadata and must be taken from the actual workbook values:

- `Crude steel production (ttpa)`
- `EAF steel production (ttpa)`
- `BOF steel production (ttpa)`
- `OHF steel production (ttpa)`
- `Other/Unknown steel production (ttpa)`
- `Iron production (ttpa)`
- `BF production (ttpa)`
- `DRI production (ttpa)`
- `Other/Unknown iron production (ttpa)`

There are 424 plants with both a crude-steel total row and one or more steel-route rows, and 189 plants with both an iron total row and one or more iron-route rows. Therefore route rows must not be summed with total rows.

### Production total versus route sums

Steel plant-year comparisons produced 1,408 matches, 4 mismatches and 1,507 non-comparable cases. The four mismatches are small (1–2 thousand tonnes) and are consistent with source rounding differences.

Iron plant-year comparisons produced 553 matches, 4 mismatches and 738 non-comparable cases. Three mismatches are small; one plant-year has a materially larger route-versus-total difference. The published source total remains authoritative when a total is available.

### Production coverage

For crude-steel total rows, numeric coverage is:

| Year | Numeric total rows | Unknown total rows |
| --- | ---: | ---: |
| 2019 | 204 | 226 |
| 2020 | 243 | 188 |
| 2021 | 258 | 173 |
| 2022 | 261 | 170 |
| 2023 | 273 | 158 |
| 2024 | 257 | 174 |
| 2025 | 5 | 426 |

The 2025 field is not suitable as the default latest-year production view. The first public production view will use 2019–2024 and describe values as reported production where available. Aggregate production views must disclose record coverage rather than imply full market coverage.

### Duplicate handling

Identical duplicate plant/type rows may be collapsed.

For non-identical duplicate rows, values may be merged only when there is no semantic conflict: a numeric value may replace another duplicate's `unknown` or blank value for the same plant/type/year. A numeric value must not automatically override `N/A`, and differing numeric values must not be guessed or averaged. Conflicting plant/type/year cells are excluded from the derived output and flagged by validation.

## Date fields

Date columns contain a mixture of plain numeric years, Excel date serials and a small number of values outside the simple year/serial heuristics. Style IDs confirm that interpretation must use XLSX number formats rather than magnitude alone.

Examples include date-formatted serial candidates below the earlier numeric threshold, and several values such as `1739`, `1757`, `1771` and `1796` stored with a year-like style. These values require a dedicated date-normalization review before publication.

Dates are therefore **not part of the first public GIST extract**. Excluding them removes this unresolved interpretation from the release gate without discarding the source fields.

## Decisions for the first public layer

1. Use `GEM plant ID` as the stable plant key.
2. Publish all valid plant coordinates while preserving `exact` versus `approximate` accuracy.
3. Preserve capacity/status rows as distinct source tranches.
4. Use source total capacity fields for totals; use route fields only as breakdowns.
5. Keep `numeric`, `unknown`, `N/A`, `>0` and blank semantically distinct.
6. Do not publish one synthetic `plant_status`.
7. Keep operating, development, mothballed and closed/cancelled capacity separate.
8. Use total production rows for aggregate production; never add total and route rows together.
9. Limit the first production trend to 2019–2024 and disclose coverage.
10. Do not publish normalized date fields until the dedicated date parser is reviewed.
11. Immediate owner may be published as a source fact. Parent strings may be displayed as source text, but parent-based grouping/navigation waits for a reviewed relationship parser.

These decisions feed the GIST plant data contract v1.0.