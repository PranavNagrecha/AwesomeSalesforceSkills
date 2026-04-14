# Examples — OmniStudio DataPack Migration

## Example 1: Silent Skip Due to Version Collision

**Context:** A developer migrates an updated OmniScript from a full-copy sandbox to production. The OmniScript has version 1.4 in both environments (the production version was not incremented before the sandbox update was applied).

**Problem:** The `packDeploy` command completes without errors. The import summary shows the OmniScript as processed. However, production users continue to see the old version because the import returned `ALREADY_EXISTS` and skipped the component silently. The developer does not notice because there is no error message.

**Solution:**
Before migrating, query the target org to detect version collisions:
```bash
# Check existing version in target org using SF CLI
sf data query --query "SELECT Name, Type, SubType, Version FROM OmniProcess WHERE Type='OmniScript' AND SubType='Intake'" --target-org production

# If version matches source, increment version in source sandbox before re-exporting
# OR use --overwrite flag on packDeploy (VBT v15+)
sf omnistudio datapack deploy --source ./my-datapack.json --target-org production --activate --overwrite
```

After import, verify active version matches expected:
```bash
sf data query --query "SELECT Name, Type, SubType, Version, IsActive FROM OmniProcess WHERE Type='OmniScript' AND IsActive=true" --target-org production
```

**Why it works:** Pre-import version check exposes the collision before it becomes a silent no-op. Post-import active version verification confirms the migration succeeded.

---

## Example 2: Missing Draft Versions in packExport

**Context:** A developer needs to migrate both the active version (1.3) and a draft of the next version (1.4) from a development sandbox to a UAT sandbox for testing.

**Problem:** Running `packExport` with default settings only exports version 1.3 (the active version). Version 1.4 (draft) is silently omitted. The UAT team cannot test the new draft version.

**Solution:**
Use Spring '25+ all-versions export flag:
```bash
# Standard active-only export (default — exports only active version)
sf omnistudio datapack export --target-org dev-sandbox --output ./datapack-active.json

# Spring '25+ all-versions export — explicitly exports all versions including drafts
sf omnistudio datapack export --target-org dev-sandbox --output ./datapack-all-versions.json --include-all-versions
```

Verify that the exported JSON contains both version 1.3 and 1.4 entries before importing to UAT.

**Why it works:** The all-versions export flag is required to capture draft versions; the default active-only export is designed for production promotions not UAT testing environments that need in-progress work.

---

## Anti-Pattern: Running packDeploy Without --activate

**What practitioners do:** They run `packDeploy` to import DataPacks to the target org and assume the deployed version is now live because the command completed successfully.

**What goes wrong:** `packDeploy` without `--activate` creates or updates the component record in the target org but does not change which version is marked Active. The previous active version continues to serve runtime traffic. Users see the old version. The error is only discovered when users report the update is not visible.

**Correct approach:** Always include `--activate` in `packDeploy` commands when the intent is to make the migrated version live:
```bash
# Correct: import and activate
sf omnistudio datapack deploy --source ./datapack.json --target-org production --activate

# Incorrect: import only — old version remains active
sf omnistudio datapack deploy --source ./datapack.json --target-org production
```
