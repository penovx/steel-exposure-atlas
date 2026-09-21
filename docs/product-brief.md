# Product brief

## Purpose

Steel Exposure Atlas is an interactive public-data study showing what becomes visible when steel production sites are connected to procurement-relevant context such as companies, products, production methods, sanctions, tariffs/trade measures and selected environmental signals.

The value is not to reproduce source databases. The atlas should shorten the path from scattered public facts to a defensible sourcing question or follow-up.

The output should be understandable in under a minute, visually strong enough to share as a portfolio piece, and transparent enough that a technically or commercially experienced reader can inspect where each statement came from.

## Intended audience

The primary reader is a decision-maker in procurement, supply chain, operations, sustainability or enterprise data who does not want another general-purpose data catalogue.

The interaction should allow the reader to begin with a place, company, plant, product or production method and follow the relationships that are actually supported by the source data.

## Interaction model

The product supports two complementary modes rather than treating every relationship as one visual chain:

1. **Overview** — understand the geographic distribution of the currently relevant steel-plant population and enter through company, plant, product or production method.
2. **Investigation** — inspect one named object, follow typed relationships to adjacent objects and see which external evidence applies and why.

The site is the primary bridge in the industrial model:

- **Company → Site** — which immediate company identity GEM records as owner/operator of the plant.
- **Site → Product** — which steel products the plant source description lists.
- **Site → Production method** — which methods have positive operating capacity at the plant and how much known operating capacity is reported.

The map provides geographic context and spatial distribution. It is not the relationship graph.

The procurement-facing layers are intentionally separate from these base relationships:

5. **Sanctions context** — reviewed direct company-identity evidence from the **EU consolidated financial sanctions list** and **U.S. OFAC lists**. EU and U.S. evidence remain separate; a non-match is never presented as sanctions clearance because ownership/control and other legal effects can affect unlisted entities.
6. **Tariff / trade-measure context** — origin- and product-dependent EU import measures only where an approved official source and a defensible product-family mapping exist. The first implementation candidate is the EU 2026 steel import measure under Regulation (EU) 2026/1384 and Commission Implementing Regulation (EU) 2026/1457.
7. **Environmental operating context** — selected facility-level public indicators such as verified emissions where a defensible plant-to-facility match exists.

Water stress remains a possible resilience layer but is not a priority for the next release.

## Relationship semantics

The visual model must not turn associations into stronger claims:

- plant ↔ company means the source provides one usable immediate owner/operator identity;
- plant ↔ product means the plant source description lists that product, not product-specific capacity, qualification or available supply;
- plant ↔ production method requires positive operating route capacity;
- production method ↔ product is **not** inferred from their coexistence at one plant; no method-to-product production relationship is shown unless a source explicitly establishes it;
- a sanctions connection means a reviewed company-identity match to a listed entity in a pinned sanctions-list snapshot;
- absence of a direct sanctions-list match does not mean the entity is compliant or unaffected by sanctions;
- EU steel trade-measure context is a scenario about possible import into the EU, not evidence that a plant exports to the EU;
- a GIST product label is not a CN/TARIC customs classification;
- tariff/quota context depends on product classification, origin, validity date and current quota state and must not be presented as plant-specific landed cost without those inputs;
- environmental indicators describe reported facility context, not an ESG score or disruption probability;
- country-level trade statistics do not identify a physical buyer-supplier route.

Sanctions are shown as categorical evidence states only. User-facing copy uses plain language such as `Listed by OFAC`, `Listed by the EU`, `Needs review` and `No direct listing found`, while the underlying data retains the technical evidence state. The product does not define a sanctions percentage, probability or risk score.

For trade measures, the evidence states must likewise distinguish source facts from mapping assumptions. A source product family, a derived family candidate and an actual customs classification are different things.

## First trade-measure use case

The initial question is deliberately narrow:

> If steel from this plant were imported into the EU, does its origin and listed product family point to a current EU steel-measure category that requires customs follow-up?

The useful chain is:

`plant -> origin country -> GIST product -> possible EU measure category -> quota structure -> procurement follow-up`

The layer may expose whether a named origin quota row exists and what additional duty applies if the relevant quota is exhausted. It must not claim live quota availability until a current quota-balance source is added.

The procurement value is the follow-up it creates: verify CN/TARIC classification, origin, applicable quota route and current quota balance before contracting/importing. It is not a tariff calculator.

## Visual direction

- premium editorial/intelligence presentation, not a generic dashboard;
- geography remains visually important, but the map serves distribution and location rather than carrying the full relationship model;
- companies, named sites, products and production methods remain directly interactive;
- selecting an object exposes one stable investigation surface without rearranging the surrounding composition;
- named sites are directly traversable from company views and act as the bridge to methods and products;
- visible relationships use explicit semantic types; line position alone must not define their meaning;
- procurement evidence appears adjacent to the actual company, site or derived relation it describes;
- dense relationships are reduced deterministically for legibility, never through hand-picked featured cases;
- progressive disclosure: global pattern first, named object and evidence detail after interaction;
- restrained controls and labels;
- country labels where useful;
- smooth motion only where it explains continuity;
- ordinary page scrolling must not be hijacked;
- reduced-motion preferences respected;
- no external fonts, runtime analytics or unnecessary third-party requests.

## Primary design acceptance task

Before public release, the interface must support this task without requiring the user to reconstruct relationships from the map:

> Start with a company, open a named site, understand its operating methods and listed products, and identify exactly which external evidence applies and why.

The same investigation must remain usable at a 390 px viewport. Compound filters must make their selected population and measure denominator explicit.

## Evidence model

Every material statement shown in the application should be classifiable as one of:

- **Source** — directly supported by a reviewed external dataset;
- **Derived** — calculated, matched or spatially joined from reviewed source data;
- **Scenario** — an explicit user or demonstrator assumption;
- **Open** — information that is not established by the available data.

Entity, facility and customs-product mapping must expose their evidence state. Fuzzy similarity or broad product-family overlap is a candidate for review, not a fact.

The public release should avoid composite supplier-risk, sanctions or ESG scores. It should expose the underlying evidence, procurement consequence and what remains unresolved.

## Non-goals

This project is not:

- a supplier qualification or sanctions-compliance service;
- a customs-classification or tariff-calculation service;
- a production-ready sourcing, tariff or ESG platform;
- a real-time disruption monitor;
- a claim that public data can reconstruct a company's supplier network;
- a substitute for legal, customs or supplier due diligence;
- a vehicle for proprietary or employer data;
- an endorsement of any data publisher or technology provider.

## Source rule

Only sources that pass `docs/source-governance.md` may enter the public product. Public accessibility alone is insufficient. Dataset-specific reuse rights, cost, attribution, snapshot/version and interpretation boundaries must be documented before publication.

## Publication

The intended public format is a static website that can be linked from a short LinkedIn screen recording. GitHub Pages may be used only after the release checklist is complete.
