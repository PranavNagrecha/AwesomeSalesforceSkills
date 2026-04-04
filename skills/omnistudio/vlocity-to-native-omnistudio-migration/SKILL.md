---
name: vlocity-to-native-omnistudio-migration
description: "Use when migrating an org from the Vlocity managed package (vlocity_ins, vlocity_cmt, vlocity_ps) to native OmniStudio. Trigger keywords: Vlocity to OmniStudio migration, namespace migration, vlocity_ins to omnistudio, OmniStudio Migration Tool, DataRaptor namespace update, OmniScript JSON export, managed package to native. NOT for new OmniStudio setup in greenfield orgs, nor for migrating between OmniStudio-native orgs, nor for Salesforce CPQ to Industries CPQ migration."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "how to migrate from Vlocity managed package to native OmniStudio in an existing org"
  - "update OmniScript and DataRaptor namespace references from vlocity_ins to omnistudio after enabling native runtime"
  - "use the OmniStudio Migration Tool in Setup to convert Vlocity components to native format"
  - "side-by-side testing strategy when transitioning from vlocity_cmt to native OmniStudio deployment"
  - "LWC custom element tags still use c-omni-script after enabling enableOaForCore org setting"
tags:
  - omnistudio
  - vlocity
  - migration
  - namespace
  - omniscript
  - dataraptor
  - integration-procedure
  - flexcard
  - managed-package
  - native-omnistudio
  - migration-tool
inputs:
  - "Current Vlocity namespace in use: vlocity_ins (Insurance/Health), vlocity_cmt (Communications), or vlocity_ps (Public Sector)"
  - "Inventory of existing Vlocity OmniScript, DataRaptor, Integration Procedure, and FlexCard definitions"
  - "List of custom LWC components that embed or extend OmniStudio components"
  - "Any Apex classes referencing Vlocity service classes (e.g., vlocity_ins.IntegrationProcedureService)"
  - "Org edition and whether Industries Cloud license includes native OmniStudio entitlement"
outputs:
  - "Namespace audit report identifying all vlocity_* references in metadata files"
  - "Migration readiness assessment: components that can auto-migrate vs. require manual rework"
  - "Updated LWC markup and Apex class files with corrected namespace references"
  - "Side-by-side test plan comparing Vlocity and native component behavior"
  - "Post-migration validation checklist"
dependencies:
  - omnistudio/omniscript-design-patterns
  - omnistudio/omnistudio-lwc-integration
  - omnistudio/dataraptor-patterns
  - omnistudio/integration-procedures
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Vlocity to Native OmniStudio Migration

This skill activates when the work involves transitioning an org from a Vlocity managed package deployment (vlocity_ins, vlocity_cmt, or vlocity_ps) to the native OmniStudio runtime that ships as part of the Salesforce platform in Industries Cloud licenses. It covers component inventory, namespace migration, use of the OmniStudio Migration Tool in Setup, LWC markup updates, Apex class updates, and a side-by-side testing strategy. NOT for new OmniStudio setup in greenfield orgs, nor for CPQ product migration, nor for re-platforming to non-Salesforce systems.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Identify the Vlocity namespace.** Three Vlocity namespaces exist in active use: `vlocity_ins` (Insurance and Health Cloud), `vlocity_cmt` (Communications Cloud), and `vlocity_ps` (Public Sector Solutions). The namespace determines which managed package is installed and which service class names appear in Apex. The migration path is the same for all three, but the find-and-replace strings differ.
- **Confirm native OmniStudio entitlement and enablement.** Native OmniStudio requires the `enableOaForCore` org setting to be enabled. This setting is controlled by Salesforce support or via the OmniStudio Settings page in Setup (available once the Industries Cloud license includes OmniStudio). Enabling this setting does NOT automatically convert existing Vlocity components — conversion requires running the OmniStudio Migration Tool.
- **Understand the two-track deployment window.** During migration, both the Vlocity managed package and native OmniStudio can coexist in the org for a transitional period. This means components can be tested side-by-side before the managed package is uninstalled. However, mixed-namespace references in a single LWC file or Apex class will cause runtime failures.
- **Know the feature gap risk.** As of Spring '25, most OmniScript, DataRaptor, Integration Procedure, and FlexCard features have native equivalents. However, some Vlocity-specific features — particularly around OmniOut (external deployment of OmniScripts outside Salesforce), certain Vlocity Industry-specific DataPack types, and advanced CPQ integration hooks — may not have direct native counterparts. Inventory these before committing to a migration timeline.

---

## Core Concepts

### Two Deployment Models: Vlocity Managed Package vs Native OmniStudio

Salesforce Industries Cloud components (OmniScript, DataRaptor, Integration Procedure, FlexCard) have historically been delivered via Vlocity managed packages with industry-specific namespaces. These packages predate Salesforce's acquisition of Vlocity and are still installed in many production orgs.

Native OmniStudio, available since Winter '23 as GA, ships the same component set as part of the core Salesforce platform under the `omnistudio` namespace. No separate package is installed. Components are built and stored as platform metadata, not as managed package records.

The key distinction is where the component definitions live. In a Vlocity org, OmniScript definitions are stored as custom object records under `%vlocity_namespace%__OmniScript__c`. In a native org, they are stored as platform metadata with the `OmniScriptDefinition` metadata type. This difference drives the migration complexity — it is not just a namespace rename.

### The OmniStudio Migration Tool

Salesforce provides a Setup-based OmniStudio Migration Tool (also called the OmniStudio Migration Assistant) that automates the conversion of Vlocity managed package components to native OmniStudio format. The tool scans the org for installed Vlocity components, converts the component definitions from managed package records to native metadata, and registers them in the native OmniStudio runtime.

The Migration Tool handles OmniScripts, DataRaptors, Integration Procedures, and FlexCards. It does not handle custom LWC components that embed or extend these components, Apex classes that call Vlocity service classes, or DataPacks that include non-OmniStudio component types.

After running the Migration Tool, practitioners must separately:
1. Update all LWC markup that references managed package component tags.
2. Update all Apex code that calls `%vlocity_namespace%.IntegrationProcedureService` or similar.
3. Update any DataPacks or deployment scripts that reference Vlocity object API names.

### Namespace Differences in Code and Metadata

The namespace differences between Vlocity and native OmniStudio surface in four places:

1. **LWC HTML markup** — Managed package uses `<c-omni-script>`, native uses `<omnistudio-omni-script>`. Same pattern applies to FlexCard (`<c-flex-card>` vs `<omnistudio-flex-card>`) and other components.
2. **Apex class references** — Managed package calls go to `vlocity_ins.IntegrationProcedureService.runIntegrationService(...)`. Native calls go to `omnistudio.IntegrationProcedureService.runIntegrationService(...)`.
3. **SOQL queries** — Any Apex or Flow that queries Vlocity objects (e.g., `vlocity_ins__OmniScript__c`) must be updated to query native OmniStudio objects or removed if the component is now a metadata type rather than a record-stored definition.
4. **DataPack export/import tooling** — The Vlocity Build Tool (VBT) and its DataPacks format are not compatible with native OmniStudio. Native OmniStudio uses standard Salesforce deployment (SFDX/CLI, Metadata API). Projects that use DataPacks for CI/CD must rebuild their deployment pipelines.

### Side-by-Side Testing and Cutover Strategy

Because the managed package and native runtime can coexist during migration, the recommended approach is:
1. Run the Migration Tool to create native copies of all components.
2. Test the native copies in a sandbox while the Vlocity versions remain active.
3. Update all LWC and Apex references to point to native components.
4. Perform user acceptance testing on the native versions.
5. Set Vlocity components to inactive/deprecated.
6. Uninstall the managed package once all dependencies are resolved.

This approach reduces the cutover risk but requires careful management of component activation states — activating a native OmniScript with the same type/subtype as an active Vlocity OmniScript can cause conflicts depending on how components are invoked.

---

## Common Patterns

### Pattern 1: Bulk Namespace Audit Before Migration

**When to use:** Before running the Migration Tool, to understand the full scope of changes required in custom code.

**How it works:**
1. Run the checker script (`check_vlocity_to_native_omnistudio_migration.py --manifest-dir force-app/`) to scan all LWC HTML files for `c-omni-script`, `c-flex-card`, and similar managed package tags.
2. Scan all Apex class files for `vlocity_ins.`, `vlocity_cmt.`, or `vlocity_ps.` references.
3. Scan all custom metadata, workflow rules, and Process Builder flows for Vlocity object API names.
4. Produce a count of affected files and a mapping of Vlocity references to their native equivalents.
5. Use the count to scope migration effort and identify high-risk areas for testing.

**Why not the alternative:** Running the Migration Tool blind, without a prior audit, means practitioners discover broken LWC and Apex components only after the native runtime is active. Pre-auditing catches the custom code scope early.

### Pattern 2: Phased Component Cutover by Domain

**When to use:** Large orgs with hundreds of OmniScripts, DataRaptors, and Integration Procedures where a single-pass migration is high risk.

**How it works:**
1. Group components by business domain (e.g., Claims, Billing, Service).
2. Migrate one domain at a time: run the Migration Tool scoped to that domain's components, update LWC and Apex for that domain, test in sandbox, then promote.
3. Use Vlocity component active/inactive flags to control which version is live for end users during the transition.
4. Track progress in a migration tracker spreadsheet with component name, migration status, test result, and cutover date.

**Why not the alternative:** A single all-at-once cutover is high risk for large component inventories. If issues are discovered post-cutover, rolling back requires reinstating Vlocity component activation and reverting code — which is operationally complex and error-prone.

### Pattern 3: DataPack Pipeline Replacement

**When to use:** The org uses the Vlocity Build Tool (VBT) or a DataPacks-based CI/CD pipeline, which does not work for native OmniStudio components.

**How it works:**
1. Identify all DataPack export/import jobs in the CI/CD pipeline.
2. Replace DataPack exports with Salesforce CLI (`sf project retrieve`) using native OmniStudio metadata types (`OmniScriptDefinition`, `OmniIntegrationProcedure`, `OmniDataTransform`, `OmniUiCard`).
3. Update deployment scripts to use `sf project deploy` instead of the VBT deploy command.
4. Validate the new pipeline in a CI environment before decommissioning the VBT pipeline.

**Why not the alternative:** Attempting to continue using DataPacks for native OmniStudio components leads to silent data loss in deployments. Native OmniStudio components are platform metadata, not records, and DataPacks cannot serialize them correctly.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org has fewer than 50 OmniScripts and DataRaptors | Single-pass Migration Tool run + bulk code update | Low complexity; manageable testing scope |
| Org has 100+ components across multiple domains | Phased domain-by-domain migration | Limits blast radius; allows domain-level testing |
| Custom LWC uses `c-omni-script` tag | Replace with `omnistudio-omni-script` after Migration Tool run | Native runtime does not resolve managed package component tags |
| Apex class calls `vlocity_ins.IntegrationProcedureService` | Replace with `omnistudio.IntegrationProcedureService` | Managed package service class is not available in native runtime |
| CI/CD pipeline uses Vlocity Build Tool DataPacks | Rebuild pipeline using SFDX + native metadata types | VBT cannot serialize native OmniStudio metadata |
| Vlocity OmniOut is in use (external OmniScript embedding) | Assess native OmniOut equivalent before migrating | Native OmniOut support is not fully equivalent to Vlocity OmniOut in all releases |
| Component uses a Vlocity-only DataPack type (e.g., Product Catalog) | Do not attempt to migrate via Migration Tool | Only OmniStudio-type components (OmniScript, DR, IP, FlexCard) are in scope |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Run a namespace audit.** Execute `python3 scripts/check_vlocity_to_native_omnistudio_migration.py --manifest-dir force-app/` on the org's source metadata to identify all Vlocity namespace references in LWC, Apex, and metadata files. Record the count and file list.
2. **Inventory Vlocity components.** In the org Setup page, open the OmniStudio Migration Tool (Setup > OmniStudio > Migration Tool). Review the list of Vlocity OmniScript, DataRaptor, Integration Procedure, and FlexCard components discovered. Note any components flagged as not migrateable.
3. **Enable native OmniStudio if not already active.** Confirm `enableOaForCore` is set to `true` in the org's OmniStudio Settings. If not, coordinate with Salesforce support or your account team to enable it — this is a licensed feature, not a self-service toggle in all orgs.
4. **Run the OmniStudio Migration Tool.** In Setup, use the Migration Tool to migrate all eligible components. The tool creates native copies of the components. Migrated components are initially inactive. Review the migration log for any components that were skipped or flagged with errors.
5. **Update custom code.** Replace all Vlocity managed package references in LWC HTML files (component tags), Apex classes (service class calls and SOQL object names), and any custom metadata or configuration files. Use the namespace audit output from step 1 as the hit list.
6. **Activate native components and test side-by-side.** In a sandbox, activate the native copies of migrated components. Run functional tests against the native versions. Compare output against the still-active Vlocity versions. Resolve any behavioral differences — these commonly arise from DataRaptor formula differences, Integration Procedure HTTP action namespace changes, or FlexCard data source bindings.
7. **Promote and decommission Vlocity.** Once native components pass UAT, deactivate Vlocity components, deploy the updated LWC and Apex code, and validate in production. After a monitoring period, uninstall the Vlocity managed package to eliminate the managed package dependency.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All LWC HTML files use `omnistudio-*` component tags, not `c-omni-script` or `c-flex-card`
- [ ] All Apex classes reference `omnistudio.IntegrationProcedureService`, not `vlocity_ins/cmt/ps.IntegrationProcedureService`
- [ ] CI/CD pipeline uses SFDX + native metadata types, not Vlocity Build Tool DataPacks
- [ ] OmniStudio Migration Tool log reviewed; no components in error or skipped state without documented reason
- [ ] All native migrated components activated and functionally tested in sandbox
- [ ] DataRaptor formulas and Integration Procedure HTTP actions verified for namespace-specific differences post-migration
- [ ] Vlocity OmniOut usage assessed and native equivalent confirmed or gap documented
- [ ] Vlocity managed package uninstall dependency check completed (no remaining references)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Migration Tool creates inactive copies — they are not live until manually activated** — After running the OmniStudio Migration Tool, all converted native components are created in an inactive state. Practitioners who assume the migration is complete immediately after the tool run will find that end users still hit the Vlocity versions. Each component must be explicitly activated in the OmniStudio designer, or via metadata deployment with the `isActive` flag set to `true`.
2. **Vlocity OmniScript type/subtype conflicts with native copies** — If both a Vlocity OmniScript and its native migrated copy share the same type and subtype, and both are active simultaneously, the runtime can resolve to either version depending on how the component is launched (FlexCard action, LWC tag, URL invocation). This creates unpredictable user experiences during the transition window. Deactivate the Vlocity version before activating the native version.
3. **DataRaptor formulas use namespace-prefixed field names that break post-migration** — Some DataRaptor Extract and Load operations that were built for Vlocity managed packages include field API names prefixed with the Vlocity namespace (e.g., `vlocity_ins__Status__c`). After migration, if the org's data model still has these fields on standard objects, the DataRaptor references remain valid. However, any DataRaptor that was referencing Vlocity-owned objects or fields that do not exist in the native model will fail silently — the Extract returns empty results rather than throwing an error.
4. **`sf project retrieve` does not retrieve native OmniStudio components by default** — Native OmniStudio metadata types (`OmniScriptDefinition`, `OmniIntegrationProcedure`, `OmniDataTransform`, `OmniUiCard`) must be explicitly listed in the `package.xml` manifest or project configuration for SFDX retrieval. Orgs that have migrated from Vlocity and assume their existing SFDX project captures all components will miss the native OmniStudio metadata in source control.
5. **Apex classes compiled against the Vlocity managed package fail after package uninstall** — Any Apex class in the org that references `vlocity_ins.*` (or the relevant namespace) will fail to compile if the managed package is uninstalled before the Apex is updated. This makes managed package uninstall a blocking step that can only happen after all Apex references are fully updated. Package uninstall can also be blocked if there are referencing metadata records, not just code.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Namespace audit report | Output of checker script listing all Vlocity namespace references by file and line |
| Migration Tool log | Log from the OmniStudio Migration Tool showing component conversion status |
| Updated LWC markup | HTML files with managed package tags replaced by native `omnistudio-*` tags |
| Updated Apex classes | Service class references updated from `vlocity_*` to `omnistudio` namespace |
| Rebuilt CI/CD pipeline | SFDX-based deployment pipeline replacing Vlocity Build Tool DataPacks |
| Side-by-side test plan | Test matrix comparing Vlocity and native component behavior for each migrated component |
| Post-migration validation checklist | Completed checklist confirming native runtime is fully operational and Vlocity dependencies cleared |

---

## Related Skills

- `omnistudio/omnistudio-lwc-integration` — use when updating LWC components to use native `omnistudio-*` tags post-migration; covers seed data, pubsub, and custom element conventions
- `omnistudio/omniscript-design-patterns` — use when native OmniScript behavior needs to be redesigned after migration uncovers feature gaps
- `omnistudio/dataraptor-patterns` — use when DataRaptor formulas or field references need rework post-migration
- `omnistudio/integration-procedures` — use when Integration Procedure HTTP actions or service class calls need namespace updates
- `omnistudio/omnistudio-deployment-datapacks` — use when understanding the Vlocity DataPacks model before replacing it with SFDX-native deployment
