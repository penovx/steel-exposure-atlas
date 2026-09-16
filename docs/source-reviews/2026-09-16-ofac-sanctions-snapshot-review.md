# OFAC sanctions snapshot review — 2026-09-16

## Purpose

Record the first real local Steel Exposure Atlas snapshot of the official U.S. Department of the Treasury Office of Foreign Assets Control sanctions lists before company matching.

The raw files remain local under the ignored `tmp/source-packages/ofac/` path. This review records provenance and source structure only; it is not a sanctions finding for any steel company.

## Retrieval

- Retrieval timestamp: `2026-09-16T15:47:54+00:00`
- Distribution service: OFAC Sanctions List Service
- Format: basic OFAC XML
- Raw files: local only; not committed and not published in `public/data/`

## SDN List snapshot

- Dataset: Specially Designated Nationals and Blocked Persons List
- Stable source endpoint: `https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML`
- Source publish date: `09/16/2026`
- SHA-256: `3D594ED7CDB5E0FD13F126A3815255146D730F791DCF672665C67416D03A7C1F`
- Raw size: `29,076,910` bytes
- Entries: `19,385`
- Unique UIDs: `19,385`
- Aliases: `24,615`

### SDN entry types

| Type | Entries |
| --- | ---: |
| Entity | 9,972 |
| Individual | 7,531 |
| Vessel | 1,540 |
| Aircraft | 342 |

Only `Entity` records enter the first GEM-company candidate screen. Individual, Vessel and Aircraft records remain part of the local source snapshot but are excluded from automatic company matching.

## Consolidated Non-SDN snapshot

- Dataset: Consolidated Non-SDN Sanctions List
- Stable source endpoint: `https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/CONSOLIDATED.XML`
- Source publish date: `09/14/2026`
- SHA-256: `C59772F3EDD625812AC43C4AEC57513D08CDD180135A3B6368DBC086AB81DF7D`
- Raw size: `1,062,957` bytes
- Entries: `481`
- Unique UIDs: `481`
- Aliases: `1,186`

### Consolidated entry types

| Type | Entries |
| --- | ---: |
| Entity | 363 |
| Individual | 118 |

No Vessel or Aircraft records were reported by the first profile for this snapshot.

## Combined company-screening population

The first Entity-only transformation therefore starts from:

- `9,972` SDN Entity records;
- `363` Consolidated Non-SDN Entity records;
- `10,335` Entity records in total before any cross-list deduplication or GEM matching.

The two lists retain separate source identities. A UID is not assumed to be globally unique across the two datasets; derived entity IDs are prefixed by source list.

## Freshness observation

The SDN source publish date matches the retrieval date. The Consolidated Non-SDN source publish date is two calendar days earlier.

The atlas must preserve source publish date and retrieval timestamp separately. Retrieval on a given day is not treated as evidence that every source list was generated that same day.

## Interpretation boundary

- SDN and Consolidated Non-SDN records are not collapsed into one legal-effect flag.
- A direct list identity match is evidence that the reviewed company identity corresponds to an official list record in this snapshot.
- A non-match is not sanctions clearance.
- OFAC ownership rules can affect entities not separately named on the SDN List.
- Name similarity alone is not confirmation.
- No fuzzy matching is used in the first candidate profile.

## Next gate

1. derive an Entity-only local subset from both XML snapshots;
2. preserve primary names, aliases, OFAC UID, source list, program tags, countries, addresses and identifiers needed for review;
3. compare GEM immediate-owner identities using conservative normalized-name and legal-form candidate generation;
4. report candidate counts and affected plant counts;
5. manually review any candidate before a public `Direct list match` is produced.

## Related source review

See `docs/source-reviews/2026-09-16-ofac-sanctions-source-review.md` for source, reuse and publication decisions.
