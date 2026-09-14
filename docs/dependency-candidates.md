# Dependency candidates

This file tracks third-party software that may become useful during implementation but is **not** a dependency merely because it appears here.

A package is added to `package.json`, Python/R environment files, build scripts or production code only when there is a concrete technical need. At that point its exact version, licence and transitive dependency impact are reviewed.

## Eurostat `correspondenceTables`

**Status:** candidate only; not installed and not required by the current architecture.

**Potential use:** retrieve or work with official correspondence tables between statistical classifications such as CN, CPA and NACE if the trade-data pipeline needs classification mapping.

**Repository:** https://github.com/eurostat/correspondenceTables

**Observed licence:** the repository README links to the EUPL and the package `DESCRIPTION` declares `License: EUPL`.

**Decision:** do not introduce it now. The project has not selected an R runtime and no classification mapping problem has yet justified the dependency. If it is selected later, review the exact release and EUPL obligations before distribution.

## Entity-resolution libraries

`recordlinkage` and `dedupe` may be evaluated only if deterministic matching between plant-owner names and external legal-entity data proves insufficient.

They are not preselected. Matching logic must remain explainable and tested even if a library is introduced.

## Principle

Data sources, build-time tools and runtime dependencies are governed separately. A permissively licensed tool does not make the data it accesses freely reusable, and an open dataset does not justify adding software that the project does not need.
