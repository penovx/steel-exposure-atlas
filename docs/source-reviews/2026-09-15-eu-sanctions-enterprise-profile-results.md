# EU sanctions enterprise profile results — 2026-09-15

## Snapshot

Pinned raw SHA-256:

`049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015`

The raw CSV remains local-only under `tmp/source-packages/eu-sanctions/`.

## Population

- source rows: 43,851
- enterprise rows: 17,812
- person rows excluded before enterprise profiling: 26,039
- other subject rows excluded: 0
- unique enterprises after grouping by `Entity_LogicalId`: 1,772

## Flattening

Rows per enterprise:

- minimum: 1
- median: 7
- 95th percentile: 26
- maximum: 112

Distinct source names per enterprise:

- minimum: 1
- median: 5
- 95th percentile: 24
- maximum: 107

1,564 enterprises expose more than one source name.

## Field coverage at unique-enterprise level

- `Entity_EU_ReferenceNumber`: 1,772 / 1,772 (100.0%)
- `Entity_UnitedNationId`: 23 / 1,772 (1.3%)
- `Entity_DesignationDate`: 1,586 / 1,772 (89.5%)
- `Entity_Regulation_Programme`: 1,772 / 1,772 (100.0%)
- `Address_CountryIso2Code`: 1,518 / 1,772 (85.7%)
- `Address_CountryDescription`: 1,518 / 1,772 (85.7%)
- `Identification_Number`: 916 / 1,772 (51.7%)
- `Identification_TypeCode`: 916 / 1,772 (51.7%)
- `Identification_TypeDescription`: 916 / 1,772 (51.7%)

## Interpretation

The 17,812 enterprise rows are a flattened representation, not 17,812 sanctioned companies. `Entity_LogicalId` is therefore the required grouping key for the first entity-only transformation.

The source is name-rich: the median enterprise exposes five distinct `NameAlias_WholeName` values and 1,564 of 1,772 enterprises expose multiple names. The first matcher must therefore consider the reviewed set of source names rather than select one arbitrary source row as a primary company name.

Identification data is potentially useful but cannot yet be treated as a generic company identifier. The next profile must inspect source identification type codes/descriptions and test value uniqueness within each type before any type is admitted as deterministic identifier evidence.

Country context is useful for disambiguation but is incomplete and must not become a mandatory match field.
