# EU sanctions matchability gate — 2026-09-15

This gate follows the first enterprise-only profile of the pinned EU sanctions snapshot.

## Observed enterprise shape

From the pinned snapshot `049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015`:

- 17,812 enterprise rows collapse to 1,772 unique `Entity_LogicalId` values;
- median rows per enterprise: 7;
- median distinct source names per enterprise: 5;
- 1,564 enterprises have more than one source name;
- 51.7% of enterprises expose source identification fields;
- 85.7% expose country context;
- every enterprise has an EU reference number and regulation programme.

## Why matching is not started yet

The source is highly flattened and name-rich. Matching directly from flattened rows would overcount entities and could treat one enterprise's aliases as separate sanctions subjects.

Before the first real GIST-company screen, two ambiguity classes must be quantified:

1. **Name ambiguity** — whether the same conservatively normalized source name belongs to more than one EU enterprise, and how much additional ambiguity appears when legal forms are removed.
2. **Identifier semantics** — which `Identification_TypeCode` / `Identification_TypeDescription` values occur, whether their numbers are unique within type, and which types are defensible as company identifiers.

The project must not assume that an identification value is a company-registration number or LEI merely because it is populated.

## Allowed next step

Run `pipeline/profile_eu_sanctions_matchability.py` locally against the pinned raw CSV. The profiler emits aggregate collision/type statistics only and does not emit enterprise names, identification numbers, or person records.

Only after this gate is reviewed should the project create a local enterprise subset and run `pipeline/sanctions_match.py` against GIST company identities.
