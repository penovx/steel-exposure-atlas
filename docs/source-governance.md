# Source governance

Every external dataset must pass the same review before it can become part of a published build.

The public atlas is reviewed as **commercial-capable use** because it may be shared as a professional portfolio project. If a licence is safe only for clearly non-commercial use, that is not sufficient for publication here.

## Scope

This document governs **data sources**. Software libraries and build tools are reviewed separately. A software licence does not grant rights to the data accessed through that software, and an open dataset does not justify introducing an unnecessary dependency.

## States

1. `candidate` — potentially useful; no publication decision made.
2. `reviewed` — dataset-specific terms and intended use have been checked and documented.
3. `approved_for_processing` — local analysis is allowed for the intended project use.
4. `approved_for_publication` — the exact data or derived output may be shipped with the public site under documented conditions.
5. `rejected` — source is not used because rights, cost, quality or interpretation are unsuitable.

Processing approval and publication approval are deliberately separate. A source can be suitable for local analysis without permitting redistribution.

## Required review

For each candidate source, record:

- publisher and dataset name
- exact dataset/version or release date
- canonical source and terms/licence links
- retrieval date
- access method and whether registration is required
- cost or usage limits
- permissions relevant to analysis, modification and redistribution
- attribution requirements
- restrictions relevant to commercial/public portfolio use
- fields intended for use
- transformations and derived outputs
- publication decision and review notes

## Publication rule

A file may enter `public/data/` only when its source record is `approved_for_publication` and the required attribution can be satisfied by the application and repository documentation.

Unresolved licence scope, third-party rights, registration obligations, paid access, usage-based billing or unclear redistribution rights block publication by default. A general statement that a publisher supports open data is not enough when the selected dataset has more specific terms.

Attribution shown in the application must be generated from or checked against the approved source record. Do not improvise shortened credits that drop required licence, modification or source information.

## Cost rule

No paid dataset, subscription, metered API, trial that can convert to a paid service, or usage-based map service may be introduced without explicit owner approval. Prefer downloadable, self-hosted inputs where this is compatible with the source terms and practical for the site.

## Interpretation rule

The project must not state more than the source supports. In particular:

- country trade statistics do not identify a buyer-supplier relationship or physical route;
- site proximity does not establish sourcing or dependency;
- screening indicators such as water stress do not establish an outage probability;
- ownership records do not by themselves establish operational control at the date of every observation;
- absence of a relationship record does not establish absence of a parent or ownership relationship;
- an identified production site is not automatically a commercially or technically qualified sourcing alternative.

When uncertainty materially changes interpretation, show it in the UI or methodology rather than hiding it in implementation notes.
