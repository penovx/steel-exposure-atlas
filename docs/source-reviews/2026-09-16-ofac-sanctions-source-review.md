# OFAC sanctions source review — 2026-09-16

## Purpose

Assess the U.S. Department of the Treasury Office of Foreign Assets Control (OFAC) sanctions-list data for use as a second sanctions-evidence layer in Steel Exposure Atlas.

The intended use is narrow: resolve GEM company identities against official OFAC list identities and publish only the minimum evidence needed to support a reviewed direct-list result. The atlas is not a sanctions-compliance service and must not convert list evidence into a supplier-risk score.

## Sources in scope

Two official OFAC datasets are in scope:

1. **Specially Designated Nationals and Blocked Persons List (SDN List)**
2. **Consolidated Non-SDN Sanctions List**

OFAC's Sanctions List Service (SLS) is the current official distribution service for both lists and offers machine-readable downloads. OFAC also provides a customization tool and a sanctions-list search interface, but the atlas should use pinned downloadable files rather than a live runtime API.

For the first ingestion version, use the basic XML files:

- `SDN.XML`
- `CONSOLIDATED.XML`

The advanced XML format is not required for the first company-identity screening layer. OFAC states that its XML products contain the same core sanctions-list data, while the advanced format adds richer metadata. Keeping the first parser on the basic XML reduces implementation complexity and avoids an unnecessary 100+ MB advanced source file.

## Official endpoints

- SDN XML: `https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML`
- Consolidated XML: `https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/CONSOLIDATED.XML`
- Basic XML schema: `https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML.xsd`
- SLS overview: `https://ofac.treasury.gov/sanctions-list-service`

The SLS download endpoints redirect to short-lived publication objects. The project must store the stable OFAC endpoint, retrieval timestamp, final transport URL, file size and its own SHA-256 fingerprint rather than persisting or documenting a temporary signed object URL as the canonical source.

## Access and cost

- Public download; no account or API key is required for the listed file downloads.
- No paid or metered service is required.
- Runtime access is unnecessary: snapshots should be downloaded during the controlled local build/review process.

## Reuse decision

The official Data.gov catalogue records for both the OFAC SDN List and Consolidated Non-SDN Sanctions List identify the datasets as public and specify **CC0 1.0 Universal** as the licence.

This is also consistent with the general U.S. rule in 17 U.S.C. §105 that copyright protection under U.S. copyright law is not available for works of the United States Government, subject to the statute's limits and exceptions.

### Project decision

- **Processing:** approved.
- **Publication of a reviewed minimal derived subset:** approved.
- **Raw OFAC files in `public/data/`:** not planned. Keep them local even though the reuse basis is broad.

The public output should contain only fields required to explain the displayed evidence, for example source list, OFAC UID, reviewed matched name/alias, program tag(s), snapshot date and project identity-resolution state.

The project should identify OFAC / U.S. Department of the Treasury as the source for provenance even though CC0 does not require attribution.

## Integrity and freshness

OFAC states that SLS provides current sanctions-list data for immediate download. OFAC also publishes hash values or file signatures to help users confirm that sanctions-list files have not been altered.

The atlas ingestion must independently calculate SHA-256 for every retrieved source file and retain:

- stable source endpoint;
- retrieval timestamp;
- source-reported publication date where present;
- local SHA-256;
- byte size;
- HTTP content type, final URL, ETag and Last-Modified where available.

The project must never equate retrieval time with source-effective time when the file exposes a separate publication date.

## Interpretation boundary

### SDN and Non-SDN are not one legal state

The SDN List is a blocking list in general terms, but specific treatment still depends on the applicable program and legal authority. The Consolidated Non-SDN file contains records from lists whose restrictions do not necessarily entail blocking.

Therefore the atlas must preserve at least:

- source list (`SDN` or `Consolidated Non-SDN`);
- OFAC UID;
- program/list tag(s);
- direct matched name or alias;
- snapshot provenance.

Do not flatten all OFAC records into a generic `sanctioned = true` field without retaining the underlying list/program evidence.

### No direct match is not sanctions clearance

OFAC's 50 Percent Rule states that property and interests in property of entities owned directly or indirectly, in the aggregate, 50 percent or more by one or more blocked persons are considered blocked. Such an entity may therefore be affected even when it is not separately named on the SDN List.

The first atlas layer performs **direct official-list identity screening only**. It does not establish ownership-rule clearance.

Permitted public evidence states remain:

- `Direct list match`
- `Review required`
- `No direct list match in this snapshot`

Never use `clear`, `compliant`, `safe`, `not sanctioned` or an equivalent conclusion for a non-match.

## First matching scope

The first GEM-to-OFAC pass should be company/entity-only.

For the basic XML structure, preserve and profile:

- `uid`;
- primary name components;
- `sdnType`;
- `programList`;
- aliases from `akaList` including OFAC alias category where available;
- address/country context when available;
- identifier records when useful for manual review.

Exclude `Individual`, `Vessel` and `Aircraft` records from automatic company candidate generation. They remain part of the local source snapshot but should not be candidates for a GEM company identity match.

Name similarity alone is not confirmation. Candidate generation may use normalized names, aliases and context; publication requires the same reviewed identity-resolution discipline already used for the EU layer.

## Why basic XML first

OFAC's legacy relational flat files require multiple linked files for a complete record. OFAC explicitly warns that downloading only one CSV file can omit aliases, addresses or other list content.

The basic XML files keep the core screening fields in one source document per list. OFAC states that the advanced XML format contains the same core list data plus additional metadata. For the current atlas requirement, the basic XML therefore provides the cleaner dependency boundary.

Advanced XML remains a future option if the atlas later needs metadata that the basic XML cannot support.

## Gate result

**PASS for controlled ingestion and profiling.**

The next step is to retrieve both official XML files locally, fingerprint them, profile entry types/programs/aliases and review the real snapshot before any GEM matching is added.

No OFAC source content should enter `public/data/` during this snapshot/profile step.

## Official references

- https://ofac.treasury.gov/sanctions-list-service
- https://ofac.treasury.gov/sdn-list-data-formats-data-schemas/frequently-asked-questions-on-advanced-sanctions-list-standard
- https://ofac.treasury.gov/sdn-list-data-formats-data-schemas/tutorial-on-the-use-of-list-related-legacy-flat-files
- https://ofac.treasury.gov/specially-designated-nationals-list-sdn-list/hash-values-for-ofac-sanctions-list-files
- https://ofac.treasury.gov/faqs/topic/1521
- https://catalog.data.gov/dataset/specially-designated-nationals-sdn-and-blocked-persons-list
- https://catalog.data.gov/dataset/consolidated-non-sdn-sanctions-list
- https://uscode.house.gov/view.xhtml?req=(title:17%20section:105%20edition:prelim)
