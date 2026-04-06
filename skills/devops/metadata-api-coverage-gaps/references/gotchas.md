# Gotchas -- Metadata API Coverage Gaps

Non-obvious Salesforce platform behaviors that cause real production problems when dealing with metadata coverage gaps.

---

## Gotcha 1: Metadata Coverage Report Lags Behind API Releases

**What happens:** The Metadata Coverage Report at `developer.salesforce.com/docs/metadata-coverage` is not always updated on the same day as a new Salesforce release. A type listed as "Not Supported" may have been added in the latest API version but not yet reflected in the report.

**When it occurs:** During the first 2-4 weeks after a major Salesforce release (Spring, Summer, Winter). Teams that upgrade their `sourceApiVersion` immediately after a release may find discrepancies.

**How to avoid:** Cross-reference the Metadata Coverage Report with the Metadata API Developer Guide release notes for the specific API version. Test retrieval and deployment of newly supported types in a sandbox before relying on them in CI/CD.

---

## Gotcha 2: "Supported" Does Not Mean "Fully Supported"

**What happens:** A metadata type is listed as "Supported" in the Metadata Coverage Report, but certain fields within that type are not retrievable or deployable. For example, `CaseSettings` is supported, but specific sub-elements related to Email-to-Case routing may not deploy correctly.

**When it occurs:** When deploying complex Settings types that contain nested sub-components. The parent type is supported but individual child elements are silently ignored.

**How to avoid:** After deploying a Settings type to a new org, compare the deployed configuration in Setup against the source XML. Automate this comparison with a Tooling API query where possible.

---

## Gotcha 3: .forceignore Patterns Are Glob-Based and Can Over-Exclude

**What happens:** A `.forceignore` entry intended to exclude one unsupported component (e.g., `**/ForecastingSettings.settings-meta.xml`) accidentally matches other files if the glob pattern is too broad. For instance, `**/*Settings*` would exclude `SecuritySettings`, `CaseSettings`, and every other settings type.

**When it occurs:** When practitioners add broad patterns to `.forceignore` without testing which files they match.

**How to avoid:** Use specific file paths or narrow glob patterns. Run `sf project retrieve start --metadata Settings` after adding `.forceignore` entries to confirm that only the intended types are excluded. Review `.forceignore` in code review.

---

## Gotcha 4: API Version Pinning Creates Divergent Behavior Across Team

**What happens:** One developer pins `sourceApiVersion` to `58.0` in `sfdx-project.json`, but another developer's CLI defaults to `60.0`. Metadata retrieval and deployment behave differently for types whose support status changed between those versions, leading to "works on my machine" issues.

**When it occurs:** On teams that do not enforce a consistent `sourceApiVersion` or where developers have different SF CLI versions installed.

**How to avoid:** Always set `sourceApiVersion` explicitly in `sfdx-project.json` and enforce it in CI. Update it deliberately as a team decision, not as an individual developer action.

---

## Gotcha 5: Destructive Deployments Cannot Remove Unsupported Types

**What happens:** A practitioner creates a `destructiveChanges.xml` to remove a metadata component from the target org. If the type is not supported by Metadata API, the destructive deployment silently skips it. The component remains in the org but is removed from source control, creating permanent drift.

**When it occurs:** During org cleanup or refactoring projects that use destructive deployments to remove deprecated components.

**How to avoid:** Check the Metadata Coverage Report before adding types to `destructiveChanges.xml`. For unsupported types, document the manual deletion step in the release runbook with the exact Setup path and confirmation check.

---

## Gotcha 6: Managed Package Types Have Stricter Coverage Than Unlocked

**What happens:** A metadata type that works in `sf project deploy start` and in unlocked packages fails when included in a 2GP managed package version create. The Metadata Coverage Report shows "Supported" for Metadata API and Unlocked Packages but "Not Supported" for Managed Packages.

**When it occurs:** When ISVs or internal teams transition from unlocked packages to managed packages for AppExchange distribution.

**How to avoid:** Always check the "Managed Packages" column in the Coverage Report, not just the "Metadata API" column. Test `sf package version create` for the managed package type early in the development cycle.
