# Product UI principles

## Evidence -> relationship -> meaning

The primary interface must show what the available data establishes, which relationship or pattern it reveals, and what that relationship means inside the current company, plant, product or geography context.

The atlas is not a procurement-process adviser. It must not prescribe sourcing, qualification, contracting, compliance-routing or other internal actions that are not contained in the public evidence.

The main interaction must also not become a list of analyses the project did not perform.

## Stress test for every visible statement

A statement belongs in the primary interface only if it passes all of these questions:

1. **What positive fact is supported?** The statement must be grounded in source data or a reviewed deterministic derivation.
2. **What relationship does it reveal?** Name the relationship explicitly: company attribution, product-to-site relation, production method, geography or regulatory context.
3. **Is the interpretation fully derivable from the data?** Do not infer qualification, substitutability, availability, resilience, supplier performance or internal business process state.
4. **Does it avoid absence as the headline?** Do not promote missing analyses, missing alternatives or missing records into the main story.
5. **Does it avoid process advice?** Do not tell the user to confirm, route, qualify, source, negotiate or approve something unless that action itself is part of the source evidence.
6. **Would the statement still be understandable without atlas jargon?** Avoid unexplained words such as `connected` when the actual relationship can be named.
7. **Is it more useful than the raw value alone?** If not, keep the raw value in Evidence / Sources rather than the company brief.

## Preferred wording

Prefer explicit relationships:

- `GEM names ArcelorMittal as the immediate owner or operator of four sites in this view, across three countries.`
- `Plate is listed at Dunkerque, France.`
- `Basic oxygen furnace capacity totals 42.7 Mtpa across the sites in this view.`
- `The company identity is listed by OFAC since 10 Jan 2020 under the stated designation context.`
- `For the mapped origin and product family, the EU measure uses an origin-specific quota; the additional duty is 50% after quota exhaustion.`

Avoid shorthand or advice:

- `4 connected sites`;
- `1/4 sites`;
- `no second source visible`;
- `confirm the customs code`;
- `route to compliance`;
- `live quota availability not evaluated`.

## Necessary boundaries

A limitation may appear in the main interaction only when omitting it would create a materially false inference. Phrase the boundary as part of the supported relationship, not as a catalogue of unfinished analysis.

For example, a broad product-family mapping should be labelled as a broad mapping rather than converted into a process instruction.

## Progressive disclosure

Keep interpretation close to the object that caused it:

- first company click -> select the company and reveal `View company brief ->`;
- second click -> open the non-modal company brief;
- company brief -> relationships and reviewed interpretations supported by the available data;
- detailed source identifiers, raw records, dates and methodology -> Evidence / Sources.

The company brief must not take over the whole screen or prevent continued exploration of the atlas.
