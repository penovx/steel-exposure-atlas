# EU steel import measure source review — 2026-09-16

## Decision

**Approved for local processing. Public publication of a minimal derived measure layer is conditional on pinning and fingerprinting the exact EUR-Lex source snapshot produced by the fetch pipeline.**

The first trade layer will use the current EU steel import measure as a bounded procurement scenario. It will not present a generic tariff score and will not imply that a GIST plant exports to the EU.

## Intended product use

Scenario question:

> If steel from this plant were imported into the EU, does the plant's origin and listed product family point to a current EU steel-measure category that requires customs follow-up?

The useful relationship is:

`plant -> origin country -> GIST product label -> possible EU measure category -> quota structure -> procurement follow-up`

The layer must distinguish source facts from derived product-family mapping. A GIST product label is not a CN/TARIC classification.

## Official legal sources

### Regulation (EU) 2026/1384

Publisher: European Parliament and Council of the European Union.

Title: `Regulation (EU) 2026/1384 ... addressing the negative trade-related effects of global overcapacity on the Union steel market`.

Official ELI:

- https://eur-lex.europa.eu/eli/reg/2026/1384/oj/eng

Relevant source facts checked on 2026-09-16:

- the Regulation applies from **1 July 2026**;
- annual tariff quotas are opened for the product categories in Annex I;
- imports in a covered product category are subject to a **50% ad valorem out-of-quota duty** when the applicable quota is exhausted or the imports do not benefit from a quota;
- Iceland, Liechtenstein and Norway are excluded from the Article 2 quota/duty mechanism;
- product scope is defined by CN/TARIC classification, not by commercial product labels;
- the `melt and pour` evidence requirement in Article 4(1) applies from **1 October 2026**, so it must not be presented as already applicable before that date.

### Commission Implementing Regulation (EU) 2026/1457

Publisher: European Commission.

Title: `Commission Implementing Regulation (EU) 2026/1457 ... on the distribution of tariff quotas opened under Regulation (EU) 2026/1384`.

Official ELI:

- https://eur-lex.europa.eu/eli/reg_impl/2026/1457/oj/eng

Relevant source facts checked on 2026-09-16:

- legal status shown by EUR-Lex: **in force**;
- the implementing regulation applies from **1 July 2026 to 31 December 2026**;
- it distributes quotas for the 26 legal product categories defined by the Steel Regulation;
- Annex I exposes product number, product-category description, CN/TARIC codes, country/allocation row, annual and quarterly quota volumes, additional duty rate and customs order number;
- all quota rows in the current Annex I use a 50% additional duty rate;
- quota access can be country-specific, FTA-related or residual and is administered on a first-come, first-served basis.

The Annex table contains split product numbers such as `1.A` / `1.B`, `3.A` / `3.B`, `4.A` / `4.B` and `25.A` / `25.B`. UI copy must therefore avoid casually equating the number of displayed product-number rows with the legal count of product categories.

## Why this source is preferable to generic TARIC for the first trade layer

The earlier source gate left TARIC unapproved because no exact reusable extract had been pinned. Regulation 2026/1457 is narrower but directly answers a useful steel-specific question and contains the current product/category/origin quota structure in one authoritative legal source.

TARIC remains relevant later for a transaction-grade customs lookup. It is not required for this first scenario layer.

## Reuse / publication assessment

The European Commission legal notice states that EU-owned Commission website content is reusable under **CC BY 4.0** unless otherwise indicated, with attribution and indication of changes. The Commission reuse policy is implemented through Commission Decision 2011/833/EU.

References:

- https://commission.europa.eu/legal-notice_en
- https://eur-lex.europa.eu/eli/dec/2011/833/oj/eng

Project publication policy:

- do not republish the full Official Journal document;
- keep the downloaded source snapshot local;
- publish only the minimal derived fields needed for the atlas;
- identify the European Union / European Commission and the exact regulation as source;
- record retrieval timestamp and SHA-256;
- link back to the official ELI;
- stop publication if a source-specific conflicting reuse notice is discovered.

Because the exact fetched bytes have not yet been fingerprinted in the repository workflow, publication remains conditional until the fetch step is run and reviewed.

## Interpretation boundaries

The atlas may say:

- `EU steel import measure — possible product-category match`;
- `Country-specific quota row exists for this origin and category`;
- `Additional duty if the applicable quota is exhausted: 50%`;
- `Customs classification required`;
- `If imported into the EU`.

The atlas must not say, based only on GIST:

- `this plant is subject to a 50% tariff`;
- `this supplier has X% tariff exposure`;
- `quota is available` or `quota is exhausted` without current quota-balance evidence;
- `this product is definitely CN code ...`;
- `this plant exports to the EU`;
- `landed cost increases by 50%`.

## Product mapping rule

GIST uses broad plant-level product descriptions. The EU measure uses CN/TARIC codes. Therefore product mapping has three evidence states:

1. `family_candidate` — the GIST label points clearly to one legal product family, but CN/TARIC classification is still required;
2. `ambiguous_family_candidate` — the GIST label can correspond to multiple measure categories;
3. `no_supported_mapping` — the current GIST label does not support a defensible mapping.

No state is equivalent to a customs classification.

## First profile objective

Before any UI is added, profile the 1,293 GIST plants and answer:

- how many non-EU plants have at least one product-family candidate;
- which GIST product labels produce a one-family vs multi-family candidate;
- how many candidates have an explicit country row in Regulation 2026/1457;
- how many require residual-quota interpretation;
- which plants are in the EU or the exempt EEA origins and therefore should not be presented as an EU-import duty scenario.
