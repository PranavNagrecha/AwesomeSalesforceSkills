# LLM Anti-Patterns — Post Deployment Validation

Common mistakes AI coding assistants make when generating or advising on Post Deployment Validation.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting a native "rollback" or "undo deployment" API

**What the LLM generates:** "Use the Metadata API rollback endpoint to revert the deployment" or "Call `sf project deploy rollback --job-id <id>`" — implying Salesforce has a built-in undo mechanism for deployments.

**Why it happens:** Many deployment platforms (AWS, Kubernetes, Azure DevOps) have native rollback commands. LLMs transfer this pattern to Salesforce, which does not have one. There is no `rollback` subcommand in sf CLI and no rollback endpoint in the Metadata API.

**Correct pattern:**

```bash
# Rollback = re-deploy the prior version from source control
git checkout HEAD~1 -- force-app/
sf project deploy start \
  --source-dir force-app \
  --target-org production \
  --test-level RunLocalTests
```

**Detection hint:** Look for the words "rollback endpoint", "undo deploy", or "sf project deploy rollback" in generated output.

---

## Anti-Pattern 2: Treating the validation ID as the quick deploy ID

**What the LLM generates:** "After quick deploy completes, check status with `sf project deploy report --job-id <validationId>`" — reusing the validation ID to monitor the quick deploy.

**Why it happens:** LLMs see the validation ID used in the `sf project deploy quick --job-id` command and assume the same ID tracks the resulting deployment. In reality, quick deploy returns a new, separate deployment ID.

**Correct pattern:**

```bash
# Quick deploy returns a NEW job ID — capture it
sf project deploy quick --job-id 0Af7g00000XXXXX --target-org prod
# Output: Deploy ID: 0Af7g00000YYYYY

# Monitor the NEW ID, not the validation ID
sf project deploy report --job-id 0Af7g00000YYYYY
```

**Detection hint:** If the same `--job-id` value appears in both `deploy quick` and the subsequent `deploy report`, the LLM likely reused the validation ID.

---

## Anti-Pattern 3: Claiming quick deploy re-runs tests

**What the LLM generates:** "Quick deploy will re-run a subset of tests to verify" or "Quick deploy runs tests faster than a full deploy." This misrepresents what quick deploy does.

**Why it happens:** The name "quick deploy" suggests a faster variant of deploy, leading LLMs to assume it still runs tests but faster. In reality, quick deploy skips test execution entirely because the tests already passed during the validation step.

**Correct pattern:**

```text
Quick deploy commits the validated metadata without re-running any Apex tests.
Tests are skipped because they already passed during the validation deploy (checkOnly:true).
The validation must be less than 10 days old for quick deploy to succeed.
```

**Detection hint:** Look for phrases like "quick deploy runs tests", "quick deploy executes a subset", or "quick deploy validates" in the generated output.

---

## Anti-Pattern 4: Suggesting checkOnly deploys land metadata in the org

**What the LLM generates:** "Run a checkOnly deploy to push the metadata to production for testing" or "After the validation deploy, your changes are live in the org."

**Why it happens:** LLMs confuse "validation deploy" with "deploying to a validation/staging environment." A checkOnly deploy runs the full compilation and test cycle but does NOT commit any metadata to the org. The org is completely unchanged after a validation deploy.

**Correct pattern:**

```text
A validation deploy (checkOnly:true / --dry-run) does NOT modify the target org.
It only confirms that the deployment WOULD succeed.
To actually land the metadata, you must either:
  1. Run a quick deploy using the validation ID, or
  2. Run a full (non-checkOnly) deployment.
```

**Detection hint:** Look for claims that a "dry-run" or "checkOnly" deploy makes changes visible in the org, or that users can "test the changes" after a validation deploy.

---

## Anti-Pattern 5: Confusing org-wide 75% coverage with per-class 75% coverage

**What the LLM generates:** "Ensure your org has at least 75% overall code coverage to pass the deployment" — when the deployment uses RunSpecifiedTests.

**Why it happens:** The 75% org-wide coverage rule is the most commonly cited Salesforce deployment requirement. LLMs default to this rule without distinguishing between test levels. With RunSpecifiedTests, the 75% threshold applies per individual class in the deployment package, not as an org average.

**Correct pattern:**

```text
RunSpecifiedTests: 75% coverage required PER CLASS in the deployment package.
RunLocalTests / RunAllTestsInOrg: 75% org-wide average required.

A single class at 60% coverage will fail a RunSpecifiedTests deployment
even if the org average is 95%.
```

**Detection hint:** Look for "75% overall" or "org-wide coverage" advice in the context of RunSpecifiedTests deployments. The correct advice should reference per-class coverage.

---

## Anti-Pattern 6: Inventing sf CLI flags that do not exist

**What the LLM generates:** Flag variations like `sf project deploy status --live`, `sf project deploy resume --from-validation`, or `sf project deploy quick --skip-validation`.

**Why it happens:** LLMs generate plausible-looking CLI commands by pattern-matching against other CLI tools, and the `sf` rewrite renamed almost every `sfdx force:source:*` command, so stale forms and invented flags are both common.

**Do not over-correct.** `sf project deploy validate` and `sf project deploy preview` are **real, documented commands** and are the backbone of the safest production deployment path on the platform. Rejecting them is a worse failure than accepting a fake flag, because it pushes teams off validate-then-quick-deploy and onto a live deploy against production.

**Correct pattern:**

```bash
# Validate-only deployment (returns a job ID; does not execute)
sf project deploy validate --manifest package.xml --test-level RunLocalTests --target-org prod

# Quick deploy the previously validated job (skips re-running tests)
sf project deploy quick --job-id <validationId> --target-org prod

# Preview what would deploy, including conflicts and ignored files
sf project deploy preview --target-org prod

# Check deployment status
sf project deploy report --job-id <deployId>

# Resume a canceled/timed-out deploy
sf project deploy resume --job-id <deployId>
```

**Detection hint:** the documented `sf project deploy` subcommands are `start`, `validate`, `quick`, `preview`, `report`, `resume`, `cancel`, and the `pipeline` group (`pipeline start` / `validate` / `quick` / `report` / `resume`, Beta). Anything outside that list is likely hallucinated — but check the current CLI reference before rejecting, rather than relying on a memorised allow-list. `sf project list metadata` is a genuine fake; the real command is `sf org list metadata`.


---

## Anti-Pattern 7: Declaring the real `sf project deploy validate` command a hallucination

**What the LLM generates:** An anti-pattern rule, lint check, or review comment asserting that `sf project deploy validate` does not exist, usually with an allow-list of "the only real subcommands" that omits `validate` and `preview` — and a rewrite to `sf project deploy start --dry-run`.

**Why it happens:** Over-correction. The `sfdx` → `sf` migration produced a genuine flood of stale and invented commands, so "this sf subcommand is probably fake" is a high-prior heuristic. A model that has been primed to hunt CLI hallucinations then applies it to a command it does not happen to recall, and an allow-list written from memory silently omits the less-frequently-typed members. `--dry-run` (which does exist on `deploy start`) is close enough in meaning to feel like the "real" version, completing the false correction.

This one is worth calling out separately because of **where it lands**: an anti-patterns file is the document an assistant reads specifically to decide what to *reject*. An inverted claim there does not merely mislead, it is executed as a rule — every future review refuses the correct command.

**Correct version:** From the Salesforce CLI command reference — `sf project deploy validate`: *"Validate a metadata deployment without actually executing it."* It returns a job ID that `sf project deploy quick --job-id` consumes to deploy without re-running tests, which is the standard production release pattern. `sf project deploy preview` also exists: *"Preview a deployment to see what will deploy to the org, the potential conflicts, and the ignored files."*

**Detection hint:** any rule that asserts a command is fake **without a link to the CLI reference section it is absent from**. Concretely: grep this repo for `sf project deploy validate` — it appears as a recommended command in dozens of skills (e.g. `skills/architect/ci-cd-pipeline-architecture`), so a file claiming it is hallucinated is contradicting the rest of the corpus, and internal contradiction is the cheapest available signal that one side is wrong. Generalisable rule: **a claim that something does not exist needs a source too.** Negative claims feel safe and are not.
