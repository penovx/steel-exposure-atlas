# GLEIF source review — 2026-09-14

## Scope

This review covers the official GLEIF Concatenated Files used only for legal-entity identification and ownership context:

- LEI-CDF v3.1 (Level 1: legal-entity reference data)
- RR-CDF v2.1 (Level 2: relationship records)

The published atlas will use a derived subset rather than redistribute the complete source files. The exact source snapshot date must be recorded when ingestion is implemented.

## Rights and cost

GLEIF states that its Access Service is free and that LEIs and LEI Reference Data made available through that service are provided under CC0 1.0 Universal.

The project may therefore process and redistribute a derived subset for this public demonstrator. CC0 does not require attribution, but the atlas will still identify GLEIF as the source and preserve the retrieval/snapshot date as provenance.

## Conditions that still apply

The GLEIF terms are not only a licence statement. The project must also respect the Access Service conditions:

- use GLEIF-provided access methods and do not circumvent technical restrictions;
- do not use the GLEIF trademark or logo without permission;
- do not imply that the atlas, its analysis or its outputs are provided, supported, authorised, granted or otherwise associated with GLEIF;
- do not present derived outputs as GLEIF products or services.

## Interpretation boundary

RR-CDF records describe reported direct and ultimate accounting-consolidating parent relationships where the relevant parent has an LEI. Reporting exceptions also exist.

Accordingly:

- a recorded relationship can be used as ownership context;
- absence of a relationship record must not be interpreted as evidence that no parent exists;
- the relationship data do not prove operational control of a plant, supply dependency, buyer-supplier relationships or physical product flows;
- if GLEIF records are matched to a steel-plant owner name, that match is a separate derived step and must carry its own confidence/evidence status.

## Decision

**Approved for processing and publication of a derived subset** from the official LEI-CDF v3.1 and RR-CDF v2.1 Concatenated Files, subject to a pinned source snapshot date and the conditions above.

No paid or metered service is introduced.

## Official references

- https://www.gleif.org/en/meta/lei-data-terms-of-use
- https://www.gleif.org/en/lei-data/gleif-concatenated-file/download-the-concatenated-file
- https://www.gleif.org/en/lei-data/access-and-use-lei-data/level-2-data-relationship-record-rr-cdf-2-1-format
