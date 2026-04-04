# Gotchas — OmniStudio Deployment DataPacks

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Successful Import Does Not Mean the Component Is Active

**What happens:** `packDeploy` (or `sf omnistudio datapack import`) completes and the import log shows `Success` for every component. Practitioners mark the deployment done. But when end users open the OmniScript or FlexCard, they see the old behavior — or nothing at all if there was no previously active version.

**When it occurs:** Any time an import is run without the `--activate` flag, or when activation is run but fails silently on one or more components (activation errors are sometimes not propagated to the top-level CLI exit code in older plugin versions).

**How to avoid:** Always include `--activate` in the import command for components that support versioning (OmniScript, Integration Procedure, FlexCard). After import, run an explicit activation verification step: query the org for `OmniProcess` or `OmniIntegrationProcedure` records where `Name` matches your components and confirm `IsActive = true` on the expected version. In CI pipelines, treat an inactive component post-import as a pipeline failure.

---

## Gotcha 2: Environment-Specific Record IDs in DataPack JSON Break Cross-Org Imports

**What happens:** A DataPack export captures the component faithfully, but embedded inside the JSON are Salesforce record IDs from the source org. These IDs appear in lookup fields, related record references, and sometimes hardcoded values inside element configurations. When the same DataPack is imported into a different org, those IDs do not exist, so the component either imports with broken references or throws a `RECORD_NOT_FOUND` error at runtime.

**When it occurs:** Most commonly in DataRaptor Load components that target lookup fields, Integration Procedure elements that reference Custom Settings records by ID, OmniScripts with Set Values elements that store source-org IDs as defaults, and FlexCards with hardcoded record ID filters in their data source configuration.

**How to avoid:** Configure `matchingKey` in the DataPack type definitions so that cross-record references are resolved by a natural key (Name, ExternalId, a unique text field) rather than by Salesforce ID. Review exported DataPack JSON files for any 15- or 18-character alphanumeric values that look like Salesforce IDs and trace them to their source fields. For values that legitimately differ by environment (endpoint URLs, record names), use the CI pipeline override mechanism to inject the correct target-org value at deploy time rather than baking it into the exported JSON.

---

## Gotcha 3: vlocity CLI Version Mismatch Causes Silent Property Loss or Schema Errors

**What happens:** The import appears to succeed — exit code zero, `Success` in the log — but the component behaves differently from the source org. On inspection, certain properties in the imported component (e.g., a custom property on an IP action, a display condition expression, or a DataRaptor formula) are missing or reset to defaults.

**When it occurs:** When the vlocity CLI version used for import is behind the managed package version installed in the target org, or ahead of the source org's package version. Newer schema fields that the older CLI does not know about are silently dropped during the export serialisation. Conversely, if the CLI writes newer properties that the target org's package does not recognise, those properties are silently ignored on import.

**How to avoid:** Pin the vlocity CLI or `@salesforce/plugin-omnistudio` version in `package.json` (or in the CI pipeline's tool installation step) to match the OmniStudio package version in the org. Reference the compatibility matrix in the OmniStudio Developer Guide before upgrading either the CLI or the org package. When upgrading the org package, update the CLI version in all pipelines at the same time.

---

## Gotcha 4: Dependency Ordering Failure When Mixing Managed and Unmanaged Components

**What happens:** An OmniScript that calls a managed-package Integration Procedure (namespace `vlocity_cmt__`) alongside a custom unmanaged Integration Procedure in the same DataPack set fails import with a dependency error on the managed IP, even though the managed IP is installed in the target org.

**When it occurs:** The vlocity CLI treats managed-package components and custom components differently during dependency resolution. If the DataPack export included a reference to a managed IP that it cannot re-export (because managed components are read-only), the dependency graph becomes incomplete. The CLI cannot confirm the managed IP exists in the target and reports it as missing.

**How to avoid:** Exclude managed-package components from the DataPack export scope. Only export and import custom (non-namespaced) components. For managed IP dependencies, verify their presence in the target org separately (e.g., confirm the managed package version is installed) and set `--skipCurrentOrg` or equivalent CLI flags to tell the import step that managed-package records should be treated as already satisfied in the target.

---

## Gotcha 5: DataPack Export Captures the Active Version Only — In-Progress Draft Versions Are Not Included

**What happens:** A developer has been working on a new OmniScript version (version 2) in sandbox but has not activated it. The team runs an export assuming it will capture the latest work. The export captures version 1 (the active version) and the in-progress version 2 is absent from the DataPack.

**When it occurs:** The default export query filters for active components (`IsActive = true`). Any component version that has been created but not yet activated is invisible to the export.

**How to avoid:** When exporting in-progress work intentionally (e.g., for backup or cross-developer handoff), modify the export query to remove the `IsActive = true` filter. Be explicit about which version number you are exporting. Establish a team convention that in-progress versions are either exported with a clear naming convention or kept exclusively in source control as a JSON patch rather than re-imported as a DataPack until activation-ready.
