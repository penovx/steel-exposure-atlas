# EU steel bilateral safeguard review — 2026-09-16

## Decision

**Approved for local processing. Public publication remains conditional on pinning and fingerprinting the exact EUR-Lex snapshot through the project fetch pipeline.**

This review supplements `2026-09-16-eu-steel-import-measure-review.md`.

## Why this additional source is needed

Regulation (EU) 2026/1384 establishes the general steel tariff-quota framework, but Article 2(5)(b) excludes origins for which bilateral safeguard measures apply under Article 6.

Commission Implementing Regulation (EU) 2026/1930 is therefore required to describe the current legal route for the affected free-trade-agreement origins rather than treating them as ordinary third-country cases under Article 2 of Regulation 2026/1384.

## Official source

Publisher: European Commission.

Title: `Commission Implementing Regulation (EU) 2026/1930 of 4 August 2026 on the implementation of bilateral safeguard measures on imports of steel products covered by Regulation (EU) 2026/1384 ...`

Official ELI:

- https://eur-lex.europa.eu/eli/reg_impl/2026/1930/oj/eng

Relevant source facts checked on 2026-09-16:

- the measure covers the same 26 steel product categories defined in Annex I of Regulation 2026/1384;
- Article 1 applies bilateral safeguard measures to steel products originating in **Albania, Israel, Jordan, Morocco, North Macedonia, Serbia, Switzerland, Tunisia and Türkiye**;
- the measure uses an **out-of-quota duty of 50% ad valorem**;
- the duty applies after the applicable tariff quota distributed under Implementing Regulation 2026/1457 has been exhausted, whether that quota is country-specific or accessed in competition with other countries;
- Article 2 applies Union non-preferential-origin rules for determining origin;
- the Regulation entered into force on the day following its publication in the Official Journal on 5 August 2026, therefore **6 August 2026**.

## Product consequence

For the atlas, this source changes legal provenance, not the product UX hierarchy.

A user should still see a simple EU-import scenario such as:

- relevant EU steel measure;
- origin;
- product-family candidate;
- applicable quota route;
- additional duty if the relevant quota is exhausted;
- procurement follow-up.

The UI should not force the user to understand whether the legal route comes from Article 2 of Regulation 2026/1384 or a bilateral safeguard under Regulation 2026/1930. That distinction belongs in evidence detail and provenance unless it materially changes the decision.

## Derived-model rule

The trade profile must preserve one of these legal routes for non-EU origin plants:

- `steel_regulation_2026_1384`;
- `bilateral_safeguard_2026_1930`;
- `eea_exempt_origin`;
- `intra_eu_origin`.

The legal route is a source/derived evidence field. It is not a risk score.

## Reuse / publication

The same project policy used for the other EUR-Lex steel-measure source applies:

- raw Official Journal content remains local;
- publish only minimal derived fields needed by the atlas;
- identify the European Union / European Commission and exact regulation;
- preserve retrieval date and SHA-256;
- link to the official ELI;
- stop publication if a conflicting source-specific reuse notice is found.

The exact 2026/1930 bytes have not yet been fingerprinted by the local pipeline at the time of this review, so public publication is not yet approved.
