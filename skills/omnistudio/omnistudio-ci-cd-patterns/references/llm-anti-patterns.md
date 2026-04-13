# LLM Anti-Patterns — OmniStudio CI/CD Patterns

Common mistakes AI coding assistants make when generating or advising on OmniStudio CI/CD.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using SFDX Metadata Deploy for Package Runtime OmniStudio Components

**What the LLM generates:** "Run `sf project deploy start --metadata OmniScript:MyScript` to deploy your OmniScript to the target org."

**Why it happens:** LLMs default to SFDX metadata deployment as the universal Salesforce deployment mechanism. The distinction between Package Runtime (data records) and Standard Runtime (metadata) is not widely documented in the training corpus.

**Correct pattern:**

```
For Package Runtime orgs:
  sf omnistudio datapack export --manifest manifest.json --output-dir datapacks/
  sf omnistudio datapack deploy --source-dir datapacks/ --activate --target-org target-alias

For Standard/Core Runtime orgs:
  sf project deploy start --metadata OmniScript:MyScript --target-org target-alias

First confirm runtime: Check Setup > OmniStudio Settings for vlocity_cmt/vlocity_ins namespace.
```

**Detection hint:** Any `sf project deploy start` or `force:source:deploy` recommendation for OmniStudio without first confirming Standard/Core Runtime.

---

## Anti-Pattern 2: Omitting --activate from DataPack Deploy

**What the LLM generates:** "Deploy your DataPack with `sf omnistudio datapack deploy --source-dir datapacks/ --target-org production`."

**Why it happens:** LLMs generate deploy commands based on documentation that emphasizes the deploy step, without prominently featuring the activation requirement as a separate mandatory flag.

**Correct pattern:**

```bash
# ALWAYS include --activate for Package Runtime deployments
sf omnistudio datapack deploy \
  --source-dir datapacks/ \
  --activate \
  --target-org production

# Verify activation after deploy
sf data query \
  --query "SELECT IsActive FROM OmniScript__c WHERE Name = 'MyScript' ORDER BY LastModifiedDate DESC LIMIT 1" \
  --target-org production
```

**Detection hint:** Any `omnistudio datapack deploy` or `packDeploy` command that does not include `--activate`.

---

## Anti-Pattern 3: Storing Credentials in the DataPack Job File

**What the LLM generates:** 

```yaml
options:
  username: myuser@example.com
  password: MyPassword123
  vlocityNamespace: vlocity_cmt
```

**Why it happens:** The OmniStudio Build Tool job file format supports inline credentials as a convenience feature for local development. LLMs generate this pattern from local-development examples without flagging the security risk in CI/CD contexts.

**Correct pattern:**

```yaml
# job file — no credentials inline
options:
  vlocityNamespace: vlocity_cmt
  # credentials provided via environment at runtime

# Pipeline step
- name: Deploy DataPacks
  run: sf omnistudio datapack deploy --activate --target-org $ORG_ALIAS
  env:
    SF_ACCESS_TOKEN: ${{ secrets.ORG_ACCESS_TOKEN }}
```

Use JWT bearer flow with a connected app for CI/CD authentication. Store private keys as encrypted CI/CD secrets. Never commit credentials to source control.

**Detection hint:** Any job file or pipeline YAML with inline `username`, `password`, or `securityToken` fields.

---

## Anti-Pattern 4: Not Handling DataPack Dependency Gaps

**What the LLM generates:** "Export just the OmniScript component for your hotfix: `sf omnistudio datapack export --component OmniScript:MyScript`."

**Why it happens:** LLMs optimize for minimal change scope, which is a sound general principle, without knowing that OmniStudio runtime dependencies must be co-deployed.

**Correct pattern:**

```bash
# Include all dependencies in the export
sf omnistudio datapack export \
  --manifest manifest.json \
  --max-depth 5 \
  --output-dir datapacks/

# manifest.json should include the OmniScript + its IPs + DataRaptors
# Verify all referenced components exist in target org after deploy
```

If a targeted hotfix is required, explicitly verify that all dependencies (Integration Procedures, DataRaptors) already exist at the correct version in the target org before deploying only the changed OmniScript.

**Detection hint:** Any export command that targets a single OmniScript without mentioning dependency verification.

---

## Anti-Pattern 5: Using the Same Pipeline for Both Package Runtime and Standard Runtime Orgs

**What the LLM generates:** A single CI/CD pipeline that runs `sf omnistudio datapack deploy --activate` for all environments, regardless of runtime type.

**Why it happens:** LLMs do not know which orgs in a multi-environment landscape use Package Runtime vs. Standard Runtime. They generate a single unified pipeline without a runtime-detection step.

**Correct pattern:**

```bash
# Runtime detection step
RUNTIME=$(sf data query \
  --query "SELECT COUNT() FROM InstalledSubscriberPackage WHERE SubscriberPackage.NamespacePrefix = 'vlocity_cmt'" \
  --target-org $ORG_ALIAS --json | jq '.result.totalSize')

if [ "$RUNTIME" -gt "0" ]; then
  echo "Package Runtime detected — using DataPack deploy"
  sf omnistudio datapack deploy --activate --source-dir datapacks/ --target-org $ORG_ALIAS
else
  echo "Standard Runtime detected — using SFDX metadata deploy"
  sf project deploy start --manifest package.xml --target-org $ORG_ALIAS
fi
```

**Detection hint:** Any pipeline that applies DataPack deploy to all orgs without a runtime-detection check.
