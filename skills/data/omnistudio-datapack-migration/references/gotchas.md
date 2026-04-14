# Gotchas — OmniStudio DataPack Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: ALREADY_EXISTS Status Is a Silent No-Op — Not a Successful Update

**What happens:** When `packDeploy` encounters a component with the same Type, Sub Type, and Version Number as an existing component in the target org, it returns an `ALREADY_EXISTS` status in the import result and moves on without updating the existing component. The import summary shows the overall operation as successful with no errors. The previously active version continues serving traffic.

**When it occurs:** Any time a DataPack is migrated to an org where the same version already exists — which is common when re-running a migration after a failed deployment attempt, or when a component was previously imported manually before the automated migration ran.

**How to avoid:** Before running `packDeploy`, query the target org for existing version numbers. If the same version already exists and the content has changed, either increment the version number in the source org before re-exporting, or use the `--overwrite` flag (VBT v15+). After import, verify active version numbers match expectations.

---

## Gotcha 2: packExport Active-Only Default Silently Omits Drafts

**What happens:** `packExport` with default settings exports only the currently active version of each component. Draft versions, versions in Review status, and any version not marked as Active are silently omitted from the export package. There is no warning in the export output listing omitted versions.

**When it occurs:** When migrating a component that has an active version in production and a newer draft version in the development sandbox that needs to be captured for UAT or version history.

**How to avoid:** If draft or non-active versions must be migrated, use the Spring '25+ `--include-all-versions` export flag explicitly. Confirm the exported JSON contains the expected version entries before importing to the target org.

---

## Gotcha 3: Custom matchingKey Creates Duplicates Instead of Updates

**What happens:** Post-VBT v15, if a DataPack contains a custom `matchingKey` value in the JSON that differs from the target org's default matching strategy for that component type, the import treats the component as a new component rather than an update to an existing one. This creates a duplicate component in the target org — two entries for the same OmniScript or Integration Procedure with different internal IDs. Both are inactive (the original active remains unchanged). The duplicates must be manually cleaned up.

**When it occurs:** When DataPacks are created or modified in an org where a custom `matchingKey` override was applied, and the target org uses the default matching strategy.

**How to avoid:** Before migrating, review the DataPack JSON for `matchingKey` fields. Confirm the target org's OmniStudio settings match the export org's `matchingKey` configuration. Use the same OmniStudio VBT version in both orgs to reduce matchingKey divergence.

---

## Gotcha 4: OmniStudio Migration Assistant Is Not a DataPack Migration Tool

**What happens:** Practitioners confuse the OmniStudio Migration Assistant (OMA) with the DataPack migration workflow. OMA is a separate SF CLI plugin specifically for migrating components from managed-package runtime (VBT-managed) to OmniStudio Standard Runtime (on-Core). Running OMA commands expecting a standard org-to-org migration fails or produces unexpected results.

**When it occurs:** When documentation mentions "OmniStudio migration" without specifying which type — org-to-org (DataPack) vs runtime migration (OMA).

**How to avoid:** Before starting any OmniStudio migration, identify the migration type: (1) same-runtime org-to-org = DataPack workflow; (2) managed-package to Standard Runtime = OMA CLI plugin. Never use OMA for org-to-org DataPack migrations.
