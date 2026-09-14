# Release checklist

Use this checklist before making a public build available.

## Data and rights

- [ ] Every published dataset has an exact source/version recorded.
- [ ] Dataset-specific terms or licence have been reviewed for the intended public use.
- [ ] Redistribution or publication of each shipped data file/derived output is explicitly allowed.
- [ ] Required attribution is present in the site and repository.
- [ ] No source with unresolved rights is bundled in `public/data/`.
- [ ] No paid, metered or trial service has been introduced without explicit approval.

## Provenance and data quality

- [ ] Original downloaded packages have a recorded retrieval date and cryptographic hash where practical.
- [ ] Published layers can be traced from source/version through transformation to output.
- [ ] Original source files are kept separate from working and derived files.
- [ ] Country identifiers and dates use documented, unambiguous conventions.
- [ ] Material completeness, positional, temporal, classification or matching limitations are documented.
- [ ] Derived joins and entity matches expose material uncertainty rather than silently treating it as fact.

## Claims and methodology

- [ ] Source facts, derived values and assumptions are distinguishable.
- [ ] Trade data is not presented as a buyer-supplier relationship or physical route.
- [ ] Exposure indicators are not presented as disruption probabilities or supplier ratings.
- [ ] Material data dates and limitations are visible where needed.
- [ ] Derived calculations have tests or reproducible validation checks.

## Privacy and external services

- [ ] No analytics, advertising pixels or behavioural tracking are enabled by default.
- [ ] No secrets, tokens, personal data or local paths are committed.
- [ ] External fonts, map tiles, images and APIs have reviewed terms and privacy implications.
- [ ] Runtime network calls are documented and necessary.
- [ ] No user accounts, user uploads or runtime AI processing are introduced without a new privacy/security review.
- [ ] A public privacy notice accurately describes unavoidable hosting/network processing before release.

## Security and integrity

- [ ] Published inputs and generated artefacts are reproducible from reviewed sources.
- [ ] Source-integrity checks such as pinned versions, hashes or upstream identities are used where practical.
- [ ] Dependency versions are pinned and lock files are committed once dependencies are introduced.
- [ ] No unnecessary third-party runtime dependency has been added.

## Accessibility

- [ ] Keyboard operation has been checked for interactive controls.
- [ ] Visible focus states and accessible names are present.
- [ ] Information is not conveyed by colour alone.
- [ ] Text/control contrast has been checked against the WCAG 2.2 AA target.
- [ ] Material map-only information has an accessible textual or tabular equivalent where practical.
- [ ] Mobile and desktop interaction have been checked.

## Standards and assurance claims

- [ ] Public wording does not claim ISO/IEC certification, formal conformity or third-party audit.
- [ ] Any reference to standards is consistent with `docs/standards-and-assurance.md`.
- [ ] No data publisher, standards body or third party is presented as endorsing the atlas unless explicitly authorised.

## Engineering and publication

- [ ] Production build succeeds from a clean checkout.
- [ ] Dependency and asset licences have been reviewed and notices updated.
- [ ] Link preview metadata has been checked.
- [ ] GitHub Pages or another deployment target is enabled only after the checks above are complete.
