# Examples — LWC Conditional Rendering

## Example 1: Loading / Error / Ready State Machine

**Context:** A record-detail helper component calls Apex on `connectedCallback` and must show a spinner while the request is in flight, an inline error card if the call fails, or the rendered data when it succeeds.

**Problem:** A naive implementation uses three parallel `<template if:true={...}>` blocks, which (a) relies on JS to maintain mutual exclusivity, (b) cannot short-circuit, and (c) uses the legacy directive that Salesforce has explicitly flagged for future removal.

**Solution:**

HTML (`accountSummary.html`):

```html
<template>
  <template lwc:if={isLoading}>
    <lightning-spinner alternative-text="Loading" size="small"></lightning-spinner>
  </template>
  <template lwc:elseif={isError}>
    <div class="slds-notify slds-notify_alert slds-theme_error" role="alert">
      <p>{errorMessage}</p>
      <button onclick={handleRetry}>Retry</button>
    </div>
  </template>
  <template lwc:else>
    <article class="slds-card">
      <header class="slds-card__header">
        <h2>{account.Name}</h2>
      </header>
      <div class="slds-card__body">
        <p>{account.Industry}</p>
        <p>{account.AnnualRevenueFormatted}</p>
      </div>
    </article>
  </template>
</template>
```

JavaScript (`accountSummary.js`):

```javascript
import { LightningElement, api } from 'lwc';
import getAccount from '@salesforce/apex/AccountController.getAccount';

export default class AccountSummary extends LightningElement {
    @api recordId;
    status = 'loading'; // 'loading' | 'error' | 'ready'
    account;
    errorMessage;

    connectedCallback() {
        this.loadAccount();
    }

    async loadAccount() {
        this.status = 'loading';
        try {
            this.account = await getAccount({ accountId: this.recordId });
            this.status = 'ready';
        } catch (err) {
            this.errorMessage = err?.body?.message ?? 'Unable to load account.';
            this.status = 'error';
        }
    }

    handleRetry = () => this.loadAccount();

    // Getters keep template expressions trivial.
    get isLoading() { return this.status === 'loading'; }
    get isError()   { return this.status === 'error'; }
    // Note: no isReady getter — `lwc:else` already means "ready".
}
```

**Why it works:** The chained directives make exclusivity a template-level invariant — there is no way for two branches to render simultaneously, even if `status` gets an unexpected value. Each branch also re-mounts on re-entry, so retrying cleanly creates a fresh spinner and fresh error surface. Getters hold all the computed logic, keeping the template declarative.

---

## Example 2: Advanced-Filter Panel — Reset-State vs Keep-State Toggle

**Context:** A list view has a "Show advanced filters" button. Product has two very different requirements depending on the UX:

- **Variant A (reset on close):** The panel is a confirmation-style tool — every open starts clean.
- **Variant B (preserve input):** The panel contains a multi-step filter the user refines over minutes; closing and reopening must preserve their partial input.

**Problem:** Teams default to `lwc:if` for both, which silently loses state in Variant B. Or they default to CSS hide for both, which leaks stale state in Variant A. The choice should be deliberate.

**Solution — Variant A (`lwc:if`, re-mount):**

```html
<template>
  <button onclick={toggleFilters}>
    {filterButtonLabel}
  </button>
  <template lwc:if={isFilterOpen}>
    <!-- Fresh instance every time the panel opens. -->
    <c-advanced-filter-panel onapply={handleApply}></c-advanced-filter-panel>
  </template>
</template>
```

**Solution — Variant B (mount once, hide with CSS):**

```html
<template>
  <button onclick={toggleFilters}>
    {filterButtonLabel}
  </button>
  <!-- Always mounted; visibility toggled via a computed class. -->
  <div class={filterPanelClass}>
    <c-advanced-filter-panel onapply={handleApply}></c-advanced-filter-panel>
  </div>
</template>
```

```javascript
import { LightningElement } from 'lwc';

export default class FilteredList extends LightningElement {
    isFilterOpen = false;

    toggleFilters = () => { this.isFilterOpen = !this.isFilterOpen; };

    get filterButtonLabel() {
        return this.isFilterOpen ? 'Hide advanced filters' : 'Show advanced filters';
    }

    // Variant B only — computed class swaps visibility without unmounting.
    get filterPanelClass() {
        return this.isFilterOpen ? 'filter-panel' : 'filter-panel slds-hide';
    }
}
```

**Why it works:** The `lwc:if` variant guarantees a clean slate (fresh inputs, fresh validation, fresh focus), which is exactly what a reset-on-close panel needs. The CSS-hide variant keeps the `c-advanced-filter-panel` instance alive, so partially filled inputs, scroll position, and internal component state survive the toggle. Picking the wrong one is a subtle bug — if a user complains that "my filters reset every time," the fix is to switch from `lwc:if` to the CSS approach; if a user complains that "stale filters come back after I close it," the fix is the reverse.

---

## Anti-Pattern: Chained `if:true` / `if:false` As A Fake Else

**What practitioners do:** They need three mutually exclusive branches and write it like this because the template pre-dates `lwc:if`:

```html
<template>
  <template if:true={isLoading}>
    <lightning-spinner></lightning-spinner>
  </template>
  <template if:true={showError}>
    <p class="error">{errorMessage}</p>
  </template>
  <template if:false={isLoading}>
    <template if:false={showError}>
      <c-ready-view record={record}></c-ready-view>
    </template>
  </template>
</template>
```

**What goes wrong:** There is no short-circuit. Every `if:true` and `if:false` is evaluated independently, so a JS bug that leaves both `isLoading` and `showError` true renders two branches simultaneously. The nested `if:false` inside `if:false` is the classic "fake else" — brittle, hard to read, and described by Salesforce's own docs as the slower, legacy path. The directive pair may be removed in the future.

**Correct approach:** Convert to the modern trio and move the logic into getters so the template stays declarative:

```html
<template>
  <template lwc:if={isLoading}>
    <lightning-spinner></lightning-spinner>
  </template>
  <template lwc:elseif={isError}>
    <p class="error">{errorMessage}</p>
  </template>
  <template lwc:else>
    <c-ready-view record={record}></c-ready-view>
  </template>
</template>
```

Run the skill checker after migration to confirm no legacy `if:true` / `if:false` remains.
