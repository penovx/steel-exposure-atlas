# Product UI principles

## Evidence -> meaning -> action

The primary user interface must explain what the available evidence establishes, what it means for the current sourcing/procurement question, and what useful follow-up follows from it.

The main interaction must not become a list of analyses the project did not perform.

### User-facing rule

Prefer:

1. **Evidence** — the fact or reviewed derived result that is actually supported.
2. **Meaning** — why that result matters in the current company, plant, product or geography context.
3. **Action** — the concrete follow-up a procurement or supply-chain user can take.

Do not promote implementation notes or absent analyses into primary copy, for example:

- `customs classification not performed`;
- `live quota availability not evaluated`;
- `fuzzy matching not run`;
- `plant-level finding not emitted`.

Such information belongs in Sources / Methodology when it is useful for auditability.

### Necessary boundaries

A limitation may appear in the main interaction only when omitting it would create a materially false inference. Phrase that boundary in user-relevant language rather than as a technical deficiency.

Examples:

- `No direct listing found` may be followed by `This is not sanctions clearance.`
- a broad product-family candidate may be followed by `Confirm the customs code before using this measure for an import decision.`

The interface should not list every missing input merely because the underlying pipeline knows it is missing.

### Progressive disclosure

Keep the strongest user-relevant signal close to the object that caused it:

- company/plant selection -> compact context card;
- procurement consequence -> visible in the card;
- detailed evidence, source identifiers, dates and methodology -> lower evidence area or Sources.

The context card is non-modal: it must not take over the whole screen or prevent continued exploration of the atlas.
