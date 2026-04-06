# LLM Anti-Patterns — sf CLI and SFDX Essentials

Common mistakes AI coding assistants make when generating or advising on Salesforce CLI commands and SFDX project setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using deprecated sfdx commands instead of the current sf CLI

**What the LLM generates:**

```bash
sfdx force:source:push -u myOrg
sfdx force:org:create -f config/project-scratch-def.json
sfdx force:auth:web:login
```

**Why it happens:** LLMs were trained on older documentation that used the `sfdx` CLI with `force:` namespaced commands. The `sfdx` binary is deprecated; the current CLI is `sf` with restructured command names. The old commands may still work as aliases but are not maintained and may be removed.

**Correct pattern:**

```bash
sf project deploy start --target-org myOrg
sf org create scratch --definition-file config/project-scratch-def.json --alias myScratch
sf org login web
```

**Detection hint:** Commands starting with `sfdx force:` — should be migrated to `sf` equivalents.

---

## Anti-Pattern 2: Using --sourcepath instead of --source-dir or --manifest

**What the LLM generates:**

```bash
sf project deploy start --sourcepath force-app/main/default/classes/MyClass.cls
```

**Why it happens:** LLMs use the old `--sourcepath` flag from `sfdx force:source:deploy`. The current `sf project deploy start` uses `--source-dir` for directory-based deployment and `--manifest` for package.xml-based deployment.

**Correct pattern:**

```bash
# Deploy a specific directory
sf project deploy start --source-dir force-app/main/default/classes --target-org myOrg

# Deploy using a manifest
sf project deploy start --manifest manifest/package.xml --target-org myOrg

# Deploy specific metadata components
sf project deploy start --metadata ApexClass:MyClass --target-org myOrg
```

**Detection hint:** `--sourcepath` flag in `sf` commands — should be `--source-dir`, `--manifest`, or `--metadata`.

---

## Anti-Pattern 3: Not setting a default org or passing --target-org

**What the LLM generates:**

```bash
sf project deploy start
# Error: No default target org set. Use -o or --target-org
```

**Why it happens:** LLMs omit the `--target-org` flag assuming a default is set. In CI/CD pipelines and fresh environments, no default org exists. The command fails silently or with a confusing error.

**Correct pattern:**

```bash
# Always specify the target explicitly in scripts and CI
sf project deploy start --target-org myOrg --source-dir force-app

# Or set a default for interactive use
sf config set target-org myOrg
```

**Detection hint:** `sf project deploy` or `sf project retrieve` commands without `--target-org` or `-o` flag, especially in CI scripts.

---

## Anti-Pattern 4: Generating a scratch org definition with invalid or outdated fields

**What the LLM generates:**

```json
{
  "orgName": "My Scratch Org",
  "edition": "Enterprise",
  "features": ["MultiCurrency", "StateAndCountryPicklist"],
  "settings": {
    "lightningExperienceSettings": {
      "enableS1DesktopEnabled": true
    }
  }
}
```

**Why it happens:** LLMs generate scratch org definitions with field names from older API versions. Fields like `enableS1DesktopEnabled` are renamed or removed. Feature names change between releases. Using outdated fields causes scratch org creation to fail with opaque errors.

**Correct pattern:**

```json
{
  "orgName": "My Scratch Org",
  "edition": "Enterprise",
  "features": ["MultiCurrency"],
  "settings": {
    "lightningExperienceSettings": {
      "enableLightningExperience": true
    }
  }
}
```

**Detection hint:** Scratch org definition JSON with `enableS1DesktopEnabled`, or feature names not found in current documentation.

---

## Anti-Pattern 5: Using sf org login jwt without specifying the instance URL for sandboxes

**What the LLM generates:**

```bash
sf org login jwt --client-id CONSUMER_KEY --jwt-key-file server.key --username admin@myorg.sandbox
# Defaults to login.salesforce.com — fails for sandbox orgs
```

**Why it happens:** LLMs omit `--instance-url` for JWT auth. Sandbox orgs use `test.salesforce.com` (or a custom domain). Without the correct instance URL, authentication fails with a misleading "invalid grant" error.

**Correct pattern:**

```bash
# For sandbox orgs
sf org login jwt --client-id CONSUMER_KEY --jwt-key-file server.key \
  --username admin@myorg.sandbox \
  --instance-url https://test.salesforce.com \
  --alias mySandbox

# For production orgs
sf org login jwt --client-id CONSUMER_KEY --jwt-key-file server.key \
  --username admin@myorg.com \
  --instance-url https://login.salesforce.com \
  --alias myProd
```

**Detection hint:** `sf org login jwt` with a `.sandbox` username but no `--instance-url https://test.salesforce.com`.

---

## Anti-Pattern 6: Running deploy without --dry-run or --check-only for production validation

**What the LLM generates:**

```bash
# "Deploy to production"
sf project deploy start --manifest manifest/package.xml --target-org prod
```

**Why it happens:** LLMs generate the deploy command without suggesting a validation-only run first. For production orgs, best practice is to run a check-only deployment first (`--dry-run`) to validate tests pass and components compile without actually deploying.

**Correct pattern:**

```bash
# Step 1: Validate (check-only) — runs tests without deploying
sf project deploy start --manifest manifest/package.xml --target-org prod \
  --dry-run --test-level RunLocalTests

# Step 2: If validation passes, deploy with --validated-deploy-request-id
sf project deploy start --manifest manifest/package.xml --target-org prod \
  --test-level RunLocalTests

# Or quick-deploy a validated deployment
sf project deploy quick --job-id <validationId> --target-org prod
```

**Detection hint:** `sf project deploy start` targeting a production org without `--dry-run` or a preceding validation step.
