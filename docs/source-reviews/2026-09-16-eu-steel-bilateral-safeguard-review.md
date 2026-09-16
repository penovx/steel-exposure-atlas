# EU steel bilateral safeguard review — 2026-09-16

## Decision

**Approved for publication of a minimal derived context layer.**

This review supplements `2026-09-16-eu-steel-import-measure-review.md` and records the exact snapshot that closes the remaining publication condition.

## Why this additional source is needed

Regulation (EU) 2026/1384 establishes the general steel tariff-quota framework, but Article 2(5)(b) excludes origins for which bilateral safeguard measures apply under Article 6.

Commission Implementing Regulation (EU) 2026/1930 is therefore required to describe the current legal route for the affected free-trade-agreement origins rather than treating them as ordinary third-country cases under Article 2 of Regulation 2026/1384.

## Official source

Publisher: European Commission.

Title: `Commission Implementing Regulation (EU) 2026/1930 of 4 August 2026 on the implementation of bilateral safeguard measures on imports of steel products covered by Regulation (EU) 2026/1384 ...`

Official ELI:

- https://eur-lex.europa.eu/eli/reg_impl/2026/1930/oj/eng

## Pinned snapshot

Local fetch completed on 2026-09-16.

- retrieved at: `2026-09-16T17:44:31+00:00`
- SHA-256: `5F0214CD0FC9FC85A114B9EC485E2D6887F3F2137BD177EE357CC00FE2BB32BE`
- bytes: `351,592`
- bilateral safeguard origins parsed: `9`
- additional duty rate parsed: `50%`
- effective from: `2026-08-06`

The raw EUR-Lex snapshot remains local. Only minimal derived legal-route/context fields may be published.

## Relevant source facts

The reviewed source establishes that:

- the measure covers the same steel product framework defined by Regulation (EU) 2026/1384;
- Article 1 applies bilateral safeguard measures to steel products originating in **Albania, Israel, Jordan, Morocco, North Macedonia, Serbia, Switzerland, Tunisia and Türkiye**;
- the measure uses an **out-of-quota duty of 50% ad valorem**;
- the duty applies after the applicable tariff quota distributed under Implementing Regulation 2026/1457 has been exhausted, whether that quota is country-specific or accessed in competition with other countries;
- Article 2 applies Union non-preferential-origin rules for determining origin;
- the Regulation entered into force on **6 August 2026**.

## Product consequence

For the atlas, this source changes legal provenance, not the primary UX hierarchy.

A user-facing EU-import context may expose:

- relevant EU steel measure;
- origin;
- product-family candidate;
- applicable quota route;
- additional duty if the relevant quota is exhausted;
- procurement follow-up.

The UI should not require the user to interpret whether the legal route comes from Article 2 of Regulation 2026/1384 or a bilateral safeguard under Regulation 2026/1930 unless that distinction materially changes the decision. The route remains available in evidence/provenance.

## Derived-model rule

The trade profile preserves one of these legal routes:

- `steel_regulation_2026_1384`;
- `bilateral_safeguard_2026_1930`;
- `eea_exempt_origin`;
- `intra_eu_origin`.

The legal route is evidence/provenance, not a risk score.

## Reuse / publication

Project publication policy:

- raw Official Journal content remains local;
- publish only minimal derived fields needed by the atlas;
- identify the European Union / European Commission and exact regulation;
- preserve retrieval date and SHA-256;
- link to the official ELI;
- stop publication if a conflicting source-specific reuse notice is found.

The exact source bytes are now pinned and fingerprinted. Together with the reviewed Commission reuse basis, this closes the source-specific publication condition for a minimal derived trade-context layer.
