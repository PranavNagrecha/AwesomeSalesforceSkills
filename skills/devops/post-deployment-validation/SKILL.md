---
name: post-deployment-validation
description: "Verifying a Salesforce deployment worked after the metadata landed: quick deploy from a validated ID, Apex test result interpretation, Deployment Status page drill-down, functional smoke testing, JUnit/coverage output for CI, and rollback strategies. NOT for polling a deploy that is still running or stuck Pending — use devops/deployment-monitoring. NOT for the gate-check before you click deploy — use devops/pre-deployment-checklist."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I verify my Salesforce deployment actually worked"
  - "validation deploy vs quick deploy difference"
  - "deployment succeeded but features are broken in production"
  - "how to roll back a failed Salesforce deployment"
  - "quick deploy expired after 10 days what do I do"
  - "check the status of a Salesforce deploy from the CLI"
  - "generate JUnit and coverage output from a deployment for CI"
tags:
  - post-deployment-validation
  - deployment-verification
  - quick-deploy
  - validation-deploy
  - rollback
  - deployment-status
inputs:
  - Deployment ID or validated deploy request ID from a checkOnly deployment
  - Target org alias or credentials for the org being validated
  - List of metadata components included in the deployment
  - Expected functional behavior changes resulting from the deployment
outputs:
  - Post-deployment validation checklist confirming metadata landed correctly
  - Apex test result summary with per-class coverage analysis
  - Rollback plan if deployment introduced regressions
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-07-07
---

# Post Deployment Validation

This skill activates when a practitioner or agent needs to confirm that a Salesforce deployment completed successfully and that the target org is functioning correctly after the metadata landed. It covers the full lifecycle from validation deploys through quick deploy execution, test result interpretation, functional smoke testing, and rollback planning when things go wrong.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify whether this is a validation deploy (checkOnly:true) that still needs a quick deploy to commit, or a completed deployment that needs post-landing verification. These are fundamentally different states.
- Confirm the Apex test level used during the deployment. RunSpecifiedTests requires 75% code coverage per class in the deployment package, while RunLocalTests checks org-wide coverage. Test failures during deployment do not always mean the metadata failed to land — they can be pre-existing failures surfaced by the deployment.
- Know the 10-day expiration window for validation deploys. A validated deploy ID is valid for quick deploy for exactly 10 days from the time the validation completed. After that, you must re-validate from scratch.

---

## Core Concepts

### Validation Deploy (checkOnly)

A validation deploy uses `checkOnly: true` in the Metadata API deploy call or `--dry-run` in sf CLI. It runs all the same steps as a real deployment — metadata compilation, Apex test execution, and dependency resolution — but does not commit the changes to the org. On success, the Metadata API returns a qualified validation ID (the `id` field on the DeployResult). This ID can be used for a quick deploy within the 10-day validity window.

Validation deploys are the foundation of a safe deployment pipeline. They let teams run the full deployment and test cycle in production without affecting end users, confirming that the package will succeed before anyone presses the final deploy button.

### Quick Deploy

Quick deploy takes a previously validated deployment and commits it to the org without re-running Apex tests. You POST the validated deploy request ID to the Metadata API's `deployRecentValidation` endpoint or use `sf project deploy quick --use-most-recent` or `sf project deploy quick --job-id <validatedId>`. The quick deploy skips tests because they already passed during validation. The quick deploy returns a new deployment ID (distinct from the validation ID). The validation ID expires 10 days after the validation completed — after that, quick deploy will fail and you must re-validate.

### Deployment Status and Test Drill-Down

The Deployment Status page in Setup (Setup > Deployment Status) shows both in-progress and completed deployments. It is a unified view — it lists **all** deployments regardless of how they were initiated: change sets, Metadata API-based deployments, deployments started from the Salesforce Extensions for Visual Studio Code, and package installations. The page tracks deployments that are in progress or that completed in the last 30 days, so the same window that governs retrieval of a deployment's detail applies here.

While a deployment runs, the page renders real-time progress charts. The first chart shows how many components have already been deployed out of the total, including the number of components with errors. Once all components deploy, a second chart shows how many Apex tests have run out of the total and the number of errors returned. This gives live progress before any terminal status is reached, so you do not have to poll blindly.

For each completed deployment you can drill into Deployment Details to see the component-level success/failure breakdown, per-test class results with individual method pass/fail, per-class code coverage percentages, and error details for any failed components. The Deployment Details page also surfaces Apex test errors **with stack-trace information**, code coverage warnings, and information about slow tests — data that is easy to miss if you only read the aggregate pass/fail count.

The Metadata API also exposes this through `checkDeployStatus` which returns `DeployResult` with nested `RunTestsResult`, `CodeCoverageResult`, and `CodeCoverageWarning` objects. `DeployResult` additionally carries a `stateDetail` field that names exactly which component is being deployed or which Apex test class is currently running — the field that powers live-progress reporting rather than terminal-state polling. The REST deploy-status response nests the current `deployResult` alongside the original `deployOptions` (checkOnly, rollbackOnError, testLevel) and reports creation/start/lastModified/completion timestamps plus the creating and (if applicable) canceling user, so an audit trail can reconstruct who requested the deploy and with which options. The sf CLI surfaces all of this with `sf project deploy report --job-id <id>`.

### Reporting on a Deploy with `sf project deploy report`

`sf project deploy report` retrieves the status of a deploy operation for post-hoc analysis and CI integration. Two distinct — and easily confused — time windows govern it:

- `--job-id <id>` targets a specific deploy operation and is **valid for 10 days post-deployment**. This is the same 10-day figure as the validation-ID quick-deploy window, but it is a separate constraint: it governs how long you can *report on* any deploy job, not just how long a validation stays quick-deployable.
- `--use-most-recent` (`-r`) retrieves the status of the most recent deploy **but is limited to a 3-day window for performance**. If the last deploy is older than 3 days, `--use-most-recent` will not find it even though the job ID itself is still reportable for 10 days via `--job-id`. Reach for the explicit job ID once a deploy ages past 3 days.

For CI, two flags matter. `--junit` emits JUnit-format test results that pipelines consume for test reporting. `--coverage-formatters` accepts eleven output formats beyond `json`: `clover`, `cobertura`, `html-spa`, `html`, `json`, `json-summary`, `lcovonly`, `none`, `teamcity`, `text`, and `text-summary` — pick `cobertura` or `clover` for coverage-gating in most CI servers, `text-summary` for a quick human-readable console line. `--results-dir` controls where coverage and JUnit output land (it defaults to the deploy ID).

One caveat: `sf project deploy report` **doesn't update source tracking information**. It is a read-only status/reporting command, so running it never advances the local source-tracking state of an sf project — you still need a retrieve or a tracked deploy to reconcile tracking.

### Rollback Strategy

Salesforce has no native "undo deployment" button. Rollback means re-deploying the prior version of the metadata that was changed. This requires maintaining a known-good snapshot of the org's metadata before each deployment — either through source control (the prior commit) or through a pre-deployment retrieve. For Apex classes and triggers, the prior version must compile cleanly against the current org state. For declarative metadata like flows, page layouts, and permission sets, re-deploying the prior version overwrites the changes from the failed deployment.

---

## Common Patterns

### Pattern 1 — Validate Then Quick Deploy

**When to use:** Production deployments where you want a zero-test-execution commit window to minimize disruption.

**How it works:**
1. Run a validation deploy against production: `sf project deploy start --manifest package.xml --target-org prod --dry-run --test-level RunLocalTests`.
2. Wait for the validation to complete. Check status with `sf project deploy report --job-id <validationId>`.
3. Once validated, execute the quick deploy within the 10-day window: `sf project deploy quick --job-id <validationId> --target-org prod`.
4. The quick deploy returns a new deployment ID. Monitor it with `sf project deploy report`.
5. Verify components landed using the Deployment Status page or a targeted retrieve.

**Why not the alternative:** Deploying directly to production runs tests during the commit window, increasing the deployment duration and the time users are exposed to a partially deployed state.

### Pattern 2 — Post-Landing Smoke Test Protocol

**When to use:** After any deployment completes (whether via quick deploy or full deploy) to confirm the org is functioning correctly.

**How it works:**
1. Check Deployment Status in Setup for the deployment ID. Confirm all components show success.
2. Review Apex test results: open the test drill-down, check for any newly failing tests. Compare against the pre-deployment test baseline.
3. Manually verify the key functional changes — open the modified page layouts, trigger the modified flows, check that new fields appear on the expected objects.
4. If the deployment included Apex triggers or classes, execute a representative transaction in the UI and check debug logs for unexpected errors.
5. Confirm permission assignments — if new fields or objects were deployed, verify that permission sets or profiles grant access.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Production deployment with a maintenance window | Validate first, then quick deploy during the window | Quick deploy skips tests, minimizing the commit window duration |
| Deployment failed mid-way with partial component success | Re-deploy the full package; do not attempt to deploy only the failed components | Partial re-deploy can leave the org in an inconsistent intermediate state |
| Apex tests pass but functional behavior is wrong | Check code coverage per-class for gaps; add integration tests covering the regression | Passing tests with low coverage can mask broken logic paths |
| Validation expired (older than 10 days) | Re-run the full validation deploy from scratch | There is no way to extend or refresh a validation ID |
| Need to roll back a production deployment | Re-deploy the prior version from source control | Salesforce has no native undo; rollback is a forward deploy of the old version |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the deployment state** — Determine whether you are dealing with a validation deploy that needs quick deploy execution, a completed deployment that needs post-landing verification, or a failed deployment that needs diagnosis and rollback. Check the Deployment Status page or run `sf project deploy report --job-id <id>`.
2. **Review test results** — Pull the full test result detail from the Deployment Status page or Metadata API. On the Deployment Details page, check the code coverage warnings and slow-test information, not just the aggregate pass/fail. Check per-class code coverage against the 75% threshold. Identify any newly failing tests versus pre-existing failures. Use `sf project deploy report --job-id <id> --coverage-formatters json` for programmatic analysis; add `--junit` when a CI pipeline needs JUnit output, and choose a coverage formatter such as `cobertura` or `clover` for coverage gating. If the deploy is older than 3 days, use the explicit `--job-id` rather than `--use-most-recent`, whose lookup window is only 3 days.
3. **Verify component landing** — Confirm that the key components in the deployment actually landed in the target org. Use a targeted retrieve (`sf project retrieve start --metadata <Type:Name>`) or check Setup directly for critical items like permission sets, flows, and custom objects.
4. **Execute functional smoke tests** — Walk through the primary user-facing changes introduced by the deployment. Trigger relevant automations, verify field visibility, test page layouts, and confirm Lightning app navigation. Check debug logs for unexpected errors.
5. **Document and escalate** — If post-deployment issues are found, document the regression, determine whether a rollback is needed, and execute the rollback by re-deploying the prior version from source control. Update the deployment runbook with any lessons learned.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Deployment Status page shows all components as successfully deployed
- [ ] Apex test results reviewed — no newly failing tests introduced by the deployment
- [ ] Per-class code coverage meets the 75% minimum for all classes in the package
- [ ] Key functional changes verified in the target org (fields, layouts, flows, permissions)
- [ ] Permission sets and profiles updated to grant access to new components
- [ ] Rollback plan documented with the prior version commit hash or retrieved metadata snapshot
- [ ] Deployment runbook updated with validation ID, quick deploy ID, and test result summary

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Quick deploy returns a different ID than the validation** — The deployment ID from `deployRecentValidation` is a new ID, not the validation ID. Monitoring the validation ID after quick deploy will show the old validation status, not the actual commit status. Always capture and track the new ID returned by the quick deploy call.
2. **Validation IDs expire silently** — There is no notification when a validation approaches or passes its 10-day expiry. A quick deploy against an expired validation simply fails. Teams must track validation timestamps and re-validate proactively if the deploy window slips.
3. **RunSpecifiedTests coverage is per-class in the package** — When using RunSpecifiedTests as the test level, the 75% code coverage requirement applies to each individual Apex class in the deployment package, not just the org-wide average. A single under-covered class will fail the entire deployment even if the org average is well above 75%.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Post-deployment validation checklist | Filled-in checklist confirming all components landed and functional tests passed |
| Test result summary | Per-class coverage report and pass/fail breakdown from the deployment |
| Rollback plan | Document identifying the prior version and the re-deployment steps if regression is found |

---

## Related Skills

- `destructive-changes-deployment` — use when the deployment includes metadata deletions that require destructive manifests alongside the standard deployment
- `continuous-integration-testing` — use for setting up automated test execution in CI pipelines that feed into the validation deploy workflow
- `release-management` — use for broader release planning, environment promotion strategy, and deployment sequencing across multiple orgs
