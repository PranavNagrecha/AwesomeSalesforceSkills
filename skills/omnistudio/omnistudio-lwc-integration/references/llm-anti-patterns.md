# LLM Anti-Patterns — OmniStudio LWC Integration

Common mistakes AI coding assistants make when generating or advising on OmniStudio LWC integration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using the Wrong Component Namespace Tag

**What the LLM generates:** The AI recommends `c-omni-script` in a native OmniStudio context, or recommends `omnistudio-omni-script` in a managed package context, because it has seen both in training data without understanding the runtime dependency.

**Why it happens:** OmniStudio documentation covers both native and managed package runtimes. LLMs trained on mixed documentation surfaces both tags without consistently tracking which applies to which runtime. The tags look similar and are easy to conflate.

**Correct pattern:**

```html
<!-- Native OmniStudio (enableOaForCore = true) -->
<omnistudio-omni-script
  omni-script-type="ServiceRequest"
  omni-script-sub-type="New"
  omni-seed-json={seedJson}
  oncomplete={handleComplete}
></omnistudio-omni-script>

<!-- Managed Package (vlocity_cmt / vlocity_ins / vlocity_ps) -->
<c-omni-script
  omni-script-type="ServiceRequest"
  omni-script-sub-type="New"
  omni-seed-json={seedJson}
  oncomplete={handleComplete}
></c-omni-script>
```

**Detection hint:** Grep the generated markup for both `omnistudio-omni-script` and `c-omni-script` in the same file or component. If both appear, the AI has conflated the runtimes. Also check if the AI has used `c-omni-script` without confirming the managed package runtime.

---

## Anti-Pattern 2: Missing or Incorrectly Structured Seed Data JSON Wrapper

**What the LLM generates:** The AI passes seed data as a flat key-value object without matching the OmniScript's expected field hierarchy, or wraps it in an extra nesting level that the OmniScript does not expect.

```javascript
// Wrong: flat object where OmniScript expects nested path
return JSON.stringify({ recordId: this.recordId });

// Wrong: extra wrapper key that OmniScript does not expect
return JSON.stringify({ seed: { AccountId: this.recordId } });
```

**Why it happens:** LLMs default to simple flat JSON when they lack knowledge of the specific OmniScript's data model. The OmniScript seed data JSON must mirror the exact field hierarchy that the OmniScript uses internally, which is script-specific and not inferable from the component API.

**Correct pattern:**

```javascript
// Correct: keys match the OmniScript's internal field names and nesting
get seedJson() {
  return JSON.stringify({
    AccountId: this.recordId,
    AccountName: this.accountName
    // Field names and nesting must match the OmniScript data model exactly
  });
}
```

**Detection hint:** If the AI generates seed data as a simple `{ id: value }` structure without referencing the OmniScript type/subtype's expected data shape, flag it for review. Seed data structures are script-specific and must be validated against the OmniScript definition.

---

## Anti-Pattern 3: Setting Seed Data Imperatively After Component Mount

**What the LLM generates:** The AI sets the seed data on the OmniScript component reference in `connectedCallback` or `renderedCallback` after the component has already mounted.

```javascript
// Wrong: setting seed data after mount — OmniScript ignores it
connectedCallback() {
  const el = this.template.querySelector('omnistudio-omni-script');
  el.omniSeedJson = JSON.stringify({ AccountId: this.recordId });
}
```

**Why it happens:** LLMs pattern-match on standard LWC property-setting patterns, where setting a property imperatively on a child component reference is a common and valid pattern. They do not know that the OmniScript runtime initializes its data model at connection time and ignores post-mount seed changes.

**Correct pattern:**

```html
<!-- Correct: seed JSON bound as a reactive template expression -->
<omnistudio-omni-script
  omni-seed-json={seedJson}
></omnistudio-omni-script>
```

```javascript
// seedJson is a reactive getter evaluated before the child connects
get seedJson() {
  return JSON.stringify({ AccountId: this.recordId });
}
```

**Detection hint:** Look for `querySelector` combined with `omniSeedJson =` or `omni-seed-json` attribute assignment inside `connectedCallback`, `renderedCallback`, or an event handler.

---

## Anti-Pattern 4: Using `@wire` Inside Custom OmniScript LWC Elements

**What the LWC generates:** The AI adds `@wire(getRecord, { recordId: ... })` or other wire adapters inside the custom LWC element component, expecting them to resolve correctly inside the OmniScript runtime.

```javascript
// Wrong: wire adapter inside a custom OmniScript element
@wire(getRecord, { recordId: '$omniJsonData.recordId', fields: [NAME_FIELD] })
record;
```

**Why it happens:** Wire adapters are the standard LWC pattern for data fetching. LLMs apply them broadly without knowing that the OmniScript runtime's handling of the wire service lifecycle may not align with step navigation, causing wire subscriptions to not re-resolve after step transitions.

**Correct pattern:**

```javascript
// Correct: use omniJsonData to receive context from the OmniScript runtime
// and use imperative Apex for additional data needs
import { LightningElement, api } from 'lwc';
import getAdditionalData from '@salesforce/apex/MyController.getAdditionalData';

export default class MyOmniElement extends LightningElement {
  @api omniJsonData;

  async connectedCallback() {
    if (this.omniJsonData?.recordId) {
      const result = await getAdditionalData({ recordId: this.omniJsonData.recordId });
      // use result
    }
  }
}
```

**Detection hint:** Look for `@wire` decorator usage in any LWC that also declares `@api omniJsonData` or `@api omniOutputMap` — those are markers of a custom OmniScript element.

---

## Anti-Pattern 5: Calling Integration Procedures via Direct REST from LWC

**What the LWM generates:** The AI generates a `fetch` call to the OmniStudio Integration Procedure REST endpoint directly from LWC JavaScript, bypassing Apex.

```javascript
// Wrong: direct REST call bypasses sharing rules and CSRF protections
const response = await fetch('/services/apexrest/v1/integrationprocedure/MyIP_Run', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(inputData)
});
```

**Why it happens:** LLMs know that Integration Procedures expose REST endpoints and recommend the direct approach because it is fewer lines of code. They do not model the security and governor limit implications of bypassing the Apex service layer.

**Correct pattern:**

```apex
// Correct: Apex bridge that respects sharing and governor limits
public with sharing class IntegrationProcedureBridge {
  @AuraEnabled
  public static Map<String, Object> run(String procedureName, Map<String, Object> input) {
    return (Map<String, Object>) omnistudio.IntegrationProcedureService
      .runIntegrationService(procedureName, input, new Map<String, Object>());
  }
}
```

```javascript
// LWC calls the Apex bridge
import runIP from '@salesforce/apex/IntegrationProcedureBridge.run';
const result = await runIP({ procedureName: 'MyIP_Run', input: inputData });
```

**Detection hint:** Grep generated JavaScript for `fetch('/services/apexrest` or `XMLHttpRequest` targeting an Integration Procedure endpoint. Any direct HTTP call to an OmniStudio service endpoint from LWC is a red flag.

---

## Anti-Pattern 6: Using Standard LWC Navigation to Launch OmniScript Without Seed Data

**What the LLM generates:** The AI generates a `NavigationMixin.Navigate` call to a `standard__component` page reference for the OmniScript without including seed data, causing the OmniScript to launch blank.

```javascript
// Wrong: navigates to OmniScript without seed data
this[NavigationMixin.Navigate]({
  type: 'standard__component',
  attributes: {
    componentName: 'omnistudio__OmniScriptWrapper'
  }
});
```

**Why it happens:** LLMs know the NavigationMixin pattern for Lightning navigation but do not consistently include the `state` property for passing seed data to the OmniScript wrapper component.

**Correct pattern:**

```javascript
// Correct: include state with the OmniScript attributes and seed data
this[NavigationMixin.Navigate]({
  type: 'standard__component',
  attributes: {
    componentName: 'omnistudio__OmniScriptWrapper'
  },
  state: {
    omnistudio__recordId: this.recordId,
    'omnistudio__omniScriptType': 'ServiceRequest',
    'omnistudio__omniScriptSubType': 'New',
    'omnistudio__omniSeedJson': JSON.stringify({ AccountId: this.recordId })
  }
});
```

**Detection hint:** Look for `standard__component` navigation to an OmniScript wrapper without a `state` property. Any navigation to an OmniScript without seed data configuration should be flagged for review.
