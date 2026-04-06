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

**What the LLM generates:** Commands like `sf project deploy validate`, `sf project deploy status --live`, `sf project deploy resume --from-validation`, or `sf project deploy quick --skip-validation`.

**Why it happens:** LLMs generate plausible-looking CLI commands by pattern-matching against other CLI tools. The sf CLI has specific subcommands (`deploy start`, `deploy quick`, `deploy report`, `deploy resume`) and specific flags, but LLMs frequently hallucinate variations.

**Correct pattern:**

```bash
# Validation deploy
sf project deploy start --manifest package.xml --dry-run --test-level RunLocalTests --target-org prod

# Quick deploy from validation
sf project deploy quick --job-id <validationId> --target-org prod

# Check deployment status
sf project deploy report --job-id <deployId>

# Resume a canceled/timed-out deploy
sf project deploy resume --job-id <deployId>
```

**Detection hint:** Any `sf project deploy` subcommand other than `start`, `quick`, `report`, `resume`, `cancel`, or `pipeline` is likely hallucinated. Cross-check against the Salesforce CLI Reference.
