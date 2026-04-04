# Examples — LWC in Flow Screens

## Example 1: Output Variable Stays Blank After the Screen

**Scenario:** A custom address-entry LWC collects a full address from the user. The Flow is expected to store the formatted address string in a Flow Text variable called `formattedAddress`. After the screen, the variable is always blank even though the component renders correctly.

**Problem:** The developer assigned the value inside the component by writing `this.formattedAddress = fullAddress;`. Because `formattedAddress` is an `@api` property, the assignment has no effect on the Flow runtime's internal variable storage. The Flow variable remains at its initial value.

**Solution:**

Replace the direct assignment with a `FlowAttributeChangeEvent` dispatch:

```js
import { LightningElement, api } from 'lwc';
import { FlowAttributeChangeEvent } from 'lightning/flowSupport';

export default class AddressEntry extends LightningElement {
  @api street;
  @api city;
  @api formattedAddress; // output-only

  _buildAddress() {
    return [this.street, this.city].filter(Boolean).join(', ');
  }

  handleStreetChange(event) {
    this.street = event.detail.value; // local mutation is fine for internal state
    this._emitAddress();
  }

  handleCityChange(event) {
    this.city = event.detail.value;
    this._emitAddress();
  }

  _emitAddress() {
    this.dispatchEvent(
      new FlowAttributeChangeEvent('formattedAddress', this._buildAddress())
    );
  }
}
```

In `.js-meta.xml` declare `formattedAddress` with `role="outputOnly"` so Flow Builder treats it as a writable output:

```xml
<property name="formattedAddress" type="String" role="outputOnly" label="Formatted Address" />
```

**Why it works:** `FlowAttributeChangeEvent` is the contract the Flow runtime uses to receive values from a screen component. It tells the runtime "update this named Flow variable with this value." Direct `@api` mutation from inside the component is not observed by the runtime. ([Salesforce Developers: Configure a Component for Flow Screens](https://developer.salesforce.com/docs/platform/lwc/guide/use-config-for-flow-screens.html))

---

## Example 2: Derived Output Lost After Back Navigation

**Scenario:** A quantity selector component receives a unit price from Flow and outputs a computed total price (`unitPrice × quantity`). On first load the total is correct. If the user clicks Back and then Next again, the `totalPrice` Flow variable reverts to blank.

**Problem:** The `totalPrice` output is only emitted inside the `handleQuantityChange` handler. When the user navigates back and then forward, the component remounts, `connectedCallback` runs, but no `FlowAttributeChangeEvent` is fired on mount — so the output starts blank again for that page-load cycle.

**Solution:**

Fire `FlowAttributeChangeEvent` for the derived output in both `connectedCallback` and the setter for the driving input:

```js
import { LightningElement, api } from 'lwc';
import { FlowAttributeChangeEvent } from 'lightning/flowSupport';

export default class QuantitySelector extends LightningElement {
  _unitPrice = 0;
  _quantity = 1;

  @api
  get unitPrice() {
    return this._unitPrice;
  }
  set unitPrice(val) {
    this._unitPrice = Number(val) || 0;
    this._emitTotal(); // Re-emit derived output when input changes
  }

  @api totalPrice; // output only

  connectedCallback() {
    this._emitTotal(); // Emit on mount so output is populated even on back-nav
  }

  handleQuantityChange(event) {
    this._quantity = Number(event.detail.value) || 1;
    this._emitTotal();
  }

  _emitTotal() {
    const total = this._unitPrice * this._quantity;
    this.dispatchEvent(new FlowAttributeChangeEvent('totalPrice', total));
  }
}
```

**Why it works:** The component remounts on every forward navigation past this screen. Firing in `connectedCallback` guarantees the output is populated before the user can move forward. Firing in the setter covers the case where Flow re-assigns `unitPrice` reactively after mount. ([Salesforce Developers: Best Practices for Reactivity in Screen Flows](https://developer.salesforce.com/docs/platform/lwc/guide/use-best-practices-reactivity.html))

---

## Example 3: Custom Validation Blocking Navigation

**Scenario:** A date-range picker component collects a start date and end date. The business rule is that end date must be after start date. The component needs to block the user from pressing Next if the rule is violated.

**Problem:** Validation logic was placed in a click handler for an internal "Confirm" button. The standard Flow Next button bypasses this handler entirely, so the user can navigate forward with an invalid date range.

**Solution:**

Implement the public `validate()` method so Flow's navigation cycle calls it automatically:

```js
import { LightningElement, api } from 'lwc';
import { FlowAttributeChangeEvent } from 'lightning/flowSupport';

export default class DateRangePicker extends LightningElement {
  @api startDate = '';
  @api endDate = '';

  handleStartChange(event) {
    this.dispatchEvent(new FlowAttributeChangeEvent('startDate', event.detail.value));
  }

  handleEndChange(event) {
    this.dispatchEvent(new FlowAttributeChangeEvent('endDate', event.detail.value));
  }

  @api validate() {
    const start = new Date(this.startDate);
    const end = new Date(this.endDate);
    const isValid = this.startDate && this.endDate && end > start;
    return {
      isValid: Boolean(isValid),
      errorMessage: isValid ? '' : 'End date must be after start date.'
    };
  }
}
```

**Why it works:** The Flow runtime calls `validate()` on every component that exposes it when the user attempts to navigate. If `isValid` is `false`, Flow displays the `errorMessage` and prevents navigation. The method name must be exactly `validate` (case-sensitive). ([Salesforce Developers: Validate Flow User Input](https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-validate-user-input-for-custom-components.html))

---

## Anti-Pattern: Firing a Navigation Event and FlowAttributeChangeEvent in the Same Synchronous Call

**What practitioners do:** A "Save and Continue" button handler fires `FlowAttributeChangeEvent` to write the final output value and immediately dispatches `FlowNavigationNextEvent` to move to the next screen, all in the same function call.

**What goes wrong:** The Flow runtime may process the navigation before it has fully resolved the attribute change. The next screen or subsequent decision logic may see a stale or missing value for the output variable. This is a documented race condition. ([Salesforce Developers: Best Practices for Reactivity in Screen Flows](https://developer.salesforce.com/docs/platform/lwc/guide/use-best-practices-reactivity.html))

**Correct approach:** Fire `FlowAttributeChangeEvent` from the change handler as the user interacts, so the output is always current before any navigation. Let the navigation be triggered separately (either by the user pressing the standard Next button or by firing the navigation event in a subsequent microtask if programmatic navigation is required). Do not batch both events in the same synchronous handler.
