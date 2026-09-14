# Product brief

## Purpose

Steel Exposure Atlas is a small interactive study showing what becomes visible when independently published datasets about steel production, trade, water stress and legal entities are connected carefully.

The output should be understandable in under a minute, visually strong enough to share as a portfolio piece, and transparent enough that a technically or commercially experienced reader can inspect where each statement came from.

## Intended audience

The primary reader is a decision-maker in procurement, supply chain, operations, sustainability or enterprise data who does not want another general-purpose data catalogue. The atlas should lead with questions that matter to that reader and let the evidence remain inspectable underneath.

## Interaction model

The same map evolves as the user changes the question. The first release is expected to move through four views:

1. **Production** — where tracked crude-steel capacity is located and how production methods differ.
2. **Trade** — how selected steel product groups are distributed across EU import origins at country level.
3. **Water** — where tracked production sites overlap basin-level water-stress screening indicators.
4. **Ownership** — how selected plant owners relate to legal entities or parent relationships where a defensible match can be made.

The views must not imply that country-level trade identifies a physical route or that a legal-entity match proves a buyer-supplier relationship.

## Visual direction

- full-screen map as the primary object, not a dashboard of tiles;
- progressive disclosure: global pattern first, site detail only after interaction;
- restrained controls and labels;
- smooth continuity between views rather than separate dashboard pages;
- mobile interaction designed intentionally, not treated as a shrunk desktop layout;
- sources and evidence reachable from the view without dominating it.

## Evidence model

Every material statement shown in the application should be classifiable as one of:

- **Source** — directly supported by a reviewed external dataset;
- **Derived** — calculated or spatially joined from reviewed source data;
- **Scenario** — an explicit user or demonstrator assumption;
- **Open** — information that is not established by the available data.

The initial public release should avoid a composite supplier-risk score. It should expose the underlying indicators and let the user see what is known and what remains unresolved.

## Non-goals

This project is not:

- a supplier rating or due-diligence service;
- a production-ready sourcing or ESG platform;
- a real-time disruption monitor;
- a claim that public data can reconstruct a company's supplier network;
- a vehicle for proprietary or employer data;
- an endorsement of any data publisher or technology provider.

## Publication

The intended public format is a static website that can be linked from a short LinkedIn screen recording. GitHub Pages may be used only after the release checklist is complete.
