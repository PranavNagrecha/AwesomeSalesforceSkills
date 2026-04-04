# LLM Anti-Patterns — Release Management

## 1. Recommending `--test-level NoTestRun` for Production Deployments

**What the LLM generates wrong:** When asked to provide a production deployment command, the LLM sometimes suggests `--test-level NoTestRun` to skip tests and speed up the deployment.

**Why it happens:** `NoTestRun` is a valid test level used for sandbox deployments. The LLM sees it in documentation and suggests it without distinguishing between sandbox and production contexts.

**Correct pattern:** `NoTestRun` is not allowed for production deployments. Salesforce enforces test execution for production regardless of the CLI flag. The valid test levels for production are `RunLocalTests`, `RunAllTestsInOrg`, and `RunSpecifiedTests`. For fastest production deployment, use Validation Deploy + Quick Deploy.

**Detection hint:** Look for `--test-level NoTestRun` in any command targeting a production org.

---

## 2. Claiming Quick Deploy Can Be Run at Any Time After Validation

**What the LLM generates wrong:** The LLM states "after running a validation deploy, you can run Quick Deploy whenever you are ready."

**Why it happens:** Documentation states Quick Deploy uses the validated deployment — the LLM omits the 10-day expiration.

**Correct pattern:** The validated deployment ID is valid for exactly 10 days from the validation date. After 10 days, `sf project deploy quick` returns an error indicating the validation has expired and a new validation deploy must be run.

**Detection hint:** Any Quick Deploy guidance that omits the "10-day validity window" caveat.

---

## 3. Suggesting `--source-tracking ignore` as a Normal Deployment Practice

**What the LLM generates wrong:** When a deployment has tracking conflicts, the LLM suggests `--ignore-conflicts` or `--source-tracking ignore` as the routine fix.

**Why it happens:** These flags exist for specific recovery scenarios, but the LLM treats them as standard options.

**Correct pattern:** `--ignore-conflicts` discards source tracking state and can cause the tracking file and org to diverge permanently. Use it only to recover from corrupted tracking state, not as a routine workaround. The correct approach to tracking conflicts is to understand what changed in the org vs source and explicitly resolve the conflict.

**Detection hint:** Any deployment command that includes `--ignore-conflicts` without explaining the specific conflict being resolved.

---

## 4. Providing a Rollback Command That Does Not Exist

**What the LLM generates wrong:** The LLM suggests commands like `sf project deploy rollback` or `sf deploy undo` for production rollback.

**Why it happens:** Other deployment tools (Kubernetes, Terraform) have native rollback commands. The LLM analogizes to those.

**Correct pattern:** Salesforce has no native `rollback` command. Rollback is always "redeploy the prior version": retrieve the prior metadata, then run `sf project deploy start` with that metadata. For packages, rollback is `sf package install --package <prior-version-id>`.

**Detection hint:** Any mention of `rollback`, `undo`, or `revert` as CLI commands in a Salesforce deployment context.

---

## 5. Assuming Org-Based Version Numbers Exist Natively

**What the LLM generates wrong:** The LLM suggests querying a system field like `ApiVersion` or `VersionNumber` to track what version of metadata is in an org.

**Why it happens:** 2GP packages have version numbers. The LLM generalizes this to all Salesforce deployments.

**Correct pattern:** Org-based deployments have no native version numbers on individual metadata components. The only built-in version indicator is the `ApiVersion` XML attribute, which is the Salesforce platform API version of the component (e.g., 61.0), not a business release version. Teams must maintain version tracking via git tags, release notes, or a custom Version tracking object.

**Detection hint:** Any claim that `ApiVersion` or a similar field tracks "which release" a component is on in an org-based deployment.
