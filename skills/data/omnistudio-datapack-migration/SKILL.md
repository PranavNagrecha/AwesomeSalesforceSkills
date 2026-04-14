---
name: omnistudio-datapack-migration
description: "Use this skill when migrating OmniStudio components (OmniScript, Integration Procedures, DataRaptors, FlexCards) between Salesforce orgs using the DataPack export/import mechanism — covering version management, environment-specific data resolution, conflict handling, and silent-skip gotchas. Trigger keywords: DataPack migration, OmniStudio org-to-org migration, packExport packDeploy, DataPack versioning, DataPack conflict. NOT for OmniStudio CI/CD pipeline automation (use omnistudio/omnistudio-ci-cd-patterns), managed-package-to-standard-runtime migration (use OmniStudio Migration Assistant), or standard Salesforce metadata migration."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "need to migrate OmniScript or Integration Procedure from sandbox to production using DataPacks"
  - "DataPack import completed but components are not active or running the old version"
  - "packExport is missing some versions or draft components after the export"
  - "DataPack import skipped a component silently without an error message"
  - "version conflict when importing DataPacks — same version already exists in target org"
tags:
  - omnistudio
  - datapack
  - migration
  - deployment
  - omnistudio-datapack-migration
inputs:
  - "Source org DataPack export (JSON package)"
  - "Target org OmniStudio version and runtime type (Package vs Standard)"
  - "List of component versions to migrate (active only vs all versions)"
  - "Environment-specific data to remap (Named Credentials, custom labels, org-specific IDs)"
outputs:
  - "DataPack import result with activated component versions"
  - "Version conflict resolution guidance"
  - "Post-import activation verification checklist"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-14
---

# OmniStudio DataPack Migration

This skill activates when a practitioner needs to migrate OmniStudio components between Salesforce orgs using the DataPack export/import mechanism. It covers the full migration lifecycle: export configuration, version management, silent-skip conflict resolution, environment-specific data remapping, and post-import activation verification.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm both source and target orgs are running the same OmniStudio runtime (Package Runtime / Standard Runtime). Cross-runtime DataPack migrations are not supported — use the OmniStudio Migration Assistant (OMA) for managed-package-to-standard-runtime migration, which is a different tool entirely.
- Confirm OmniStudio version (VBT version for Package Runtime). Version mismatches between source and target can cause import failures.
- The most common wrong assumption: `packExport` captures all versions by default. It does not — `packExport` only exports the active version of each component. Draft versions are silently omitted. Spring '25+ adds an option to export all versions explicitly.
- Version-number collision is a critical gotcha: if the same component version already exists in the target org, the import skips it silently (ALREADY_EXISTS status) without overwriting or warning. The practitioner sees a successful import with no indication that the component was not updated.

---

## Core Concepts

### DataPack Export Modes

DataPack exports have two modes:
- **Active-only export (default)** — `packExport` exports only the currently active version of each component. Draft versions, newer inactive versions, and previous versions are not included. This is the default behavior in all versions prior to Spring '25.
- **All-versions export (Spring '25+)** — Spring '25 introduces the ability to export all versions of a component. This must be explicitly enabled in the export configuration; the default remains active-only.

Migration plans must specify which export mode is appropriate — active-only for production deployments, all-versions for version history preservation.

### Version-Number Collision and Silent Skip

The most dangerous DataPack migration behavior:
- If a component with the same Type, Sub Type, and Version Number already exists in the target org (regardless of whether it is active), the import skips it silently with an `ALREADY_EXISTS` status
- The import summary reports success; there is no error or warning
- The previously active version continues serving traffic — the "migrated" version has not been applied

To resolve: either increment the version number in the source before re-exporting, or use the `--overwrite` flag (available in VBT v15+) to force overwrite of existing versions.

### Custom matchingKey Override (VBT v15+)

Post-VBT v15, custom `matchingKey` values in DataPacks override the package default matching strategy:
- `matchingKey` controls how the import identifies whether a component already exists
- A custom `matchingKey` in the DataPack JSON that differs from the target org's settings causes the import to create a duplicate component instead of updating the existing one
- This produces orphaned components in the target org that must be manually cleaned up

### OmniStudio Migration Assistant vs DataPack Migration

These are distinct tools for different scenarios:
- **DataPack migration** — org-to-org component migration between two orgs running the same runtime (Package-to-Package or Standard-to-Standard)
- **OmniStudio Migration Assistant (OMA)** — SF CLI plugin for migrating from managed-package runtime to Standard Runtime (OmniStudio on Core). OMA converts managed-package components to standard-runtime format — it is NOT used for org-to-org migration

---

## Common Patterns

### Pattern: Safe DataPack Migration Workflow

**When to use:** Any org-to-org OmniStudio component migration using DataPacks.

**How it works:**
1. Export from source: run `packExport` with explicit component list; confirm active-only or all-versions mode
2. Inspect the exported JSON for version numbers — note the version of each component
3. In the target org: query existing components to detect version-number collisions before import
4. If collision exists: increment version in source or use `--overwrite`
5. Import to target: run `packDeploy` with `--activate` flag
6. Post-import: verify active version in target org matches the expected version number

**Why not the alternative:** Skipping the pre-import collision check leads to silent skips. Skipping `--activate` creates or updates the component record but leaves the previous version active — the most common DataPack migration mistake.

### Pattern: Environment-Specific Data Remapping

**When to use:** When the DataPack references org-specific IDs, Named Credentials, custom labels, or Record Type IDs that differ between environments.

**How it works:**
1. Before export, identify all environment-specific references in the OmniScript/IP/DataRaptor: Named Credential names, Record Type Developer Names, custom label API names, external system URLs
2. Use DataPack Transform to substitute environment-specific values at import time (VBT/OmniStudio supports JSON transform mappings in the package configuration)
3. Alternatively: document all environment-specific values and manually update after import

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Migrating active components between two Package Runtime orgs | Standard DataPack packExport/packDeploy with --activate | Default migration path for Package Runtime |
| Draft versions need to be migrated alongside active | Spring '25 all-versions export | Default active-only export silently omits drafts |
| Same version exists in target and content has changed | Use --overwrite or increment version number | Silent skip (ALREADY_EXISTS) will not update the existing component |
| Migrating from managed-package runtime to Standard Runtime | OmniStudio Migration Assistant (OMA) CLI plugin | OMA handles format conversion; DataPack migration does not |
| High-frequency migrations in a CI/CD pipeline | See omnistudio/omnistudio-ci-cd-patterns skill | Pipeline automation patterns are distinct from single migration operations |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Confirm source and target orgs are running the same OmniStudio runtime type — if not, stop and use the OmniStudio Migration Assistant instead.
2. List all components to migrate and their current active version numbers from the source org.
3. Query the target org for existing components with the same Type, Sub Type, and Version Number — identify any version-number collisions before export.
4. Run `packExport` from the source org; if draft versions are required, use the Spring '25+ all-versions export option explicitly.
5. Inspect the exported DataPack JSON to confirm all expected components and versions are included — drafts are silently omitted in default export mode.
6. Resolve any version collisions: either increment the source version number or prepare to use `--overwrite` flag on import.
7. Run `packDeploy` with the `--activate` flag on the target org; `--activate` is mandatory — importing without it creates/updates the record but leaves the previous version active.
8. Post-import: verify each component in the target org shows the expected version number in Active status; spot-check one component in Preview mode to confirm it runs correctly.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Source and target orgs confirmed as same runtime type
- [ ] Version numbers from source documented before export
- [ ] Pre-import collision check performed in target org
- [ ] Export mode (active-only vs all-versions) explicitly chosen and confirmed
- [ ] packDeploy run with --activate flag
- [ ] Post-import active version verified in target org
- [ ] Environment-specific references remapped if applicable
- [ ] No orphaned duplicate components left from matchingKey conflicts

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **packDeploy without --activate leaves the old version active** — Running `packDeploy` without `--activate` creates or updates the component record but does not change the active version. The previously active version continues serving runtime traffic. This is the most common DataPack migration mistake — the import shows success but users still see the old version.
2. **ALREADY_EXISTS is silent success — not an update** — When a component with the same version already exists in the target, the import returns `ALREADY_EXISTS` status and moves on. The import summary shows no errors. The content of the existing component is not changed. Practitioners interpret this as a successful update when it is actually a no-op.
3. **Custom matchingKey overrides create duplicate components** — Post-VBT v15, a DataPack with a custom `matchingKey` that doesn't match the target org's matchingKey settings creates a duplicate component rather than updating the existing one. The duplicate is inactive and appears in the component list causing confusion.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DataPack export package | JSON file containing OmniStudio components exported from source org |
| Version collision report | List of components with version conflicts in the target org before import |
| Post-import activation checklist | Verified active version numbers per component after deployment |

---

## Related Skills

- `omnistudio/omnistudio-ci-cd-patterns` — use for pipeline automation of DataPack deployments
- `omnistudio/omnistudio-deployment-datapacks` — use for DataPack deployment configuration and CLI plugin setup
- `devops/deployment-monitoring` — use to monitor deployment success and set up post-deploy verification
