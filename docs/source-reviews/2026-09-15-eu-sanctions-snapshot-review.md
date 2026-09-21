# EU sanctions snapshot review — 2026-09-15

## Purpose

Record the first real local snapshot of the official EU Consolidated Financial Sanctions File 1.1 before any entity extraction or matching is performed.

This is an evidence record for Sofa Case Study No. 1: source availability, structure, freshness and reuse are part of the finding, not only the eventual match result.

## Snapshot

- Publisher: European Commission
- Dataset: Consolidated Financial Sanctions File 1.1
- Format: CSV
- Retrieval timestamp: `2026-09-15T21:53:03+00:00`
- SHA-256: `049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015`
- Raw size: `25,166,172` bytes
- Source rows: `43,851`
- Unique `Entity_LogicalId` values across all subject types: `6,234`
- Columns: `118`
- Raw file remains local under the ignored `tmp/source-packages/eu-sanctions/` path and is not committed.

## Observed subject types

The real 1.1 snapshot contains exactly two `Entity_SubjectType_ClassificationCode` values:

| Subject type | Flattened rows |
| --- | ---: |
| `enterprise` | 17,812 |
| `person` | 26,039 |

This closes the earlier schema question for this snapshot. The first public sanctions layer may therefore use `enterprise` as the source filter and must exclude `person` rows before any derived record is created.

The row counts are not counts of unique sanctioned enterprises or persons. The source is flattened and repeats one logical entity across names, addresses, identifiers and other related records. Entity extraction must group by `Entity_LogicalId`.

## Freshness observation

Every row reports `fileGenerationDate = 05/08/2026`, while the file was retrieved on 2026-09-15. Interpreting the source date as 5 August 2026 gives a gap of about 41 days between the reported file generation date and retrieval.

The data.europa.eu catalogue describes the dataset accrual periodicity as `daily`. The observed gap does **not** by itself prove that the sanctions content is stale or wrong: the exact semantics of `fileGenerationDate`, publication refresh behaviour and whether the file is regenerated only when source content changes still need to be distinguished.

For the atlas, freshness must therefore be explicit evidence. A sanctions result may not be presented as current merely because the endpoint was retrieved today. The UI or methodology must retain both retrieval time and source generation date.

## Reuse decision

The project treats the EU source as approved for processing and for publication of a reviewed derived entity-only subset under the European Commission reuse basis / CC BY 4.0, provided the downloaded resource does not carry a conflicting specific notice.

The raw 25 MB source file is not intended for redistribution by the atlas. Publication should contain only the minimal fields needed to support the displayed evidence, plus source, snapshot date, hash, transformation statement and attribution.

## Next transformation gate

Before matching against steel-company identities:

1. filter `enterprise` before deriving output;
2. group flattened rows by `Entity_LogicalId`;
3. preserve all source names without inventing a `primary` name when the flattened source does not explicitly establish one;
4. profile source identifiers and country context separately from names;
5. exclude person rows and person-only fields entirely;
6. report unique enterprise count, name multiplicity and identifier coverage;
7. retain both `fileGenerationDate` and retrieval timestamp.

Only after this profile is reviewed should the entity subset be adapted to the sanctions matcher.

## Official references

- https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions?locale=en
- https://webgate.ec.europa.eu/fsd/fsf#!/files
- https://commission.europa.eu/legal-notice_en
