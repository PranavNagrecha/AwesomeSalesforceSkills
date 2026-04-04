# Examples — Common LWC Runtime Errors

## Example 1: Wire Adapter Data Access Before Resolution

**Context:** A developer builds an account detail card that displays the account name and industry. The component uses `@wire(getRecord)` and accesses `this.wiredAccount.data.fields.Name.value` directly in the template.

**Problem:** On initial render, the wire service has not yet responded. `this.wiredAccount` is `{}` and `.data` is `undefined`. The template expression `{wiredAccount.data.fields.Name.value}` throws `TypeError: Cannot read properties of undefined (reading 'fields')` in the browser console. With debug mode off, this surfaces as a blank component with no visible error in the UI.

**Solution:**

```js
// accountCard.js
import { LightningElement, wire, api } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import ACCOUNT_NAME from '@salesforce/schema/Account.Name';
import ACCOUNT_INDUSTRY from '@salesforce/schema/Account.Industry';

const FIELDS = [ACCOUNT_NAME, ACCOUNT_INDUSTRY];

export default class AccountCard extends LightningElement {
    @api recordId;
    accountName;
    accountIndustry;
    errorMessage;
    isLoading = true;

    @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
    handleAccount({ data, error }) {
        this.isLoading = false;
        if (data) {
            this.accountName = getFieldValue(data, ACCOUNT_NAME);
            this.accountIndustry = getFieldValue(data, ACCOUNT_INDUSTRY);
        } else if (error) {
            this.errorMessage = error.body?.message ?? 'Failed to load record';
        }
    }
}
```

```html
<!-- accountCard.html -->
<template>
    <template lwc:if={isLoading}>
        <lightning-spinner alternative-text="Loading account"></lightning-spinner>
    </template>
    <template lwc:elseif={errorMessage}>
        <div class="slds-text-color_error">{errorMessage}</div>
    </template>
    <template lwc:else>
        <div class="slds-card__body">
            <p><strong>{accountName}</strong></p>
            <p>{accountIndustry}</p>
        </div>
    </template>
</template>
```

**Why it works:** The wire handler destructures `data` and `error` directly instead of storing the whole wire result object. It maps the resolved values into plain tracked properties (`accountName`, `accountIndustry`) that the template can safely access without chaining through the wire object. The `isLoading` flag covers the interim state before the first wire response arrives.

---

## Example 2: Custom Event Not Crossing Shadow Boundary

**Context:** A multi-step form wizard has a parent component `c-wizard` that renders a child `c-step-form`. The child dispatches a `nextstep` custom event when the user clicks Next. The parent has `onnextstep={handleNextStep}` on the child element but the handler never fires.

**Problem:** The child dispatches the event with `new CustomEvent('nextstep', { bubbles: true })` but omits `composed: true`. The event bubbles within the child's shadow tree and reaches the child's shadow root, then stops. It never reaches the parent's DOM listener because it does not cross the shadow boundary.

**Solution:**

```js
// stepForm.js — child component
handleNextClick() {
    // composed: true allows the event to cross the shadow boundary into the parent.
    // bubbles: true allows it to bubble up through the DOM tree once it exits the shadow.
    this.dispatchEvent(new CustomEvent('nextstep', {
        bubbles: true,
        composed: true,
        detail: {
            stepData: this.collectFormData(),
            stepIndex: this.currentStep
        }
    }));
}
```

```js
// wizard.js — parent component
handleNextStep(event) {
    // IMPORTANT: use event.detail for payload data.
    // event.target is the host element (c-step-form), not the button inside it,
    // because composed events retarget at shadow boundaries.
    const { stepData, stepIndex } = event.detail;
    this.processStep(stepData, stepIndex);
}
```

```html
<!-- wizard.html -->
<template>
    <c-step-form
        current-step={currentStep}
        onnextstep={handleNextStep}>
    </c-step-form>
</template>
```

**Why it works:** `composed: true` instructs the LWC runtime to allow the event to cross shadow boundaries as it propagates. Without it, shadow DOM encapsulation stops the event at the child's shadow root. The payload is in `event.detail` — relying on `event.target` to access child-internal DOM elements would fail due to retargeting.

---

## Example 3: NavigationMixin Silently Failing in Experience Cloud

**Context:** A custom LWC component on an Experience Cloud page tries to navigate to a record detail page when a user clicks a row in a data table. The `NavigationMixin.Navigate` call completes without error but the page does not change.

**Problem:** The developer used `type: 'standard_recordPage'` (single underscore) instead of `type: 'standard__recordPage'` (double underscore). NavigationMixin does not throw an error on an unrecognized type — it silently does nothing.

**Solution:**

```js
// recordList.js
import { LightningElement, wire } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';

export default class RecordList extends NavigationMixin(LightningElement) {
    handleRowAction(event) {
        const { row } = event.detail;
        if (!row?.Id) {
            console.error('RecordList: row.Id is undefined, cannot navigate', row);
            return;
        }

        // CORRECT: 'standard__recordPage' with double underscores
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: {
                recordId: row.Id,
                actionName: 'view'
            }
        });
    }
}
```

**Why it works:** The correct page reference `type` strings use double underscores as separators. The defensive check on `row.Id` prevents a silent failure when the wire hasn't loaded data yet. In Experience Cloud, also confirm that the record detail page type is configured and published in the Experience Builder site — a valid `pageReference` navigates to a page that does not exist in the site map silently.

---

## Example 4: DOM Access Failing in connectedCallback

**Context:** A component wraps a third-party date-picker library. The developer initializes the library instance in `connectedCallback` using `this.template.querySelector('input')`.

**Problem:** `connectedCallback` fires when the component's JavaScript class is instantiated and attached to the DOM host element, but the template has not yet been rendered. `this.template.querySelector('input')` returns `null`. The library initialization fails with a `TypeError` on the `null` reference.

**Solution:**

```js
// datePicker.js
import { LightningElement } from 'lwc';

export default class DatePicker extends LightningElement {
    _picker;

    // connectedCallback: template NOT yet rendered — do NOT query the DOM here.
    connectedCallback() {
        // Only set up non-DOM state here (subscribe to stores, set up data fetches, etc.)
    }

    // renderedCallback: template IS rendered — safe to query the DOM.
    renderedCallback() {
        // Guard: only initialize once. renderedCallback fires on every render cycle.
        if (this._picker) return;

        const input = this.template.querySelector('input.date-input');
        if (!input) return; // defensive; should not happen but prevents crash if template changes

        // Initialize the third-party library against the actual DOM element.
        this._picker = new window.ThirdPartyPicker(input, {
            format: 'YYYY-MM-DD',
            onChange: (date) => {
                this.dispatchEvent(new CustomEvent('datechange', {
                    detail: { date },
                    bubbles: false,
                    composed: false
                }));
            }
        });
    }

    disconnectedCallback() {
        // Always destroy third-party instances to prevent memory leaks.
        if (this._picker) {
            this._picker.destroy();
            this._picker = undefined;
        }
    }
}
```

**Why it works:** `renderedCallback` is the correct lifecycle hook for DOM-dependent initialization because the template is guaranteed to be rendered when it fires. The `this._picker` guard prevents re-initialization on subsequent renders. `disconnectedCallback` prevents memory leaks from stale library instances.

---

## Anti-Pattern: Using `document.querySelector` Instead of `this.template.querySelector`

**What practitioners do:** Call `document.querySelector('.my-element')` inside a component to find an element rendered by that component's template.

**What goes wrong:** Under LWC's shadow DOM encapsulation, `document.querySelector` cannot reach into a component's shadow root. It returns `null` regardless of whether the element exists in the DOM. Under legacy Locker Service, `document.querySelector` is additionally restricted and may throw an `Access check failed` error. This also breaks composability: if two instances of the component exist on the page, a `document.querySelector` targeting a class name might find an element from the wrong instance.

**Correct approach:** Always use `this.template.querySelector('.my-element')` to find elements within the current component's own shadow. If you need to reach a child component's internal elements, that is a design smell — expose the operation as an `@api` method on the child instead.
