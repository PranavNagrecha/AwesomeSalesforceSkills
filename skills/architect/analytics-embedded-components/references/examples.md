# Examples — Analytics Embedded Components

## Example 1: Embedding a Dashboard on a Lightning Record Page with Record Context Filtering

**Context:** A sales team wants to see an Account-level revenue analytics dashboard directly on the Account record page. The dashboard must automatically scope to the account being viewed — no manual filtering required.

**Problem:** Without the `record-id` attribute correctly bound, the dashboard loads in its global default state and shows all accounts' data regardless of which account record is open. Practitioners commonly set a hardcoded record ID or omit the binding entirely.

**Solution:**

In Lightning App Builder, drag the "CRM Analytics Dashboard" component onto the Account record page. Set:
- `Dashboard` (or `Developer Name`): the API name `Account_Revenue_Overview`
- `Record ID`: `{!recordId}` (App Builder populates this at runtime with the current record's 18-char ID)

If building a custom LWC wrapper that hosts the embedded dashboard:

```html
<!-- accountDashboardHost.html -->
<template>
    <wave-wave-dashboard-lwc
        developer-name="Account_Revenue_Overview"
        record-id={recordId}
        show-title="false"
        show-sharing-button="false">
    </wave-wave-dashboard-lwc>
</template>
```

```javascript
// accountDashboardHost.js
import { LightningElement, api } from 'lwc';

export default class AccountDashboardHost extends LightningElement {
    @api recordId; // populated by Lightning runtime on record pages
}
```

```xml
<!-- accountDashboardHost.js-meta.xml -->
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordPage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <property name="recordId" type="String" label="Record ID" />
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**Why it works:** `wave-wave-dashboard-lwc` is the correct component for Lightning App Builder pages. The `record-id` attribute passes the current record's 18-char ID to the dashboard at render time. The dashboard must have been designed in Analytics Studio with a filter or binding that reads this passed record ID — the attribute makes the ID available; it does not automatically scope data on its own. Using `developer-name` instead of `dashboard` makes the configuration portable across orgs (sandbox vs. production IDs differ; developer names are stable).

---

## Example 2: Embedding a Custom LWC Inside an Analytics Dashboard Canvas (Pattern B)

**Context:** A dashboard designer wants to add a "Create Follow-up Task" button directly inside a CRM Analytics dashboard. When a sales rep selects a deal from a dashboard chart, they should be able to click the button to create a Salesforce Task record without leaving Analytics. A custom LWC implements the Task creation logic.

**Problem:** Practitioners attempt to add a standard LWC button to an Analytics dashboard by dragging it from the App Builder component palette. Standard LWCs do not appear in the Analytics dashboard widget picker. The `analytics__Dashboard` LWC target must be declared in `js-meta.xml` for the component to be available inside a dashboard.

**Solution:**

Step 1 — Declare the `analytics__Dashboard` target in `js-meta.xml`:

```xml
<!-- createFollowUpTask.js-meta.xml -->
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>analytics__Dashboard</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="analytics__Dashboard">
            <property name="taskSubject"
                      type="String"
                      label="Default Task Subject"
                      default="Follow up" />
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

Step 2 — Implement the LWC:

```html
<!-- createFollowUpTask.html -->
<template>
    <lightning-button
        label="Create Follow-up Task"
        onclick={handleCreateTask}>
    </lightning-button>
</template>
```

```javascript
// createFollowUpTask.js
import { LightningElement, api } from 'lwc';
import { createRecord } from 'lightning/uiRecordApi';
import TASK_OBJECT from '@salesforce/schema/Task';
import SUBJECT_FIELD from '@salesforce/schema/Task.Subject';

export default class CreateFollowUpTask extends LightningElement {
    @api taskSubject = 'Follow up';

    handleCreateTask() {
        const fields = {};
        fields[SUBJECT_FIELD.fieldApiName] = this.taskSubject;
        createRecord({ apiName: TASK_OBJECT.objectApiName, fields })
            .then(() => { /* success handling */ })
            .catch(error => { console.error(error); });
    }
}
```

Step 3 — Deploy the component to the org. In Analytics Studio, open the dashboard in edit mode. The "Create Follow-up Task" component appears in the widget picker under "Custom Components." Drag it onto the canvas and configure the `taskSubject` property from the widget property panel.

**Why it works:** The `analytics__Dashboard` target registration tells the Analytics runtime that this LWC is a valid dashboard widget. Without it, the component is invisible to the dashboard canvas widget picker regardless of how the LWC is deployed. The `targetConfig` block exposes the `taskSubject` property as a configurable widget property, allowing dashboard designers to customize it without touching code.

---

## Anti-Pattern: Using wave-community-dashboard on a Lightning Record Page

**What practitioners do:** When instructed to "embed a dashboard," practitioners search for available components and find `wave-community-dashboard` in documentation or package contents. They use it on a Lightning record page because the attribute surface looks similar to `wave-wave-dashboard-lwc`.

**What goes wrong:** `wave-community-dashboard` is designed for the Experience Cloud (community/portal) runtime. On a Lightning App Builder page it either does not appear in the component palette or renders broken. The component fails silently — the user sees a blank space where the dashboard should be, with no error message in the page or console.

**Correct approach:** Use `wave-wave-dashboard-lwc` for Lightning App Builder pages (record pages, app pages, home pages). Reserve `wave-community-dashboard` exclusively for Experience Builder pages in Experience Cloud. The surface type determines the component — not the dashboard content or analytics app type.
