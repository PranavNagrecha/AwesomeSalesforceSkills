---
name: omnistudio-deployment-datapacks
description: "Use when exporting, importing, or version-controlling OmniStudio components using DataPacks via the OmniStudio DataPacks tool or vlocity CLI. Covers DataPack export/import, Git version control integration, CI/CD for OmniStudio. NOT for SFDX-based metadata deployment of non-OmniStudio components."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I move OmniStudio components between orgs using DataPacks"
  - "vlocity CLI export OmniScript DataRaptor Integration Procedure to Git"
  - "DataPack import failing with dependency error or missing record"
  - "how to version control OmniStudio assets in a CI/CD pipeline"
  - "DataPack import succeeds but component is not activated in target org"
  - "environment-specific record IDs breaking DataPack deployment"
tags:
  - omnistudio
  - datapacks
  - vlocity-cli
  - deployment
  - ci-cd
  - version-control
inputs:
  - "List of OmniStudio component names and types (OmniScript, DataRaptor, Integration Procedure, FlexCard, OmniProcess) to export"
  - "Source org credentials and target org credentials (or named credential / sfdx auth URL)"
  - "Git repository root where DataPack JSON files should be committed"
  - "Any environment-specific configuration (Named Credential names, Custom Setting values, endpoint URLs) that differ between orgs"
outputs:
  - "DataPack JSON files committed to Git, one per component, structured for diff-friendly version control"
  - "Import result log showing per-component success, failure, or activation state in the target org"
  - "CI/CD pipeline configuration for automated OmniStudio promotion"
  - "Troubleshooting guidance for failed imports with dependency errors, version conflicts, or activation failures"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# OmniStudio Deployment — DataPacks

This skill activates when a practitioner needs to export OmniStudio components as DataPacks, commit them to Git for version control, import them into a target org, or build a CI/CD pipeline that promotes OmniStudio assets across the delivery lifecycle. It provides structured procedures for the three most common deployment scenarios — export to Git, import to target org, and troubleshooting failed imports — along with the non-obvious platform behaviors that cause DataPack deployments to silently fail or produce misactivated components.

---

## Before Starting

Gather this context before working on anything in this domain:

- **OmniStudio package mode**: is the org running OmniStudio managed package (namespace `vlocity_*` or `omnistudio`) or Standard (non-namespaced) OmniStudio built into the Salesforce Platform? The vlocity CLI and DataPacks tooling apply to both, but the metadata type names and property keys differ by namespace mode. Confirm before generating export queries.
- **vlocity CLI version**: run `vlocity --version` (or `sf omnistudio --version` if using the Salesforce CLI plugin) to confirm the tooling version matches the target org's OmniStudio package version. Version drift is a common import failure root cause.
- **Target org environment type**: sandbox, scratch org, or production. Production imports require that all dependent components already exist or are included in the same DataPack set. Scratch orgs require the OmniStudio package or metadata layer to already be installed.
- **Environment-specific data**: DataPacks can embed record IDs from the source org (e.g., Custom Settings values, Named Credential references, lookup field values). Identify these before exporting so they can be overridden or excluded.

---

## Core Concepts

### 1. What a DataPack Is

A DataPack is a JSON-formatted export of one or more OmniStudio components — OmniScript, DataRaptor (Extract, Load, Transform, Turbo Extract), Integration Procedure, FlexCard, OmniProcess, Product Configuration, or related supporting records — along with their dependencies. Each DataPack is a self-contained JSON file (or folder of JSON files for large components) stored under a top-level `dataPacks` array. The format includes component type, a set of data records that constitute the component, and all referenced child or sibling records that the component depends on.

DataPacks are the native migration format for OmniStudio. Unlike SFDX metadata deployment, which works with static XML files representing configuration state, DataPacks are record-based: they represent the component as Salesforce object records and import them via upsert operations in the target org. This means import depends on org-resident data (lookup records, related configuration) existing in the target, not just metadata being deployed. (Source: OmniStudio DataPacks — Salesforce Help.)

### 2. Export and the vlocity CLI

The vlocity CLI (`vlocity` or its Salesforce CLI plugin `sf omnistudio`) is the primary tool for DataPack export and import from the command line. Key operations:

- **Export**: queries the source org for the specified component types and writes DataPack JSON files to a local directory. Each component is written as a separate file, enabling Git-level diff per component.
- **Import**: reads DataPack JSON files from the local directory and upserts them into the target org, resolving dependencies in the correct order.
- **Activate**: post-import activation of components (OmniScript, Integration Procedure, FlexCard versions must be activated to be live). The import step alone does not activate a component.

The export/import cycle is driven by a `propertySetConfig.json` (or inline flags) that specifies which component types to include and any filter criteria. (Source: OmniStudio Developer Guide — vlocity Build Tool.)

### 3. Dependency Resolution During Import

OmniStudio components reference each other: an OmniScript may call an Integration Procedure, which calls a DataRaptor. DataPacks represent these as dependency links inside the JSON. During import, the vlocity CLI processes the dependency graph and imports components in dependency order — DataRaptors before Integration Procedures before OmniScripts. If a dependency is missing from the DataPack set and is not already present in the target org, the import will report a `MISSING_DEPENDENCY` error for the dependent component and either skip it or fail the entire import, depending on the `--maxDepth` and `--ignore-all-errors` configuration. Always export the full dependency closure when migrating between orgs with no shared component baseline.

### 4. Activation After Import

Importing a DataPack creates or updates the component records in the target org but does not automatically activate the component version. For OmniStudio components that support versioning (OmniScript, Integration Procedure, FlexCard), the specific version that was imported must be explicitly activated before it becomes the live runtime version. The vlocity CLI supports an `--activate` flag on import to trigger activation after all records are upserted. Without this flag, the imported version exists in the org in an inactive state and the previously active version (if any) continues to serve runtime requests. This is the most common cause of "import succeeded but nothing changed" reports.

---

## How This Skill Works

### Mode 1: Export OmniStudio Components to Git

Use when: a team wants to source-control OmniStudio assets, establish a deployment baseline, or prepare components for promotion to a higher environment.

**Step-by-step:**

1. Install the vlocity CLI. For Salesforce CLI plugin:
   ```bash
   sf plugins install @salesforce/plugin-omnistudio
   ```
   For standalone vlocity build tool:
   ```bash
   npm install -g vlocity
   ```

2. Authenticate against the source org. With Salesforce CLI:
   ```bash
   sf org login web --alias my-sandbox
   ```

3. Create a `propertySetConfig.json` that specifies component types to export:
   ```json
   {
     "queries": [
       { "query": "Select Id from OmniProcess where Type = 'OmniScript' and IsActive = true", "VlocityDataPackType": "OmniScript" },
       { "query": "Select Id from OmniIntegrationProcedure where IsActive = true", "VlocityDataPackType": "IntegrationProcedure" },
       { "query": "Select Id from OmniDataTransform", "VlocityDataPackType": "DataRaptor" },
       { "query": "Select Id from OmniUiCard where IsActive = true", "VlocityDataPackType": "FlexCard" }
     ]
   }
   ```
   Adjust object API names for managed package namespaces (e.g., `vlocity_cmt__OmniScript__c`).

4. Run the export:
   ```bash
   vlocity -sfdx.username my-sandbox -job propertySetConfig.json packExport
   ```
   Or with Salesforce CLI plugin:
   ```bash
   sf omnistudio datapack export --target-org my-sandbox --job propertySetConfig.json --output datapacks/
   ```

5. The tool writes one JSON file per component into the output directory, organized by DataPack type. Commit the output directory to Git:
   ```bash
   git add datapacks/
   git commit -m "chore: export OmniStudio components from sandbox [YYYY-MM-DD]"
   ```

6. Review the diff before committing. Environment-specific values embedded in JSON (record IDs, endpoint URLs, Named Credential names) should be identified and either replaced with placeholder tokens or managed via environment-variable substitution in the CI pipeline.

### Mode 2: Import DataPacks into a Target Org

Use when: deploying exported DataPack files from Git into a sandbox, UAT org, or production.

**Step-by-step:**

1. Authenticate against the target org:
   ```bash
   sf org login web --alias target-org
   ```

2. Run the import with activation:
   ```bash
   vlocity -sfdx.username target-org -job propertySetConfig.json packDeploy
   ```
   Or with Salesforce CLI plugin:
   ```bash
   sf omnistudio datapack import --target-org target-org --source-dir datapacks/ --activate
   ```

3. The CLI resolves the dependency graph and imports in order: DataRaptors → Integration Procedures → OmniScripts → FlexCards.

4. Review the import log. Each component reports `Success`, `Error`, or `Skipped (Already Active)`. For errors, the log includes the DataPack type, component name, and error reason.

5. Verify activation in the target org: navigate to the OmniStudio app and confirm the expected version is marked Active for each component.

6. For environment-specific overrides (e.g., different Named Credential name in production), apply overrides using the CLI's `--overrideSettings` flag or a post-import Apex script that updates the relevant Custom Setting or Custom Metadata record.

### Mode 3: Troubleshoot DataPack Import Failures

Use when: an import reports errors, components are created but not activated, or the import succeeds but runtime behavior is wrong.

**Common failure modes and resolution:**

| Error | Cause | Resolution |
|---|---|---|
| `MISSING_DEPENDENCY` | A referenced component is not in the DataPack set and not in the target org | Re-export with `--maxDepth -1` to include all transitive dependencies |
| `ALREADY_EXISTS` on import of inactive version | A same-name component exists and a version conflict occurred | Use `--buildFile` with `--overwrite` or increment the version number before exporting |
| Import succeeds, component not active | `--activate` flag not used, or activation failed silently | Run a separate activate step: `sf omnistudio datapack activate` or manually activate in the UI |
| Record ID mismatch for lookup fields | The DataPack embeds source-org record IDs that do not exist in the target | Identify ID-bearing fields via `matchingKey` configuration, use `matchingKey` to resolve by name rather than ID |
| Import hangs or times out | Large DataPack set imported without chunking | Split the job by DataPack type or use `--maxDepth 0` to import without transitive dependencies, then promote dependencies separately |

---

## CI/CD Integration

For automated OmniStudio promotion across a pipeline (DEV → QA → UAT → PROD):

1. Store DataPack JSON files in Git alongside standard SFDX source.
2. In the CI pipeline (GitHub Actions, Copado, Azure DevOps), authenticate against the target org using a connected app JWT flow.
3. Run `packDeploy` (or `sf omnistudio datapack import`) as a pipeline step after SFDX metadata deployment completes. OmniStudio record-based components must be deployed after the metadata layer that backs them.
4. Pass environment-specific override values via CI environment variables, injected into the vlocity job file at pipeline runtime.
5. Fail the pipeline on any `Error` in the import log using the CLI's exit code (`vlocity` returns non-zero on import errors).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Moving components between two orgs with a shared baseline | `packDeploy` without `--maxDepth -1` | Transitive dependencies already exist in target; full re-export adds noise |
| Fresh target org with no shared components | `packExport` with `--maxDepth -1` then `packDeploy` | Ensures full dependency closure is included in the DataPack set |
| Scripted CI/CD promotion | Salesforce CLI `sf omnistudio` plugin with JWT auth | Designed for non-interactive automation; supports exit-code-based failure signaling |
| Environment-specific record IDs embedded in DataPacks | `matchingKey` configuration in the DataPack type definition | Resolves records by name/key in the target rather than by source-org ID |
| Component imported but not live | Use `--activate` flag or explicit activate step | Import alone does not make a version active in the target org |
| Large DataPack set timing out | Split by DataPack type, deploy DataRaptors first then IPs then OmniScripts | Respects dependency order and reduces per-job payload size |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking a DataPack deployment complete:

- [ ] Source org and target org OmniStudio package versions are compatible (same major version)
- [ ] Export includes all transitive dependencies (`--maxDepth -1`) or target org already has dependencies
- [ ] Environment-specific values (record IDs, Named Credential names, endpoint URLs) identified and handled via `matchingKey` or overrides
- [ ] Import run with `--activate` flag or a separate activate step executed after import
- [ ] Import log reviewed — zero `Error` entries, all expected components show `Success`
- [ ] Active version verified in the OmniStudio app for each imported component
- [ ] Named Credentials and Remote Site Settings required by Integration Procedures confirmed to exist in the target org
- [ ] Post-import smoke test run against a representative user in the target org

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Import does not activate — the previous version stays live** — Running `packDeploy` without the `--activate` flag creates or updates the component records in the target org but leaves the previously active version serving runtime requests. Teams frequently interpret a successful import log as meaning the component is live. It is not. Always include `--activate` in automated pipelines, or verify activation status explicitly in the OmniStudio app after every import.

2. **Environment-specific record IDs embedded in DataPack JSON break cross-org imports** — When a DataRaptor Load or Integration Procedure references a lookup record (e.g., a Custom Setting value, a Product record, or a Pricebook entry) by Salesforce record ID, that ID is typically embedded in the exported DataPack JSON. Record IDs are org-specific — the same record has a different 18-character ID in sandbox and production. Importing such a DataPack into a different org will succeed at the record-upsert level, but the component's runtime behavior will be broken because it tries to reference an ID that does not exist in the target. Prevent this by configuring `matchingKey` for lookup relationships to resolve by a natural key (Name, ExternalId, or a combination) rather than ID.

3. **vlocity CLI version mismatch causes silent property loss or schema errors** — The vlocity CLI and the OmniStudio managed package in the org must be on compatible versions. If the CLI version is ahead of the package, it may write properties into the DataPack JSON that the target org's package version does not recognise, resulting in silent property loss on import. If the CLI is behind the package, it may fail to read newer schema fields from the export. Pin the CLI version in `package.json` or your CI pipeline to match the target org's package release. (Source: OmniStudio Developer Guide — vlocity Build Tool compatibility notes.)

4. **Dependency order is not always automatically resolved for cross-type dependencies** — The vlocity CLI resolves dependencies within the same DataPack export job, but if an OmniScript references a FlexCard that in turn references an Integration Procedure that was deployed in a prior pipeline run, the current job may not re-include that IP. If the IP version in the target was updated out-of-band, the FlexCard will continue to call the version that was active at the time of the last DataPack import, not the latest. Always verify the full dependency closure when making changes to shared components.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DataPack JSON files | One file per OmniStudio component, organized by type, committed to Git and diff-friendly for code review |
| Import result log | Per-component status (Success / Error / Skipped) with error detail for failed items |
| CI/CD pipeline config | Pipeline YAML (GitHub Actions or equivalent) for automated export-on-change and deploy-on-merge |
| Environment override map | Mapping of source-org values to target-org equivalents for environment-specific fields |

---

## Related Skills

- `omnistudio/omnistudio-debugging` — Use when an imported component behaves unexpectedly at runtime; the debugging skill covers IP Debug tab and Action Debugger procedures.
- `omnistudio/integration-procedures` — Use when the Integration Procedure design itself needs to change, not just be promoted between environments.
- `omnistudio/flexcard-design-patterns` — Use when FlexCard versioning or activation behaviour is the focus.
- `devops/devops-center-pipeline` — Use when coordinating OmniStudio DataPack deployment alongside SFDX metadata in a Salesforce DevOps Center pipeline.
