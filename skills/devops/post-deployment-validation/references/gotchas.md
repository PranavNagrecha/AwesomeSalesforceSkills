# Gotchas — Post Deployment Validation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Quick Deploy Returns a New Deployment ID

**What happens:** When you execute a quick deploy using `deployRecentValidation` (Metadata API) or `sf project deploy quick`, the system returns a brand-new deployment ID that is different from the original validation ID. If you continue monitoring the validation ID, you see the old validation status — not the quick deploy's commit status.

**When it occurs:** Every time a quick deploy is executed. This is by design, not an edge case.

**How to avoid:** Always capture the deployment ID returned by the quick deploy call. Use that new ID for all subsequent status checks, reporting, and audit trails. Do not assume the validation ID doubles as the commit tracking ID.

---

## Gotcha 2: Validation IDs Expire After Exactly 10 Days

**What happens:** A validated deploy request ID becomes invalid 10 days after the validation completed. Attempting a quick deploy against an expired validation produces an error with no option to extend or refresh the validation.

**When it occurs:** When the deployment window slips past the 10-day mark from the original validation run — common in organizations with lengthy change approval processes.

**How to avoid:** Track validation completion timestamps in your deployment runbook or CI/CD pipeline. Set calendar reminders or automated alerts at the 7-day mark. If the window is at risk, re-validate early rather than waiting for expiry.

---

## Gotcha 3: RunSpecifiedTests Enforces 75% Per Class, Not Org Average

**What happens:** When using `RunSpecifiedTests` as the test level during a deployment, the 75% code coverage threshold is enforced individually for each Apex class included in the deployment package. A single class at 60% coverage will fail the entire deployment, even if the org-wide average is 90%.

**When it occurs:** When the deployment package includes an Apex class that the specified tests do not adequately cover. This is especially common when a utility class is included in the package but the specified tests only exercise the main business logic class.

**How to avoid:** Before deploying with RunSpecifiedTests, run the specified tests locally and check per-class coverage in the Developer Console or via `sf apex run test --code-coverage`. Ensure every class in the deployment package meets the 75% threshold individually. Add tests for utility and helper classes that are often overlooked.

---

## Gotcha 4: Deployment Status Shows "Succeeded" but Components Did Not Actually Change

**What happens:** The Deployment Status page shows a successful deployment, but the components in the org are identical to what was there before. This occurs when the deployed source is identical to what already exists in the org — the Metadata API treats it as a successful no-op rather than flagging that nothing changed.

**When it occurs:** When deploying from a stale branch that was already deployed, or when a team member already pushed the same changes through a different channel (e.g., change set, another pipeline run).

**How to avoid:** After deployment, perform a targeted retrieve of key components and compare them against the expected source. Do not rely solely on the deployment status message. Include a diff check in your post-deployment validation script.

---

## Gotcha 5: Test Failures During Deployment May Be Pre-Existing

**What happens:** A deployment triggers Apex test execution, and tests fail — but the failures existed before the deployment. The Deployment Status page does not distinguish between pre-existing test failures and failures introduced by the deployment package.

**When it occurs:** In orgs with existing flaky or broken tests. Running RunLocalTests or RunAllTests during a deployment surfaces every failing test in the org, not just tests related to the deployed components.

**How to avoid:** Maintain a pre-deployment test baseline. Run the full test suite before the deployment and record the results. After the deployment, compare the new failures against the baseline. Only failures that are new should be attributed to the deployment.

---

## Gotcha 6: Rollback Requires the Prior Version to Compile Against Current Org State

**What happens:** You attempt to roll back by re-deploying the prior version of an Apex class from source control, but the prior version references a field or object that was added in the same deployment you are rolling back. The rollback deployment fails with a compile error.

**When it occurs:** When a deployment included both schema changes (custom fields, objects) and Apex changes that reference the new schema. Rolling back the Apex without also rolling back the schema leaves the code referencing components that may or may not still exist depending on rollback order.

**How to avoid:** Rollback plans must account for all metadata types deployed together. If Apex references new schema, either roll back both simultaneously (using a complete prior-state package) or roll back in reverse dependency order: Apex first (removing references to new schema), then schema.
