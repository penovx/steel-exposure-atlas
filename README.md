# Steel Exposure Atlas

Public-data atlas for exploring steel companies, plants, production methods, products and selected external evidence in one connected view.

## Status

Pre-publication demonstrator. The current build combines a reviewed steel-plant dataset with cartography, company-level sanctions evidence and EU steel import-measure context. It is not a supplier ranking, due-diligence service, disruption forecast or operational decision system.

The core interaction is relational: company → sites → production methods → products, with external evidence linked through explicit company, plant, origin and product relationships. Evidence states and source provenance remain visible; no composite supplier-risk or ESG score is calculated.

GitHub Pages should remain disabled until `docs/release-checklist.md` is complete.

## Current public-data sources

- Global Energy Monitor · Global Iron and Steel Tracker · June 2026 (V1)
- Natural Earth · Admin 0 Countries · v5.1.1
- Pinned OFAC and EU sanctions source artifacts used for deterministic company-level screening
- Pinned EU steel trade-measure artifacts used for the atlas import-context layer

Source versions, hashes, transformations and publication boundaries are documented in the repository. No proprietary or employer data is used.

## Run locally

The current atlas is static and requires no application dependency install.

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

The reviewed runtime artifacts used by the atlas are already stored under `public/data/`. Runtime reads are same-origin; the interactive atlas does not require live map tiles, external fonts, user accounts or runtime AI calls.

## Validate

Run the repository contracts:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The CI workflow also runs the responsive and interaction audit across the supported viewport matrix. To run that browser audit locally, install the pinned Playwright version used by CI and Chromium, then run:

```bash
python tests/browser_responsive_smoke.py
```

## Product boundaries

- Company means the immediate owner or operator recorded by GEM; it does not establish ultimate parentage or independent control.
- Product labels are plant-level source descriptions; they do not establish product-specific capacity, grade availability or available supply.
- Operating capacity is not available supply.
- Sanctions findings are categorical evidence states, not probabilities or risk scores.
- EU steel trade context is modeled as a hypothetical import-into-the-EU relationship; plant product labels do not determine customs classification.
- Lines in the atlas represent modeled relationships, not shipments, buyer-supplier relationships or contractual supply.

## Principles

- Review intended use and redistribution terms before publishing a dataset.
- Add no paid datasets, metered APIs, trials or billable services without explicit approval.
- Keep source, version, retrieval date, terms, transformations and attribution traceable.
- Distinguish source data from derived calculations and interpretations.
- Keep uncertainty explicit rather than forcing unresolved matches into facts.
- Keep claims proportional to the evidence.
- Use no proprietary or employer data.

## Repository layout

```text
src/                 web application
pipeline/            ingestion, transformation and validation
public/data/         reviewed runtime/publication artifacts
data/                source registry and local data conventions
tests/               automated contracts and browser audit
docs/                product scope, methodology, architecture and release controls
.github/             repository configuration and CI
```

See `docs/product-brief.md`, `docs/product-ui-principles.md`, `docs/architecture.md`, `docs/source-governance.md` and `docs/release-checklist.md` for the current boundaries and controls.

## Licensing

No project-wide licence has been granted yet. Third-party datasets and assets remain subject to their own terms. See `DATA_LICENSES.md` and `THIRD_PARTY_NOTICES.md`.
