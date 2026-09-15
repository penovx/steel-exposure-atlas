# EU + OFAC sanctions distribution review — 2026-09-15

## Purpose

This review narrows the sanctions package to exact official machine-readable distributions and applies the project publication gate before any source file is downloaded or transformed.

Current product scope is limited to:

1. European Union consolidated financial sanctions data.
2. United States / OFAC sanctions data.

UK sanctions are out of scope.

## Decision summary

| Source | Exact distribution candidate | Processing | Public derived output | Raw/source bundling |
| --- | --- | --- | --- | --- |
| EU consolidated financial sanctions | Consolidated Financial Sanctions File 1.1, CSV or XML | Approved for local review | **Blocked pending exact distribution licence URI/notice** | Blocked |
| OFAC | SDN + Consolidated Non-SDN, preferably Advanced XML | Approved for local review | **Blocked under conservative international-publication gate pending explicit redistribution basis** | Blocked |

No sanctions data may enter `public/data/` from either source yet.

## European Union

Publisher: European Commission, Directorate-General for Financial Stability, Financial Services and Capital Markets Union.

### Exact distribution candidate

The European Data Portal catalogue lists the following official distributions for the consolidated EU financial sanctions dataset:

- `Consolidated Financial Sanctions File 1.1` — CSV
- `Consolidated Financial Sanctions File 1.1` — XML

The dataset is public and marked with daily accrual periodicity. The catalogue quality metadata indicates that licence information exists for these distributions.

The current official CSV 1.1 endpoint follows the Commission Financial Sanctions Files service:

`https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw`

The XML 1.1 equivalent is:

`https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw`

The project should prefer v1.1 because it is the newer structured distribution and is available in both CSV and XML.

### Reuse basis

The European Commission legal notice states that EU-owned Commission website content is licensed under CC BY 4.0 unless otherwise indicated, with attribution and indication of changes required.

However, the project governance rule requires the exact dataset/distribution reuse basis to be pinned rather than relying only on a general website notice. The data portal confirms that licence metadata exists for the distributions, but the exact licence URI/notice has not yet been independently captured in this review.

### Decision

`approved_for_processing` for local structure/matching research only.

`approved_for_publication` remains **blocked** until the exact 1.1 CSV/XML distribution licence URI or an equivalent dataset-specific reuse notice is captured and stored with the source review.

Do not publish or bundle any EU sanctions source or derived match output before that gate is closed.

Official references:

- https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions?locale=en
- https://webgate.ec.europa.eu/fsd/fsf#!/files
- https://commission.europa.eu/legal-notice_en

## United States / OFAC

Publisher: U.S. Department of the Treasury, Office of Foreign Assets Control.

### Exact distribution candidate

OFAC's Sanctions List Service is the primary official delivery mechanism. The package needed for this atlas consists of:

- Specially Designated Nationals and Blocked Persons (SDN) List;
- Consolidated Non-SDN sanctions data.

OFAC provides legacy CSV/XML files and newer Advanced XML files. OFAC states that all formats contain the same basic sanctions-list data at their core and that the Advanced XML format adds richer metadata. It also states that anyone may use the Advanced XML files.

For the atlas, the preferred technical candidate is therefore:

- SDN Advanced XML;
- Consolidated Non-SDN Advanced XML.

OFAC also publishes hashes/signatures for sanctions-list files, allowing the exact snapshot to be integrity-checked.

### Reuse basis

Two relevant facts are documented:

1. OFAC explicitly states that anyone may use the Advanced XML files.
2. 17 U.S.C. § 105 states that copyright protection under U.S. copyright law is not available for works of the United States Government.

These points provide a strong basis for local processing and ordinary use of the official files. They do not, by themselves, provide the same globally explicit redistribution licence as CC BY 4.0 or OGL, and U.S. statutory public-domain treatment does not automatically settle copyright treatment in every foreign jurisdiction.

Because the atlas is intentionally reviewed as a public, commercial-capable portfolio product available internationally, the project keeps a stricter publication gate.

### Decision

`approved_for_processing` for local structure/matching research.

Public redistribution of OFAC source files and public derived sanctions-match output remain **blocked** until the project pins an explicit redistribution/publication basis that is acceptable for the internationally accessible site.

This is deliberately more conservative than the minimum U.S. domestic copyright position.

Official references:

- https://ofac.treasury.gov/sanctions-list-service
- https://ofac.treasury.gov/sdn-list-data-formats-data-schemas/frequently-asked-questions-on-advanced-sanctions-list-standard
- https://ofac.treasury.gov/specially-designated-nationals-list-sdn-list/hash-values-for-ofac-sanctions-list-files
- https://uscode.house.gov/view.xhtml?edition=prelim&num=0&req=granuleid%3AUSC-prelim-title17-section105

## Implementation consequence

No real sanctions data is downloaded yet.

The next permitted work is limited to:

- documenting the exact EU distribution licence URI/notice;
- documenting an explicit OFAC redistribution/publication basis acceptable for this public international portfolio use;
- keeping the existing source-agnostic matcher and synthetic tests unchanged.

Only after each source independently reaches `approved_for_publication` may its entity-only derived match output be considered for `public/data/` and the UI.
