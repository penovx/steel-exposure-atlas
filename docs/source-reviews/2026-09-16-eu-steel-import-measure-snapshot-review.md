# EU steel import measure snapshot review — 2026-09-16

## Regulation 2026/1457 snapshot

Local fetch completed on 2026-09-16.

- source: official EUR-Lex HTML for Commission Implementing Regulation (EU) 2026/1457
- retrieved at: `2026-09-16T17:15:49+00:00`
- SHA-256: `B869A4BB8C4E4F7AE320B4CE4A117A33B05CADEEDF1C9DF106845EBCA9D9B21B`
- bytes: `1,075,406`
- legal product categories: `26`
- Annex-I product numbers: `30`
- parsed allocation rows: `283`
- additional duty rate in parsed rows: `50%`
- current allocation validity represented by the source: `2026-07-01` through `2026-12-31`

The raw EUR-Lex snapshot remains local. The derived parser output is a review artifact, not yet a published website layer.

## First GIST profile result

Against 1,293 GIST plants:

- EU-origin plants: `124`
- exempt non-EU EEA origins: `1`
- plants with at least one supported product-family candidate: `764`
- candidate plants with a named origin quota row: `482`
- candidate plants requiring pooled/residual quota interpretation: `282`
- plants without a supported product-family candidate: `404`

These counts establish that the source and GIST product vocabulary overlap sufficiently for a useful scenario layer. They do not establish customs classification for individual plant products.

## Publication gate still open

Commission Implementing Regulation (EU) 2026/1930 must also be pinned because it provides the current bilateral-safeguard legal route for nine FTA origins. Until that source snapshot is fetched and fingerprinted, the combined trade layer remains local-review only.
