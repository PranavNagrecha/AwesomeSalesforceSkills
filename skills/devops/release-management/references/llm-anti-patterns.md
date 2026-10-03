# LLM Anti-Patterns: Release Management

Common mistakes AI coding assistants make when generating or advising on Salesforce release management. Each entry gives the mistake, why it happens, and the correct move.

## Anti-Pattern 1: Recommending `--test-level NoTestRun` for Production Deployments

**What the LLM generates wrong:** When asked for a production deployment command, the LLM suggests `--test-level NoTestRun` to speed things up.

**Why it happens:** `NoTestRun` is a valid CLI option and appears in many sandbox examples. The LLM does not separate sandbox and production contexts.

**Correct pattern:** The Metadata API Developer Guide says NoTestRun "applies only to deployments to development environments, such as sandbox, Developer Edition, or trial organizations." Production deployments use RunLocalTests, RunAllTestsInOrg, RunSpecifiedTests, or the RunRelevantTests beta. For the fastest release night, validate early and quick deploy.

**Detection hint:** `--test-level NoTestRun` in any command or CI step that targets a production alias.

---

## Anti-Pattern 2: Claiming Quick Deploy Works at Any Time After Validation

**What the LLM generates wrong:** "After running a validation deploy, you can run Quick Deploy whenever you are ready."

**Why it happens:** The LLM remembers that quick deploy reuses a validation and drops the expiry.

**Correct pattern:** The validation must have succeeded for the same target within the last 10 days (`deployRecentValidation()`). Pass the job ID explicitly, because `--use-most-recent` only finds validations from the last 3 days. Re-validate when the window lapses.

**Detection hint:** Quick deploy guidance with no "10 days" caveat, or a runbook that uses `--use-most-recent` with a gap of more than 3 days.

---

## Anti-Pattern 3: Suggesting Conflict-Ignoring Flags as a Normal Production Practice

**What the LLM generates wrong:** When a deployment reports conflicts, the LLM adds `--ignore-conflicts` (or an invented `--source-tracking ignore` flag) as the routine fix, including for production.

**Why it happens:** The flag exists and makes the error go away in a scratch org, so the LLM generalizes it.

**Correct pattern:** `--source-tracking` is not an `sf project deploy start` flag. The CLI help says `--ignore-conflicts` "applies only to orgs that allow source tracking. It has no effect on orgs that don't allow it, such as production orgs." In a source-tracked org it deploys local files "even if they overwrite changes in the org", so resolve the conflict deliberately instead of overwriting someone's work.

**Detection hint:** `--ignore-conflicts` with no explanation of the conflict, or any `--source-tracking` flag on a deploy command.

---

## Anti-Pattern 4: Providing a Rollback Command That Does Not Exist

**What the LLM generates wrong:** `sf project deploy rollback` or `sf deploy undo`.

**Why it happens:** Kubernetes, Terraform, and similar tools have native rollback commands, and the LLM analogizes.

**Correct pattern:** Salesforce has no rollback command. Org-based rollback is "redeploy the archived prior version" with `sf project deploy start --manifest backups/<date>/package.xml`. For unlocked packages a lower-version install is possible but is not a rollback. For managed 2GP, downgrade isn't allowed, so roll forward.

**Detection hint:** `rollback`, `undo`, or `revert` used as a Salesforce CLI subcommand.

---

## Anti-Pattern 5: Assuming Org-Based Version Numbers Exist Natively

**What the LLM generates wrong:** The LLM suggests querying `ApiVersion` or a `VersionNumber` field to tell which release is deployed.

**Why it happens:** Packages have version numbers, and the LLM generalizes to all metadata.

**Correct pattern:** Org-based metadata has no business version number. The `apiVersion` element is the platform API version of the component (for example 67.0). Track releases with git tags, release notes, or a custom version record.

**Detection hint:** Any claim that `ApiVersion` or a similar field tracks which release a component is on.

---

## Anti-Pattern 6: Describing Managed 2GP Patches With Patch Orgs and `--package-id`

**What the LLM generates wrong:** "Create a patch org from the released version, then run `sf package version create --package-id 04t...`."

**Why it happens:** Patch orgs are the managed 1GP mechanism, and the LLM merges 1GP and 2GP material.

**Correct pattern:** The Second-Generation Managed Packaging Developer Guide says managed 2GP "doesn't use packaging or patch orgs." Increment the patch number in `sfdx-project.json`, set a managed-released ancestor with the same major and minor numbers, and run `sf package version create --package <alias or 0Ho ID>`. Patch versioning must be enabled by Partner Support for packages that passed security review. `sf package version create` has a `--package` flag, not `--package-id`.

**Detection hint:** "patch org" in a 2GP answer, or `--package-id` on `sf package version create`.

---

## Anti-Pattern 7: Using `--ignore-errors` to Push a Partial Release to Production

**What the LLM generates wrong:** "Add `--ignore-errors` so the components that are fine still deploy."

**Why it happens:** Partial success sounds pragmatic, and the flag exists on `sf project deploy start`.

**Correct pattern:** The Metadata API `rollbackOnError` option "must be set to true if you're deploying to a production org." Treat a failed component as a failed release, fix it, and redeploy the whole set.

**Detection hint:** `--ignore-errors` or `-r` on a deploy command that targets production.
