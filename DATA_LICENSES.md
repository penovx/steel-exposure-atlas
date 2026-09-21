# Data licences and reuse status

This file records third-party datasets and derived data outputs that are actually bundled with the public Steel Exposure Atlas runtime.

Publication approval is dataset-specific. The source registry remains the authoritative record for review status, source versions, hashes and publication boundaries.

## Global Energy Monitor — Global Iron and Steel Tracker

- **Runtime file:** `public/data/gist-plants.v1.json`
- **Publisher:** Global Energy Monitor
- **Dataset/version:** Global Iron and Steel Tracker, June 2026 (V1)
- **Source:** https://globalenergymonitor.org/projects/global-iron-steel-tracker/
- **Retrieved:** 2026-09-14
- **Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Redistribution decision:** approved for the reviewed derived subset; original GEM workbooks remain outside the repository
- **Attribution:** Global Energy Monitor, Global Iron and Steel Tracker, June 2026 (V1) release. Distributed under CC BY 4.0. Steel Exposure Atlas identifies its transformations and derived calculations.
- **Transformation:** selected plant, ownership-context, capacity/status, production-method, product and 2019–2024 production fields are transformed into the documented `steel-exposure-atlas/gist-plant-v1.0` runtime schema
- **Material boundary:** operating capacity is not available supply; plant product descriptions are not product-specific capacity or customs classifications; immediate owner/operator identity is not automatically an ultimate parent

Reviewed source workbook SHA-256: `A5768B59CD7E6CEC217692AE45EDA80EA70AAB1666AEF74332CC1B41DD5338EB`.

## Natural Earth — 1:110m Admin 0 Countries

- **Runtime file:** `public/data/ne_110m_admin_0_countries.v5.1.1.geojson`
- **Publisher:** Natural Earth
- **Dataset/version:** 1:110m Admin 0 — Countries, v5.1.1
- **Source:** https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/
- **Licence/status:** public domain
- **Redistribution decision:** permitted
- **Attribution:** not required; the atlas provides a courtesy Natural Earth credit
- **Transformation:** the pinned upstream GeoJSON is validated and written as a compact local runtime file
- **Source integrity:** upstream Git blob SHA-1 `1e6ab74c7042f97013be69ceec798be8e1aff27d`
- **Retrieval provenance:** the exact retrieval timestamp was not separately recorded; it remains unresolved rather than being inferred from the later repository publication commit
- **Material boundary:** Natural Earth uses de facto boundaries; the atlas does not present the basemap as a legal or political determination

## European Commission — Consolidated Financial Sanctions File 1.1

- **Runtime file:** `public/data/eu-sanctions-owner-status.v1.json`
- **Publisher:** European Commission
- **Dataset:** Consolidated Financial Sanctions File 1.1
- **Source:** https://webgate.ec.europa.eu/fsd/fsf#!/files
- **Retrieved:** 2026-09-15T21:53:03+00:00
- **Source file generation date:** 05/08/2026
- **Licence/reuse basis:** European Commission reuse basis / CC BY 4.0 unless otherwise indicated, as documented in the source review
- **Redistribution decision:** approved for the reviewed minimal enterprise-only derived status layer; the raw sanctions CSV remains outside the repository
- **Attribution:** Source: European Commission, Consolidated Financial Sanctions File 1.1. Derived, transformed and entity-matched by Steel Exposure Atlas.
- **Transformation:** person rows are excluded; enterprise records are profiled and used for deterministic candidate screening plus reviewed entity-resolution decisions; public output contains company-level evidence states rather than the raw list
- **Material boundary:** no direct list match means only no direct deterministic match in the pinned snapshot; it is not sanctions clearance and does not resolve ownership/control effects

Source snapshot SHA-256: `049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015`.

## U.S. Department of the Treasury / OFAC sanctions lists

- **Runtime file:** `public/data/ofac-sanctions-owner-status.v1.json`
- **Publisher:** U.S. Department of the Treasury, Office of Foreign Assets Control
- **Datasets:** Specially Designated Nationals and Blocked Persons List and Consolidated Non-SDN Sanctions List
- **Source:** https://ofac.treasury.gov/sanctions-list-service
- **Retrieved:** 2026-09-16T15:47:54+00:00
- **Licence/status:** CC0 1.0 Universal according to the reviewed official Data.gov catalogue records
- **Redistribution decision:** approved for the reviewed minimal derived company-status layer; complete OFAC source files remain outside the repository
- **Attribution:** attribution is not required by CC0, but the atlas identifies OFAC, the source list, snapshot date and source hash for provenance
- **Transformation:** relevant entity records are screened against usable GIST owner identities; reviewed matches retain source-list, program and designation context
- **Material boundary:** a no-match is not sanctions clearance and does not evaluate OFAC ownership/control effects such as the 50 Percent Rule

Reviewed source hashes:

- SDN XML: `3D594ED7CDB5E0FD13F126A3815255146D730F791DCF672665C67416D03A7C1F`
- Consolidated Non-SDN XML: `C59772F3EDD625812AC43C4AEC57513D08CDD180135A3B6368DBC086AB81DF7D`

## European Union / European Commission — 2026 steel import measures

- **Runtime file:** `public/data/eu-steel-trade-context.v1.json`
- **Publisher:** European Union / European Commission
- **Sources:** Commission Implementing Regulations (EU) 2026/1457 and 2026/1930
- **Official sources:** https://eur-lex.europa.eu/eli/reg_impl/2026/1457/oj/eng and https://eur-lex.europa.eu/eli/reg_impl/2026/1930/oj/eng
- **Retrieved:** 2026-09-16
- **Licence/reuse basis:** reviewed European Commission reuse basis / CC BY 4.0 unless otherwise indicated
- **Redistribution decision:** approved for the minimal derived trade-context layer; the raw Official Journal snapshots are not republished
- **Attribution:** Source: European Union / European Commission, Commission Implementing Regulations (EU) 2026/1457 and 2026/1930. Derived product-family and plant context by Steel Exposure Atlas.
- **Transformation:** plant origin and GIST plant product labels are mapped to reviewed measure categories and quota-route context
- **Material boundary:** this is a hypothetical import-into-the-EU scenario; GIST product labels are candidate product-family evidence, not CN/TARIC classification; the layer does not claim live quota availability or transaction-specific landed cost

Reviewed source hashes:

- Regulation (EU) 2026/1457 snapshot: `B869A4BB8C4E4F7AE320B4CE4A117A33B05CADEEDF1C9DF106845EBCA9D9B21B`
- Regulation (EU) 2026/1930 snapshot: `5F0214CD0FC9FC85A114B9EC485E2D6887F3F2137BD177EE357CC00FE2BB32BE`

## Sources not bundled

A source appearing in `data/source-registry.json` is not automatically part of the public runtime. Sources with `publication_status: not_approved`, unresolved publication gates or no current runtime artifact are not covered by this file.
