# Initial source review — 2026-09-14

This review records whether candidate data sources are suitable for a public, independently published portfolio demonstrator. The project treats that use as **commercial-capable** for review purposes because it may support professional self-promotion.

This is a project governance review, not legal advice. Unresolved rights, attribution or access conditions block publication by default.

## Decision summary

| Source | Decision | Cost | Reason |
| --- | --- | --- | --- |
| Natural Earth 1:110m Admin 0 Countries v5.1.1 | Approved for publication | Free | Public-domain map data; modification and redistribution allowed. |
| Global Energy Monitor — Global Iron and Steel Tracker, June 2026 (V1) | Reviewed; package retrieval required before publication | Free | GEM states tracker data are available under CC BY 4.0 unless otherwise noted; exact downloaded package and attribution elements still need to be checked. |
| WRI Aqueduct 4.0 Current and Future Global Maps Data | Reviewed; package retrieval and sharing/registration step required before publication | Free | WRI states Aqueduct is CC BY 4.0 and allows sharing/adaptation with attribution; WRI asks users sharing or adapting data to register. |
| Eurostat Comext | Reviewed; not approved yet | Free | Eurostat generally permits reuse with attribution but lists commercial-reuse exceptions relevant to country and trade data. The exact table and output must be checked before use. |

## Natural Earth

**Selected scope:** 1:110m Admin 0 — Countries, version 5.1.1.

Natural Earth states that all raster and vector map data on its site are in the public domain and may be used, modified and redistributed for personal, educational and commercial purposes. Attribution is not required.

The selected country layer uses de facto boundaries. The project must therefore treat disputed-boundary presentation as a design and interpretation issue rather than silently presenting the geometry as a legal or political claim.

**Decision:** approved for the specified file and version.

Official references:

- https://www.naturalearthdata.com/about/terms-of-use/
- https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/

## Global Energy Monitor — Global Iron and Steel Tracker

The current tracker page identifies the most recent release as March 2026 with a limited quarterly update in June 2026 and recommends the citation `Global Iron and Steel Tracker, Global Energy Monitor, June 2026 (V1) release.` The publisher's tracker licensing material states that GEM tracker data are available under CC BY 4.0 unless otherwise noted.

The intended project use is limited to fields such as plant location, ownership, operating status, steel/iron production method and capacity. Linked wiki text, images and underlying third-party references are not assumed to inherit the tracker-data licence.

**Decision:** reviewed and suitable in principle, but do not bundle or publish GIST records until the exact download package has been obtained and its included attribution and any exceptions have been checked.

Official references:

- https://globalenergymonitor.org/projects/global-iron-steel-tracker/
- https://globalenergymonitor.org/creative-commons-license

## WRI Aqueduct 4.0

WRI states that Aqueduct products, methodologies and datasets are available under CC BY 4.0. Its FAQ explicitly allows sharing, reproducing and adapting Aqueduct data with attribution and asks users who adapt or share the data to register with WRI. The current WRI Data Explorer record for Aqueduct 4.0 was last updated on 2026-09-10.

Aqueduct is a screening and prioritisation source. A high baseline water-stress classification must not be translated into an outage probability, supplier-failure statement or site-specific resilience conclusion.

**Decision:** reviewed and suitable in principle, but publication remains blocked until the exact package is retrieved, the requested registration/sharing step is completed, fields are selected and attribution is implemented.

Official references:

- https://www.wri.org/data/aqueduct-global-maps-40-data
- https://www.wri.org/aqueduct/faq

## Eurostat Comext

Eurostat generally permits commercial and non-commercial reuse of statistical data with attribution, but its copyright notice lists exceptions. Relevant examples include restrictions on commercial reuse of certain data concerning countries outside the EU/EFTA/accession-candidate group and specific trade data originating from Switzerland, Liechtenstein and Austria.

Because the atlas may display extra-EU steel trade and is intended as a public professional showcase, the project will not rely on the general reuse statement alone.

**Decision:** not approved for publication until the exact Comext datacode, declaring geography, partner scope, product classification, aggregation and intended published output are selected and checked against the listed exceptions.

Official reference:

- https://ec.europa.eu/eurostat/help/copyright-notice

## Publication gates created by this review

1. Only Natural Earth v5.1.1 is currently approved for inclusion in `public/data/`.
2. No GIST or Aqueduct record is committed to the public repository until its exact package is reviewed.
3. No Comext output is published until the exact dataset selection passes a commercial-capable reuse review.
4. Attribution text must be generated from the approved source registry rather than typed ad hoc in the UI.
5. A source's factual scope constrains wording in the interface; visual prominence does not justify stronger claims.
