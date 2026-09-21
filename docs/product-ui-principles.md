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
7. **Is it more useful than the raw value alone?** If not, keep the raw value in Evidence / Sources rather than the primary profile.

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

## Typed relationships

The interface must not present the exploration narrative as one uniformly evidenced chain.

The supported base relationships are:

- company identity → site: the immediate owner or operator recorded by GEM;
- site → production method: positive operating capacity for that method at the site;
- site → product: the plant source description lists that product expression.

Do not imply production method → product merely because both occur at the same site.

External evidence attaches at its actual subject:

- sanctions evidence attaches to a reviewed company identity;
- EU steel trade context attaches to a site-origin + product-evidence mapping;
- future facility evidence attaches only through a reviewed site-to-facility relationship.

Every visual connection that matters to interpretation should make its relationship type understandable without relying on line position alone.

## Site as the investigation bridge

The named site is the primary bridge between company attribution and production facts.

A site record must support direct traversal to:

- its recorded company owner/operator;
- operating production methods;
- listed source product expressions or reviewed product concepts;
- origin/geography;
- relevant external evidence;
- source and provenance.

Company views must expose named sites as navigable records rather than static reading content.

## Stable investigation surface

The public interaction uses one consistent inspection model, but it is not required to live below the full atlas.

- one selection on a company, site, product, production method or area exposes its inspectable record;
- the inspection surface preserves the surrounding exploration context instead of rearranging it;
- related named objects are directly traversable;
- facts and typed relationships stay in the inspection surface;
- navigation instructions, methodology and broad limitations belong in `Sources & interpretation`;
- detailed source identifiers or official source pages may remain one click away because they are evidence, not a second interpretation layer.

The inspection surface must not replace geographic context or force the user to hunt for the selected object again.

## Scope and denominator

The interface must visibly distinguish:

- geographic base scope;
- active relational filters;
- list/search state;
- selected object;
- map camera.

Every aggregate measure must state the population it summarizes.

For compound selections such as product + production method, distinguish method capacity at matching sites from total operating crude-steel capacity across the same sites. Never imply product-specific capacity unless the source establishes it.

## Product semantics

Source product expressions and reviewed product concepts are different objects.

Do not visually collapse distinct source tokens into one apparent option while the matching logic still treats them as separate populations. If several source expressions are grouped into one concept, the mapping and provenance must remain inspectable.
