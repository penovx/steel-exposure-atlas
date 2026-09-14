# Steel Exposure Atlas

Interactive exploration of public data on steel production, trade and water stress.

## Status

Early-stage public-data demonstrator. It is intended to show what can be explored by combining public datasets with modern data tooling and AI-assisted development. It is not a supplier-risk product, due-diligence service, or operational decision system.

The current foundation renders a reviewed Natural Earth basemap with browser-native HTML, CSS, JavaScript and SVG. Production, trade, water and ownership layers are introduced only after their exact source packages pass the repository's publication gates.

## Run locally

No application dependency install is required for the current foundation.

```bash
python pipeline/fetch_public_data.py natural-earth
python -m http.server 8000
```

Then open `http://localhost:8000`.

The fetch step downloads the exact approved Natural Earth v5.1.1 GeoJSON and verifies its pinned Git blob identity before writing it to `public/data/`.

Validation without network access:

```bash
python -m unittest discover -s tests -p 'test_*.py'
node --check src/app.js
node --check src/map/render-world.js
```

## Principles

- Review the intended use and redistribution terms of every dataset before publishing it.
- Add no paid datasets, metered APIs, trials, or billable services without explicit approval.
- Keep source, version, retrieval date, terms, transformations and attribution traceable.
- Distinguish source data from derived calculations.
- Keep claims proportional to the evidence; exposure indicators are not disruption probabilities.
- Use no proprietary or employer data.

## Repository layout

```text
src/                 web application
pipeline/            ingestion, transformation and validation
public/data/         approved publication-ready data only
data/                source registry and local data conventions
tests/               automated checks
docs/                product scope, methodology, architecture and release controls
.github/             repository configuration
```

See `docs/product-brief.md`, `docs/architecture.md` and `docs/source-governance.md` for the current boundaries and design decisions.

## Licensing

No project-wide licence has been granted yet. Third-party datasets and assets remain subject to their own terms. See `DATA_LICENSES.md` and `THIRD_PARTY_NOTICES.md` as the project develops.
