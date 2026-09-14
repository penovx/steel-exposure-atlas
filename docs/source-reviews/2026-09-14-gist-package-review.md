# GIST package review — 2026-09-14

## Scope

This review covers the exact Global Energy Monitor download package retrieved for the Steel Exposure Atlas on 2026-09-14.

The original ZIP is retained outside Git and identified by SHA-256:

- `gem-download.zip`
- `81F3D43B44949F5783E87FAB1651671EAEC18E96A9FD0D8FA707D6508AB0F5BB`

The package contained:

| File | SHA-256 | Decision |
| --- | --- | --- |
| `Plant-level_data_Global_Iron_and_Steel_Tracker_June_2026_V1.xlsx` | `A5768B59CD7E6CEC217692AE45EDA80EA70AAB1666AEF74332CC1B41DD5338EB` | reviewed for derived publication use |
| `Steel_unit_data_Global_Iron_and_Steel_Tracker_June_2026_V1.xlsx` | `D5355ACD307930C0104D21DC9C6E6D62451856E044CE1AA3C576D9CB14B4D425` | fingerprinted; separate field review if needed |
| `Iron_unit_data_Global_Iron_and_Steel_Tracker_June_2026_V1.xlsx` | `A770DDDB8DDC6475ECCB32D9B54981F5F81A53253B097ADB8715C193E9F73F6A` | fingerprinted; separate field review if needed |
| `Global-Energy-Ownership-Tracker-August-2026-V2.xlsx` | `C17C148B23CE054621C295274CD66B659E61D68DBC1EAD5A76CD22455D954FFF` | separate source review required |
| `Production-Consumption-of-Met-Coal-Iron-Ore-by-Steel-Industry-December-2025-Standard-Copy-V1.xlsx` | `399B9CE88985B3BCC6642AD32950E345387C9C5E78C7597D9D63155FDE613F2F` | separate source review required |

## Licence and attribution

The `About` worksheet of the reviewed plant-level workbook identifies the dataset as `Global Iron and Steel Tracker, June 2026 (V1)` and states that it is distributed under the Creative Commons Attribution 4.0 International License.

The workbook recommends the citation:

> Global Energy Monitor, Global Iron and Steel Tracker, June 2026 (V1) release.

For the atlas, attribution must additionally identify that fields have been transformed and calculations derived by this project. The project must not imply Global Energy Monitor endorsement, sponsorship or responsibility for derived outputs.

The approval recorded here is limited to a documented derived subset from the reviewed workbook. The original XLSX and full download package remain outside the public repository.

Linked GEM.wiki pages, images and external references are not automatically treated as covered by this review.

## Workbook structure confirmed

The reviewed plant-level workbook contains five visible worksheets:

- `About`
- `Metadata`
- `Plant data`
- `Plant capacities and status`
- `Plant production`

Observed row counts from read-only inspection:

- `Plant data`: 1,293 records plus header
- `Plant capacities and status`: 1,845 records plus header
- `Plant production`: 1,393 records plus header

## Key semantics

`GEM plant ID` is the plant-level key shared across the relevant worksheets.

Capacity/status records are one-to-many from plant. A plant can have different technology groups and statuses at the same time. No importer may reduce this to a single row without an explicit, tested aggregation rule.

Production records are also one-to-many from plant and distinguish production type by technology route and year.

The source distinguishes at least three materially different value states:

- numeric or textual observation
- `unknown`: the attribute or technology can exist, but the value was not found
- `N/A`: the attribute or technology does not apply

These states must not be collapsed into zero or a single null value where that would change meaning.

Coordinate accuracy is explicitly defined by the source as:

- `exact`: location confirmed via satellite imagery
- `approximate`: location estimated or undefined

The distinction must remain available to the UI and spatial-analysis pipeline.

## Date handling

Metadata documents plant dates in `YYYY-MM-DD` form, but raw XLSX storage may encode dates as Excel serial numbers tied to cell formatting. The ingestion pipeline must decode workbook date semantics and must not interpret every numeric date cell as a plain integer.

## Ownership handling

The plant workbook provides immediate owner and parent information, including GEM entity IDs and ownership shares where available. Parent fields can contain multiple parent/share values.

Do not infer ultimate ownership, operational control, buyer-supplier relationships or commercial sourcing dependency from these fields alone. Any later match to GLEIF is a separate derived step and requires its own match evidence.

## Decision

The exact plant-level GIST June 2026 (V1) workbook is approved for processing and for publication of a documented derived subset under CC BY 4.0 with attribution and modification disclosure.

No original GEM workbook is approved for direct repository bundling by this decision.

Before plant records enter `public/data/`, the project must still complete full profiling, define the transformation contract and validate the resulting public extract.
