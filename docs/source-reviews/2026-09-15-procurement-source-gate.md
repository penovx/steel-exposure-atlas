# Procurement-facing source gate — 2026-09-15

This review applies the project source-governance rules to procurement-oriented data sources: sanctions, tariffs/trade measures and environmental/ESG context.

The public atlas is reviewed as commercial-capable professional use. Public accessibility alone is not enough; unclear redistribution rights block publication by default.

## Current jurisdiction scope

The sanctions package for the atlas is intentionally limited to:

1. **European Union** — primary sanctions jurisdiction for the European procurement perspective.
2. **United States / OFAC** — second sanctions jurisdiction for global procurement context.

The UK Sanctions List is outside the current product scope and must not be ingested, matched or shown in the UI unless the product scope is explicitly changed later.

## Decision summary

| Source | Decision | Cost | Intended use |
| --- | --- | --- | --- |
| EU consolidated financial sanctions list | Approved for processing; publication blocked pending dataset-specific licence confirmation | Free | Primary EU sanctions-list screening context |
| OFAC SDN and Consolidated Non-SDN files | Approved for processing; publication blocked pending explicit redistribution basis | Free | US-jurisdiction sanctions-list screening context |
| EU TARIC | Reviewed; not approved yet | Free | Import-duty and trade-measure context |
| Access2Markets | Rejected as primary redistributable data feed | Free | Reference only; not a publication source |
| EEA EU ETS data from the Union Registry | Approved for processing and publication of a derived subset | Free | Facility-level verified-emissions context |
| EEA Industrial Emissions reporting dataset | Approved for processing; publication pending dataset-specific rights check | Free | Facility-level environmental context |

## EU consolidated financial sanctions list

Publisher: European Commission, Directorate-General for Financial Stability, Financial Services and Capital Markets Union.

The official consolidated financial sanctions dataset is available through the Commission sanctions portal and the European data portal in CSV and XML formats and is updated on a daily basis. The Commission's general reuse notice applies CC BY 4.0 to EU-owned Commission website content unless a more specific notice applies.

However, the European data portal explicitly states that dataset-specific licence information governs individual resources and that, where licence information is missing, the original portal conditions must be checked. The sanctions dataset catalogue record exposes the distributions and public access but does not currently give us a sufficiently explicit distribution-level reuse statement for this project's publication gate.

**Decision:** approved for local processing and matching research; **not yet approved for publication**. Publication requires pinning the exact CSV/XML distribution and confirming its dataset-specific reuse basis.

Interpretation boundary:

- only direct listed-entity evidence may be shown as a direct sanctions-list match;
- ownership/control effects are separate legal facts and must not be inferred from name matching alone;
- the UI must never label a non-match as `clear` or `compliant`.

Official references:

- https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions?locale=en
- https://webgate.ec.europa.eu/fsd/fsf#!/files
- https://commission.europa.eu/legal-notice_en
- https://finance.ec.europa.eu/publications/guidance-due-diligence_en

## OFAC sanctions files

Publisher: U.S. Department of the Treasury, Office of Foreign Assets Control.

OFAC publishes SDN and Consolidated Non-SDN data in XML, CSV and other formats. OFAC states that anyone may use the advanced XML files and publishes file hashes for integrity checking.

That is sufficient for local technical evaluation, but this review did not find an explicit dataset-level redistribution licence comparable to CC BY or OGL.

**Decision:** approved for local processing; public redistribution or bundling remains blocked until the reuse/redistribution basis is pinned explicitly.

Interpretation boundary:

- a direct OFAC list match is evidence about the pinned OFAC source snapshot, not a complete legal conclusion;
- sectoral or ownership/control effects must not be inferred from name matching alone;
- the UI must never label a non-match as `clear`, `compliant` or `safe`.

Official references:

- https://ofac.treasury.gov/sdn-list-data-formats-data-schemas/frequently-asked-questions-on-advanced-sanctions-list-standard
- https://ofac.treasury.gov/specially-designated-nationals-list-sdn-list/hash-values-for-ofac-sanctions-list-files

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

1. EU sanctions — primary legal/compliance context once the publication licence gate is closed.
2. US OFAC sanctions — second legal/compliance jurisdiction once the redistribution gate is closed.
3. TARIC — landed-cost/trade-measure context after an exact reusable extract is identified.
4. EEA EU ETS — environmental operating context; useful but secondary to compliance and landed cost.
5. Water stress — optional resilience context, no longer a priority for the next release.

The sanctions UI must identify jurisdiction explicitly and use language such as `Direct list match`, `No direct list match in this snapshot` and `Review required`. It must never show `sanctions clear`, `compliant` or an automatic red/green supplier verdict.
