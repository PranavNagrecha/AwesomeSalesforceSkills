# Examples — LWC Dynamic Components

## Example 1: Record-Type-Driven Form Renderer

**Context:** A service console app has three Case record types — Technical, Billing, and General — each with a distinct detail form LWC. The team wants a single host component on the record page that loads the correct form at runtime without bundling all three into the initial payload.

**Problem:** Using `lwc:if` with three statically imported components works functionally, but all three modules are included in the page bundle even when only one renders. For large form components, this inflates first-paint cost for every user regardless of record type.

**Solution:**

`caseFormRouter/caseFormRouter.js`
```js
import { LightningElement, api, track } from 'lwc';

const RECORD_TYPE_MAP = {
    '012Technical000000': 'c/caseTechnicalForm',
    '012Billing0000000': 'c/caseBillingForm',
    '012General0000000': 'c/caseGeneralForm',
};

export default class CaseFormRouter extends LightningElement {
    @api recordTypeId;
    @api recordId;
    @track dynamicCtor = null;
    hasError = false;

    async connectedCallback() {
        const specifier = RECORD_TYPE_MAP[this.recordTypeId] ?? 'c/caseGeneralForm';
        try {
            const { default: Ctor } = await import(specifier);
            this.dynamicCtor = Ctor;
        } catch (err) {
            console.error('[CaseFormRouter] failed to load component', specifier, err);
            this.hasError = true;
        }
    }
}
```

`caseFormRouter/caseFormRouter.html`
```html
<template>
    <template lwc:if={dynamicCtor}>
        <lwc:component
            lwc:is={dynamicCtor}
            record-id={recordId}
            onformsubmit={handleSubmit}>
        </lwc:component>
    </template>
    <template lwc:elseif={hasError}>
        <p class="slds-text-color_error">Failed to load the form. Please refresh the page.</p>
    </template>
    <template lwc:else>
        <lightning-spinner alternative-text="Loading form..." size="small"></lightning-spinner>
    </template>
</template>
```

**Why it works:** The `import()` call for each specifier is a static literal string that the LWC build toolchain can analyze and split into separate chunks. Only the chunk matching the current record type is fetched at runtime. The other two are never downloaded for that session. The `try/catch` ensures the user sees a clear error instead of a blank area if the module fails to load.

---

## Example 2: Feature-Flag-Driven Component Swap

**Context:** A product team is running an A/B test between two dashboard summary components — a legacy `c/summaryCardV1` and an experimental `c/summaryCardV2`. A server-side Apex method returns which variant the current user should see. The swap needs to happen without a full page reload.

**Problem:** Hardcoding both components in the template with `lwc:if` means both modules are loaded at page initialization. The team wants V2 to be invisible to V1 users, including in the network waterfall, to avoid any measurement contamination.

**Solution:**

`featureDashboard/featureDashboard.js`
```js
import { LightningElement, wire, track } from 'lwc';
import getVariantFlag from '@salesforce/apex/FeatureFlagController.getVariantFlag';

export default class FeatureDashboard extends LightningElement {
    @track dashboardCtor = null;
    @track wiredDone = false;

    @wire(getVariantFlag)
    async handleFlag({ data, error }) {
        if (error) {
            console.error('Failed to retrieve feature flag', error);
            // fall back to V1
            const { default: Ctor } = await import('c/summaryCardV1');
            this.dashboardCtor = Ctor;
            return;
        }
        if (data !== undefined) {
            try {
                const specifier = data === 'v2' ? 'c/summaryCardV2' : 'c/summaryCardV1';
                const { default: Ctor } = await import(specifier);
                this.dashboardCtor = Ctor;
            } catch (err) {
                console.error('Dynamic import failed', err);
            }
        }
    }
}
```

`featureDashboard/featureDashboard.html`
```html
<template>
    <template lwc:if={dashboardCtor}>
        <lwc:component lwc:is={dashboardCtor}></lwc:component>
    </template>
    <template lwc:else>
        <lightning-spinner alternative-text="Loading dashboard..."></lightning-spinner>
    </template>
</template>
```

**Why it works:** The wire adapter provides the flag value before the import is called, so the routing decision is made with fresh server data. The `import()` call uses a literal specifier in each branch — the build toolchain sees both strings and creates two chunks, but only one is fetched per user session. Users on V1 never download the V2 chunk.

---

## Anti-Pattern: Passing the Module Object Instead of the Constructor

**What practitioners do:** Call `await import('c/myComponent')` and assign the result directly to `lwc:is` without accessing `.default`.

```js
// Wrong
const mod = await import('c/myComponent');
this.dynamicCtor = mod; // mod is the module namespace object, not the constructor
```

**What goes wrong:** `lwc:is` receives a plain object. The framework does not recognize it as a constructor and renders nothing. There is no runtime error in most cases — the component host element simply remains empty. This is particularly confusing because the import itself succeeds.

**Correct approach:**

```js
// Correct
const { default: Ctor } = await import('c/myComponent');
this.dynamicCtor = Ctor;
```

Always destructure `default` from the resolved module, or access it explicitly via `mod.default`. This is the constructor that `lwc:is` requires.
