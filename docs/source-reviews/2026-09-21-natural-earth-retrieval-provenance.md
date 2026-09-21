# Natural Earth retrieval provenance decision — 2026-09-21

## Purpose

Resolve the remaining v0.1 provenance gap for the Natural Earth basemap without inventing a retrieval timestamp that is no longer independently supported.

## Established evidence

The published basemap is unambiguously tied to:

- Publisher: Natural Earth
- Dataset: 1:110m Admin 0 — Countries
- Version: v5.1.1
- Reviewed source path: `nvkelso/natural-earth-vector/v5.1.1/geojson/ne_110m_admin_0_countries.geojson`
- Pinned upstream Git blob SHA-1: `1e6ab74c7042f97013be69ceec798be8e1aff27d`
- Runtime output: `public/data/ne_110m_admin_0_countries.v5.1.1.geojson`
- Reuse status: public domain; modification and redistribution permitted

The fetch pipeline rejects a different upstream blob identity.

## Missing evidence

The original local retrieval timestamp was not separately recorded before the runtime file was committed.

The later repository publication commit occurred on 2026-09-16, but that commit date does not prove the exact time or date at which the upstream file was fetched. It is therefore not used as a substitute.

The source registry intentionally retains:

`retrieved_at: null`

## Materiality

For this source, the missing historical timestamp does not prevent reconstruction of the published input:

- the exact upstream release is versioned;
- the exact upstream file identity is pinned by Git blob SHA-1;
- the atlas does not depend on a mutable unversioned Natural Earth URL at runtime;
- the dataset is used only as cartographic context;
- publication/reuse rights do not depend on the retrieval date.

The gap affects process provenance, not the identity of the published cartographic source.

## v0.1 decision

**Accepted as an explicit provenance exception for v0.1.**

The project will not fabricate a retrieval date. Instead, the source registry records the missing timestamp and this decision record documents why the exact version plus pinned upstream identity are sufficient for the current release.

This is not a general relaxation of the retrieval-date rule.

For any future Natural Earth refresh or version change:

1. record a timezone-aware retrieval timestamp at ingestion;
2. record the exact source URL and source identity before transformation;
3. update the source registry before publishing the new runtime artifact.

## Interpretation boundary

Natural Earth provides cartographic context only. Its de facto boundary representation is not presented as a legal or political determination by Steel Exposure Atlas.
