# Gotchas — Multi-Package Development

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LATEST Resolves at Build Time, Not Install Time

**What happens:** When a dependency uses `"versionNumber": "1.2.0.LATEST"`, the CLI resolves `LATEST` to the highest build number of that major.minor.patch at the moment `sf package version create` runs. If a teammate pushed a new build of the dependency 5 minutes ago, your package silently picks up that build — even if it introduced a breaking change.

**When it occurs:** Any time the dependency's version number uses `LATEST` and multiple developers or CI jobs are creating versions of the upstream package concurrently.

**How to avoid:** In production CI/CD pipelines, pin to an explicit build number (e.g., `"1.2.0.4"`) rather than `LATEST`. Use `LATEST` only during local development for convenience.

---

## Gotcha 2: Package Directory Order in sfdx-project.json Does Not Determine Build Order

**What happens:** Developers assume that listing Base before Sales in the `packageDirectories` array means the CLI will build or deploy them in that order. It does not. The array order has no behavioral effect on build or install sequencing.

**When it occurs:** When a practitioner runs `sf package version create` for a downstream package before its dependency has been versioned.

**How to avoid:** Always build packages explicitly in topological order using separate CLI commands or CI/CD job dependencies. Do not rely on array position.

---

## Gotcha 3: Removing a Field from a Released Package Breaks Dependents

**What happens:** Package A (Base) releases version 1.0.0 with `Account.Region__c`. Package B (Sales) depends on Base@1.0.0 and references `Account.Region__c` in Apex. If Base version 2.0.0 removes `Region__c`, installing Base@2.0.0 in an org that has Sales installed causes a compile failure in Sales.

**When it occurs:** Whenever a released package removes or renames a component that downstream packages reference.

**How to avoid:** Treat released package components as a public API. Deprecate fields instead of removing them. If removal is necessary, coordinate with all downstream package owners to release updated versions that no longer reference the removed component, then install upgrades in reverse-dependency order.

---

## Gotcha 4: Scratch Org Definition Must Include All Dependency Features

**What happens:** A scratch org created for a downstream package fails to install upstream dependencies because the org definition file does not enable required features (e.g., `MultiCurrency`, `StateAndCountryPicklist`).

**When it occurs:** When the upstream Base package uses features that are not in the default scratch org shape.

**How to avoid:** Maintain a single scratch org definition file that includes the union of all features required by all packages in the project. Review upstream packages' feature requirements when adding new dependencies.

---

## Gotcha 5: Unpackaged Metadata Deployed Before Dependencies Are Installed

**What happens:** A CI/CD pipeline deploys the unpackaged directory (containing profiles, permission sets, or page layouts that reference packaged components) before installing the packages. The deploy fails with `FIELD_NOT_FOUND` or `ENTITY_NOT_FOUND` errors.

**When it occurs:** When the pipeline treats unpackaged metadata as "just another deploy step" without enforcing ordering relative to package installs.

**How to avoid:** Always deploy unpackaged metadata as the last step, after all packages are installed. If the unpackaged metadata references components from multiple packages, all those packages must be installed first.
