# Release checklist

Use this checklist before making a public build available.

## Data and rights

- [ ] Every published dataset has an exact source/version recorded.
- [ ] Dataset-specific terms or licence have been reviewed for the intended public use.
- [ ] Redistribution or publication of each shipped data file/derived output is explicitly allowed.
- [ ] Required attribution is present in the site and repository.
- [ ] No source with unresolved rights is bundled in `public/data/`.
- [ ] No paid, metered or trial service has been introduced without explicit approval.

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

## Engineering and publication

- [ ] Production build succeeds from a clean checkout.
- [ ] Dependency lock files are committed.
- [ ] Dependency and asset licences have been reviewed and notices updated.
- [ ] Mobile and desktop interaction have been checked.
- [ ] Link preview metadata has been checked.
- [ ] GitHub Pages or another deployment target is enabled only after the checks above are complete.
