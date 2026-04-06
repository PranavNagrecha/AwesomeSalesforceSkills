# LLM Anti-Patterns -- Pre-Deployment Checklist

Common mistakes AI coding assistants make when generating or advising on pre-deployment checklists for Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating RunLocalTests and RunSpecifiedTests Coverage Rules

**What the LLM generates:** "Ensure 75% code coverage before deploying" without specifying which test level or clarifying aggregate vs. per-class requirements.

**Why it happens:** Training data treats 75% as a single universal rule. In reality, `RunLocalTests` enforces 75% aggregate across all local Apex in the org, while `RunSpecifiedTests` enforces 75% per class included in the deployment package. These are materially different constraints.

**Correct pattern:**

```text
If using RunLocalTests: confirm 75% aggregate code coverage across all local Apex in the org.
If using RunSpecifiedTests: confirm 75% coverage per Apex class included in the deployment package.
```

**Detection hint:** Any checklist that says "75% coverage" without specifying which test level and whether it is aggregate or per-class.

---

## Anti-Pattern 2: Suggesting Validation Deploy Writes Metadata

**What the LLM generates:** "Be careful when running validation deploys — they may partially update metadata if interrupted" or recommending validation deploys only during off-peak hours due to write risk.

**Why it happens:** LLMs conflate validation deploys with actual deploys. A validation deploy (`checkOnly: true`) never writes metadata to the org. It compiles Apex, resolves dependencies, and runs tests, but commits nothing. It is safe to run at any time.

**Correct pattern:**

```text
A validation deploy (checkOnly: true / sf project deploy validate) is a zero-write operation.
It is safe to run during business hours against production. It will not modify any metadata.
```

**Detection hint:** Any guidance that warns about data loss, partial writes, or timing restrictions specific to validation deploys.

---

## Anti-Pattern 3: Inventing Quick-Deploy CLI Flags That Do Not Exist

**What the LLM generates:** `sf project deploy start --quick-deploy --validation-id <id>` or `sfdx force:source:deploy --quickdeploy`.

**Why it happens:** LLMs hallucinate plausible-sounding flags. The actual CLI command is `sf project deploy quick --job-id <validatedDeployRequestId>`. There is no `--quick-deploy` flag on `sf project deploy start`.

**Correct pattern:**

```bash
sf project deploy quick --job-id 0Af5g00000XXXXX --target-org production
```

**Detection hint:** Any `sf project deploy start` command with a `--quick` or `--quickdeploy` flag, or any `sfdx` command using `--quickdeploy` as a flag on `force:source:deploy`.

---

## Anti-Pattern 4: Recommending MetadataComponentDependency Without Tooling API Context

**What the LLM generates:** "Run this SOQL query: `SELECT ... FROM MetadataComponentDependency`" without mentioning that this object is only available through the Tooling API, not the standard SOQL API.

**Why it happens:** LLMs treat all SOQL-queryable objects as accessible through the same endpoint. `MetadataComponentDependency` is a Tooling API object and must be queried through `/services/data/vXX.0/tooling/query/` or via the CLI with `sf data query --use-tooling-api`.

**Correct pattern:**

```bash
sf data query --query "SELECT MetadataComponentName, RefMetadataComponentName FROM MetadataComponentDependency WHERE ..." --use-tooling-api --target-org production
```

**Detection hint:** Any `MetadataComponentDependency` query that does not specify `--use-tooling-api` or the Tooling API endpoint.

---

## Anti-Pattern 5: Treating Sandbox Test Results as a Production Gate

**What the LLM generates:** "All tests pass in staging, so the deployment is ready for production" or checklists that mark "tests pass in sandbox" as the final test gate.

**Why it happens:** LLMs do not account for environmental differences between sandboxes and production: data volume, managed packages, sharing rules, org-wide defaults, and installed AppExchange packages all differ. Tests that pass in a sandbox can fail in production for reasons unrelated to the code change.

**Correct pattern:**

```text
Sandbox test pass is a development gate, not a release gate.
The release gate is a validation deploy (checkOnly: true) run directly against production.
```

**Detection hint:** Any checklist where the final test verification step references a sandbox environment instead of a production validation deploy.

---

## Anti-Pattern 6: Omitting the 10-Day Quick-Deploy Expiration

**What the LLM generates:** "Run a validation deploy, then quick-deploy whenever you're ready" without mentioning the 10-day expiration window or the fact that re-validating invalidates prior quick-deploy IDs.

**Why it happens:** Training data mentions quick deploy as a feature but often omits the time constraint. The 10-calendar-day window is a hard cutoff with no warning.

**Correct pattern:**

```text
A successful validation deploy earns a quick-deploy ID valid for 10 calendar days.
After 10 days, the ID expires silently and you must re-validate.
Re-validating the same components invalidates any prior quick-deploy ID.
```

**Detection hint:** Any quick-deploy guidance that does not mention the 10-day window or the invalidation-on-re-validation behavior.

---

## Anti-Pattern 7: Forgetting Pre-Release Backup in the Checklist

**What the LLM generates:** Checklists that go straight from "tests pass" to "deploy to production" without a backup step.

**Why it happens:** Backup is not part of the Metadata API deploy flow itself -- it is a separate retrieve operation. LLMs that focus on the deploy command sequence often skip the retrieve step that should precede it.

**Correct pattern:**

```bash
# Before deploying: retrieve current production state
sf project retrieve start --manifest package.xml --target-org production --output-dir backups/2026-04-05/

# Then deploy
sf project deploy start --manifest package.xml --target-org production
```

**Detection hint:** Any pre-deployment checklist that does not include a backup or retrieve step before the deploy command.
