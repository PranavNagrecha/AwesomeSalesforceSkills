# OmniStudio DataPack Migration — Work Template

Use this template when executing a DataPack migration between Salesforce orgs.

## Scope

**Skill:** `omnistudio-datapack-migration`

**Migration Type:** Org-to-Org (DataPack) / Runtime Migration (OMA — different tool)
**Source Org:** (fill in)
**Target Org:** (fill in)
**OmniStudio Runtime (both orgs):** Package Runtime (VBT) / Standard Runtime (Spring '25+)
**VBT/OmniStudio Version (if Package Runtime):** (fill in)

---

## Components to Migrate

| Component Name | Type | Sub Type | Source Version | Source Status |
|---|---|---|---|---|
| | OmniScript / IntegrationProcedure / DataRaptor / FlexCard | | | Active / Draft |

**Export mode needed:** Active-only (default) / All versions (Spring '25+ flag)

---

## Pre-Import Version Collision Check

Query target org before import:
```bash
sf data query --query "SELECT Name, Type, SubType, Version FROM OmniProcess" --target-org [target-org-alias]
```

| Component Name | Version in Source | Version in Target | Collision? | Resolution |
|---|---|---|---|---|
| | | | Yes/No | Increment version / --overwrite / No action needed |

---

## Export Command

```bash
# Active-only export (default):
sf omnistudio datapack export --target-org [source-org] --output ./datapack-export.json

# All-versions export (Spring '25+, if draft versions needed):
sf omnistudio datapack export --target-org [source-org] --output ./datapack-all.json --include-all-versions
```

---

## Import Command

```bash
# Deploy and activate (standard migration):
sf omnistudio datapack deploy --source ./datapack-export.json --target-org [target-org] --activate

# Deploy with overwrite (if version collision exists):
sf omnistudio datapack deploy --source ./datapack-export.json --target-org [target-org] --activate --overwrite
```

---

## Post-Import Verification

```bash
# Verify active versions in target org
sf data query --query "SELECT Name, Type, SubType, Version, IsActive FROM OmniProcess WHERE IsActive=true" --target-org [target-org]
```

| Component Name | Expected Version | Actual Active Version | Result |
|---|---|---|---|
| | | | Pass / Fail |

---

## Review Checklist

- [ ] Source and target orgs confirmed as same runtime type
- [ ] Version numbers from source documented before export
- [ ] Pre-import collision check completed in target org
- [ ] Export mode explicitly chosen (active-only or all-versions)
- [ ] packDeploy run WITH --activate flag
- [ ] Post-import active version verified in target org
- [ ] No ALREADY_EXISTS no-ops for components that needed updating
- [ ] Environment-specific values remapped if applicable
