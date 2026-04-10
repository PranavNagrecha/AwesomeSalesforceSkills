# LLM Anti-Patterns — FSL Mobile App Extensions

Common mistakes AI coding assistants make when generating or advising on FSL Mobile App Extensions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Omitting the Page Layout Placement Step

**What the LLM generates:** A complete LWC component and Quick Action metadata, with deployment instructions that say "add to App Builder page" — never mentioning the page layout.

**Why it happens:** Training data about LWC Quick Actions overwhelmingly describes the App Builder configuration path because that is the standard Lightning Experience pattern. The FSL-specific requirement that page layout placement is what enables offline availability is a niche detail under-represented in training data.

**Correct pattern:**

```
Deployment checklist:
1. Deploy LWC component and Quick Action metadata.
2. Open Setup > Object Manager > WorkOrder > Page Layouts > [Layout Name].
3. In "Salesforce Mobile and Lightning Experience Actions", add the Quick Action.
   (This step — not App Builder — enables offline availability.)
4. Assign "Enable Lightning SDK for FSL Mobile" permission set to all target users.
```

**Detection hint:** Any deployment guide for an FSL Mobile LWC extension that mentions only App Builder and does not mention "page layout" is incomplete.

---

## Anti-Pattern 2: Using Imperative Apex Calls for Data Needed Offline

**What the LLM generates:**

```javascript
handleLoadData() {
    getWorkOrderDetails({ recordId: this.recordId })
        .then(data => { this.details = data; })
        .catch(err => { console.error(err); });
}
```
Called from a button click or `connectedCallback`, without a wire adapter.

**Why it happens:** Imperative Apex calls are the dominant pattern in Apex + LWC tutorials because they give explicit control over when a call fires. LLMs generalize this to mobile contexts where LDS caching and offline behavior require wire adapters.

**Correct pattern:**

```javascript
@wire(getWorkOrderDetails, { recordId: '$recordId' })
wiredDetails({ data, error }) {
    if (data) { this.details = data; }
    else if (error) { this.handleError(error); }
}
```

**Detection hint:** Any `import ... from '@salesforce/apex/...'` that is called inside a function body (not decorated with `@wire`) in an FSL Mobile extension is a candidate for this anti-pattern.

---

## Anti-Pattern 3: Generating LWC Imports Inside an HTML5 Mobile Extension

**What the LLM generates:**

```javascript
// In an HTML5 Mobile Extension Toolkit file
import { LightningElement, api } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';
```

**Why it happens:** The distinction between the HTML5 Extension Toolkit (a separate, pre-LWC framework) and LWC Quick Actions is often collapsed in general FSL mobile documentation. LLMs conflate the two models and generate LWC syntax for files that must be plain HTML/JavaScript.

**Correct pattern:**

```javascript
// HTML5 Mobile Extension Toolkit — no LWC imports
// Access Apex data via REST API only
fetch('/services/apexrest/MyEndpoint', {
    method: 'GET',
    headers: { Authorization: 'Bearer ' + sessionId }
}).then(res => res.json()).then(data => { /* handle */ });
```

**Detection hint:** Any `import` statement containing `lwc`, `lightning/`, or `@salesforce/` inside a file described as an HTML5 Mobile Extension is wrong.

---

## Anti-Pattern 4: Recommending Briefcase Builder for Custom Metadata Types

**What the LLM generates:** "Add `Failure_Code__mdt` to your Briefcase Builder priming configuration to make it available offline."

**Why it happens:** Briefcase Builder supports standard and custom objects. LLMs generalize this to Custom Metadata Types because the distinction between Custom Objects and Custom Metadata Types is subtle in training data. The documentation for Briefcase Builder does not prominently state that CMTs are excluded.

**Correct pattern:**

```
Custom Metadata Types CANNOT be primed via Briefcase Builder.
To make CMT data available offline:
1. Create a Custom Object (e.g., FailureCodeCache__c) linked to ServiceResource.
2. Apex controller queries CMT and writes to the Custom Object when online.
3. Briefcase Builder primes the Custom Object (it IS supported).
4. LWC reads from the Custom Object via getRecord when offline.
```

**Detection hint:** Any configuration or instruction that places a `__mdt` object in a Briefcase Builder priming target list is wrong.

---

## Anti-Pattern 5: Assuming `lightning__GlobalAction` Renders in Lightning Experience

**What the LLM generates:** "You can test your FSL Mobile action by opening the global actions menu in Lightning Experience. Click the waffle icon and find the action in the dropdown."

**Why it happens:** `lightning__GlobalAction` is a real target type in Lightning Experience. LLMs correctly associate it with the global actions menu. The FSL-specific behavior — that an LWC targeted at `lightning__GlobalAction` for FSL Mobile renders only in the FSL native app — is not reflected in mainstream LWC documentation.

**Correct pattern:**

```
An LWC component targeted at lightning__GlobalAction for FSL Mobile
does NOT render in standard Lightning Experience or standard Salesforce Mobile.
Test exclusively in the FSL native mobile app on a device.
For desktop testing, create a separate lightning__RecordAction version
of the component.
```

**Detection hint:** Any testing instruction for an FSL Mobile Global Action that references the Lightning Experience UI (browser, waffle icon, global actions menu) is incorrect for validating FSL Mobile behavior.

---

## Anti-Pattern 6: Ignoring the 1,000 Page-Reference Limit in Priming Guidance

**What the LLM generates:** "Configure Briefcase Builder to prime all ServiceAppointments, WorkOrders, and WorkOrderLineItems for your technicians."

**Why it happens:** General Briefcase Builder documentation describes the configuration steps without prominently surfacing the 1,000 page-reference limit. LLMs repeat the configuration guidance without the operational constraint.

**Correct pattern:**

```
Briefcase Builder has a hard limit of 1,000 page references per priming run.
Exceeding the limit causes records to be silently dropped — no error is surfaced.

Apply filters to stay well below the limit:
- Date range: next 7 days of appointments
- Status: Scheduled, Dispatched (exclude Completed, Cancelled)
- Territory: technician's assigned territory only

Target < 750 page references to maintain a safe buffer.
```

**Detection hint:** Any Briefcase Builder configuration recommendation that does not include date-range or status filters for a territory with more than a handful of technicians is likely to cause silent data loss.
