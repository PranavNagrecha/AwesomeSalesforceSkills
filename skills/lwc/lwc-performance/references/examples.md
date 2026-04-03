# Examples — LWC Performance

## Example 1: Defer An Analytics Panel Until The User Opens It

**Context:** A sales workspace component on the Opportunity record page shows a summary immediately, but the chart-heavy analytics section is only useful to a subset of users on each visit.

**Problem:** Rendering the analytics child component on first paint loads extra JavaScript, creates expensive chart DOM, and performs record work before the user has asked for the analytics view.

**Solution:**

```javascript
// opportunityWorkspace.js
import { LightningElement, api } from 'lwc';

export default class OpportunityWorkspace extends LightningElement {
    @api recordId;
    showAnalytics = false;

    handleAnalyticsTabActive() {
        this.showAnalytics = true;
    }
}
```

```html
<!-- opportunityWorkspace.html -->
<template>
    <lightning-tabset variant="scoped">
        <lightning-tab label="Summary">
            <c-opportunity-summary record-id={recordId}></c-opportunity-summary>
        </lightning-tab>

        <lightning-tab label="Analytics" onactive={handleAnalyticsTabActive}>
            <template lwc:if={showAnalytics}>
                <c-opportunity-analytics record-id={recordId}></c-opportunity-analytics>
            </template>
        </lightning-tab>
    </lightning-tabset>
</template>
```

**Why it works:** The expensive analytics component is not instantiated until the tab becomes active. The summary renders quickly, and the user only pays the analytics cost when that view is actually needed.

## Example 2: Paginate A Large Repeated List And Delegate Events

**Context:** A custom contact search returns hundreds of rows. Users want a quick scan of the first results and an easy way to open a selected record.

**Problem:** Rendering every row at once, and attaching a click handler to every button, makes the component sluggish and increases DOM and listener count.

**Solution:**

```javascript
// contactSearchResults.js
import { LightningElement, api } from 'lwc';

const PAGE_SIZE = 25;

export default class ContactSearchResults extends LightningElement {
    @api contacts = [];
    pageNumber = 1;

    get visibleContacts() {
        return this.contacts.slice(0, this.pageNumber * PAGE_SIZE);
    }

    get disableLoadMore() {
        return this.visibleContacts.length >= this.contacts.length;
    }

    handleResultsClick(event) {
        const button = event.target.closest('button[data-record-id]');
        if (!button) {
            return;
        }

        this.dispatchEvent(
            new CustomEvent('openrecord', {
                detail: { recordId: button.dataset.recordId }
            })
        );
    }

    handleLoadMore() {
        this.pageNumber += 1;
    }
}
```

```html
<!-- contactSearchResults.html -->
<template>
    <ul class="slds-has-dividers_bottom-space" onclick={handleResultsClick}>
        <template for:each={visibleContacts} for:item="contact">
            <li key={contact.Id} class="slds-item slds-p-around_small">
                <span class="slds-m-right_small">{contact.Name}</span>
                <button
                    class="slds-button slds-button_neutral"
                    data-record-id={contact.Id}>
                    Open
                </button>
            </li>
        </template>
    </ul>

    <lightning-button
        label="Load More"
        onclick={handleLoadMore}
        disabled={disableLoadMore}>
    </lightning-button>
</template>
```

**Why it works:** The DOM stays bounded to a manageable slice of results, each row has a stable key from Salesforce data, and one delegated click listener replaces dozens or hundreds of row-level listeners.

## Example 3: Use Dynamic Components Only For Runtime-Selected Heavy Renderers

**Context:** A managed-package analytics component needs to render one of three heavy chart visualizations chosen from metadata. Loading all renderers up front slows first paint for users who only ever see one chart type.

**Problem:** Static imports of every renderer increase the base bundle size, but a fully dynamic approach also needs to respect current Salesforce constraints for dynamic components.

**Solution:**

```javascript
// chartHost.js
import { LightningElement, api } from 'lwc';

const RENDERERS = {
    bar: () => import('c/barChart'),
    pie: () => import('c/pieChart'),
    line: () => import('c/lineChart')
};

export default class ChartHost extends LightningElement {
    @api chartType = 'bar';
    chartCtor;
    loadError;

    async connectedCallback() {
        await this.loadRenderer(this.chartType);
    }

    async loadRenderer(type) {
        try {
            const module = await RENDERERS[type]();
            this.chartCtor = module.default;
            this.loadError = undefined;
        } catch (error) {
            this.chartCtor = undefined;
            this.loadError = error.body?.message ?? error.message;
        }
    }
}
```

```html
<!-- chartHost.html -->
<template>
    <template lwc:if={loadError}>
        <div class="slds-text-color_error">{loadError}</div>
    </template>
    <lwc:component lwc:is={chartCtor}></lwc:component>
</template>
```

```xml
<!-- chartHost.js-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>64.0</apiVersion>
    <isExposed>false</isExposed>
    <capabilities>
        <capability>lightning__dynamicComponent</capability>
    </capabilities>
</LightningComponentBundle>
```

**Why it works:** Only the selected renderer is loaded at runtime, the import map remains statically analyzable, and the bundle declares the capability Salesforce requires for dynamic components.

---

## Anti-Pattern: Fetching Layout Data For A Tiny Card And Keying Rows By Index

**What practitioners do:** Use `getRecord` with `layoutTypes: ['Full']` for a compact summary card, then render a repeated list with `key={index}` because it is convenient.

**What goes wrong:** The record payload becomes much larger than the UI needs, and the list loses stable identity when rows are inserted, removed, or reordered. That combination increases both network cost and rerender churn.

**Correct approach:** Request explicit fields for the card, paginate or progressively reveal the list, and use a record-derived stable key such as `key={contact.Id}`.
