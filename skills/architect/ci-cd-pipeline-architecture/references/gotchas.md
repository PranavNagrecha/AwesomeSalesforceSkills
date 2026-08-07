# Gotchas — CI/CD Pipeline Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in pipeline design.

## Gotcha 1: No Native Rollback for Declarative Metadata

**What happens:** After a Flow, Page Layout, Custom Object field, or Validation Rule is deployed to production, there is no "undo deployment" or "rollback deployment" button in Salesforce. The Deployment Status page shows no rollback option. The only recovery path is to revert the source in Git and re-deploy the previous version, or to deploy a destructive changes package to remove the offending component.

**When it occurs:** Every production deployment of declarative metadata carries this risk. It becomes acute when a Flow activation change breaks a business-critical process and the team assumes there is a platform-level rollback.

**How to avoid:** Document the rollback procedure explicitly in the pipeline runbook before the first release, not after an incident. For each stage transition, record: (a) the git revert command to produce the previous state, (b) whether a destructive changes package is needed, and (c) the estimated redeploy time including Apex tests. For high-risk changes, perform a dry-run revert on a staging sandbox before the production deploy to confirm the rollback procedure works. Full Sandbox refresh is available as a last-resort rollback for the sandbox itself, but it destroys all sandbox-only changes.

---

## Gotcha 2: Apex Test Timeout Produces a Non-Test-Failure Error

**What happens:** If a single Apex test class runs for more than 10 minutes, the deployment (or validation-only deploy) fails with a timeout error, not a test assertion failure. The error message references a deployment timeout, not a failed test. CI pipeline scripts that parse JUnit XML or deployment result JSON looking for `<failure>` or `RunResult.Status = Failed` will find nothing and may incorrectly mark the gate as passed — or will fail with an unhandled error code and give a confusing error message.

**When it occurs:** Most common in orgs with large test data factories that run DML against complex object graphs in every test method, or tests that invoke callouts with real synchronous wait logic. Becomes more frequent as the org grows and test execution time creeps upward unmonitored.

**How to avoid:** Monitor average and 95th-percentile test class execution times as part of the CI pipeline. Set a warning threshold at 5 minutes per class. Explicitly handle deployment exit codes that indicate timeout (distinct from test failure) in CI scripts. Split test classes that approach the limit. For the CI gate at Stage 1, run only the most directly related tests (RunSpecifiedTests or a curated suite) rather than RunLocalTests, to reduce the risk of hitting the aggregate time limit.

---

## Gotcha 3: DevOps Center Has No Stage-Count Limit — Sandbox Supply Is the Real Ceiling

**What happens:** A team maps a complex environment topology, hears (or is told by an assistant) that DevOps Center caps pipelines at some number of stages, and rejects the tool on that basis — buying Copado or AutoRABIT for a constraint that does not exist. Salesforce's pipeline planning documentation states: **"Your pipeline can contain any number of pipeline stages."**

**When it occurs:** Regulated industries (financial services, healthcare, government) are most susceptible, because they genuinely do need separate UAT sandboxes per business unit, multiple sign-off environments, and a pre-production sandbox mirroring production. Those topologies invite a plausible-sounding "you'll exceed the stage limit" objection.

**The constraint that is real:** Every DevOps Center stage requires its own connected environment and its own long-lived branch. The ceiling on a deep pipeline is therefore your **sandbox licence entitlement** — how many Developer, Developer Pro, Partial Copy, and Full sandboxes the edition provides, and the refresh intervals on each — not a stage counter. A 9-stage pipeline that needs three Full sandboxes fails on Full-sandbox entitlement, not on stage count. Promotion is also sequential: each additional stage adds a merge and a deploy to every work item's path, so deep pipelines cost lead time.

**How to avoid:** Map the required environment topology and price it against the org's actual sandbox entitlement before choosing a promotion tool. If you conclude DevOps Center is unsuitable, name the specific capability gap driving that (non-linear/branching promotion, per-stage approvals, data seeding, back-promotion) — never a stage-count limit. Consolidating stages remains a good idea for lead-time reasons; it is not forced by a limit.

---

## Gotcha 4: Quick Deploy Window Expires After 96 Hours

**What happens:** A validation-only deploy produces a deployment ID that can be used for a "quick deploy" — re-deploying the validated package without re-running Apex tests, reducing the production change window significantly. However, this ID expires after **96 hours** (4 days). If the CAB approval cycle, a release freeze, or a scheduling conflict pushes the production deploy beyond that window, the full validation must be re-run.

**When it occurs:** Organizations with weekly change advisory boards that approve on Tuesday for Friday deployment often find the validation ID has aged out if the validation was run on Monday. Change freezes over quarter-end or holidays are particularly risky.

**How to avoid:** Design the pipeline to run the Stage 4 validation-only deploy as close to the scheduled production deploy window as possible — ideally within 48 hours. Document the 96-hour expiry in the runbook and build an automated check in the pipeline that computes the age of the validation ID and warns if it is approaching expiry. If the window is missed, treat re-validation as a standard pre-deploy step, not an incident.

---

## Gotcha 5: Partial Copy Sandbox Does Not Reproduce Production Data Volume

**What happens:** Integration and regression tests that pass on a Partial Copy sandbox may fail on a Full Sandbox or production because Partial Copy sandboxes contain a representative but not full-volume sample of production data. SOQL queries that return well within the 50,000 row limit in QA may hit governor limits in production when the underlying data has grown. Batch Apex jobs that complete in 2 minutes on a Partial Copy may exceed heap or CPU time limits on production data volumes.

**When it occurs:** Any data-intensive component — batch Apex, complex SOQL in triggers, report snapshots, or Flows that query large datasets — is at risk. Most commonly surfaces in financial services, retail, and healthcare orgs with large Account, Contact, or Transaction record counts.

**How to avoid:** Reserve a Full Sandbox specifically for performance and data-volume testing. Do not use it as the primary QA environment — treat it as a dedicated pre-production gate. For batch Apex, always test against full data volume before a production deploy. Include explicit heap size and CPU time assertions in Apex unit tests for code that processes large collections.

---

## Gotcha 6: Metadata Deployed via DevOps Center Cannot Be Simultaneously Managed via Changesets

**What happens:** Once a component is managed by DevOps Center (tracked in the pipeline's Git branch), deploying the same component via a Change Set in the same org creates a conflict. The DevOps Center pipeline will detect an unexpected diff on the next promotion, potentially overwriting the Change Set deployment with the Git-tracked version — or failing the promotion with a merge conflict.

**When it occurs:** Common in organizations that are mid-migration from change sets to DevOps Center, or that have a separate admin team using change sets for "quick fixes" while developers use the DevOps Center pipeline for features.

**How to avoid:** Establish a single promotion tool per org as a hard policy once DevOps Center is activated. Remove Change Set permissions from users whose changes are managed through DevOps Center. During the migration period, document a freeze window where no Change Set deployments are made to environments already tracked in DevOps Center pipelines.
