# LLM Anti-Patterns — OmniStudio DataPack Migration

Common mistakes AI coding assistants make when generating or advising on OmniStudio DataPack migration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Omitting --activate Flag from packDeploy Commands

**What the LLM generates:** DataPack deployment commands without the `--activate` flag — e.g., `sf omnistudio datapack deploy --source ./datapack.json --target-org production`.

**Why it happens:** LLMs model deployment as a single-step "deploy and it's live" pattern from standard Salesforce metadata deployments. They don't model OmniStudio's two-step deploy-then-activate lifecycle.

**Correct pattern:**
```bash
# Always include --activate to make the deployed version live
sf omnistudio datapack deploy --source ./datapack.json --target-org production --activate
```

**Detection hint:** Any `sf omnistudio datapack deploy` command missing `--activate` is incorrect when the goal is a live deployment.

---

## Anti-Pattern 2: Treating ALREADY_EXISTS as a Successful Update

**What the LLM generates:** Migration instructions that say "run packDeploy — if the output shows no errors, the migration is complete" — without noting that ALREADY_EXISTS is a no-op, not an update.

**Why it happens:** LLMs treat a non-error status as a success indicator. They don't model that ALREADY_EXISTS in OmniStudio DataPack import means the content was skipped, not updated.

**Correct pattern:**
```
Post-import verification is mandatory:
1. Check import result for ALREADY_EXISTS status per component
2. Query active version in target org and compare to expected version
3. If ALREADY_EXISTS was returned, the content was NOT updated
4. Resolution: increment version in source or use --overwrite flag and re-deploy
```

**Detection hint:** Migration instructions that end after `packDeploy` without a post-import active version verification step.

---

## Anti-Pattern 3: Recommending OmniStudio Migration Assistant for Org-to-Org Migration

**What the LLM generates:** Instructions that say "use the OmniStudio Migration Assistant to migrate your OmniScript from sandbox to production."

**Why it happens:** LLMs see "OmniStudio migration" and associate it with the OmniStudio Migration Assistant (OMA) tool, which has "migration" in its name. They don't distinguish between OMA (managed-package-to-Standard-Runtime conversion) and DataPack-based org-to-org migration.

**Correct pattern:**
```
Two distinct OmniStudio migration tools:
1. DataPack workflow (packExport/packDeploy/sf omnistudio datapack) — org-to-org migration between same-runtime orgs
2. OmniStudio Migration Assistant (OMA) — managed-package runtime → Standard Runtime (OmniStudio on Core) conversion
OMA is NOT for org-to-org migrations. DataPack workflow is NOT for runtime conversions.
```

**Detection hint:** Any recommendation to use "OmniStudio Migration Assistant" for sandbox-to-production or org-to-org migrations.

---

## Anti-Pattern 4: Assuming packExport Captures All Versions

**What the LLM generates:** Export instructions stating "run packExport to capture all your OmniStudio components" — implying a complete backup including drafts.

**Why it happens:** LLMs treat export tools as comprehensive backup mechanisms by default. They don't model that `packExport` is active-only by default and silently omits draft versions.

**Correct pattern:**
```
packExport default behavior: active version only
- Draft versions: NOT exported
- Previous inactive versions: NOT exported
- Review/pending versions: NOT exported

For complete version export (Spring '25+):
sf omnistudio datapack export --target-org source --output ./all-versions.json --include-all-versions
```

**Detection hint:** Export instructions that describe capturing "all components" or "full backup" without noting the active-only default.

---

## Anti-Pattern 5: Not Checking for Version Collisions Before Import

**What the LLM generates:** Migration instructions that run `packDeploy` directly without a pre-import check for existing version numbers in the target org.

**Why it happens:** LLMs model deployment as an idempotent operation ("run it and it applies the latest"). They don't model that OmniStudio DataPack import is NOT idempotent — re-importing the same version is a no-op, not an update.

**Correct pattern:**
```bash
# Before packDeploy, check for version collisions in target
sf data query \
  --query "SELECT Name, Type, SubType, Version FROM OmniProcess WHERE Type='OmniScript'" \
  --target-org production

# Compare to source version numbers
# If collision found: increment version in source OR use --overwrite
sf omnistudio datapack deploy --source ./datapack.json --target-org production --activate --overwrite
```

**Detection hint:** Migration scripts or instructions that go directly from `packExport` to `packDeploy` without a target org version query step in between.
