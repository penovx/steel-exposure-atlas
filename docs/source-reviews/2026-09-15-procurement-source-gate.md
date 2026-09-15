# Procurement-facing source gate — 2026-09-15

This review applies the project source-governance rules to procurement-oriented data sources: sanctions, tariffs/trade measures and environmental/ESG context.

The public atlas is reviewed as commercial-capable professional use. Public accessibility alone is not enough; unclear redistribution rights block publication by default.

## Current sanctions scope

The current sanctions layer is intentionally limited to the **European Union consolidated financial sanctions list**.

The UK Sanctions List and U.S. OFAC sanctions files are outside the current product scope and must not be ingested, matched or shown in the UI unless the product scope is explicitly changed later.

## Decision summary

| Source | Decision | Cost | Intended use |
| --- | --- | --- | --- |
| EU consolidated financial sanctions list | **Approved for processing and publication of a derived entity-only subset** | Free | EU sanctions-list screening context |
| EU TARIC | Reviewed; not approved yet | Free | Import-duty and trade-measure context |
| Access2Markets | Rejected as primary redistributable data feed | Free | Reference only; not a publication source |
| EEA EU ETS data from the Union Registry | Approved for processing and publication of a derived subset | Free | Facility-level verified-emissions context |
| EEA Industrial Emissions reporting dataset | Approved for processing; publication pending dataset-specific rights check | Free | Facility-level environmental context |

## EU consolidated financial sanctions list

Publisher: European Commission, Directorate-General for Financial Stability, Financial Services and Capital Markets Union.

### Distribution

The official consolidated financial sanctions dataset is available through the Commission Financial Sanctions Files service and the European Data Portal in CSV and XML formats. The selected technical candidate is `Consolidated Financial Sanctions File 1.1`.

The catalogue quality metadata reports licence information for the distribution. The Commission legal notice states that EU-owned content on Commission websites is licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)** unless otherwise indicated. CC BY 4.0 permits reuse, including adaptation and commercial reuse, subject to appropriate attribution and indication of changes.

No conflicting dataset-specific restriction has been identified for the selected sanctions distribution in the review performed on 2026-09-15.

### Decision

**Approved for processing and publication of a derived entity-only subset**, subject to the following controls:

- pin the exact downloaded 1.1 distribution, retrieval timestamp and SHA-256;
- record the exact source URL and file format;
- retain attribution to the European Commission / European Union and CC BY 4.0;
- indicate that the atlas transforms and matches source records;
- stop publication if the downloaded resource or accompanying notice contains a more specific conflicting restriction;
- exclude person records and personal identifiers from the first public sanctions layer;
- publish only the minimum entity fields needed for match evidence and provenance;
- never describe a non-match as `sanctions clear`, `compliant` or `safe`.

Interpretation boundary:

- only direct listed-entity evidence may be shown as a direct sanctions-list match;
- fuzzy similarity is review evidence, not a sanctions finding;
- ownership/control effects are separate legal facts and must not be inferred from name matching alone;
- absence of a direct match means only that no direct deterministic match was found in the pinned snapshot.

Attribution baseline:

`Source: European Commission, Consolidated Financial Sanctions File 1.1. Licensed under CC BY 4.0. Derived and transformed by Steel Exposure Atlas.`

Official references:

- https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions?locale=en
- https://webgate.ec.europa.eu/fsd/fsf#!/files
- https://commission.europa.eu/legal-notice_en
- https://creativecommons.org/licenses/by/4.0/
- https://finance.ec.europa.eu/publications/guidance-due-diligence_en

## EU TARIC

Publisher: European Commission, Directorate-General for Taxation and Customs Union.

TARIC is the official EU customs-tariff database and integrates Common Customs Tariff measures and related commercial/agricultural legislation. The Commission states that TARIC data are transmitted daily to Member State administrations.

For the atlas, the useful procurement fields would be commodity code, origin country, measure type, duty rate, validity dates and legal basis.

The current review has not yet pinned a clean bulk or machine-readable extract together with dataset-specific reuse terms. The general Commission CC BY 4.0 notice is not enough on its own under this project's governance rule when the exact dataset distribution has not been fixed.

**Decision:** reviewed; not approved for processing or publication until the exact extract/access method and reuse conditions are documented.

Official reference:

- https://taxation-customs.ec.europa.eu/online-services/online-services-and-databases-customs/eu-customs-tariff-taric_en

## Access2Markets

Access2Markets is highly useful as a human reference for tariffs and import requirements. It is not a suitable primary publication feed for this project because parts of the non-EU import-condition content are explicitly copyright-protected and geographically restricted.

**Decision:** rejected as a primary redistributable machine-data source. It may be cited or used manually to understand tariff logic, but no Access2Markets content is bundled into the atlas.

Official reference:

- https://trade.ec.europa.eu/access-to-markets/

## EEA EU ETS data from the Union Registry

Publisher: European Environment Agency, using data from the European Commission Union Registry.

The EEA Datahub provides downloadable EU ETS data, including entity-level records used to aggregate verified emissions and allowances. The EEA states that its reports, graphs and data can be reused for commercial and non-commercial purposes under its standard reuse policy with source acknowledgement unless otherwise indicated.

**Decision:** approved for processing and publication of a derived subset from a pinned EEA dataset snapshot, subject to attribution and facility matching evidence.

Intended interpretation:

- verified emissions are reported installation-level emissions context;
- they are not an ESG rating, supplier-risk score, product carbon footprint or forecast;
- a match from a steel plant to an ETS installation is a derived entity/facility match and must carry evidence/confidence.

Official references:

- https://www.eea.europa.eu/en/datahub/datahubitem-view/98f04097-26de-4fca-86c4-63834818c0c0
- https://www.eea.europa.eu/en/legal-notice

## EEA Industrial Emissions reporting dataset

The European Industrial Emissions Portal provides downloadable facility-level data on industrial complexes, pollutant releases, waste transfers and related reporting. EEA's standard reuse policy is permissive, but the dataset includes information reported and owned through national competent-authority systems.

**Decision:** approved for local processing; publication remains blocked until the exact dataset snapshot and its specific rights/metadata notice are checked.

Official references:

- https://industry.eea.europa.eu/industrial-emissions/dataset
- https://www.eea.europa.eu/en/legal-notice

## Product consequence

For a procurement-oriented atlas, source priority is now:

1. EU sanctions — approved source path for the next procurement-facing layer.
2. TARIC — landed-cost/trade-measure context after an exact reusable extract is identified.
3. EEA EU ETS — environmental operating context; useful but secondary to compliance and landed cost.
4. Water stress — optional resilience context, no longer a priority for the next release.

The sanctions UI must use language such as `Direct list match`, `No direct list match in this snapshot` and `Review required`. It must never show `sanctions clear`, `compliant` or an automatic red/green supplier verdict.
