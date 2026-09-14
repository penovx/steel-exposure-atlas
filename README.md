# Steel Exposure Atlas

Interactive exploration of public data on steel production, trade and water stress.

## Status

Early-stage public-data demonstrator. It is intended to show what can be explored by combining public datasets with modern data tooling and AI-assisted development. It is not a supplier-risk product, due-diligence service, or operational decision system.

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
docs/                methodology, architecture and release controls
.github/             repository and CI configuration
```

The application stack and data packages will be added only after the relevant source and licence checks are complete.

## Licensing

No project-wide licence has been granted yet. Third-party datasets and assets remain subject to their own terms. See `DATA_LICENSES.md` and `THIRD_PARTY_NOTICES.md` as the project develops.
