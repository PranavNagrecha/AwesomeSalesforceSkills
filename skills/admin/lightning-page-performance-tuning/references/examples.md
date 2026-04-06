# Examples — Lightning Page Performance Tuning

## Example 1: Record Page With 18 Components Causing 6-Second EPT

**Context:** A financial services org built an Account record page with 18 components: Highlights Panel, Record Detail, Path, 4 Related Lists (Contacts, Opportunities, Cases, Activities), 2 Report Charts (pipeline by stage, case trend), a custom LWC showing compliance status, a Chatter feed, a Flow component for account review, Rich Text with team guidelines, a Knowledge sidebar, a custom LWC for external credit score lookup, and 3 quick action buttons. Lightning Experience Insights showed P75 subsequent-load EPT of 6.2 seconds — well above the org average of 2.1 seconds.

**Problem:** All 18 components render on initial page load. The 4 Related Lists query child records, the 2 Report Charts execute their underlying reports, and the credit score LWC makes an external callout — all on every page view. The cumulative DOM and XHR cost pushes EPT above 6 seconds.

**Solution:**

```
Tab layout applied in Lightning App Builder:

Main viewport (renders on initial load):
  - Highlights Panel
  - Path
  - Record Detail (Dynamic Form)
  - Related List - Single: Contacts (5 rows, 3 columns)
  - Quick Action buttons

Tab 1 — "Related" (default tab):
  - Related List: Opportunities
  - Related List: Cases

Tab 2 — "Activity":
  - Activities Related List
  - Chatter Feed

Tab 3 — "Analytics":
  - Report Chart: Pipeline by Stage
  - Report Chart: Case Trend

Tab 4 — "Compliance":
  - Custom LWC: Compliance Status
  - Custom LWC: External Credit Score Lookup
  - Flow: Account Review

Removed entirely:
  - Rich Text (team guidelines) → moved to a Knowledge article linked from the page
  - Knowledge Sidebar → rarely used; linked from utility bar instead
```

**Why it works:** Initial load now renders 6 components instead of 18. The 2 Report Charts (each executing a report query) and the external credit score callout are deferred to tabs that users click only when needed. Post-change P75 EPT dropped from 6.2 seconds to 2.4 seconds. The 12 deferred components saved approximately 14 XHR calls on initial load.

---

## Example 2: Home Page Slow Due to Embedded Dashboard Components

**Context:** An admin built a custom home page with 6 Report Chart components showing key sales metrics, a dashboard snapshot, a Chatter feed, a list view for "My Open Opportunities", and a custom LWC showing daily tasks. Every user in the org sees this home page on login. Users reported that logging in "takes forever" — first-load EPT was 8.4 seconds.

**Problem:** The 6 Report Chart components each execute their underlying report on every home page load. Three of the reports target Opportunity (2M records) with broad date filters. The dashboard snapshot also triggers a refresh. Home pages are loaded by every user on every login, so the aggregate server load from these report queries is substantial.

**Solution:**

```
Revised home page layout:

Main viewport:
  - Assistant component (lightweight, no XHR)
  - Custom LWC: Daily Tasks (single SOQL query, cached via wire)
  - List View: My Open Opportunities (already optimized with owner filter)

Tab 1 — "My Metrics" (default):
  - Report Chart: My Pipeline This Quarter (filtered to Owner = Current User)
  - Report Chart: My Closed Won This Month

Tab 2 — "Team Metrics":
  - Report Chart: Team Pipeline by Stage
  - Report Chart: Team Closed Won Trend
  - Dashboard Snapshot

Removed entirely:
  - 2 Report Charts showing org-wide metrics (moved to a dedicated dashboard page)
  - Chatter Feed (available via utility bar)
```

**Why it works:** Initial home page load now renders 3 lightweight components instead of 10 data-heavy ones. The 4 remaining Report Charts are split across tabs and filtered to current user where possible, reducing query scope. First-load EPT dropped from 8.4 seconds to 3.1 seconds. The removed org-wide Report Charts were consolidated onto a dedicated dashboard page that only managers access.

---

## Example 3: Conditional Rendering to Defer a Heavy Custom Component

**Context:** A custom LWC component (`renewalWidget`) on the Opportunity record page makes an imperative Apex call to calculate renewal pricing by querying 3 related objects. The component renders on every Opportunity page load, but renewal pricing is only relevant when Stage = "Closed Won" and Type = "Renewal". For 80% of page loads, the component renders, makes the Apex call, and then displays "Not applicable."

**Problem:** The imperative Apex call takes 400ms on average and runs on every page load regardless of whether the result is useful. On a page with 12 other components, this single component adds 400ms to EPT for 80% of page views.

**Solution:**

```html
<!-- renewalWidget.html — before -->
<template>
    <lightning-card title="Renewal Pricing">
        <template if:true={isApplicable}>
            <!-- pricing display -->
        </template>
        <template if:false={isApplicable}>
            <p>Not applicable for this opportunity.</p>
        </template>
    </lightning-card>
</template>

<!-- renewalWidget.html — after -->
<template>
    <template lwc:if={isRenewalOpportunity}>
        <lightning-card title="Renewal Pricing">
            <!-- pricing display; Apex call only fires when rendered -->
        </lightning-card>
    </template>
</template>
```

```javascript
// renewalWidget.js — key change
import { LightningElement, api, wire } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import STAGE_FIELD from '@salesforce/schema/Opportunity.StageName';
import TYPE_FIELD from '@salesforce/schema/Opportunity.Type';

export default class RenewalWidget extends LightningElement {
    @api recordId;

    @wire(getRecord, { recordId: '$recordId', fields: [STAGE_FIELD, TYPE_FIELD] })
    opportunity;

    get isRenewalOpportunity() {
        return (
            getFieldValue(this.opportunity.data, STAGE_FIELD) === 'Closed Won' &&
            getFieldValue(this.opportunity.data, TYPE_FIELD) === 'Renewal'
        );
    }
    // imperative Apex call is inside the conditionally rendered child component
    // and only fires when isRenewalOpportunity is true
}
```

**Why it works:** The `lwc:if` directive prevents the component subtree from rendering at all when the condition is false. The imperative Apex call (inside the conditionally rendered section) never fires for non-renewal opportunities. This eliminates the 400ms Apex call from 80% of page loads without any change to the user experience for renewal opportunities.
