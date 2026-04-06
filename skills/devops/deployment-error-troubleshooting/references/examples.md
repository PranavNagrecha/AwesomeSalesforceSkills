# Examples — Deployment Error Troubleshooting

## Example 1: Fixing a "Dependent class is invalid" Error

**Context:** A developer deploys an updated `AccountService` class to a sandbox. The deployment fails with: "Dependent class is invalid and needs recompilation: LegacyAccountHelper — line 42, column 1: Method does not exist or incorrect signature: void processAccount(Account, Boolean)."

**Problem:** The developer assumes the error is in `AccountService` and spends time reviewing the deployment package. In reality, `LegacyAccountHelper` — a class already in the target org but not in the package — was broken before the deployment. It references a method signature in `AccountService` that was changed in a previous partial deploy but never reconciled.

**Solution:**

1. Open Setup > Apex Classes in the target org.
2. Find `LegacyAccountHelper` and click Compile.
3. The class fails to compile — confirming a pre-existing break.
4. Fix `LegacyAccountHelper` to use the correct method signature and include it in the deployment package.
5. Re-deploy the full package including both `AccountService` and the fixed `LegacyAccountHelper`.

```bash
# Validate the fix with a dry run first
sf project deploy start --dry-run \
  --source-dir force-app/main/default/classes/AccountService.cls \
  --source-dir force-app/main/default/classes/LegacyAccountHelper.cls \
  --test-level RunLocalTests \
  --target-org mySandbox
```

**Why it works:** The error message names the broken class explicitly. Fixing it at the source and including it in the package ensures all dependent classes compile cleanly during deployment.

---

## Example 2: Resolving RunSpecifiedTests Coverage Failure

**Context:** A CI pipeline deploys an `OpportunityValidator` class using `RunSpecifiedTests` with `--tests OpportunityValidatorTest`. The deployment fails with: "Code coverage for class OpportunityValidator is 65%. Minimum required is 75%."

**Problem:** The same deployment passes with `RunLocalTests` because the org-wide coverage is 82%. The developer does not understand why switching to `RunSpecifiedTests` changed the outcome.

**Solution:**

1. Check the deploy result JSON for `codeCoverageWarnings` to see which classes are under-covered.
2. Understand that `RunSpecifiedTests` evaluates each deployed class individually against 75%.
3. Add test methods to `OpportunityValidatorTest` to cover the missing lines, or add another test class that exercises `OpportunityValidator` to the `--tests` list.

```bash
# After adding coverage, validate
sf project deploy start --dry-run \
  --source-dir force-app/main/default/classes/OpportunityValidator.cls \
  --test-level RunSpecifiedTests \
  --tests OpportunityValidatorTest OpportunityIntegrationTest \
  --target-org production
```

**Why it works:** `RunSpecifiedTests` uses per-class coverage. Adding more test classes to the `--tests` parameter ensures the coverage of every deployed class meets the 75% threshold individually.

---

## Example 3: Diagnosing an API Version Mismatch

**Context:** A team develops on a sandbox that was upgraded to Summer '25 (API v62.0). They set `sourceApiVersion` to `62.0` in `sfdx-project.json`. When deploying to production, which is still on Spring '25 (API v61.0), the deployment fails with `UNSUPPORTED_API_VERSION`.

**Problem:** The error message is terse and does not explain that the issue is the gap between the source metadata API version and the target org's release version.

**Solution:**

1. Check the target org's current API version: Setup > Company Information, or run `sf org display --target-org production --json` and check the `apiVersion` field.
2. Update `sfdx-project.json` to set `sourceApiVersion` to the target org's version (e.g., `61.0`).
3. Scan all `-meta.xml` files for `<apiVersion>62.0</apiVersion>` and downgrade to `61.0`.
4. Re-deploy.

```bash
# Find all meta files with the wrong API version
grep -rl "<apiVersion>62.0</apiVersion>" force-app/ --include="*-meta.xml"

# Bulk-replace (after confirming the list)
find force-app -name "*-meta.xml" -exec sed -i '' 's/<apiVersion>62.0</<apiVersion>61.0</g' {} +
```

**Why it works:** The metadata XML schema is versioned. Downgrading to the target org's supported version ensures all XML elements are recognized by the deployment engine.

---

## Anti-Pattern: Reading Only the Top-Level Error Status

**What practitioners do:** Run `sf project deploy start`, see "Deploy failed", and attempt to fix based on the summary line or top-level `errorStatusCode` without examining `componentFailures`.

**What goes wrong:** The top-level status says "Failed" but does not identify which component failed or why. The practitioner guesses at the root cause, makes changes, re-deploys, and gets a different error — or the same one — wasting deployment cycles.

**Correct approach:** Always run `sf project deploy report --json` and read the `result.details.componentFailures` array. Each entry has `fullName`, `componentType`, `problem`, and `problemType`. The `problem` field contains the specific error message that identifies the root cause.
