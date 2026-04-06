# LLM Anti-Patterns — Rollback And Hotfix Strategy

Common mistakes AI coding assistants make when generating or advising on Rollback And Hotfix Strategy.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting a Native Salesforce Rollback Button

**What the LLM generates:** "Navigate to Setup > Deployment Status and click the Rollback button to undo the last deployment."

**Why it happens:** LLMs generalize from platforms that have native rollback (AWS, Heroku, Kubernetes) and assume Salesforce has an equivalent feature. Training data may include outdated or speculative forum posts mentioning rollback functionality.

**Correct pattern:**

```text
Salesforce has no native metadata rollback mechanism. Rollback = re-deploying
the previous version of every changed component. Use a pre-deploy archive
or reconstruct from source control, then deploy that state forward.
```

**Detection hint:** Look for phrases like "rollback button", "undo deployment", "revert deployment in Setup", or "automatic rollback" — none of these exist in Salesforce.

---

## Anti-Pattern 2: Assuming All Metadata Types Are Rollbackable via Deployment

**What the LLM generates:** "Deploy the previous version of all changed components including Record Types and Picklist values to roll back completely."

**Why it happens:** LLMs treat all metadata types uniformly, not knowing that certain types have special API restrictions. The Metadata API documentation does not prominently flag these exceptions in a single location.

**Correct pattern:**

```text
Record Types cannot be deleted via Metadata API. Picklist values are
additive-only — the API will not remove existing values. Active Flow
versions cannot be deactivated via deployment. These require manual
Setup intervention as part of the rollback plan.
```

**Detection hint:** Rollback instructions that include Record Types, Picklist values, or Flow version changes in a `destructiveChanges.xml` or assume deploying an older Flow definition will deactivate the current active version.

---

## Anti-Pattern 3: Confusing Quick Deploy with Skipping Tests Entirely

**What the LLM generates:** "Use `sf project deploy start --test-level NoTestRun` to deploy the hotfix faster by skipping all tests."

**Why it happens:** LLMs conflate quick deploy (which relies on a prior successful validation) with the `NoTestRun` test level. In production orgs, `NoTestRun` is not permitted for deployments that include Apex — the platform will reject the deployment.

**Correct pattern:**

```bash
# Step 1: Validate with tests
sf project deploy validate --manifest package.xml \
  --test-level RunLocalTests --target-org production
# Step 2: Quick deploy using the validation ID (tests already passed)
sf project deploy quick --job-id 0Af5g00000EXAMPLE --target-org production
```

**Detection hint:** Any suggestion to use `--test-level NoTestRun` for a production deployment containing Apex code, or any claim that quick deploy means "no tests needed."

---

## Anti-Pattern 4: Building the Hotfix Branch from the Development Branch

**What the LLM generates:** "Create a hotfix branch from `develop`: `git checkout -b hotfix/fix develop`"

**Why it happens:** LLMs default to standard Git Flow guidance where feature branches come from develop. For hotfixes, this is wrong because the develop branch may contain unreleased features that would accidentally reach production.

**Correct pattern:**

```bash
# Hotfix must branch from the production-matching tag or branch
git checkout -b hotfix/fix v3.2-production
# or
git checkout -b hotfix/fix main  # if main tracks production
```

**Detection hint:** `git checkout -b hotfix/ develop` or `git checkout -b hotfix/ feature/` — any hotfix branch created from a non-production source.

---

## Anti-Pattern 5: Omitting the Merge-Back Step After Hotfix Deployment

**What the LLM generates:** A hotfix workflow that ends at "deploy to production" without mentioning merging the hotfix branch back into the development branch.

**Why it happens:** LLMs focus on the immediate problem (fix production) and truncate the workflow before the cleanup step. The merge-back is not part of the Salesforce deployment process itself, so it falls outside the LLM's "Salesforce deployment" mental model.

**Correct pattern:**

```bash
# After successful production deployment:
git checkout main && git merge hotfix/fix
git checkout develop && git merge hotfix/fix
git push origin main develop
git branch -d hotfix/fix
```

**Detection hint:** A hotfix workflow that ends with `sf project deploy` and has no subsequent `git merge` step. The word "merge" or "back-merge" should appear in any complete hotfix guide.

---

## Anti-Pattern 6: Suggesting Metadata API Rollback via SOAP `cancelDeploy`

**What the LLM generates:** "Call the `cancelDeploy()` SOAP method to roll back an in-progress deployment."

**Why it happens:** The Metadata API does have a `cancelDeploy` operation, but it only cancels a deployment that is still queued or in progress. It does not undo a completed deployment. LLMs conflate "cancel" with "rollback."

**Correct pattern:**

```text
cancelDeploy() stops a deployment that has not yet finished. Once a
deployment completes successfully, the changes are committed and
cancelDeploy has no effect. To revert completed changes, build and
deploy a rollback package from the pre-deploy archive.
```

**Detection hint:** References to `cancelDeploy`, `checkDeployStatus` with rollback intent, or any suggestion that the Metadata SOAP API can undo a completed deployment.
