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

**Why it happens:** LLMs conflate validation deploys with actual deploys. A validation deploy (`checkOnly: true`) validates "but not deploy[s]" the components (api_meta 264 L3596) and commits nothing. It still takes the single deployment slot, so it queues behind a running deploy (L4246-4249).

**Correct pattern:**

```text
A validation deploy (checkOnly: true / sf project deploy validate) is a zero-write operation.
It does not modify metadata; it queues like any deployment, so check the Deployment Status page first.
```

**Detection hint:** Any guidance that warns about data loss or partial writes from a validation deploy.

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

## Anti-Pattern 4: Recommending a Dependency Query Without Tooling API Context (object UNVERIFIED, 2026-10-20)

**What the LLM generates:** "Run this SOQL query: `SELECT ... FROM MetadataComponentDependency`" without mentioning that this object is only available through the Tooling API, not the standard SOQL API.

**Why it happens:** LLMs treat all SOQL-queryable objects as accessible through the same endpoint. UNVERIFIED (2026-10-20): `MetadataComponentDependency` as a Tooling API object is in neither corpus. The `--use-tooling-api` flag on `sf data query` is documented (pkg2_dev 264 L19969).

**Correct pattern:**

```bash
sf data query --query "SELECT MetadataComponentName, RefMetadataComponentName FROM MetadataComponentDependency WHERE ..." --use-tooling-api --target-org production
```

**Detection hint:** Any `MetadataComponentDependency` query that does not specify `--use-tooling-api` or the Tooling API endpoint.

---

## Anti-Pattern 5: Treating Sandbox Test Results as a Production Gate

**What the LLM generates:** "All tests pass in staging, so the deployment is ready for production" or checklists that mark "tests pass in sandbox" as the final test gate.

**Why it happens:** LLMs do not account for environmental differences between sandboxes and production. UNVERIFIED (2026-10-20): the specific differences (data volume, managed packages, sharing rules, org-wide defaults) are this package's reasoning, not corpus statements. Tests that pass in a sandbox can fail in production for reasons unrelated to the code change.

**Correct pattern:**

```text
Sandbox test pass is a development gate, not a release gate.
The release gate is a validation deploy (checkOnly: true) run directly against production.
```

**Detection hint:** Any checklist where the final test verification step references a sandbox environment instead of a production validation deploy.

---

## Anti-Pattern 6: Omitting the 10-Day Quick-Deploy Expiration

**What the LLM generates:** "Run a validation deploy, then quick-deploy whenever you're ready" without mentioning the 10-day validation window.

**Why it happens:** Training data mentions quick deploy as a feature but often omits the time constraint. The window is "within the last 10 days" (api_meta 264 L3579); "hard cutoff with no warning" is UNVERIFIED (2026-10-20).

**Correct pattern:**

```text
A successful validation deploy earns a quick-deploy ID usable within 10 days.
After 10 days the validation no longer qualifies and you must re-validate (UNVERIFIED, 2026-10-20: "expires silently").
UNVERIFIED (2026-10-20): that re-validating the same components invalidates any prior quick-deploy ID.
```

**Detection hint:** Any quick-deploy guidance that does not mention the 10-day window.

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
