# LLM Anti-Patterns — Vlocity to Native OmniStudio Migration

Common mistakes AI coding assistants make when generating or advising on Vlocity to native OmniStudio migration tasks. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Telling the User the Migration Tool Completes the Migration

**What the LLM generates:** "Run the OmniStudio Migration Tool in Setup and your migration is complete. The tool will convert all your Vlocity components to native OmniStudio format automatically."

**Why it happens:** The Migration Tool is a prominent, named feature that LLMs correctly identify. Training data likely contains marketing and documentation that emphasizes the tool's automation. LLMs conflate "the tool handles component definitions" with "the tool handles everything."

**Correct pattern:**
```
The OmniStudio Migration Tool handles component definition migration only.
After running the tool, you must separately:
1. Update all LWC HTML files that use managed package component tags (c-omni-script → omnistudio-omni-script)
2. Update all Apex classes that call Vlocity service classes (vlocity_ins.IntegrationProcedureService → omnistudio.IntegrationProcedureService)
3. Rebuild CI/CD pipelines from Vlocity Build Tool DataPacks to SFDX + native metadata types
4. Activate all migrated components (the tool creates them inactive)
5. Test and validate all migrated components before decommissioning Vlocity versions
```

**Detection hint:** Any migration guidance that says "run the tool and you're done" without mentioning code updates, activation steps, or pipeline replacement is incomplete.

---

## Anti-Pattern 2: Using `c-omni-script` Tags After Migration in LWC

**What the LLM generates:**
```html
<template>
    <c-omni-script
        omni-script-type="Claims"
        omni-script-sub-type="NewLoss">
    </c-omni-script>
</template>
```

**Why it happens:** The `c-omni-script` tag is prevalent in Salesforce community forums, older documentation, and Vlocity implementation guides. LLMs trained on this corpus frequently generate managed package tags even when the user specifies a native OmniStudio context.

**Correct pattern:**
```html
<!-- Native OmniStudio (enableOaForCore = true) -->
<template>
    <omnistudio-omni-script
        omni-script-type="Claims"
        omni-script-sub-type="NewLoss">
    </omnistudio-omni-script>
</template>
```

**Detection hint:** Any generated LWC that uses `c-omni-script`, `c-flex-card`, or `c-omni-card` in an org described as "native OmniStudio" or "enableOaForCore enabled" is using the wrong tag. Search LWC HTML output for `<c-omni-` to catch this.

---

## Anti-Pattern 3: Recommending Vlocity Build Tool DataPacks for Native OmniStudio Deployment

**What the LLM generates:** "To deploy your OmniStudio components between environments, use the Vlocity Build Tool: `vlocity -job deploy -key OmniScript/Claims/NewLoss`"

**Why it happens:** The Vlocity Build Tool and DataPacks format are widely documented and the LLM has extensive training data on VBT usage. The LLM does not distinguish between managed-package-era and native-era deployment approaches.

**Correct pattern:**
```bash
# Native OmniStudio uses standard SFDX deployment
# Add OmniStudio types to package.xml:
# OmniScriptDefinition, OmniIntegrationProcedure, OmniDataTransform, OmniUiCard

sf project retrieve start --manifest package.xml --target-org sourceOrg
sf project deploy start --manifest package.xml --target-org targetOrg
```

**Detection hint:** Any deployment advice for native OmniStudio that references `vlocity -job deploy`, DataPacks, or the Vlocity Build Tool CLI is inappropriate for a post-migration native org. The correct tooling is the Salesforce CLI (`sf` or `sfdx`) with the appropriate metadata types in the manifest.

---

## Anti-Pattern 4: Recommending Direct REST Calls to Integration Procedure Endpoints from LWC

**What the LLM generates:**
```javascript
// In LWC JavaScript
async runIntegrationProcedure() {
    const response = await fetch('/api/v1/integrationprocedures/Accounts_GetDetails', {
        method: 'POST',
        body: JSON.stringify(this.inputData)
    });
}
```

**Why it happens:** Some Vlocity documentation and community posts describe REST endpoint invocation for Integration Procedures. LLMs trained on this material may suggest direct HTTP calls as a shortcut, not recognizing the security implications.

**Correct pattern:**
```apex
// Apex class (server-side)
public class IntegrationProcureBridge {
    @AuraEnabled
    public static Map<String, Object> runAccountsGetDetails(Map<String, Object> input) {
        Map<String, Object> output = new Map<String, Object>();
        Map<String, Object> options = new Map<String, Object>();
        omnistudio.IntegrationProcedureService.runIntegrationService(
            'Accounts_GetDetails', input, output, options
        );
        return output;
    }
}
```
```javascript
// LWC JavaScript (client-side)
import runAccountsGetDetails from '@salesforce/apex/IntegrationProcureBridge.runAccountsGetDetails';
```

**Detection hint:** Any generated LWC code that calls Integration Procedure endpoints via `fetch`, `XMLHttpRequest`, or any HTTP client without going through an `@AuraEnabled` Apex intermediary bypasses Apex sharing rules. Check LWC JavaScript for direct HTTP calls to `/api/` or Integration Procedure URL patterns.

---

## Anti-Pattern 5: Querying Vlocity Custom Objects After Migration

**What the LLM generates:**
```apex
List<vlocity_ins__OmniScript__c> scripts = [
    SELECT Id, vlocity_ins__Type__c, vlocity_ins__SubType__c
    FROM vlocity_ins__OmniScript__c
    WHERE vlocity_ins__Active__c = true
];
```

**Why it happens:** In Vlocity managed package orgs, OmniScript definitions are stored as records in the `vlocity_ins__OmniScript__c` custom object. LLMs trained on Vlocity implementation patterns naturally generate SOQL that queries this object. After migration to native OmniStudio, component definitions are stored as platform metadata, not as sObject records — this SOQL returns zero results or fails with a compile error if the package has been uninstalled.

**Correct pattern:**
```
After migrating to native OmniStudio, OmniScript definitions are platform
metadata (OmniScriptDefinition type), not sObject records. Do not query
vlocity_ins__OmniScript__c or similar managed package objects.

To retrieve OmniScript metadata programmatically, use the Metadata API
or SFDX CLI:
  sf project retrieve start --metadata OmniScriptDefinition --target-org myOrg

There is no equivalent run-time SOQL for native OmniStudio component definitions.
```

**Detection hint:** Any SOQL or Apex that references `vlocity_ins__OmniScript__c`, `vlocity_cmt__OmniScript__c`, `vlocity_ins__DataRaptor__c`, or similar Vlocity-namespaced custom objects is using the managed package data model and will not work in a fully migrated native OmniStudio org. Search Apex files for `FROM vlocity_` to catch this pattern.

---

## Anti-Pattern 6: Assuming All Vlocity Features Have Native Equivalents

**What the LLM generates:** "All Vlocity OmniStudio features are fully supported in native OmniStudio. You can migrate everything without any feature gaps."

**Why it happens:** Salesforce marketing and documentation emphasizes feature parity for core OmniStudio components. LLMs extrapolate this to mean complete equivalence, without acknowledging known gaps.

**Correct pattern:**
```
Core OmniStudio components (OmniScript, DataRaptor, Integration Procedure,
FlexCard) have native equivalents and the Migration Tool handles their
conversion. However, known feature areas that may NOT have full equivalents
in native OmniStudio (as of Spring '25) include:

- OmniOut (external deployment of OmniScripts outside Salesforce)
- Some Vlocity Industry-specific DataPack types (Product Catalog, Pricing)
- Advanced CPQ integration hooks specific to Vlocity CPQ
- Certain Vlocity-specific OmniScript element types not yet GA in native

Always inventory OmniOut usage and any non-OmniStudio component types
before committing to a migration timeline.
```

**Detection hint:** Any migration advice that states "full feature parity" or "migrate everything" without qualifying known gaps is overconfident. Validate feature parity claims against the official Salesforce OmniStudio migration documentation before proceeding.
