# AGENTS.md

Instructions for coding agents and automated contributors working in this repository.

## Project boundary

This is an independent public-data project. Do not use proprietary, confidential, employer, customer or supplier data. Do not import material from unrelated private projects.

All public-facing application text, documentation and labels must be in English.

## Data and legal rules

- Do not download, commit, transform for publication or redistribute a dataset until its specific source record has been reviewed.
- Treat general website terms as insufficient when dataset-specific terms exist.
- Do not assume that "publicly accessible" means "free to redistribute".
- Do not add paid datasets, metered APIs, free trials that can become billable, or services requiring a payment method without explicit approval.
- Record source URL, dataset/version, retrieval date, terms/licence, attribution requirements, transformation and redistribution decision in `data/source-registry.json`.
- Keep raw third-party downloads outside Git unless redistribution has been explicitly approved.
- Do not remove source attribution from derived outputs where attribution is required.

## Claims

- Separate source facts, derived calculations and assumptions in code and UI.
- Do not convert screening indicators into unsupported claims about supplier reliability, disruption probability, compliance or company performance.
- Do not infer buyer-supplier relationships from country-level trade data or site proximity.
- Surface data dates and material limitations where they affect interpretation.

## Engineering rules

- Prefer a static, client-side deployment for the demonstrator unless a backend is clearly necessary.
- Avoid runtime third-party calls where preprocessed local data is sufficient.
- No secrets in source code, fixtures, logs or examples.
- Pin dependencies with a lock file once the application stack is introduced.
- Review dependency licences before adding them.
- Add tests for transformations and calculations before relying on them in the UI.
- Keep pull requests focused and explain data or licence implications in the PR description.
- Do not enable deployment until the release checklist is satisfied.

## Visual assets

Use only assets and fonts with reviewed redistribution/use rights. Prefer system fonts or self-hosted assets with clear terms. Do not hotlink third-party images, fonts or map tiles by default.
