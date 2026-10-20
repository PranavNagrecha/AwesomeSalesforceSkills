---
name: deployment-error-troubleshooting
description: "Use when a Salesforce metadata deployment fails and you need to diagnose the error from the DeployResult componentFailures. Trigger keywords: 'deployment failed', 'component failure', 'dependent class is invalid', 'code coverage failed', 'UNSUPPORTED_API_VERSION', 'deploy error', 'test failure blocking deploy', 'rollbackOnError', 'missing dependency deploy'. NOT for `Cannot change type`, profile FLS delta, or `entity is in use` errors — use devops/deployment-error-diagnosis. NOT for a deploy that fails because the metadata type itself is unsupported — use devops/metadata-api-coverage-gaps."
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Deployment Error Troubleshooting

This skill activates when a Salesforce metadata deployment fails and the practitioner needs to diagnose the root cause, fix the issue, and re-deploy successfully. It covers the canonical error surfaces from the Metadata API DeployResult, the most common failure categories, and the resolution patterns for each.

---

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first. Only ask for what is not already there.

Gather if not available:

- The full error output from the deployment. For sf CLI deployments, this is the output of `sf project deploy start` or the deploy report from `sf project deploy report`. For Metadata API, this is the `DeployResult` object's `details.componentFailures` array. Do not rely on a top-level `errorStatusCode` alone — the actionable details are in `componentFailures`. `details` is returned only "if the includeDetails parameter is set to true in the checkDeployStatus() call" (api_meta 264 L7589-7590).
- The deployment method: sf CLI (`sf project deploy start`), change set (Setup UI), Metadata API (Ant, Workbench), or DevOps Center.
- The target org type: production orgs enforce test coverage and rollback semantics differently from sandboxes.
- The test level: `NoTestRun`, `RunSpecifiedTests`, `RunLocalTests`, or `RunAllTestsInOrg`. The choice affects both which tests run and how coverage is evaluated.
- Whether the deployment included Apex code (classes, triggers) or only declarative metadata (objects, fields, layouts, flows).

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which exact `problem` text and `componentType` came back in `componentFailures`? | Gotcha set and Core Concepts: summary status hides the cause | The failing component, not a guess |
| Is the target production or a development environment? | Gotcha 1: `rollbackOnError` must be true for production; the defaults differ by description (api_meta 264 L4385-4389, L3454) | Whether a partial deploy can have happened |
| Which test level was used, and does the package contain Apex? | Gotcha 3: `RunSpecifiedTests` is per class; `NoTestRun` is for development environments only (api_meta 264 L3268-3276) | The coverage rule that actually applied |
| Is the named class in the package or only in the target org? | Gotcha 2: deploys recompile dependent Apex (apexdev 264 L43228-43235) | Whether to fix the org, the package, or both |
| What API version do the `-meta.xml` files and `sfdx-project.json` declare? | Gotcha 5: `UNSUPPORTED_API_VERSION` is documented for retired versions (api_meta 264 L1314-1315) | Whether the version is too old, not just mismatched |
| Was a validation run, and when? | Gotcha 4: a validation is usable for 10 days (api_meta 264 L3579; sfdx_dev 264 L14372) | A quick-deploy plan with an expiry date |
| Does any Profile or PermissionSet name a permission the org no longer has? | Gotcha 6: the deploy-error text is UNVERIFIED but the triage steps are safe | A scan of `userPermissions` before the next deploy |

A proper configuration adds the exact failing component, the rollback and test settings that were in force, and a validation with an expiry date, instead of re-running the deploy and hoping.

---

## Core Concepts

### DeployMessage.componentFailures Is the Canonical Error Surface

The Metadata API `DeployResult` returns a top-level `status` and `errorStatusCode`, but these are summary fields. The actionable error details live in `details.componentFailures` — an array of `DeployMessage` objects. Each `DeployMessage` includes `componentType`, `fullName`, `problem`, and `problemType` (Error or Warning). When troubleshooting, always read `componentFailures` first. The `sf project deploy report --json` command exposes these as the `result.details.componentFailures` array (UNVERIFIED (2026-10-20): the CLI JSON shape is not in the corpus; `sf project deploy report --use-most-recent` is shown at sfdx_dev 264 L14411, and the Java sample reads `getComponentFailures()`, api_meta 264 L1868-1869).

Common `problemType` values and what they indicate:

- **Error** with `problem` containing "Dependent class is invalid" — a class in the target org that depends on a deployed class failed to compile. The dependent class may not even be in the deployment package. UNVERIFIED (2026-10-20): the message text is Help-level; the corpus documents the mechanism instead (deploys recompile Apex, apexdev 264 L43228-43235).
- **Error** with `problem` containing "Missing reference" — a component in the package references metadata that does not exist in the target org and is not included in the package. UNVERIFIED (2026-10-20): message text not in the corpus.
- **Error** with `UNSUPPORTED_API_VERSION` — corrected: the corpus documents it as what SOAP API returns for an operation on a retired API version: "If you request any resource or use an operation from a retired API version, SOAP API returns 500:UNSUPPORTED_API_VERSION" (api_meta 264 L1314-1315). Retired means old: 21.0-30.0 since Summer '25, 7.0-20.0 since Summer '22, and 31.0-40.0 deprecated from Summer '27 and retired from Summer '28 (api_meta 264 L1289-1303). An earlier version of this skill said the error meant a version newer than the target org supports; UNVERIFIED (2026-10-20): that is Help-level and the error name for a too-new version is not in the corpus.

### Dependency Errors and Transitive Compilation

When Apex is deployed, Salesforce recompiles not just the deployed classes but also every class that depends on them in the target org: "Each org's Apex code is automatically recompiled before completing a metadata deploy, package install, or package upgrade ... if you deploy a custom field, all the classes that use that custom field are recompiled" (apexdev 264 L43228-43235). Compile on deploy is on for production and full sandboxes and cannot be turned off in production; for other sandboxes, developer and scratch orgs it is off by default (apexdev 264 L43229-43232). If any of those dependent classes were already broken (a pre-existing compilation error in the org), the deployment fails even though the deployed code is correct (UNVERIFIED (2026-10-20): failing on a pre-broken dependent is Help-level). This is the "Dependent class is invalid and needs recompilation" error. From API 68.0 you can return compilation results for just the invalid classes and triggers instead of recompiling the org, via Setup or the Tooling API `apexCompileResults` resource (apexdev 264 L45121-45123). The fix is to repair or delete the broken class in the target org, not to change the deployment package.

Pre-broken classes in the org are common after sandbox refreshes, partial deploys, or manual metadata edits. The error message names the broken class and its compilation error.

### rollbackOnError and Partial Deploys

The `rollbackOnError` option in the Metadata API controls whether a deployment failure rolls back all components or leaves successfully-deployed components in place. Critical behavior differences:

The corpus does not tie the default to the org type. It says "rollbackOnError ... Indicates whether any failure causes a complete rollback (true) or not (false) ... This parameter must be set to true if you're deploying to a production org" (api_meta 264 L4385-4389); the deploy() default is stated as false there and in the REST deployRequest request (api_meta 264 L3252-3255) but "Defaults to true" in two other descriptions (api_meta 264 L3454, L7684-7688). An earlier version of this skill said production defaults to true and sandboxes to false; treat that as UNVERIFIED (2026-10-20) and set `rollbackOnError` explicitly. What is documented: with `rollbackOnError` false, "whatever set of actions can be performed without errors are performed, and errors are returned for the remaining actions" (api_meta 264 L4386-4388) — a 10-component deployment where 1 fails can leave 9 deployed, which is a partially-applied state that is difficult to diagnose and dangerous to leave in place.

For the sf CLI, the documented control is the opposite flag: `sf project deploy start --ignore-errors` deploys "regardless of whether the deployment contains errors (not recommended if deploying to a production org)" (sfdx_dev 264 L13626-13627), so omitting it is how you keep rollback on. An earlier version said `--test-level RunLocalTests` "implicitly enforces full validation" and gives atomic behaviour; UNVERIFIED (2026-10-20): no corpus line links test level to rollback. To set `rollbackOnError=true` explicitly, call the Metadata API `deploy()` with `DeployOptions.setRollbackOnError(true)` (api_meta 264 L4521).

### Test Level Semantics and Coverage Calculation

The `testLevel` parameter changes both which tests run and how coverage is evaluated:

| Test Level | Which Tests Run | Coverage Scope | Production Allowed |
|---|---|---|---|
| `NoTestRun` | None | N/A | No: "applies only to deployments to development environments, such as sandbox, Developer Edition, or trial organizations" and is their default (api_meta 264 L3268-3270) |
| `RunSpecifiedTests` | Only named tests | "Each class and trigger in the deployment package must be covered ... for a minimum of 75%", computed individually (api_meta 264 L3271-3275) | Yes |
| `RunRelevantTests` (beta) | Tests the platform selects from the payload and its dependencies | Same per-class and per-trigger 75% (api_meta 264 L3277-3285, L2741-2743) | Beta |
| `RunLocalTests` | All tests except those from installed managed and unlocked packages; default for production deployments with Apex classes or triggers (api_meta 264 L3286-3288) | Overall coverage at least 75% and "Apex triggers have some coverage" (api_meta 264 L3582) | Yes |
| `RunAllTestsInOrg` | All tests, including managed package tests (api_meta 264 L3289-3290) | Overall 75% and triggers covered (api_meta 264 L3582) | Yes |

The earlier "every trigger >= 1%" figure is UNVERIFIED (2026-10-20): the guides say "some test coverage" (api_meta 264 L3582; apexdev 264 L735), not 1%.

The critical difference: `RunSpecifiedTests` evaluates coverage per class — every Apex class in the deployment must individually achieve 75% coverage from the specified tests. `RunLocalTests` evaluates org-wide aggregate coverage. A class with 50% coverage can pass `RunLocalTests` if the org average is above 75%, but the same class will fail `RunSpecifiedTests`.

### API Version Mismatch

Metadata XML files declare their API version (e.g., `<apiVersion>61.0</apiVersion>` in `-meta.xml` files). UNVERIFIED (2026-10-20): that a declared version higher than the target org's release fails with `UNSUPPORTED_API_VERSION` or a shape validation error, and the sandbox-to-production-before-upgrade scenario below, are Help-level and not in the corpus; the only documented use of the code is for retired versions (see Core Concepts above). What is documented: Winter '27 is API 68.0 (api_meta 264 L2) and versions 41.0 through 68.0 are supported (api_meta 264 L1289). Compare the declared version with the support table before assuming a mismatch.

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
4. To prevent partial deploys in the future, keep `rollbackOnError` true: do not pass `--ignore-errors` (sfdx_dev 264 L13626-13627) or set it explicitly in a Metadata API deploy (api_meta 264 L4521). An earlier version said `--test-level RunLocalTests` gives atomic behaviour; UNVERIFIED (2026-10-20): no corpus line says so.

**Why not the alternative:** Deploying only the failed components may work but leaves the practitioner unsure whether the previously-succeeded components are truly at the expected version, especially if source was modified between the first and second deploy.

### Pattern 3: Fix RunSpecifiedTests Coverage Failures

**When to use:** Deployment passes with `RunLocalTests` but fails with `RunSpecifiedTests` due to insufficient code coverage on individual classes.

**How it works:**

1. Identify which classes failed coverage from the `codeCoverageWarnings` in the deploy result.
2. Understand that `RunSpecifiedTests` calculates coverage per class, not org-wide. Each class must individually hit 75% from the tests you specify.
3. Either add the missing test classes to the `--tests` list, or write additional test methods to cover the under-tested class.
4. Validate before the real deploy: the guide shows `sf project deploy validate ... --test-level RunSpecifiedTests` for the quick-deploy flow (sfdx_dev 264 L14365-14370) and a `sf project deploy start --dry-run` form (api_meta 264 L4114); the `--tests TestA TestB` argument form is shown at sfdx_dev 264 L14339.

**Why not the alternative:** Switching to `RunLocalTests` to avoid per-class coverage checks runs all org tests, which is slower and may surface unrelated test failures in large orgs.

---

## Decision Guidance

| Error Symptom | Root Cause Category | Resolution Path |
|---|---|---|
| "Dependent class is invalid and needs recompilation" | Pre-broken class in target org | Compile or fix the named class in the target org, then re-deploy |
| "Missing reference to [ComponentName]" | Missing transitive dependency | Add the missing component to the deployment package or deploy it first |
| Code coverage below 75% (RunSpecifiedTests) | Per-class coverage gap | Add more tests to the --tests list or increase coverage for the flagged class |
| Code coverage below 75% (RunLocalTests) | Org-wide coverage gap | Write tests for uncovered classes across the org, not just the deployed package |
| `UNSUPPORTED_API_VERSION` | Documented for a retired API version (api_meta 264 L1314-1315); the too-new-version cause is UNVERIFIED (2026-10-20) | Raise `sourceApiVersion` / `-meta.xml` versions that are retired (see the support table), and only then consider the too-new case |
| Component deployed but behavior unchanged | Stale metadata cache (UNVERIFIED (2026-10-20): Help-level, not in the corpus) | Redeploy and verify; do not rely on a whitespace change or Compile All as a cure |
| Partial deploy left sandbox in broken state | `rollbackOnError` was false (api_meta 264 L4386-4388) | Re-deploy the full package with rollback on; do not use `--ignore-errors` |

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

1. **`rollbackOnError` false leaves a partially-applied state** (the default is org-type-independent in the corpus and inconsistent between descriptions, api_meta 264 L3252-3255, L3454, L4385-4389; it must be true for production) — A failed deployment with rollback off leaves a partially-applied state. Many practitioners do not realize this until they find their sandbox with half-deployed metadata and no clear way to determine which components succeeded.
2. **RunSpecifiedTests uses per-class 75%, not org-wide** (api_meta 264 L3271-3275) — Practitioners switching from RunLocalTests to RunSpecifiedTests for faster deploys are surprised when individual classes fail coverage even though the org average is above 75%. The coverage model is fundamentally different between the two test levels.
3. **Dependent class recompilation can fail on classes not in the package** (recompilation on deploy: apexdev 264 L43228-43235) — Salesforce recompiles all transitive dependents when an Apex class is deployed. A class that was already broken in the target org will fail recompilation, blocking the deployment. The error names the broken class but the practitioner's instinct is to look at their own code.
4. **API version mismatch is invisible until deploy time** (UNVERIFIED (2026-10-20): the too-new-version behaviour is Help-level; the documented error is for retired versions) — The `sourceApiVersion` in `sfdx-project.json` or individual `-meta.xml` files may reference a version the target org does not support yet. This only manifests at deploy time, not during local development or scratch org testing on preview releases.
5. **Quick Deploy has a 10-day expiry** ("validated successfully for the target environment within the last 10 days", api_meta 264 L3579; sfdx_dev 264 L14372) — A validated deployment qualifies for Quick Deploy (no re-testing) for 10 days. UNVERIFIED (2026-10-20): that the package must be byte-identical and that any change invalidates the validation are not stated in the corpus; the documented conditions are a successful validation in the last 10 days with tests passed and coverage met (api_meta 264 L3579-3592). Treat the package as frozen anyway.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Root cause diagnosis | Identification of the error category, the specific failing component, and why it failed |
| Resolution plan | Step-by-step instructions for fixing the root cause and re-deploying |
| Preventive checklist | Items to add to the deployment runbook or CI pipeline to prevent recurrence |

---

## Related Skills

- devops/destructive-changes-deployment — when the deployment error is caused by a destructive manifest issue (wrong variant, undeletable type, missing companion package.xml)
- devops/change-set-deployment — when the deployment method is a change set through the Setup UI rather than sf CLI or Metadata API
- devops/post-deployment-validation — for validating that a successful deployment actually works as expected after it lands
- devops/rollback-and-hotfix-strategy — when a deployment error in production requires an emergency rollback or hotfix
- devops/scratch-org-management — when deployment errors in scratch orgs stem from org shape or feature configuration mismatches
