# Gotchas — OmniStudio CI/CD Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: packDeploy Exit 0 Does Not Confirm Activation

**What happens:** The `packDeploy` command (OmniStudio Build Tool) or `sf omnistudio datapack deploy` returns exit code 0 even when the `--activate` flag is missing or activation silently fails. The CI/CD pipeline treats this as a successful deployment. Users in the target org continue to see the previously active component version. No error is logged.

**When it occurs:** Any DataPack deployment that omits `--activate`. Also occurs when `--activate` is included but the activation job fails internally (e.g., a concurrent activation is in progress). The deploy step still exits 0 in both cases.

**How to avoid:** Always include `--activate` in deploy commands. Add a mandatory post-deploy verification step that queries the target org's `OmniScript__c` or `IntegrationProcedure__c` record for the deployed component and confirms `IsActive = true`. Fail the pipeline if the active version does not match the deployed version. Treat exit code 0 as "import succeeded" — not "activation succeeded."

---

## Gotcha 2: DataPack Dependency Gaps Produce Runtime Errors, Not Import Errors

**What happens:** When an OmniScript references an Integration Procedure that is not included in the same DataPack export, the OmniScript imports successfully into the target org. No import error is raised. However, when a user navigates to the step that calls the missing Integration Procedure, a runtime error occurs — often surfaced as a generic "OmniScript Error" message.

**When it occurs:** When developers export only a single component (e.g., the OmniScript) for a targeted fix, without including its dependent Integration Procedures or DataRaptors. Common in hotfix scenarios where developers try to minimize the scope of a DataPack deployment.

**How to avoid:** When defining the DataPack export manifest, always include all dependencies: OmniScript → Integration Procedure → DataRaptor chain. Use the OmniStudio Build Tool's `--maxDepth` option to capture transitive dependencies automatically. After import, verify the target org contains the correct versions of all referenced components — not just the directly deployed component.

---

## Gotcha 3: DataPack JSON Diffs Are Noisy, Masking Real Changes

**What happens:** When DataPack JSON is committed to Git, minor re-exports of the same component can produce large, noisy diffs — timestamps update, ID fields regenerate, and field ordering may change between exports. This makes pull request reviews difficult and can obscure actual logic changes within a larger diff of noise.

**When it occurs:** Any re-export of an unchanged component, especially when exported alongside changed components in a bulk export. Re-ordering of array elements (e.g., OmniScript step arrays) is particularly problematic because JSON arrays are order-sensitive.

**How to avoid:** Scope DataPack exports to only the specific components that changed (use a targeted manifest, not a full-org export). Use a DataPack normalization step in the CI pipeline (sort keys, strip volatile timestamp fields) before committing, so diffs reflect only meaningful content changes. Document the normalization approach in the pipeline README so team members understand why committed JSON differs from the raw export.
