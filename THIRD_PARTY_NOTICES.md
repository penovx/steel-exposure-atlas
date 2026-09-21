# Third-party notices

Steel Exposure Atlas is a static, browser-based project. The current public runtime does not bundle third-party application libraries, external fonts, remote map tiles, analytics or advertising code.

The repository does bundle reviewed third-party **data or derived data outputs** under `public/data/`. Their source-specific terms, versions, hashes, transformations and interpretation boundaries are documented in `DATA_LICENSES.md` and `data/source-registry.json`.

## Global Energy Monitor

The atlas includes a transformed subset of the Global Iron and Steel Tracker, June 2026 (V1), from Global Energy Monitor.

GIST data used here are distributed under Creative Commons Attribution 4.0 International (CC BY 4.0). Steel Exposure Atlas identifies its transformations and derived calculations. Global Energy Monitor does not endorse this project.

## Natural Earth

The local basemap uses Natural Earth 1:110m Admin 0 Countries v5.1.1.

Natural Earth map data are public domain. Attribution is not required; the atlas includes a courtesy Natural Earth credit.

## European Commission / European Union

The atlas includes reviewed derived outputs based on:

- European Commission, Consolidated Financial Sanctions File 1.1;
- Commission Implementing Regulation (EU) 2026/1457;
- Commission Implementing Regulation (EU) 2026/1930.

The project applies the reviewed European Commission reuse basis / CC BY 4.0 unless otherwise indicated by the source. The atlas transforms and matches the source material and links users to the official source context. No endorsement by the European Commission or European Union is implied.

## U.S. Department of the Treasury / OFAC

The atlas includes a minimal derived company-level evidence layer based on reviewed OFAC sanctions-list snapshots.

The reviewed official Data.gov catalogue records identify the underlying list datasets as CC0 1.0 Universal. Attribution is not required by CC0, but Steel Exposure Atlas identifies OFAC, source-list context, snapshot dates and hashes for provenance. No endorsement by the U.S. Department of the Treasury or OFAC is implied.

## Software and hosting

No third-party application dependency is currently required by the published runtime. Development and CI tooling, including GitHub Actions and Playwright, are not shipped as browser runtime dependencies.

Any future code dependency, font, imagery, embed, map service or hosting integration that adds separate notice requirements must be reviewed before publication.
