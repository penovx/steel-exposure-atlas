# Reviewed entity resolution — GEM E100000131956 ↔ EU 129454

Status: **resolved same legal entity for this pinned sanctions snapshot**

Review date: 2026-09-16

## Candidate

The automated GIST → EU sanctions candidate screen produced one legal-form-only candidate:

- GIST owner label: `Myanmar Economic Corp`
- GEM entity ID: `E100000131956`
- EU sanctions entity ID: `129454`
- EU reference: `EU.6313.7`
- EU source name in the pinned CSV: `Myanmar Economic Corporation Limited`
- EU source snapshot SHA-256: `049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015`

The automated rule correctly left this as `review_required_legal_form`. Removing a legal-form token is not sufficient evidence by itself.

## Independent corroboration

### Global Energy Monitor

The current GEM entity page for `E100000131956` identifies `Myanmar Economic Corp` as a legal entity registered in Myanmar and gives `Myanmar Economic Corporation (MEC)` and `MEC` as alternate names. It also exposes PermID `5083242716`.

The current GEM steel-plant page for the relevant GIST asset uses the same GEM entity ID `E100000131956` and the same PermID `5083242716` for the owner/parent identity.

These GEM web pages are used only as identity-review references here. Their page-level reuse terms are not adopted as a new public data layer.

References:

- https://www.gem.wiki/E100000131956
- https://www.gem.wiki/Myingyan_Myanmar_steel_plant

### European Union

Council Implementing Regulation (EU) 2026/926 continues to list `Myanmar Economic Corporation Limited`. Its identifying information includes Yangon, Myanmar and registration number `105444192`; the legal act's reasons refer to the entity as `Myanmar Economic Corporation (MEC)`. The listing date remains 19 April 2021.

Reference:

- https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32026R0926

The pinned EU Financial Sanctions File 1.1 snapshot independently contains:

- entity ID `129454`
- EU reference `EU.6313.7`
- source name `Myanmar Economic Corporation Limited`
- programme `MMR`
- designation date `2021-04-19`
- Myanmar address-country context
- registration-number field containing `105444192`

## Decision

For the pinned snapshot, `GEM:E100000131956` and `EU-FSF:129454` are reviewed as the **same legal entity**.

The decisive point is not legal-form stripping alone. GEM independently identifies the source entity as `Myanmar Economic Corporation (MEC)`, while the current EU legal act lists `Myanmar Economic Corporation Limited` and itself refers to the listed entity as `Myanmar Economic Corporation (MEC)`. The jurisdiction/context is consistent and no conflicting identity evidence was found in the reviewed sources.

This reviewed resolution may therefore support a source-scoped `direct_list_match` for the **company identity** in the pinned EU sanctions snapshot.

## Boundaries

This decision does **not** establish that:

- the steel plant itself is a separately listed EU sanctions entity;
- every subsidiary, asset or related party is automatically subject to the same legal treatment;
- the company is affected identically under other jurisdictions;
- the result substitutes for sanctions or legal due diligence.

The public UI should attach the sanctions evidence to the resolved company identity and may show that one plant is connected to that company. It should not label the plant itself `sanctioned` without a separately supported plant-level legal conclusion.

No special display priority or featured treatment may be created for this case. The resolution is a governed identity link, not a curated showcase example.
