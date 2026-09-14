# Architecture

## Current decision

Start with the smallest architecture that can produce a credible interactive map without introducing a dependency or service before it is needed.

The foundation therefore uses browser-native HTML, CSS, JavaScript and SVG. There is no application framework, external font, analytics service, map-tile provider, backend or runtime AI API in the current version.

This is an intentional starting point rather than a permanent ban on mapping libraries. If browser-native rendering becomes the constraint for large geospatial layers or interaction quality, a map engine can be introduced through a separate dependency review and pull request.

## Runtime

```text
index.html
   |
   +-- src/app.js
   |      |
   |      +-- src/map/render-world.js
   |
   +-- src/styles.css
   |
   +-- public/data/   reviewed publication-ready inputs only
```

The application tries to load a local reviewed basemap first. When running on localhost only, it may fall back to the exact pinned Natural Earth v5.1.1 file from the publisher's GitHub repository. The fallback is a development convenience and is not a release architecture.

## Data pipeline

Data preparation is separated from presentation:

```text
reviewed external source
        |
        v
pipeline/ fetch / validate / transform
        |
        +-- provenance and validation checks
        |
        v
public/data/ publication subset
        |
        v
browser visualization
```

A pipeline step must reject a source if its pinned identity changes unexpectedly. The initial Natural Earth fetcher verifies the Git blob SHA of the approved v5.1.1 GeoJSON before writing the local publication file.

## Network policy

The intended published site should be self-contained for data and visual assets where source terms allow it.

Runtime network calls require an explicit reason and review. In particular, the release should not depend on:

- metered map tiles;
- analytics or advertising scripts;
- remote fonts;
- an AI API call on each page load;
- unpinned raw data URLs.

## Growth path

Add complexity only in response to a measured constraint:

- use a mapping library if native SVG becomes a performance or interaction limitation;
- use columnar data or browser-side analytical tooling only if data volume justifies it;
- add a build step only when bundling, type checking or asset processing creates clear value;
- add a backend only for a use case that cannot be handled safely and reproducibly in a static site.

Each change should remain reversible and should not weaken source traceability.
