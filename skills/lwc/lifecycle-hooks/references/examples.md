# Examples: LWC Lifecycle Hooks

---

## Example 1: Full Lifecycle — Event Listener + renderedCallback Guard + Wire

```javascript
// accountCard.js
import { LightningElement, api, wire } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import getAccountDetails from '@salesforce/apex/AccountService.getAccountDetails';

export default class AccountCard extends NavigationMixin(LightningElement) {

    @api recordId;

    // Private state — not @api because parent doesn't set these
    _account;
    _error;
    _isLoading = true;
    _chartInitialized = false;          // renderedCallback guard
    _keydownHandler;                    // store bound ref for cleanup

    // Wire — both data and error branches handled
    @wire(getAccountDetails, { recordId: '$recordId' })
    wiredAccount({ data, error }) {
        this._isLoading = false;
        if (data) {
            this._account = data;
            this._error = undefined;
        } else if (error) {
            this._error = error.body?.message ?? 'An unknown error occurred.';
            this._account = undefined;
        }
    }

    // Store bound handler reference for cleanup
    connectedCallback() {
        this._keydownHandler = this.handleKeyDown.bind(this);
        window.addEventListener('keydown', this._keydownHandler);
    }

    // Remove EXACTLY the same handler reference
    disconnectedCallback() {
        window.removeEventListener('keydown', this._keydownHandler);
    }

    // One-time chart init — guarded
    renderedCallback() {
        if (this._chartInitialized || !this._account) return;
        this._chartInitialized = true;
        // Safe to do one-time DOM work here
        const container = this.template.querySelector('.chart-container');
        if (container) {
            // initializeChart(container, this._account.revenue);
        }
    }

    handleKeyDown(event) {
        if (event.key === 'Escape') this.handleClose();
    }

    handleNavigateToAccount() {
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: {
                recordId: this.recordId,
                objectApiName: 'Account',
                actionName: 'view'
            }
        });
    }

    handleSave() {
        // ... save logic ...
        this.dispatchEvent(new ShowToastEvent({
            title: 'Success',
            message: 'Account updated successfully.',
            variant: 'success'
        }));
    }

    handleClose() {
        this.dispatchEvent(new CustomEvent('close'));
    }

    get hasError() { return !!this._error; }
    get isLoaded() { return !this._isLoading && !!this._account; }
}
```

```html
<!-- accountCard.html -->
<template>
    <!-- Loading state -->
    <template lwc:if={_isLoading}>
        <lightning-spinner alternative-text="Loading account details..."></lightning-spinner>
    </template>

    <!-- Error state -->
    <template lwc:if={hasError}>
        <p class="slds-text-color_error">{_error}</p>
    </template>

    <!-- Data state -->
    <template lwc:if={isLoaded}>
        <div class="chart-container"></div>
        <p>{_account.Name}</p>
        <lightning-button label="View Account" onclick={handleNavigateToAccount}></lightning-button>
        <lightning-button label="Save" onclick={handleSave}></lightning-button>
    </template>
</template>
```

---

## Example 2: @api Property — Clone Before Modify

```javascript
// recordEditor.js
import { LightningElement, api } from 'lwc';

export default class RecordEditor extends LightningElement {

    @api record;    // Read-only from parent — never mutate directly
    _editableRecord;

    connectedCallback() {
        // Clone on connect so edits don't affect parent's data
        this._editableRecord = { ...this.record };
    }

    handleFieldChange(event) {
        const field = event.target.dataset.field;
        // Mutate the clone, not the @api property
        this._editableRecord = {
            ...this._editableRecord,
            [field]: event.target.value
        };
    }

    handleSave() {
        // Dispatch the changed record up to the parent
        this.dispatchEvent(new CustomEvent('save', {
            detail: { record: this._editableRecord }
        }));
    }
}
```

---

## Example 3: Loading External Script from Static Resource

```javascript
// chartWrapper.js
import { LightningElement, api } from 'lwc';
import { loadScript, loadStyle } from 'lightning/platformResourceLoader';
import CHART_JS from '@salesforce/resourceUrl/ChartJS';   // Uploaded to Static Resources

export default class ChartWrapper extends LightningElement {

    @api chartData;
    _loadStarted = false;      // first-render guard
    _renderError;

    // The library loads on the FIRST RENDER, not in connectedCallback: the guide
    // invokes loadStyle and loadScript "in renderedCallback() on the first render.
    // Using renderedCallback() ensures that the page loads and renders the
    // container before the graph is created."
    // (lwc_guide js-third-party-library L2680)
    renderedCallback() {
        if (this._loadStarted) {
            return;
        }
        this._loadStarted = true;

        // Promise.all aggregates both loads; then() runs only after both resolve
        // and only if neither errored. (lwc_guide js-third-party-library L2681)
        Promise.all([
            loadScript(this, CHART_JS + '/chart.min.js'),
            loadStyle(this, CHART_JS + '/chart.min.css')
        ])
            .then(() => this.initializeChart())
            .catch((error) => {
                this._renderError = 'Chart library failed to load. Please refresh the page.';
                // In production: log to structured logger
                console.error('ChartJS load failed:', error);
            });
    }

    initializeChart() {
        const canvas = this.template.querySelector('canvas');
        if (!canvas) return;
        // new Chart(canvas, { ... this.chartData ... });
    }
}
```

```html
<template>
    <template lwc:if={_renderError}>
        <p class="slds-text-color_error">{_renderError}</p>
    </template>
    <template lwc:else>
        <!-- lwc:dom="manual" marks an element whose DOM a library inserts, so the
             engine preserves encapsulation (lwc_guide js-third-party-library L2669) -->
        <canvas lwc:dom="manual"></canvas>
    </template>
</template>
```

**Key points:**
- Script loaded from Static Resource — not from a CDN URL. This is "a Lightning Web Components content security policy requirement", not a style preference (`lwc_guide js-third-party-library` L2655).
- Load failure is caught and shown to the user.
- The load starts in `renderedCallback()` behind a first-render guard, **not** in `connectedCallback()`. An earlier revision of this file claimed the opposite; the guide loads in `renderedCallback()` precisely so the container element exists (`js-third-party-library` L2680), and `connectedCallback` cannot reach rendered children at all — "You can't access child elements from the callbacks because they don't exist yet" (`create-lifecycle-hooks-dom` L4112).
- The full loading contract — zip layout, `loadStyle` ordering, LWS considerations — belongs to `lwc/static-resources-in-lwc`.


---

## Example 4: Print the Hook Order Yourself

Drop this pair on a Lightning page for five minutes when you need to *see* the order
rather than trust a table. `lifecycleTraceParent` renders `lifecycleTraceChild`.

```javascript
// lifecycleTraceParent.js — same body in lifecycleTraceChild.js with LABEL = 'child'
import { LightningElement } from 'lwc';

const LABEL = 'parent';
const stamp = (hook) => console.log(`${performance.now().toFixed(1)}  ${LABEL}.${hook}`);

export default class LifecycleTraceParent extends LightningElement {
    constructor() {
        super();            // must be first, no parameters
        stamp('constructor');
    }

    connectedCallback() {
        stamp('connectedCallback');
    }

    renderedCallback() {
        stamp('renderedCallback');   // no field writes here — nothing to guard
    }

    disconnectedCallback() {
        stamp('disconnectedCallback');
    }
}
```

Expected console output on first render, then on removal:

```text
  12.4  parent.constructor
  12.6  child.constructor
  12.7  parent.connectedCallback
  12.8  child.connectedCallback
  13.9  child.renderedCallback
  14.0  parent.renderedCallback
--- element removed from the page ---
  91.2  parent.disconnectedCallback
  91.3  child.disconnectedCallback
```

Read it against the guide: `constructor` and `connectedCallback` flow parent → child
(`lwc_guide create-lifecycle-hooks-created` L4085, `create-lifecycle-hooks-dom` L4101),
`renderedCallback` reverses to child → parent (`create-lifecycle-hooks-rendered` L4127),
and `disconnectedCallback` goes back to parent → child (`create-lifecycle-hooks-dom` L4101).

UNVERIFIED (2026-09-05): the timestamps above are illustrative. The guide states the
direction of each hook but publishes no reference console transcript, so treat the
elapsed values as filler and only the ordering as documented.

Toggle the parent behind an `lwc:if` and watch the whole block repeat — that is
`connectedCallback` firing more than once (`create-lifecycle-hooks-dom` L4111), the
behaviour every subscription guard exists to survive.
