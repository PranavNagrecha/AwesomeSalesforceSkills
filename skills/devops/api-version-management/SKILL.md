---
name: api-version-management
description: "Use this skill when auditing, upgrading, or standardizing Salesforce API versions across metadata components, sfdx-project.json sourceApiVersion, Apex classes, LWC bundles, Aura bundles, and integration endpoints. Covers version drift detection, retirement risk analysis, and upgrade planning. NOT for REST/SOAP API design patterns (use rest-api-patterns or soap-api-patterns), OAuth configuration (use oauth-flows-and-connected-apps), or Metadata API deployment mechanics (use change-set-deployment or unlocked-package-development)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "some of our Apex classes are on API version 30 and we are getting deprecation warnings"
  - "how do I find which metadata components are on an old or retired API version"
  - "our sfdx-project.json sourceApiVersion does not match the API version in individual component meta files"
  - "Salesforce retired API versions below 31 and I need to upgrade all affected metadata"
  - "what API version should I set for new LWC components and how do I keep them consistent"
  - "we need an API version upgrade plan before the next major Salesforce release"
tags:
  - api-version
  - metadata
  - version-drift
  - deprecation
  - upgrade
  - devops
  - sourceApiVersion
inputs:
  - "sfdx-project.json or project manifest with sourceApiVersion"
  - "Metadata source directory (force-app or similar) containing .cls-meta.xml, .js-meta.xml, .cmp, and other versioned metadata"
  - "Target Salesforce release or API version for upgrade"
  - "ApiTotalUsage event logs (optional, for runtime version detection)"
outputs:
  - "API version inventory report listing every component and its current version"
  - "Version drift analysis showing mismatches between sourceApiVersion and per-component versions"
  - "Upgrade plan with prioritized list of components to update"
  - "Validated sfdx-project.json and component metadata at target version"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# API Version Management

This skill activates when you need to audit, standardize, or upgrade the API versions declared across a Salesforce metadata codebase. Every Salesforce metadata component carries an API version that controls which platform behaviors, fields, and features are available at runtime. Version drift — where different components run on different API versions — causes subtle behavioral inconsistencies, test failures, and eventual breakage when Salesforce retires old versions.

---

## Before Starting

Gather this context before working on anything in this domain:

- **What is the project's `sourceApiVersion`?** Found in `sfdx-project.json`, this is the baseline version the project intends to use. Individual components can override it, and that override is where drift begins.
- **What is the current Salesforce release?** Each major release (Spring, Summer, Winter) increments the API version by 1. As of Spring '25, the current API version is 63.0. Salesforce retires versions on a rolling basis — versions 7.0 through 30.0 were retired in Summer '22, and versions 21.0-30.0 lose support according to the minimum 3-year deprecation notice policy.
- **Are there integrations using explicit API version numbers?** External systems calling `/services/data/vXX.0/` or `/services/Soap/c/XX.0` endpoints pin to a version. These must be inventoried alongside metadata.

---

## Core Concepts

### 1. The Three Layers of API Versioning

Salesforce API versions operate at three distinct layers, each independently configurable:

1. **Transport API version** — the version in REST/SOAP endpoint URLs used by external integrations (e.g., `/services/data/v63.0/`). This controls which API resources and fields are visible to the caller.
2. **`sourceApiVersion` in `sfdx-project.json`** — the default version used by the Salesforce CLI during `sf project deploy` and `sf project retrieve`. It sets the baseline for metadata operations but does not override per-component versions at runtime.
3. **Per-component `apiVersion`** — declared in each component's metadata file (`.cls-meta.xml`, `.js-meta.xml`, `.trigger-meta.xml`, `.cmp`). This is the version the platform actually uses when executing the component. An Apex class at version 50.0 sees different System method signatures than one at version 63.0.

Version drift occurs when these three layers diverge. The most dangerous drift is between `sourceApiVersion` and per-component versions, because developers assume they are deploying at one version while the platform executes at another.

### 2. Salesforce API Retirement Policy

Salesforce publishes an API End-of-Life policy with a minimum 3-year deprecation notice. When a version is retired:

- REST and SOAP calls to that version return an error.
- Metadata components pinned to that version may exhibit undefined behavior or deployment failures.
- `ApiTotalUsage` event logs in Event Monitoring track which versions are actively called, providing a detection mechanism before retirement hits.

Versions 7.0-30.0 were retired in Summer '22. The next retirement wave will follow the same 3-year notice pattern. Proactive scanning is essential because Salesforce does not automatically upgrade component versions.

### 3. LWC Component Versioning (Spring '25+)

Starting in Spring '25, Lightning Web Components require an explicit `apiVersion` in their `.js-meta.xml` file. Previously, LWC inherited the org's current version implicitly. This change means:

- New LWC bundles must declare `<apiVersion>63.0</apiVersion>` (or current).
- Existing LWC bundles without an explicit version will use the org default, but this implicit behavior is deprecated.
- The declared version controls which base components, wire adapters, and decorators are available.

### 4. ApiTotalUsage Event Logs

The `ApiTotalUsage` event type in Event Monitoring records every API call with the version used. Query these logs to find external integrations still calling deprecated versions:

```sql
SELECT ApiVersion, Client, Count
FROM ApiTotalUsage
WHERE ApiVersion < 31
ORDER BY Count DESC
```

This data is critical for building an upgrade plan that covers runtime usage, not just static metadata.

---

## Common Patterns

### Pattern 1: Full Codebase Version Audit

**When to use:** Before a major Salesforce release, after inheriting a project, or when deprecation notices arrive.

**How it works:**

1. Read `sourceApiVersion` from `sfdx-project.json`.
2. Scan all `*-meta.xml` files for `<apiVersion>` elements.
3. Scan `.cmp` and `.app` Aura files for `<aura:component>` or `<aura:application>` version attributes.
4. Compare each component's version against `sourceApiVersion` and flag drift.
5. Flag any component below the minimum safe version (currently 31.0).

**Why not the alternative:** Manual spot-checking misses components because a typical org has hundreds of versioned files scattered across classes, triggers, pages, components, and flows.

### Pattern 2: Incremental Version Pinning

**When to use:** When upgrading all components at once is too risky (large codebase, limited test coverage).

**How it works:**

1. Group components by current version into tiers.
2. Upgrade the oldest tier first (highest risk of retirement).
3. Run the full test suite after each tier upgrade.
4. Update `sourceApiVersion` in `sfdx-project.json` only after all components reach the target version.

**Why not the alternative:** A big-bang upgrade changes runtime behavior across every component simultaneously, making it difficult to isolate regressions.

### Pattern 3: CI Pipeline Version Gate

**When to use:** To prevent version drift from recurring after cleanup.

**How it works:**

1. Add a pre-commit or CI check that scans `*-meta.xml` for `<apiVersion>`.
2. Reject any component whose version is more than 2 major versions behind the project's `sourceApiVersion`.
3. Reject any component below the absolute minimum (currently 31.0).
4. Report drift percentage in CI output.

**Why not the alternative:** Without a gate, developers create new components at the CLI's default version while old components stay on legacy versions, re-introducing drift within a single sprint.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| All components within 2 versions of target | Big-bang upgrade to current version | Low risk; behavior changes are minimal across adjacent versions |
| Components span 10+ version range | Incremental tier-based upgrade | Isolates regressions; allows targeted test runs per tier |
| External integrations on old versions | Upgrade transport API version separately, coordinated with external teams | Transport version affects API consumers outside your control |
| New project setup | Pin `sourceApiVersion` to current release, add CI gate immediately | Prevents drift from day one |
| LWC bundles missing explicit `apiVersion` | Add `<apiVersion>` to every `.js-meta.xml` | Required from Spring '25; implicit versioning is deprecated |
| Managed package development | Pin to the lowest version your subscribers need | Managed packages must support the subscriber's minimum API version |

---

## Recommended Workflow

Step-by-step instructions for auditing and upgrading API versions across a Salesforce project:

1. **Read `sfdx-project.json`** — extract the `sourceApiVersion` value. This is the project's intended baseline. If it is missing, the CLI defaults to the latest version, which may not match component versions.
2. **Inventory all versioned components** — scan the metadata source directory for every `*-meta.xml`, `.cmp`, `.app`, and `.js-meta.xml` file. Extract the `<apiVersion>` element from each. Record the component name, type, and version.
3. **Identify drift and retirement risk** — compare each component's version against `sourceApiVersion`. Flag components more than 2 versions behind as drifted. Flag anything below version 31.0 as retirement-critical.
4. **Check runtime API usage** — if Event Monitoring is available, query `ApiTotalUsage` logs to find external integrations using deprecated versions. Merge this data with the metadata inventory.
5. **Build the upgrade plan** — prioritize retirement-critical components first, then drifted components, then cosmetic alignment. Group into tiers for incremental rollout. Document expected behavior changes per version jump using Salesforce release notes.
6. **Execute and validate** — upgrade each tier by updating `<apiVersion>` in metadata files. Run the full test suite after each tier. Confirm deployment succeeds in a sandbox before production.
7. **Add a CI gate** — implement a version-check step in the CI pipeline to prevent future drift. Set the minimum acceptable version to no more than 2 behind `sourceApiVersion`.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `sourceApiVersion` in `sfdx-project.json` is set to the target version
- [ ] No component has an `apiVersion` below the minimum safe version (31.0)
- [ ] All components are within 2 major versions of `sourceApiVersion`
- [ ] Every LWC `.js-meta.xml` file has an explicit `<apiVersion>` element
- [ ] External integration endpoint URLs have been checked for deprecated versions
- [ ] Full test suite passes at the new version(s)
- [ ] CI pipeline includes a version-drift gate

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`sourceApiVersion` does not override per-component versions at runtime** — many developers assume setting `sourceApiVersion` to 63.0 means all their Apex runs at 63.0. It does not. Each class executes at the version in its own `-meta.xml`. The `sourceApiVersion` only affects CLI retrieve/deploy operations.
2. **Apex behavior changes silently between versions** — certain System methods change behavior across versions (e.g., `String.valueOf()` on null, SOQL relationship name resolution, trigger context variable availability). An Apex class at version 40.0 can produce different results than the same code at version 63.0, with no compile-time warning.
3. **Retired API versions cause hard failures, not graceful fallbacks** — when Salesforce retires a version, REST/SOAP calls to that version return `UNSUPPORTED_API_VERSION` errors immediately. There is no automatic forwarding to the next supported version. Metadata components on retired versions may fail to deploy.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| API Version Inventory | Spreadsheet or table listing every component, its type, file path, and current API version |
| Version Drift Report | Summary of components that diverge from `sourceApiVersion`, grouped by severity |
| Upgrade Plan | Prioritized, tiered plan for updating components with test checkpoints |
| CI Gate Configuration | Pipeline step or pre-commit hook that enforces version consistency |

---

## Related Skills

- `unlocked-package-development` — package-level `sourceApiVersion` management and subscriber version considerations
- `scratch-org-management` — scratch org definition files reference API versions for feature availability
- `sf-cli-and-sfdx-essentials` — CLI commands that use `sourceApiVersion` during deploy and retrieve
- `metadata-api-and-package-xml` — `package.xml` version attribute and its relationship to component versions
