# Examples — LWC Error Boundaries

## Example 1: Isolating tiles on a six-widget sales dashboard

**Context:** A dashboard page composed of six independent tiles, each with its own Apex
call and its own chart rendering.

**Problem:** A null reference while building the chart in one tile blanked the entire page.
The framework unmounts the component that threw, and with nothing between that tile and the
page root the unmount took the page with it. Users reported "the dashboard is down" when
five of six tiles were perfectly healthy.

**Solution:** A wrapper component that owns nothing except the boundary, applied once per
tile. It has no wires and no imperative calls of its own, so there is nothing in the
boundary itself that can throw.

```javascript
// errorBoundary.js
import { LightningElement, api } from 'lwc';
import logClientError from '@salesforce/apex/ClientErrorLogger.logClientError';

export default class ErrorBoundary extends LightningElement {
    @api boundaryName = 'unknown';   // which widget this wraps, for the log record
    hasError = false;

    errorCallback(error, stack) {
        this.hasError = true;
        // error is a native Error object; stack is a string. Both serialise.
        logClientError({
            componentName: this.boundaryName,
            message: error?.message ?? String(error),
            stackTrace: stack
        }).catch(() => {
            // A logger failure must not throw inside the failure handler.
            // eslint-disable-next-line no-console
            console.error('Boundary log failed', this.boundaryName, error, stack);
        });
    }
}
```

```html
<!-- errorBoundary.html — fallback has no dependencies that can also fail -->
<template>
    <template lwc:if={hasError}>
        <div class="slds-box slds-box_x-small slds-theme_shade slds-text-align_center">
            <p class="slds-text-body_small">This section is unavailable.</p>
        </div>
    </template>
    <template lwc:else>
        <slot></slot>
    </template>
</template>
```

```html
<!-- salesDashboard.html — one boundary per tile, never one for the page -->
<template>
    <div class="slds-grid slds-wrap slds-gutters">
        <div class="slds-col slds-size_1-of-3">
            <c-error-boundary boundary-name="revenue-tile">
                <c-revenue-tile record-id={recordId}></c-revenue-tile>
            </c-error-boundary>
        </div>
        <div class="slds-col slds-size_1-of-3">
            <c-error-boundary boundary-name="pipeline-tile">
                <c-pipeline-tile record-id={recordId}></c-pipeline-tile>
            </c-error-boundary>
        </div>
        <div class="slds-col slds-size_1-of-3">
            <c-error-boundary boundary-name="forecast-tile">
                <c-forecast-tile record-id={recordId}></c-forecast-tile>
            </c-error-boundary>
        </div>
    </div>
</template>
```

**Why it works:** the boundary is a real ancestor of each tile, so `errorCallback` is in
scope for that tile's lifecycle errors. When one tile throws, the framework unmounts that
tile — the boundary and the other five tiles are untouched, and the user loses one card
instead of the page.

**Why `boundary-name` is worth the extra attribute:** without it every logged error says
"an LWC failed", and the boundary's own stack is uninformative about which widget was
inside the slot at the time.

---

## Example 2: The failures the boundary does not catch, handled where they happen

**Context:** The same tiles, after the boundary shipped. Errors kept reaching users with
the boundary sitting silent.

**Problem:** Two categories were slipping through. A rejected promise from an imperative
Apex call is not a render error, so it never reaches `errorCallback` — the tile just
rendered empty. And a wire adapter that fails provisions the failure onto the wired
property's own `error` member rather than throwing, so that also rendered empty.

**Solution:** Handle each in the component that owns it, and reserve the boundary for what
it actually covers.

```javascript
// revenueTile.js — async rejection and wire error both handled locally
import { LightningElement, api, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';
import getRevenueSeries from '@salesforce/apex/DashboardController.getRevenueSeries';
import AMOUNT_FIELD from '@salesforce/schema/Opportunity.Amount';

export default class RevenueTile extends LightningElement {
    @api recordId;
    series;
    loadError;
    recordError;

    // Wire failures land here, not in the boundary.
    @wire(getRecord, { recordId: '$recordId', fields: [AMOUNT_FIELD] })
    wiredOpportunity({ data, error }) {
        if (error) {
            // FetchResponse: status (404), statusText (NOT_FOUND), body from the API
            this.recordError = error.body?.message ?? error.statusText;
        } else if (data) {
            this.recordError = undefined;
        }
    }

    // Promise rejections never reach errorCallback either.
    async connectedCallback() {
        try {
            this.series = await getRevenueSeries({ recordId: this.recordId });
        } catch (error) {
            this.loadError = error.body?.message ?? error.message;
        }
    }

    // Programmatically attached handlers are NOT covered by an ancestor boundary,
    // so this one carries its own try/catch. Prefer a template handler where possible.
    handleExport() {
        try {
            this.buildCsv(this.series);
        } catch (error) {
            this.loadError = 'Export failed.';
        }
    }
}
```

**Why it works:** each failure is handled at the layer that can say something useful about
it. The wire error knows the HTTP status; the imperative call knows which Apex method
failed; the boundary knows only that something in the subtree died. Leaving all three to
the boundary produces one generic grey box for three unrelated problems, and no telemetry
worth reading.

**The division of labour, stated once:**

| Failure | Where it surfaces |
| --- | --- |
| Throw in a descendant's lifecycle hook | Ancestor `errorCallback` |
| Throw in a descendant's template-declared handler | Ancestor `errorCallback` |
| Throw in a programmatically attached handler | Nowhere — needs local `try/catch` |
| Rejected promise from imperative Apex | Nowhere — needs `.catch` / `try/await` |
| Wire adapter failure | The wired property's `error` member |
