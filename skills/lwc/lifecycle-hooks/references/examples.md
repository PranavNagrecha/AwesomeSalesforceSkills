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
    <template if:true={_isLoading}>
        <lightning-spinner alternative-text="Loading account details..."></lightning-spinner>
    </template>

    <!-- Error state -->
    <template if:true={hasError}>
        <p class="slds-text-color_error">{_error}</p>
    </template>

    <!-- Data state -->
    <template if:true={isLoaded}>
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
import { LightningElement, api, track } from 'lwc';
import { loadScript } from 'lightning/platformResourceLoader';
import ChartJS from '@salesforce/resourceUrl/ChartJS';   // Uploaded to Static Resources

export default class ChartWrapper extends LightningElement {

    @api chartData;
    _chartJsLoaded = false;
    _renderError;

    connectedCallback() {
        loadScript(this, ChartJS)
            .then(() => {
                this._chartJsLoaded = true;
                this.initializeChart();
            })
            .catch(error => {
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
    <template if:true={_renderError}>
        <p class="slds-text-color_error">{_renderError}</p>
    </template>
    <template if:false={_renderError}>
        <canvas></canvas>
    </template>
</template>
```

**Key points:**
- Script loaded from Static Resource — not from a CDN URL
- Load failure is caught and shown to user
- `initializeChart()` called only after confirmed load, not in `renderedCallback` (prevents timing issues)
