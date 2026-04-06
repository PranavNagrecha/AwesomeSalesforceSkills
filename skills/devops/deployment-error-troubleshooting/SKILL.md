---
name: deployment-error-troubleshooting
description: "Use when a Salesforce metadata deployment fails and you need to diagnose and fix the error. Trigger keywords: 'deployment failed', 'component failure', 'dependent class is invalid', 'code coverage failed', 'UNSUPPORTED_API_VERSION', 'deploy error', 'test failure blocking deploy', 'rollbackOnError', 'missing dependency deploy'. NOT for authoring destructive changes manifests (use destructive-changes-deployment). NOT for CI/CD pipeline setup (use github-actions-for-salesforce or gitlab-ci-for-salesforce). NOT for change set mechanics (use change-set-deployment)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "my deployment failed with a component error and I don't understand the message"
  - "dependent class is invalid and needs recompilation"
  - "deployment failing because of code coverage even though tests pass locally"
  - "UNSUPPORTED_API_VERSION error during metadata deploy"
  - "partial deployment went through in sandbox and left metadata in a broken state"
  - "RunSpecifiedTests failing even though RunLocalTests passes"
tags:
  - deployment
  - troubleshooting
  - metadata-api
  - deploy-errors
  - code-coverage
  - dependency-errors
inputs:
  - the full deployment error message or DeployResult output
  - deployment method (sf CLI, change set, Metadata API, DevOps Center)
  - target org type (production, sandbox, scratch org)
  - test level used (NoTestRun, RunSpecifiedTests, RunLocalTests, RunAllTestsInOrg)
  - list of components in the deployment package
outputs:
  - root cause diagnosis for the deployment failure
  - step-by-step resolution plan
  - preventive checklist to avoid recurrence
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Deployment Error Troubleshooting

This skill activates when a Salesforce metadata deployment fails and the practitioner needs to diagnose the root cause, fix the issue, and re-deploy successfully. It covers the canonical error surfaces from the Metadata API DeployResult, the most common failure categories, and the resolution patterns for each.

---

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first. Only ask for what is not already there.

Gather if not available:

- The full error output from the deployment. For sf CLI deployments, this is the output of `sf project deploy start` or the deploy report from `sf project deploy report`. For Metadata API, this is the `DeployResult` object's `details.componentFailures` array. Do not rely on a top-level `errorStatusCode` alone — the actionable details are always in `componentFailures`.
- The deployment method: sf CLI (`sf project deploy start`), change set (Setup UI), Metadata API (Ant, Workbench), or DevOps Center.
- The target org type: production orgs enforce test coverage and rollback semantics differently from sandboxes.
- The test level: `NoTestRun`, `RunSpecifiedTests`, `RunLocalTests`, or `RunAllTestsInOrg`. The choice affects both which tests run and how coverage is evaluated.
- Whether the deployment included Apex code (classes, triggers) or only declarative metadata (objects, fields, layouts, flows).

---

## Core Concepts

### DeployMessage.componentFailures Is the Canonical Error Surface

The Metadata API `DeployResult` returns a top-level `status` and `errorStatusCode`, but these are summary fields. The actionable error details live in `details.componentFailures` — an array of `DeployMessage` objects. Each `DeployMessage` includes `componentType`, `fullName`, `problem`, and `problemType` (Error or Warning). When troubleshooting, always read `componentFailures` first. The `sf project deploy report --json` command exposes these as the `result.details.componentFailures` array.

Common `problemType` values and what they indicate:

- **Error** with `problem` containing "Dependent class is invalid" — a class in the target org that depends on a deployed class failed to compile. The dependent class may not even be in the deployment package.
- **Error** with `problem` containing "Missing reference" — a component in the package references metadata that does not exist in the target org and is not included in the package.
- **Error** with `UNSUPPORTED_API_VERSION` — the metadata XML files specify an API version the target org does not support, or the `sfdx-project.json` sourceApiVersion is ahead of the org's release.

### Dependency Errors and Transitive Compilation

When Apex is deployed, Salesforce recompiles not just the deployed classes but also every class that depends on them in the target org. If any of those dependent classes were already broken (a pre-existing compilation error in the org), the deployment fails even though the deployed code is correct. This is the "Dependent class is invalid and needs recompilation" error. The fix is to repair or delete the broken class in the target org, not to change the deployment package.

Pre-broken classes in the org are common after sandbox refreshes, partial deploys, or manual metadata edits. The error message names the broken class and its compilation error.

### rollbackOnError and Partial Deploys

The `rollbackOnError` option in the Metadata API controls whether a deployment failure rolls back all components or leaves successfully-deployed components in place. Critical behavior differences:

- **Production orgs**: `rollbackOnError` defaults to `true`. A single component failure rolls back the entire deployment atomically.
- **Sandbox orgs**: `rollbackOnError` defaults to `false`. A deployment with 10 components where 1 fails will leave 9 components deployed and 1 failed. This creates a partially-applied state that is difficult to diagnose and dangerous to leave in place.

The sf CLI `sf project deploy start` does not expose a direct `--rollback-on-error` flag for source deploys. When using `--metadata` or `--manifest` deployments, the behavior follows the org-type default. To force atomic rollback in a sandbox, use the Metadata API `deploy()` call directly with `rollbackOnError=true`, or use the `sf project deploy start --test-level RunLocalTests` flag (which implicitly enforces full validation).

### Test Level Semantics and Coverage Calculation

The `testLevel` parameter changes both which tests run and how coverage is evaluated:

| Test Level | Which Tests Run | Coverage Scope | Production Allowed |
|---|---|---|---|
| `NoTestRun` | None | N/A | No (unless no Apex in package) |
| `RunSpecifiedTests` | Only named tests | Per-class 75% for each class in the package | Yes |
| `RunLocalTests` | All non-managed-package tests | Org-wide 75% + every trigger >= 1% | Yes |
| `RunAllTestsInOrg` | All tests including managed packages | Org-wide 75% + every trigger >= 1% | Yes |

The critical difference: `RunSpecifiedTests` evaluates coverage per class — every Apex class in the deployment must individually achieve 75% coverage from the specified tests. `RunLocalTests` evaluates org-wide aggregate coverage. A class with 50% coverage can pass `RunLocalTests` if the org average is above 75%, but the same class will fail `RunSpecifiedTests`.

### API Version Mismatch

Every Salesforce metadata XML file declares its API version in the top-level element (e.g., `<apiVersion>61.0</apiVersion>` in `-meta.xml` files). When the declared version is higher than the target org's current release, the deployment fails with `UNSUPPORTED_API_VERSION` or a shape validation error because the XML schema for the newer version includes elements the org does not recognize.

This commonly occurs when deploying from a sandbox on a newer release to a production org that has not yet been upgraded, or when `sfdx-project.json` sets `sourceApiVersion` to a preview release.

---

## Common Patterns

### Pattern 1: Diagnose and Fix a Dependency Compilation Error

**When to use:** Deployment fails with "Dependent class is invalid and needs recompilation" and the named class is not in the deployment package.

**How it works:**

1. Read the `componentFailures` to identify the broken dependent class name and its compilation error.
2. Open the target org. Navigate to Setup > Apex Classes, find the named class, and click Compile.
3. If the class fails to compile, the pre-existing compilation error is the root cause. Fix the class in the target org (or deploy a fix for it as part of the package), then re-deploy.
4. If the class compiles successfully after manual recompilation, the issue was a stale compilation cache. Re-deploy without changes — the recompilation resolved the dependency.

**Why not the alternative:** Practitioners often assume the error is in their deployed code and spend time debugging the wrong class. The error message explicitly names the broken dependent class — always check that class first.

### Pattern 2: Resolve a Partial Deploy in a Sandbox

**When to use:** A sandbox deployment partially succeeded (some components deployed, some failed) and the org is in an inconsistent state.

**How it works:**

1. Run `sf project deploy report --json` to get the full `DeployResult`. Separate `componentSuccesses` from `componentFailures`.
2. Fix the failing components in the source project.
3. Re-deploy the complete package (not just the failures). This ensures all components are at the expected version. The successfully-deployed components will be overwritten with identical versions (no-op), and the previously-failed components will be retried.
4. To prevent partial deploys in the future, deploy with `--test-level RunLocalTests` in sandboxes, which triggers full validation and atomic behavior.

**Why not the alternative:** Deploying only the failed components may work but leaves the practitioner unsure whether the previously-succeeded components are truly at the expected version, especially if source was modified between the first and second deploy.

### Pattern 3: Fix RunSpecifiedTests Coverage Failures

**When to use:** Deployment passes with `RunLocalTests` but fails with `RunSpecifiedTests` due to insufficient code coverage on individual classes.

**How it works:**

1. Identify which classes failed coverage from the `codeCoverageWarnings` in the deploy result.
2. Understand that `RunSpecifiedTests` calculates coverage per class, not org-wide. Each class must individually hit 75% from the tests you specify.
3. Either add the missing test classes to the `--tests` list, or write additional test methods to cover the under-tested class.
4. Validate with `sf project deploy start --dry-run --test-level RunSpecifiedTests --tests TestA TestB` before the real deploy.

**Why not the alternative:** Switching to `RunLocalTests` to avoid per-class coverage checks runs all org tests, which is slower and may surface unrelated test failures in large orgs.

---

## Decision Guidance

| Error Symptom | Root Cause Category | Resolution Path |
|---|---|---|
| "Dependent class is invalid and needs recompilation" | Pre-broken class in target org | Compile or fix the named class in the target org, then re-deploy |
| "Missing reference to [ComponentName]" | Missing transitive dependency | Add the missing component to the deployment package or deploy it first |
| Code coverage below 75% (RunSpecifiedTests) | Per-class coverage gap | Add more tests to the --tests list or increase coverage for the flagged class |
| Code coverage below 75% (RunLocalTests) | Org-wide coverage gap | Write tests for uncovered classes across the org, not just the deployed package |
| `UNSUPPORTED_API_VERSION` | Source API version > target org version | Lower `sourceApiVersion` in sfdx-project.json or update -meta.xml files |
| Component deployed but behavior unchanged | Stale metadata cache | Clear the org's metadata cache: redeploy with a trivial whitespace change, or use Setup > Apex Classes > Compile All |
| Partial deploy left sandbox in broken state | `rollbackOnError=false` default on sandboxes | Re-deploy the full package; consider enforcing `RunLocalTests` to get atomic behavior |

---

## Recommended Workflow

Step-by-step instructions for diagnosing and resolving a deployment failure:

1. **Capture the full error output.** Run `sf project deploy report --json` or read the DeployResult from your CI log. Look at `details.componentFailures`, not just the top-level status. Record every `fullName`, `componentType`, and `problem` value.
2. **Classify the error category.** Match the `problem` text against the Decision Guidance table above. The five main categories are: dependency compilation errors, missing references, coverage failures, API version mismatches, and partial deploys.
3. **Check the target org state.** For dependency errors, open the named class in Setup and attempt manual compilation. For missing references, query the target org to confirm whether the referenced component exists. For coverage errors, check whether the test level is appropriate for the deployment context.
4. **Apply the resolution.** Follow the resolution path from the Decision Guidance table. Fix the root cause in the source project or in the target org as appropriate.
5. **Validate before re-deploying.** Use `sf project deploy start --dry-run` (checkOnly deploy) with the same test level to confirm the fix works without applying changes. This avoids creating another partial deploy if the fix is incomplete.
6. **Re-deploy and verify.** Run the full deployment. After success, spot-check the deployed components in the target org to confirm expected behavior.
7. **Document the root cause.** Add the failure pattern to the team's deployment runbook so future releases include the preventive check.

---

## Review Checklist

Run through these before marking a deployment error resolved:

- [ ] Full `componentFailures` array was read, not just the top-level error status
- [ ] Error category was correctly identified (dependency, missing reference, coverage, API version, partial deploy)
- [ ] Root cause was fixed in the correct location (source project vs. target org)
- [ ] A checkOnly/dry-run deploy confirmed the fix before the real deploy
- [ ] The full package was re-deployed (not just the previously-failed components)
- [ ] Target org was spot-checked to confirm the deployment landed correctly
- [ ] Preventive step was added to the deployment runbook or CI pipeline

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Sandbox rollbackOnError defaults to false** — Unlike production, sandboxes do not roll back on failure by default. A failed deployment leaves a partially-applied state. Many practitioners do not realize this until they find their sandbox with half-deployed metadata and no clear way to determine which components succeeded.
2. **RunSpecifiedTests uses per-class 75%, not org-wide** — Practitioners switching from RunLocalTests to RunSpecifiedTests for faster deploys are surprised when individual classes fail coverage even though the org average is above 75%. The coverage model is fundamentally different between the two test levels.
3. **Dependent class recompilation can fail on classes not in the package** — Salesforce recompiles all transitive dependents when an Apex class is deployed. A class that was already broken in the target org will fail recompilation, blocking the deployment. The error names the broken class but the practitioner's instinct is to look at their own code.
4. **API version mismatch is invisible until deploy time** — The `sourceApiVersion` in `sfdx-project.json` or individual `-meta.xml` files may reference a version the target org does not support yet. This only manifests at deploy time, not during local development or scratch org testing on preview releases.
5. **Quick Deploy has a 10-day expiry and requires the exact same package** — A validated deployment qualifies for Quick Deploy (no re-testing) for 10 days, but the package must be identical. Any change to any component in the package invalidates the validation and requires a fresh validate-only deploy.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Root cause diagnosis | Identification of the error category, the specific failing component, and why it failed |
| Resolution plan | Step-by-step instructions for fixing the root cause and re-deploying |
| Preventive checklist | Items to add to the deployment runbook or CI pipeline to prevent recurrence |

---

## Related Skills

- destructive-changes-deployment — when the deployment error is caused by a destructive manifest issue (wrong variant, undeletable type, missing companion package.xml)
- change-set-deployment — when the deployment method is a change set through the Setup UI rather than sf CLI or Metadata API
- post-deployment-validation — for validating that a successful deployment actually works as expected after it lands
- rollback-and-hotfix-strategy — when a deployment error in production requires an emergency rollback or hotfix
- scratch-org-management — when deployment errors in scratch orgs stem from org shape or feature configuration mismatches
