# Examples — OmniStudio Custom LWC Elements

## Example 1: Custom Date Range Picker with Blocked-Out Dates

**Context:** A field service scheduling OmniScript needs a date picker that blocks out weekends and company holidays. The standard OmniScript Date element renders a plain date input and cannot be constrained to a custom set of available dates. A custom LWC is required to provide this UX.

**Problem:** A standard LWC calendar rendered inside the OmniScript does not communicate its selected date back to the OmniScript data model. The OmniScript step advances without capturing the selection, and downstream Integration Procedure actions receive an empty appointment date field.

**Solution — native OmniStudio:**

```javascript
// appointmentDatePicker.js
import { LightningElement, api } from 'lwc';
import pubsub from 'omnistudio/pubsub';
// For managed package orgs: import pubsub from 'vlocity_cmt/pubsub';

const BLOCKED_DATES = ['2026-12-25', '2026-01-01', '2026-07-04'];

export default class AppointmentDatePicker extends LightningElement {
  @api omniJsonData;     // Current OmniScript data passed in by the runtime
  @api omniOutputMap;    // Pubsub channel reference — required for fireEvent scoping

  _selectedDate = null;
  _isVerified = false;
  _errorMessage = '';

  connectedCallback() {
    // Restore previously selected value when user navigates back to this step
    if (this.omniJsonData && this.omniJsonData.AppointmentDate) {
      this._selectedDate = this.omniJsonData.AppointmentDate;
      this._isVerified = true;
    }
    // Subscribe to validation channel
    pubsub.registerListener('omniscriptvalidate', this.handleValidate, this);
  }

  disconnectedCallback() {
    // Always unregister to prevent duplicate handler registrations
    pubsub.unregisterListener('omniscriptvalidate', this.handleValidate, this);
  }

  handleDateChange(evt) {
    const picked = evt.target.value;
    const dayOfWeek = new Date(picked + 'T12:00:00').getDay(); // Avoid timezone off-by-one
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
    const isBlocked = BLOCKED_DATES.includes(picked);

    if (isWeekend || isBlocked) {
      this._errorMessage = 'Please select a weekday that is not a company holiday.';
      this._isVerified = false;
      this._selectedDate = null;
      return;
    }

    this._errorMessage = '';
    this._selectedDate = picked;
    this._isVerified = true;

    // Push value back to OmniScript data model
    // 'AppointmentDate' must match the output field name in the OmniScript designer exactly
    pubsub.fireEvent(this.omniOutputMap, 'omniupdatebyfield', {
      AppointmentDate: this._selectedDate
    });
  }

  handleValidate() {
    pubsub.fireEvent(this.omniOutputMap, 'omnivalidate', {
      valid: this._isVerified,
      errorMessage: this._isVerified ? '' : 'A valid appointment date is required.'
    });
  }

  get hasError() {
    return this._errorMessage !== '';
  }
}
```

```html
<!-- appointmentDatePicker.html -->
<template>
  <div class="slds-form-element">
    <label class="slds-form-element__label">Appointment Date</label>
    <div class="slds-form-element__control">
      <lightning-input
        type="date"
        label="Select a weekday"
        value={_selectedDate}
        onchange={handleDateChange}
      ></lightning-input>
    </div>
    <template if:true={hasError}>
      <p class="slds-text-color_error">{_errorMessage}</p>
    </template>
  </div>
</template>
```

**OmniScript designer configuration:**
- Element type: Custom LWC Element
- Component Name: `c/appointmentDatePicker` (or `omnistudio/appointmentDatePicker` depending on org namespace)
- Input Mapping: `AppointmentDate` from OmniScript data → `omniJsonData.AppointmentDate`
- Output Mapping: `AppointmentDate` from LWC event → OmniScript root data node

**Why it works:** The `handleValidate` method is registered on the `omniscriptvalidate` pubsub channel, which the OmniScript fires when the user clicks Next. The LWC responds with `omnivalidate` carrying a `valid: false` signal until a legal date is selected. The `connectedCallback` reads `omniJsonData.AppointmentDate` to restore the previously entered date if the user navigates back to this step, making the component stateful across navigation.

---

## Example 2: Custom Merge Map Element for Product Configuration

**Context:** A CPQ-style OmniScript has a step where the user selects a product bundle and configures its options (color, size, add-ons). The selected configuration is a nested object and needs to be stored at `SelectedProduct` in the OmniScript data model for use in a downstream Integration Procedure that prices the bundle.

**Problem:** Using `omniupdatebyfield` with a nested object requires flattening the output into individual field names and mapping each one separately in the OmniScript designer. For a product configuration with dynamic option lists, this is impractical and fragile.

**Solution — Custom Merge Map element:**

```javascript
// productConfigurator.js
import { LightningElement, api, track } from 'lwc';
import pubsub from 'omnistudio/pubsub';
import getProductOptions from '@salesforce/apex/ProductConfigController.getOptions';

export default class ProductConfigurator extends LightningElement {
  @api omniJsonData;
  @api omniOutputMap;

  @track _options = [];
  @track _config = { productId: null, options: [], basePrice: 0 };

  async connectedCallback() {
    // Restore prior config
    if (this.omniJsonData?.SelectedProduct?.productId) {
      this._config = { ...this.omniJsonData.SelectedProduct };
    }
    // Load product options via imperative Apex (NOT @wire — unreliable in OmniScript elements)
    try {
      this._options = await getProductOptions({ productId: this.omniJsonData?.productId });
    } catch (e) {
      console.error('Failed to load product options', e);
    }
  }

  disconnectedCallback() {
    // No pubsub subscriptions to clean up in this example (no validation required)
  }

  handleOptionChange(evt) {
    const optionId = evt.target.dataset.optionId;
    const checked = evt.target.checked;

    if (checked) {
      this._config = { ...this._config, options: [...this._config.options, optionId] };
    } else {
      this._config = {
        ...this._config,
        options: this._config.options.filter(o => o !== optionId)
      };
    }

    // Use 'omnimerge' event to push the full nested object
    // 'SelectedProduct' must match the merge path configured in OmniScript designer
    pubsub.fireEvent(this.omniOutputMap, 'omnimerge', {
      SelectedProduct: this._config
    });
  }
}
```

**OmniScript designer configuration:**
- Element type: Custom Merge Map Element
- Component Name: `c/productConfigurator`
- Merge Path: `SelectedProduct`

**Why it works:** The `omnimerge` event instructs the OmniScript runtime to merge the payload object at the specified path in the data model, preserving the nested structure. Using `omniupdatebyfield` here would attempt to set `SelectedProduct` as a flat field, losing the nested options array.

---

## Anti-Pattern: Using `@wire` Inside a Custom OmniScript Element

**What practitioners do:** Add `@wire(getRecord, { recordId: '$omniJsonData.RecordId' })` inside the custom LWC element to fetch a related record and display its data within the OmniScript step.

**What goes wrong:** The OmniScript step lifecycle does not guarantee that the wire service re-evaluates reactive properties after the user navigates back to the step. On the second visit, the wire adapter may return empty data or stale data from the previous render. The problem is intermittent and hard to reproduce in developer environments where the navigation path is shorter.

**Correct approach:** Call Apex imperatively in `connectedCallback`:

```javascript
// Correct: imperative Apex in connectedCallback
import getRelatedRecord from '@salesforce/apex/MyController.getRelatedRecord';

async connectedCallback() {
  if (this.omniJsonData?.RecordId) {
    try {
      this._record = await getRelatedRecord({ recordId: this.omniJsonData.RecordId });
    } catch (e) {
      console.error('Failed to load record', e);
    }
  }
}
```

The imperative call fires fresh each time `connectedCallback` runs, ensuring consistent behavior regardless of how many times the user navigates to and from the step.
