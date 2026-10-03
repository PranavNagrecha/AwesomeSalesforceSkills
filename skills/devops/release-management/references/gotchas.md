# Gotchas: Release Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each gotcha names the official source it rests on.

## Gotcha 1: Quick Deploy Returns a New Deploy ID, Not the Validation ID

**What happens:** You run `sf project deploy quick --job-id 0Af...validationId`. The command starts a separate deployment with its own ID. The validation job keeps its own status of Succeeded, because the check-only deployment did succeed. A team that polls the validation ID sees "Succeeded" while the real quick deploy is still running or has failed.

**When it occurs:** Release-night runbooks and CI jobs that store only the validation ID and then poll it for completion.

**How to avoid:** Capture the ID that `sf project deploy quick` returns and monitor it with `sf project deploy report --job-id <quickDeployId>`. Record both IDs in the release plan.

**Source:** Metadata API Developer Guide, `deployRecentValidation()`: "The deployRecentValidation() call returns the ID of the quick deployment." Salesforce CLI `sf project deploy quick --help` (CLI 2.151.7).

---

## Gotcha 2: `--use-most-recent` Looks Back Only 3 Days

**What happens:** A pipeline validates on Monday and runs `sf project deploy quick --use-most-recent` on Friday. The command finds no job ID and fails, even though the validation is still inside its 10-day window.

**When it occurs:** Any time the gap between validation and quick deploy is more than 3 days and the runbook relies on `--use-most-recent` instead of an explicit `--job-id`.

**How to avoid:** Always pass `--job-id` explicitly. The CLI help states the job ID "is valid for 10 days from when you started the validation" and that `--use-most-recent` "uses only job IDs that were validated in the past 3 days or less."

**Source:** Salesforce CLI `sf project deploy quick --help` (CLI 2.151.7), flag descriptions for `--job-id` and `--use-most-recent`. Metadata API Developer Guide, `deployRecentValidation()` (10-day requirement).

---

## Gotcha 3: RunSpecifiedTests Coverage Is Per Class and Trigger

**What happens:** A deployment with `--test-level RunSpecifiedTests --tests MyNewTest` fails with insufficient code coverage although org-wide coverage is above 80%. `MyNewTrigger` gets only 60% from `MyNewTest`.

**When it occurs:** RunSpecifiedTests (and the RunRelevantTests beta) deployments that include classes or triggers not fully exercised by the listed tests.

**How to avoid:** Make sure the listed tests cover every deployed class and trigger at 75% or more on their own. Add more test classes to `--tests` when one class is not enough. Validate in a full-copy sandbox first.

**Source:** Metadata API Developer Guide, DeployOptions `testLevel`: "Each class and trigger in the deployment package must be covered by the executed tests for a minimum of 75% code coverage. This coverage is computed for each class and triggers individually and is different than the overall coverage percentage."

---

## Gotcha 4: A Release Without Apex Runs No Tests by Default

**What happens:** A release that changes only fields, validation rules, and flows deploys to production without running a single Apex test. An existing Apex class that depends on a changed field breaks in production, and nothing caught it at deploy time.

**When it occurs:** Production deployments with no test level specified whose package contains no Apex classes or triggers. Since API version 34.0 the platform runs no tests by default for those packages.

**How to avoid:** Set `--test-level RunLocalTests` explicitly for any release that touches schema or automation used by Apex. The RunLocalTests test level "is enforced regardless of the contents of the deployment package."

**Source:** Metadata API Developer Guide, "Running Tests in a Deployment" and "Default Test Execution in Production".

---

## Gotcha 5: A Deployment During Service Downtime Restarts From the Beginning

**What happens:** A release scheduled on a Salesforce maintenance weekend takes far longer than rehearsed. Component deployment and validation are retried from the beginning after the service is restored. Only Apex tests that did not run before the downtime are re-run.

**When it occurs:** File-based deployments, change sets, package installs, managed 2GP version creation, and CLI deploys that overlap planned service downtime for the instance.

**How to avoid:** Check the instance on Salesforce Trust before fixing the release window. Avoid scheduling releases on planned upgrade windows.

**Source:** Metadata API Developer Guide, "Slow Deployments": "If your instance is due for a planned service upgrade, avoid running deployments during the service upgrade."

---

## Gotcha 6: Installing a Lower Package Version Is Not a Rollback

**What happens:** A team plans to "roll back" a bad package release by installing the previous version. For a managed 2GP package the install fails, because downgrading is not allowed. For an unlocked package the lower version installs, but data and deprecated components from the higher version do not return to their old state.

**When it occurs:** Package-based release trains that copy an org-based rollback runbook without adjusting it.

**How to avoid:** For managed 2GP, plan to roll forward with a new, higher version. For unlocked packages, treat a lower-version install as a deliberate change with its own testing, not as an undo. Keep data clean-up scripts in the release notes either way.

**Source:** Salesforce DX Developer Guide, "Upgrade a Version of an Unlocked Package": "It's possible to install a lower package version on top of a higher package version... This is not the same as a rollback, which isn't possible." Second-Generation Managed Packaging Developer Guide, package ancestry table: "Downgrading an installed package isn't allowed."

---

## Gotcha 7: Flows Deploy Inactive in Production Unless the Setting Is On

**What happens:** A release deploys an active flow from sandbox. In production the flow arrives inactive and the expected automation never fires. When the setting is on instead, deploying the active flow runs Apex tests, and the deployment rolls back if tests do not launch the required percentage of active processes and autolaunched flows.

**When it occurs:** Production deployments through change sets or Metadata API. `enableFlowDeployAsActiveEnabled` defaults to false in production and true in scratch, sandbox, and developer orgs, so the sandbox rehearsal behaves differently from production.

**How to avoid:** Decide per release whether activation is a deploy-time step (setting on, flow coverage planned) or a post-deploy manual step (setting off). Put the decision in the go/no-go criteria.

**Source:** Metadata API Developer Guide, FlowSettings field `enableFlowDeployAsActiveEnabled`, and Flow type limitations ("To deploy changes in a production org, you must enable the Deploy processes and flows as active preference").

---

## Gotcha 8: Sandbox Preview Is Decided Per Sandbox

**What happens:** A developer refreshes a sandbox during the preview window and lands on the next Salesforce release. The rest of the team is still on the current release. Metadata that uses features from the new release can't deploy to the team's non-preview sandboxes or to production.

**When it occurs:** Sandbox refreshes and creations during the weeks before a major upgrade.

**How to avoid:** Designate one sandbox for preview regression testing. Tell the team which sandboxes are on which release. Freeze refreshes of integration sandboxes during the preview window.

**Source:** UNVERIFIED (2026-10-03): the sandbox preview rules live only in Salesforce Help and the Sandbox Preview Guide on the Salesforce site, which do not fetch. Confirm the current rules there before relying on them.
