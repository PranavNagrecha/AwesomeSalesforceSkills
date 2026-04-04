# Gotchas — Vlocity to Native OmniStudio Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Migration Tool Creates Components in Inactive State

**What happens:** The OmniStudio Migration Tool successfully runs and reports that all components were migrated. However, end users still see the old Vlocity-driven OmniScripts and FlexCards. The native versions exist in the org but are not being served.

**When it occurs:** Immediately after running the Migration Tool in any org. This is the default behavior — the tool creates native copies of all converted components with `isActive` set to `false`. The Vlocity managed package components remain active until explicitly deactivated.

**How to avoid:** After the Migration Tool completes, open the OmniStudio designer for each migrated component and explicitly activate it, OR deploy the metadata with `isActive: true` via SFDX. Do not assume the tool activates components. Build an activation step into the migration runbook. During a controlled cutover, this two-phase approach (migrate inactive, activate on schedule) is actually useful for timing the switch.

---

## Gotcha 2: Same Type/Subtype Active in Both Runtimes Causes Non-Deterministic Routing

**What happens:** After activating native OmniScript components, some users are served the native version while others are served the Vlocity version for the same OmniScript type/subtype. The behavior appears inconsistent and is hard to reproduce.

**When it occurs:** When both the Vlocity managed package OmniScript and the native OmniStudio OmniScript share the same type and subtype, and both are simultaneously in an active state. The routing logic used when invoking OmniScripts via FlexCard actions, URL invocations, or LWC tags may resolve to either version depending on the invocation method and org caching.

**How to avoid:** Never have two active OmniScripts (one Vlocity, one native) with the same type/subtype at the same time. The correct cutover sequence is: (1) confirm the native version passes testing, (2) deactivate the Vlocity version, (3) activate the native version. If a rollback is needed, reverse the sequence.

---

## Gotcha 3: `sf project retrieve` Does Not Capture Native OmniStudio Components by Default

**What happens:** A developer runs `sf project retrieve start --source-dir force-app` after the migration and sees that OmniScript, DataRaptor, Integration Procedure, and FlexCard definitions are not pulled down to the local project. The source directory does not reflect what is deployed in the org.

**When it occurs:** When the SFDX project was set up before native OmniStudio was in use and the project's `package.xml` or `.forceignore` does not include native OmniStudio metadata types. Native types (`OmniScriptDefinition`, `OmniIntegrationProcedure`, `OmniDataTransform`, `OmniUiCard`) are not included in generic wildcard retrieves in all configurations.

**How to avoid:** Explicitly add all four native OmniStudio metadata types to the `package.xml` manifest. After the initial retrieve, verify that the `force-app/main/default/` directory contains subdirectories for each OmniStudio component type. Add these types to the project's source tracking configuration to ensure ongoing sync works correctly.

---

## Gotcha 4: DataRaptor Formulas Referencing Vlocity Object Fields Break Silently

**What happens:** After migration, DataRaptor Extract operations return empty results for fields that previously returned data. There are no errors in the OmniScript or DataRaptor debug log — the formula simply evaluates to null.

**When it occurs:** When a DataRaptor Extract formula includes Vlocity namespace-prefixed field API names (e.g., `vlocity_ins__PolicyNumber__c`) that refer to fields on custom objects owned by the Vlocity managed package. After the managed package is uninstalled (or in orgs where the native DataRaptor was created without these fields), the field references are invalid. DataRaptors do not throw exceptions for invalid field paths — they return empty/null values.

**How to avoid:** Before migration, audit all DataRaptor Extract formulas for namespace-prefixed field references. Determine which fields are on Vlocity-owned custom objects (which disappear on package uninstall) vs. which are on standard Salesforce objects with Vlocity-added fields (which persist). Rebuild DataRaptor formulas to reference the correct field paths in the native schema. Test each DataRaptor explicitly after migration to verify field values are populated.

---

## Gotcha 5: Apex Classes Referencing Vlocity APIs Block Managed Package Uninstall

**What happens:** The managed package uninstall fails with an error stating that the package cannot be removed because dependent Apex classes or triggers still reference managed package types.

**When it occurs:** When attempting to uninstall the Vlocity managed package before all Apex code referencing `vlocity_ins.*`, `vlocity_cmt.*`, or `vlocity_ps.*` classes has been updated and deployed. Salesforce enforces a compile-time dependency check during package uninstall — if any Apex in the org references the package namespace, the uninstall is blocked.

**How to avoid:** Complete all Apex class updates (replacing Vlocity service class calls with native equivalents) and deploy them to production before attempting the managed package uninstall. Run the namespace audit script to confirm zero remaining Apex references to Vlocity namespaces. The same constraint applies to custom metadata, flows, and other metadata types that reference managed package fields or objects.

---

## Gotcha 6: OmniOut External Deployment Is Not Feature-Equivalent in Native Runtime

**What happens:** FlexCards or OmniScripts that were deployed externally (outside Salesforce, on portals or third-party sites) using the Vlocity OmniOut capability stop functioning after migration. The OmniOut configuration references Vlocity package endpoints that no longer exist in the native runtime.

**When it occurs:** When an org uses Vlocity OmniOut — the Vlocity mechanism for embedding OmniStudio components in non-Salesforce web pages. Native OmniStudio provides a different approach to external embedding (Experience Cloud / Digital Experiences, or LWC Out) that does not directly replicate all Vlocity OmniOut capabilities as of Spring '25.

**How to avoid:** Inventory all OmniOut usage before starting the migration. Evaluate whether the native OmniStudio external embedding approach (Experience Cloud guest user access, or LWC Out for external sites) meets the business requirements. If there is a gap, document it as a migration blocker and do not decommission the Vlocity managed package until a native equivalent is confirmed. This is one of the most common reasons migration timelines extend beyond initial estimates.
