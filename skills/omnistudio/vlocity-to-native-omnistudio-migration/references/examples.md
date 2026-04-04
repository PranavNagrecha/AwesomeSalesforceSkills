# Examples — Vlocity to Native OmniStudio Migration

## Example 1: Updating LWC Markup from Managed Package Tags to Native Tags

**Context:** An Insurance Cloud org running the `vlocity_ins` managed package has a custom LWC component that embeds an OmniScript on a Lightning record page. After the org administrator enables `enableOaForCore` and runs the OmniStudio Migration Tool to create native copies of all OmniScripts, the page renders blank where the OmniScript should appear.

**Problem:** The LWC HTML file still uses the `<c-omni-script>` tag from the Vlocity managed package. With `enableOaForCore` active, the native runtime is responsible for rendering OmniStudio components, but the native runtime does not register or resolve the `c-omni-script` custom element. The component silently fails to mount.

**Solution:**

Before (managed package):
```html
<!-- claimsIntakeWrapper.html -->
<template>
    <c-omni-script
        omni-script-type="Claims"
        omni-script-sub-type="NewLoss"
        omni-seed-json={seedJson}
        oncomplete={handleComplete}>
    </c-omni-script>
</template>
```

After (native OmniStudio):
```html
<!-- claimsIntakeWrapper.html -->
<template>
    <omnistudio-omni-script
        omni-script-type="Claims"
        omni-script-sub-type="NewLoss"
        omni-seed-json={seedJson}
        oncomplete={handleComplete}>
    </omnistudio-omni-script>
</template>
```

No changes are required to the JavaScript file — the attribute names (`omni-script-type`, `omni-script-sub-type`, `omni-seed-json`) and event names (`oncomplete`) are identical between managed package and native runtime.

**Why it works:** Native OmniStudio registers component elements under the `omnistudio` namespace. The string `c-omni-script` is a managed package component that is no longer registered once the native runtime takes over. Replacing the tag name resolves the render failure.

---

## Example 2: Replacing Vlocity Service Class Calls in Apex

**Context:** A Communications Cloud org is migrating from `vlocity_cmt` to native OmniStudio. A custom Apex class exposes an `@AuraEnabled` method that LWC components use to invoke Integration Procedures server-side. After the Migration Tool is run and native Integration Procedures are activated, the LWC begins throwing errors because the Apex class is still calling the Vlocity service class.

**Problem:** `vlocity_cmt.IntegrationProcedureService` is a class inside the installed managed package. If the Integration Procedure being invoked has been migrated to native and is only active as a native component, the Vlocity service class will not find it — it only looks in the managed package component records, not in native OmniStudio metadata.

**Solution:**

Before (managed package):
```apex
public class OrderOrchestrationService {
    @AuraEnabled
    public static Map<String, Object> runOrderValidation(Map<String, Object> inputMap) {
        Map<String, Object> outputMap = new Map<String, Object>();
        Map<String, Object> options = new Map<String, Object>();
        vlocity_cmt.IntegrationProcedureService.runIntegrationService(
            'Order_ValidateEligibility',
            inputMap,
            outputMap,
            options
        );
        return outputMap;
    }
}
```

After (native OmniStudio):
```apex
public class OrderOrchestrationService {
    @AuraEnabled
    public static Map<String, Object> runOrderValidation(Map<String, Object> inputMap) {
        Map<String, Object> outputMap = new Map<String, Object>();
        Map<String, Object> options = new Map<String, Object>();
        omnistudio.IntegrationProcedureService.runIntegrationService(
            'Order_ValidateEligibility',
            inputMap,
            outputMap,
            options
        );
        return outputMap;
    }
}
```

The Integration Procedure name string (`'Order_ValidateEligibility'`) does not change — native OmniStudio uses the same type/subtype naming convention. Only the service class namespace changes.

**Why it works:** Native OmniStudio exposes `omnistudio.IntegrationProcedureService` as the equivalent server-side invocation class. The method signature is identical to the Vlocity version, so only the namespace prefix needs to change. Apex must be recompiled after this change, and the managed package must still be installed until all references are removed.

---

## Example 3: Rebuilding a DataPacks CI/CD Pipeline with SFDX

**Context:** A Health Cloud org used the Vlocity Build Tool (VBT) and DataPacks to deploy OmniStudio components between sandboxes and production. After migrating to native OmniStudio, the DataPacks pipeline stops working because native OmniStudio components are stored as platform metadata, not as record-based DataPacks.

**Problem:** Running `vlocity -job deploy -key OmniScript/Claims/NewLoss` against a native org finds nothing to deploy because the component no longer exists as a record in `vlocity_ins__OmniScript__c`. Attempting to import a DataPack exported from the old org into the new native org creates orphaned records that the native runtime does not use.

**Solution:**

Replace the VBT deploy job with SFDX:

`package.xml` (add to retrieve native OmniStudio types):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>OmniScriptDefinition</name>
    </types>
    <types>
        <members>*</members>
        <name>OmniIntegrationProcedure</name>
    </types>
    <types>
        <members>*</members>
        <name>OmniDataTransform</name>
    </types>
    <types>
        <members>*</members>
        <name>OmniUiCard</name>
    </types>
    <version>63.0</version>
</Package>
```

Retrieve command:
```bash
sf project retrieve start --manifest package.xml --target-org myOrgAlias
```

Deploy command:
```bash
sf project deploy start --manifest package.xml --target-org targetOrgAlias
```

**Why it works:** Native OmniStudio components are first-class Salesforce metadata types supported by the Metadata API and SFDX CLI. Standard CI/CD pipelines (GitHub Actions, Copado, Gearset) that use SFDX can manage these components without any Vlocity-specific tooling. The metadata types must be explicitly declared in `package.xml` because they are not included in wildcard `*` retrieves by default for all org configurations.

---

## Anti-Pattern: Running the Migration Tool Without a Pre-Migration Code Audit

**What practitioners do:** An admin runs the OmniStudio Migration Tool immediately after enabling `enableOaForCore`, assumes migration is complete when the tool reports success, and declares the org migrated.

**What goes wrong:** The Migration Tool only converts OmniStudio component definitions (the records or metadata). It does not update custom LWC files, Apex classes, flows, or any other custom code that references Vlocity namespace APIs. After the tool runs, every LWC component that uses `c-omni-script` still renders blank, every Apex class that calls `vlocity_ins.IntegrationProcedureService` still targets the managed package, and all DataPack-based CI/CD jobs still fail. Discovering these issues post-migration rather than pre-migration extends the project timeline significantly.

**Correct approach:** Run the checker script and perform a full namespace audit of the codebase before running the Migration Tool. Scope the custom code remediation effort. Only run the Migration Tool once the team has a plan to address all code-level Vlocity references in parallel.
