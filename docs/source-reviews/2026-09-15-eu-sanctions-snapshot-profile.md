# EU sanctions snapshot profile — 2026-09-15

## Purpose

This note records the first real local profile of the official European Commission `Consolidated Financial Sanctions File 1.1` used by Steel Exposure Atlas.

It records source structure and matchability observations only. The raw sanctions CSV remains outside Git under the ignored local `tmp/` workspace. No row-level sanctions records are committed here.

## Snapshot identity

- Publisher: European Commission
- Distribution: `Consolidated Financial Sanctions File 1.1` CSV
- Retrieval time: `2026-09-15T21:53:03+00:00`
- Raw SHA-256: `049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015`
- Raw size: `25,166,172` bytes
- File generation date present on every row: `05/08/2026`
- Local raw path: `tmp/source-packages/eu-sanctions/raw/eu-financial-sanctions-1.1.csv`

The retrieval timestamp and source `fileGenerationDate` are deliberately recorded separately. A successful download does not by itself establish that the published file was generated on the retrieval date.

## Source shape

The downloaded CSV contains:

- 43,851 flattened rows;
- 6,234 unique `Entity_LogicalId` values across all subject types;
- 118 columns;
- 26,039 `person` rows;
- 17,812 `enterprise` rows;
- no other observed subject type in this snapshot.

The first public sanctions layer is enterprise-only. Person rows are excluded before enterprise profiling or matching.

## Enterprise population

Grouping the 17,812 enterprise rows by `Entity_LogicalId` produces **1,772 unique enterprises**.

Flattening per enterprise:

| Measure | Min | Median | P95 | Max |
| --- | ---: | ---: | ---: | ---: |
| Rows per enterprise | 1 | 7 | 26 | 112 |
| Distinct source names per enterprise | 1 | 5 | 24 | 107 |

1,564 of 1,772 enterprises have more than one source name.

This confirms that the CSV cannot be treated as one row per sanctioned enterprise and that all reviewed source-name variants matter for entity matching. The transformation must group on `Entity_LogicalId`; it must not count flattened rows as separate enterprises.

## Enterprise field coverage

Coverage below is measured at unique-enterprise level, not row level.

| Source field | Enterprises | Coverage |
| --- | ---: | ---: |
| `Entity_EU_ReferenceNumber` | 1,772 | 100.0% |
| `Entity_UnitedNationId` | 23 | 1.3% |
| `Entity_DesignationDate` | 1,586 | 89.5% |
| `Entity_Regulation_Programme` | 1,772 | 100.0% |
| `Address_CountryIso2Code` | 1,518 | 85.7% |
| `Address_CountryDescription` | 1,518 | 85.7% |
| `Identification_Number` | 916 | 51.7% |
| `Identification_TypeCode` | 916 | 51.7% |
| `Identification_TypeDescription` | 916 | 51.7% |

## Consequences for matching

1. `Entity_LogicalId` is the technical grouping key for this source snapshot.
2. `Entity_EU_ReferenceNumber` is available for every enterprise and should be retained as source provenance/reference data.
3. Source names must be preserved as a set. This profile does **not** infer one `primary` name from `NameAlias_WholeName`.
4. Country context is useful for disambiguation but is not complete enough to be a mandatory match key.
5. Identification data could materially strengthen matching, but the observed type codes/descriptions must be profiled before any identification number is treated as a comparable company identifier.
6. Exact normalized-name collisions across different EU enterprises must be measured before an exact name can be treated as unambiguous evidence.

## Next gate

Before producing an enterprise subset for matching against GIST company identities, profile:

- conservative normalized-name uniqueness/collisions across enterprises;
- legal-form-relaxed name collisions;
- identification type distributions and whether identification values are unique within type;
- available name metadata fields such as alias strength/language if present in the real 1.1 CSV.

The matchability profile must emit aggregate statistics only. It must not commit enterprise names, identification numbers or other row-level sanctions content.
