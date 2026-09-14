# Source governance

Every external dataset must pass the same review before it can become part of a published build.

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

## Interpretation rule

The project must not state more than the source supports. In particular:

- country trade statistics do not identify a buyer-supplier relationship or physical route;
- site proximity does not establish sourcing or dependency;
- screening indicators such as water stress do not establish an outage probability;
- ownership records do not by themselves establish operational control at the date of every observation.

When uncertainty materially changes interpretation, show it in the UI or methodology rather than hiding it in implementation notes.
