# Examples -- Metadata API Coverage Gaps

Concrete worked examples of identifying and resolving metadata coverage gaps in Salesforce DevOps workflows.

---

## Example 1: Pre-Deployment Coverage Audit for a Sales Cloud Migration

**Context:** A team is migrating a Sales Cloud org to source-driven development with unlocked packages. The `package.xml` includes `ForecastingSettings`, `Territory2Model`, `FlowDefinition`, and `CustomObject`.

**Problem:** The first `sf package version create` succeeds but the installed package in the target sandbox is missing forecasting configuration and the wrong Flow version is active. No errors were raised during package creation.

**Solution:**

1. Consult the Metadata Coverage Report at `developer.salesforce.com/docs/metadata-coverage`.
2. Build the coverage gap table:

| Metadata Type | Metadata API | Source Tracking | Unlocked Pkg | Workaround |
|---|---|---|---|---|
| ForecastingSettings | Partial | No | No | Manual Setup + runbook |
| Territory2Model | Supported | Supported | Supported | None needed |
| Flow (active version) | Latest only | Latest only | Latest only | Tooling API FlowDefinition activation |
| CustomObject | Supported | Supported | Supported | None needed |

3. Add `ForecastingSettings` to `.forceignore` and create a release runbook entry with the exact Setup path: **Setup > Forecasts Settings > Configure Forecasting**.
4. Write a post-deploy script to activate the correct Flow version:

```bash
#!/bin/bash
# activate-flow.sh -- Activate a specific Flow version after deployment
FLOW_DEF_ID=$(sf data query --query "SELECT Id FROM FlowDefinition WHERE DeveloperName='My_Flow'" --target-org "$TARGET_ORG" --json | jq -r '.result.records[0].Id')
FLOW_VERSION_ID=$(sf data query --query "SELECT Id FROM Flow WHERE Definition.DeveloperName='My_Flow' AND VersionNumber=3" --target-org "$TARGET_ORG" --json | jq -r '.result.records[0].Id')
sf data update record --sobject FlowDefinition --record-id "$FLOW_DEF_ID" --values "ActiveVersionId=$FLOW_VERSION_ID" --target-org "$TARGET_ORG"
```

**Why it works:** The audit catches gaps before they reach production. The runbook and post-deploy script ensure that every deployment is repeatable, regardless of who executes it.

---

## Example 2: Handling Source Tracking Gaps in a Scratch Org Workflow

**Context:** A developer makes changes to `EmailServicesFunction` and `CaseSettings` in a scratch org using the Setup UI. When they run `sf project retrieve start`, the `CaseSettings` changes appear but `EmailServicesFunction` does not.

**Problem:** `EmailServicesFunction` is not source-tracked. The developer's changes are lost when the scratch org expires.

**Solution:**

1. Check the Metadata Coverage Report -- confirm `EmailServicesFunction` shows "No" under Source Tracking.
2. Add an explicit retrieve step to the development workflow:

```bash
# Explicit retrieve for non-tracked types -- run before committing
sf project retrieve start --metadata EmailServicesFunction --target-org my-scratch
```

3. Add this command to the project's `scripts/retrieve-untracked.sh` and document it in the project README.
4. In CI, add a pre-commit hook or pipeline step that retrieves untracked types and diffs them against the repository.

**Why it works:** Explicit retrieval compensates for source tracking gaps. Making it a scripted step prevents developers from forgetting.

---

## Example 3: Excluding Unsupported Types from a CI/CD Pipeline

**Context:** A CI pipeline running `sf project deploy start --manifest manifest/package.xml` intermittently fails with `Entity of type 'OrgPreferenceSettings' is not available in this organization` on sandbox deployments.

**Problem:** The `package.xml` includes `OrgPreferenceSettings` fields that were deprecated in API v48. Some sandboxes are on a newer API version where these fields no longer exist.

**Solution:**

1. Identify the deprecated fields by checking the Metadata API Developer Guide release notes for the API version boundary.
2. Remove deprecated `OrgPreferenceSettings` fields from the retrieved metadata XML.
3. Add a `.forceignore` entry to prevent re-retrieval:

```text
# .forceignore
**/OrgPreference.settings-meta.xml
```

4. Document the excluded settings in the release runbook with their current production values.
5. Pin the `sourceApiVersion` in `sfdx-project.json` to avoid future surprises:

```json
{
  "sourceApiVersion": "60.0"
}
```

**Why it works:** Excluding the deprecated type stops the intermittent failures. Documenting the manual settings prevents configuration drift.

---

## Anti-Pattern: Ignoring Silent Exclusions in Package Builds

**What practitioners do:** They add all metadata to the unlocked package directory, run `sf package version create`, see a success message, and assume everything was included.

**What goes wrong:** Unsupported types are silently excluded. The package installs in the target org but is missing critical configuration -- such as forecasting settings, certain custom settings data, or org-wide email addresses. The defect is not discovered until end users report missing functionality.

**Correct approach:** Run a pre-build coverage audit against the Metadata Coverage Report. Explicitly exclude unsupported types from the package directory and deploy them separately via `sf project deploy start` or document them in a release runbook. Never rely on silent exclusion behavior.
