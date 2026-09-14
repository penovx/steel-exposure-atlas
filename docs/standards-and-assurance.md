# Standards and assurance

This project uses selected concepts from established standards and engineering guidance to improve data provenance, quality, security, privacy and accessibility.

No claim of certification, formal conformity or audit against any ISO/IEC, ISO or W3C standard is made.

## Scope

The controls below apply to the public Steel Exposure Atlas and to the data pipeline that produces its published outputs.

They are intended to keep the project reproducible, legally clean and proportionate to its actual risk profile. They do not turn the demonstrator into a regulated decision system or a certified information-management system.

## Reference standards and guidance

### ISO 8601-1 — dates and times

Use unambiguous machine-readable dates for source versions, retrieval dates and generated artefacts.

Project rule:

- use `YYYY-MM-DD` for calendar dates in metadata and provenance records;
- use timezone-aware ISO 8601 timestamps where time-of-day materially matters;
- do not rely on locale-specific dates such as `09/14/26`.

### ISO 3166-1 — country codes

Use standard country identifiers where a source can be mapped reliably to them.

Project rule:

- prefer ISO 3166-1 alpha-2 or alpha-3 codes for joins and published identifiers;
- retain the source's original country field for provenance;
- document exceptions, disputed territories and source-specific geographic conventions rather than forcing an uncertain mapping.

### ISO 19115-1 — geographic metadata concepts

Use the standard's metadata concepts as guidance for documenting geospatial datasets.

Project rule:

For every published geospatial source or derived layer, record at least:

- source and publisher;
- dataset/version or snapshot date;
- retrieval date;
- spatial coverage;
- temporal coverage where relevant;
- coordinate reference system where relevant;
- lineage/transformation steps;
- distribution/publication decision;
- material limitations.

### ISO 19157-1 — geographic data quality concepts

Use data-quality concepts to make limitations visible rather than collapsing them into a single opaque risk score.

Project rule:

Assess and document, where relevant:

- completeness;
- logical consistency;
- positional accuracy or coordinate precision;
- temporal quality/currency;
- thematic/classification accuracy;
- uncertainty introduced by joins, matching or aggregation.

Quality limitations that can change interpretation must be surfaced in methodology or UI.

### ISO/IEC 27001 — information-security control concepts

Use selected security principles as engineering guidance. The project is not an ISO/IEC 27001-certified information-security management system.

Project rule:

- no secrets, tokens or credentials in Git;
- raw third-party files remain outside Git unless publication rights are explicitly approved;
- dependency versions are pinned once dependencies are introduced;
- unnecessary runtime third-party calls are avoided;
- published artefacts are reproducible from reviewed inputs;
- source integrity is checked where practical, for example through SHA-256 or pinned upstream identities;
- deployment is blocked until the release checklist is satisfied.

### Privacy by design

The first public version should minimise personal-data processing rather than adding controls around data collection that is not needed.

Project rule:

- no user accounts;
- no behavioural analytics or advertising pixels by default;
- no user uploads;
- no runtime AI service requiring visitor prompts or identifiers;
- no external fonts or third-party embeds unless separately reviewed;
- document unavoidable hosting/network processing in the public privacy notice before release.

If later features introduce material personal-data processing, perform a new privacy review before implementation.

### WCAG 2.2 Level AA — accessibility target

WCAG 2.2 AA is the accessibility target for the public interface. This is a project target, not a formal accessibility certification.

Project rule:

- keyboard-accessible controls;
- visible focus states;
- sufficient text and control contrast;
- meaningful labels and accessible names;
- no information conveyed by colour alone;
- responsive operation on mobile and desktop;
- provide a non-map textual or tabular representation for information that would otherwise be available only visually where practical.

## Evidence model

Published information is classified into three categories:

1. **Source fact** — directly supported by a reviewed source.
2. **Derived value** — produced by a documented transformation, join or calculation.
3. **Interpretation or assumption** — analytical framing that is not itself a source fact.

The application must not visually or linguistically blur these categories when the distinction affects interpretation.

Examples:

- a plant coordinate from GIST is a source fact;
- a regional capacity share calculated from selected records is a derived value;
- describing that share as concentration is an interpretation;
- converting water stress into a supplier-failure probability without supporting evidence is prohibited.

## Provenance baseline

For every public data layer, retain enough information to reconstruct:

`source -> exact version/snapshot -> retrieval -> selected fields -> transformation -> published output`

Where practical, record a cryptographic hash of original downloaded packages before processing.

Original downloads must not be silently modified. Working copies and derived datasets must be kept separate from original packages.

## Licensing and attribution

Standards guidance does not override source licences.

Every external dataset, code dependency, visual asset and font remains subject to its own terms. Publication requires the source-specific review defined in `docs/source-governance.md`.

Required attribution, modification notices, licence links and non-endorsement conditions must be preserved in the public application and repository where applicable.

## Claims deliberately not made

The project does not claim:

- ISO certification;
- formal conformity with any ISO or IEC standard;
- third-party audit or assurance;
- supplier due diligence;
- compliance assessment;
- disruption prediction;
- operational sourcing recommendations;
- endorsement by data publishers or standards bodies.

These boundaries are part of the assurance model, not disclaimers added after implementation.
