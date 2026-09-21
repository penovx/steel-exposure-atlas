# EU sanctions distribution review — 2026-09-15

## Purpose

This review pins the current EU sanctions source path and records the publication decision before any real source data is downloaded or transformed.

Current sanctions scope is limited to the European Union consolidated financial sanctions list. UK and U.S. OFAC sources are out of scope.

## Selected distribution

Publisher: European Commission, Directorate-General for Financial Stability, Financial Services and Capital Markets Union.

Selected machine-readable source:

- `Consolidated Financial Sanctions File 1.1` — CSV preferred for the first ingestion;
- XML 1.1 remains an equivalent structured fallback.

Official source service:

- https://webgate.ec.europa.eu/fsd/fsf#!/files

European Data Portal catalogue:

- https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions?locale=en

The catalogue reports licence information for the distribution and daily update periodicity.

## Reuse basis

The European Commission legal notice states that EU-owned content on Commission websites is licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)** unless otherwise indicated.

CC BY 4.0 permits sharing and adaptation, including commercial reuse, provided appropriate credit is given and changes are indicated.

No conflicting dataset-specific restriction has been identified for the selected Consolidated Financial Sanctions File 1.1 in this review.

The earlier requirement to capture a separate licence URI directly on the distribution before publication was an unnecessarily strict project gate. It is removed. The governing rule is now:

- apply the Commission CC BY 4.0 reuse notice where no more specific contrary notice applies;
- stop and re-review if the exact downloaded resource or accompanying metadata contains a conflicting restriction.

## Decision

**Approved for processing and publication of a derived entity-only subset.**

Conditions:

- pin retrieval timestamp, exact source URL, format and SHA-256;
- preserve provenance and source record identifiers;
- retain only fields needed for company/entity matching and sanctions context;
- exclude person records and personal identifiers from the first public sanctions layer;
- attribute the European Commission / European Union and CC BY 4.0;
- state that the atlas transforms and matches source records;
- do not publish raw source data by default when a minimal derived subset is sufficient;
- do not present a negative direct-match result as sanctions clearance or compliance.

Attribution baseline:

`Source: European Commission, Consolidated Financial Sanctions File 1.1. Licensed under CC BY 4.0. Derived and transformed by Steel Exposure Atlas.`

## Interpretation boundary

A direct match is evidence of a deterministic match to one listed entity in the pinned snapshot. It is not a full sanctions-compliance conclusion.

A non-match means only that no direct deterministic match was found in the pinned snapshot. It does not establish that no owner, controller, related party or entity in another jurisdiction is subject to sanctions.

Fuzzy similarity and legal-form-normalised similarity remain `review_required`, not direct matches.

## Next implementation step

The next permitted step is to download the official 1.1 CSV to a local non-public working location, record its hash and retrieval metadata, profile its structure, derive the entity-only subset, and run the existing deterministic matcher against atlas company identities.

No UI publication happens before the first real snapshot and match output are reviewed.

## Official references

- https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions?locale=en
- https://webgate.ec.europa.eu/fsd/fsf#!/files
- https://commission.europa.eu/legal-notice_en
- https://creativecommons.org/licenses/by/4.0/
