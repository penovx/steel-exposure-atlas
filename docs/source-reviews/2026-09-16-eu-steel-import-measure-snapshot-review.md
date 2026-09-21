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

## Regulation 2026/1930 snapshot

Local fetch completed on 2026-09-16.

- source: official EUR-Lex HTML for Commission Implementing Regulation (EU) 2026/1930
- retrieved at: `2026-09-16T17:44:31+00:00`
- SHA-256: `5F0214CD0FC9FC85A114B9EC485E2D6887F3F2137BD177EE357CC00FE2BB32BE`
- bytes: `351,592`
- bilateral safeguard origins parsed: `9`
- additional duty rate parsed: `50%`
- effective from: `2026-08-06`

Both raw EUR-Lex snapshots remain local. Only reviewed minimal derived context is eligible for `public/data/`.

## GIST profile result

Against 1,293 GIST plants:

- EU-origin plants: `124`
- exempt non-EU EEA origins: `1`
- plants with at least one supported product-family candidate: `764`
- candidate plants with a named origin quota row: `482`
- candidate plants requiring pooled/residual quota interpretation: `282`
- plants without a supported product-family candidate: `404`
- plants from bilateral-safeguard origins: `41`
- bilateral-origin plants with a supported product-family candidate: `38`

The compact decision-context builder therefore emits `764` plant rows:

- `482` with origin-specific quota context;
- `282` with pooled/residual quota context.

These counts establish useful overlap between the reviewed legal sources and GIST product/origin context. They do not convert broad GIST product labels into transaction-level customs classifications.

## Publication decision

**Approved for publication of a minimal derived EU steel import-context layer.**

Publication controls:

- preserve both source SHA-256 values and regulation identifiers in metadata;
- expose the layer as an `if imported into the EU` scenario, not evidence of actual EU trade;
- expose useful evidence, meaning and procurement follow-up rather than technical non-actions;
- do not present a plant-specific tariff amount, landed-cost estimate or quota-availability verdict without transaction-specific evidence;
- retain customs-code / legal-route detail as evidence where it supports the user decision, not as primary UI clutter.
