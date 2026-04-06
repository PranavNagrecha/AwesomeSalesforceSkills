---
name: pre-deployment-checklist
description: "Use when preparing a Salesforce metadata deployment for production and need a structured gate-check before releasing. Trigger keywords: 'pre-deploy checklist', 'what to check before deploying', 'validation deploy', 'deploy readiness', 'quick deploy window', 'checkOnly deploy', 'pre-release backup'. NOT for post-deployment smoke tests (use post-deployment-validation), full cutover sequencing (use go-live-cutover-planning), or change set UI workflow (use change-set-deployment)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - what should I check before deploying metadata to Salesforce production
  - how do I run a validation deploy and earn a quick deploy window
  - what gates must pass before a Salesforce release goes live
  - my deployment keeps failing in production but passes in sandbox
  - how do I back up production metadata before a release
tags:
  - pre-deployment-checklist
  - validation-deploy
  - quick-deploy
  - deployment-readiness
  - metadata-backup
inputs:
  - list of metadata components included in the release
  - source and target org details (sandbox type, production edition)
  - deployment tool in use (SF CLI, change sets, DevOps Center)
  - Apex test strategy (RunLocalTests, RunSpecifiedTests, RunAllTestsInOrg)
outputs:
  - completed pre-deployment checklist (go / no-go decision)
  - validation deploy results and quick-deploy ID
  - pre-release backup manifest and retrieved metadata archive
  - dependency gap report
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Pre-Deployment Checklist

You are a Salesforce release engineer focused on the final verification gates between a completed development cycle and a production deployment. Your goal is to catch deployment blockers, confirm test coverage, validate dependency completeness, back up current production state, and confirm the deployment window is safe -- all before anyone clicks Deploy.

This skill covers the pre-deployment phase only: everything that must be true before the deployment command executes. It does not cover post-deployment smoke tests, go-live cutover sequencing, or the mechanics of specific deployment tools.

---

## Before Starting

Gather this context before working through the checklist:

- What metadata types and specific components are included in this release (Apex classes, flows, custom objects, LWC, permission sets, etc.).
- Which deployment tool is being used: SF CLI (`sf project deploy`), change sets, DevOps Center, or Metadata API direct.
- What Apex test level is required -- `RunLocalTests` (75% org-wide), `RunSpecifiedTests` (75% per class in package), or `RunAllTestsInOrg`.
- Whether a validation deploy has already been run and, if so, when (the quick-deploy window is 10 calendar days).
- Whether the target org has any scheduled maintenance, active sandbox refreshes, or Trust site advisories.

---

## Core Concepts

### Validation Deploy (checkOnly)

A validation deploy executes the full deployment pipeline -- metadata dependency resolution, Apex compilation, and test execution -- without writing any changes to the org. The Metadata API parameter is `checkOnly: true`; the CLI equivalent is `sf project deploy validate`. A successful validation produces a `validatedDeployRequestId` that can be redeemed for a quick deploy within 10 calendar days, skipping the test-run phase entirely. This is the single most effective tool for shrinking a production deployment window.

Key constraints: the validation must use the same test level you intend for the real deploy. If you validate with `RunSpecifiedTests` but the production deploy policy requires `RunLocalTests`, the quick-deploy ID is not usable. The 10-day window resets from the timestamp of the most recent successful validation -- not the first one.

### Dependency Completeness

Every component in a deployment must have all of its transitive dependencies already present in the target org or included in the same deployment package. The `MetadataComponentDependency` tooling API object is the canonical way to check this programmatically. Common gaps:

- A Lightning Web Component that imports an Apex class not in the package.
- A Flow referencing a custom field that was renamed or deleted in the target.
- A permission set granting FLS on an object that does not exist in production yet.

The Metadata API surfaces these as deploy errors, but catching them before the deploy attempt avoids wasted validation cycles.

### Pre-Release Backup

Before deploying, retrieve the current production state of every component you are about to overwrite. Use `sf project retrieve start` with the same `package.xml` used for deployment, storing the output in a timestamped backup directory. This is the fastest rollback path if the deployment introduces a regression: redeploy the backup package rather than reverting code and re-running the full pipeline.

### Deployment Window Safety

Production deployments should avoid Salesforce maintenance windows (check trust.salesforce.com for your instance), batch Apex execution windows, and peak business hours. A deployment that overlaps with a scheduled maintenance can be interrupted mid-deploy, leaving partial metadata in an inconsistent state. Always confirm the instance status before starting.

---

## Common Patterns

### Pattern 1: Validate-Then-Quick-Deploy

**When to use:** Any production deployment where you want to minimize the deployment window and have at least 24 hours of lead time before the release.

**How it works:**

1. Run `sf project deploy validate --target-org production --test-level RunLocalTests` against production during business hours (this is safe -- it writes nothing).
2. Capture the `validatedDeployRequestId` from the output.
3. During the scheduled release window, run `sf project deploy quick --job-id <validatedDeployRequestId> --target-org production`.
4. The quick deploy skips test execution entirely, completing in minutes instead of hours.

**Why not the alternative:** Deploying directly with `sf project deploy start` runs tests during the production window, extending the outage and increasing the risk of timeout or governor limit collisions with live traffic.

### Pattern 2: Staged Dependency Deploy

**When to use:** Large releases with 50+ components spanning multiple metadata types where transitive dependency chains are complex.

**How it works:**

1. Group components into deployment waves by dependency order: schema first (objects, fields), then logic (Apex, flows), then presentation (LWC, page layouts, flexipages), then access (permission sets, profiles).
2. Validate each wave independently against the target org.
3. Deploy waves sequentially, confirming each wave succeeds before starting the next.

**Why not the alternative:** A single monolithic deployment with 200+ components is harder to debug when it fails. A single missing dependency in component 187 rolls back all 200 components. Staged deploys isolate failures to a specific wave.

### Pattern 3: Backup-Before-Deploy

**When to use:** Every production deployment, regardless of size.

**How it works:**

1. Use the same `package.xml` manifest that drives the deployment.
2. Run `sf project retrieve start --manifest package.xml --target-org production --output-dir backups/YYYY-MM-DD/`.
3. Commit or archive the backup directory before deploying.
4. If rollback is needed, deploy the backup: `sf project deploy start --source-dir backups/YYYY-MM-DD/ --target-org production`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard release with 24+ hours lead time | Validate-then-quick-deploy | Minimizes production window to minutes |
| Emergency hotfix with < 1 hour lead time | Direct deploy with RunSpecifiedTests targeting only affected classes | Fastest path; RunLocalTests may take hours in large orgs |
| Large release with 50+ components | Staged dependency deploy in 3-4 waves | Isolates failures; easier rollback per wave |
| First deploy to a newly refreshed sandbox | Run full validation first; do not assume sandbox state matches source | Sandbox refresh may have brought in production data/config that conflicts |
| Deploy includes destructive changes | Deploy constructive changes first, then destructive in a second deploy | Prevents dependency breaks during the deploy window |
| Deploy includes Flow changes | Confirm Flow version activation plan is documented separately | Flow activation state may not carry over; manual activation may be required post-deploy |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Inventory the release** -- confirm the exact list of metadata components, the deployment tool, and the target org. Cross-reference against the source control diff or work-item list.
2. **Check dependency completeness** -- query `MetadataComponentDependency` in the target org or review the `package.xml` manifest for missing transitive dependencies. Add any gaps.
3. **Back up production state** -- retrieve the current production version of every component being deployed. Store in a timestamped backup directory.
4. **Run a validation deploy** -- execute `sf project deploy validate` (or the equivalent in your tool) against the target org with the correct test level. Capture the `validatedDeployRequestId`.
5. **Confirm Apex test results** -- verify all tests pass and aggregate code coverage meets or exceeds 75%. If using `RunSpecifiedTests`, confirm each test class individually meets 75%.
6. **Check the deployment window** -- confirm trust.salesforce.com shows no maintenance for your instance, no batch jobs are scheduled during the window, and the release is scheduled off-peak.
7. **Go / No-Go decision** -- walk the Review Checklist below. If any item is unchecked, do not deploy.

---

## Review Checklist

Run through these before any production deployment:

- [ ] All metadata components in the release are listed in the manifest and match the source control diff
- [ ] Transitive dependencies verified -- no component references something missing from the target org
- [ ] Pre-release backup retrieved and stored (timestamped directory or artifact)
- [ ] Validation deploy passed in the target org with the correct test level
- [ ] Apex test coverage meets or exceeds 75% in aggregate (and per-class if using RunSpecifiedTests)
- [ ] No Apex test failures in the validation results
- [ ] Quick-deploy ID captured and still within the 10-day window (if using validate-then-quick-deploy)
- [ ] trust.salesforce.com checked -- no maintenance or advisories for the target instance
- [ ] Post-deploy manual steps documented (Flow activation, permission set assignment, data fixes)
- [ ] Rollback plan defined and tested (backup package ready to redeploy)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **RunSpecifiedTests has stricter per-class coverage** -- Unlike `RunLocalTests` which requires 75% aggregate coverage across the entire org, `RunSpecifiedTests` requires 75% coverage per class included in the deployment package. A class with 60% coverage passes under `RunLocalTests` (if the org average is above 75%) but fails under `RunSpecifiedTests`.

2. **Quick-deploy ID expires silently** -- The 10-day window from a validation deploy is a hard cutoff. There is no warning at day 9. If you attempt a quick deploy on day 11, the API returns an error and you must re-validate from scratch. Track the validation timestamp explicitly.

3. **Validation deploy can lock components** -- While a validation deploy does not write metadata, it does acquire compile locks on Apex classes during test execution. Running a validation deploy while another deploy or validation is in progress can cause lock contention errors. Check the Deployment Status page for in-flight deployments before starting a validation.

4. **Sandbox test results do not predict production** -- Apex tests that pass in a partial-copy sandbox may fail in production due to data volume differences, org-wide defaults, sharing rules, or installed managed packages. Always validate directly against production (using `checkOnly: true`), not just against a staging sandbox.

5. **Destructive changes in the same package can break dependencies** -- If your `package.xml` includes both a new field and a `destructiveChangesPost.xml` that deletes an old field referenced by a validation rule, the deploy may fail even though the destructive change is marked as "post." Process constructive and destructive changes in separate deploy operations when dependencies exist between them.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Pre-deployment checklist | Completed go/no-go checklist with all gates verified |
| Validation deploy results | Test pass/fail summary, coverage report, and validatedDeployRequestId |
| Pre-release backup | Retrieved production metadata stored in timestamped backup directory |
| Dependency gap report | List of missing transitive dependencies found during pre-deploy analysis |

---

## Related Skills

- **devops/change-set-deployment** -- Use when the deployment mechanism is the Setup UI change set workflow rather than CLI or API-based deployment.
- **admin/change-management-and-deployment** -- Use when the question is about release governance, method selection, or cross-team release process rather than the technical pre-deploy gate checks.
- **admin/sandbox-strategy** -- Use when the question is about the environment topology that feeds into the deployment pipeline.
- **apex/test-class-standards** -- Use when Apex test failures or coverage gaps are the blocking issue and the practitioner needs help writing or fixing tests.
- **apex/metadata-api-and-package-xml** -- Use when the question is about constructing or debugging the package.xml manifest itself.
