# Examples — OmniStudio LWC Integration

## Example 1: Embed an OmniScript Intake Form in a Lightning Record Page Tab

**Context:** A service team has built a "New Service Request" OmniScript (type: `ServiceRequest`, subtype: `New`). The business wants it to appear as a tab on the Account record page so agents can launch it without navigating away. The OmniScript needs to be pre-populated with the account Id and account name.

**Problem:** Placing the OmniScript component directly as an App Builder component does not allow passing dynamic data (the record Id) as seed data. Without seed data, the agent must manually enter context the LWC already has, increasing error risk and handle time.

**Solution (native OmniStudio):**

```html
<!-- serviceRequestLauncher.html -->
<template>
  <omnistudio-omni-script
    omni-script-type="ServiceRequest"
    omni-script-sub-type="New"
    omni-language="English"
    omni-seed-json={seedJson}
    hide-nav-bar="false"
    oncomplete={handleComplete}
  ></omnistudio-omni-script>
</template>
```

```javascript
// serviceRequestLauncher.js
import { LightningElement, api, wire } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import ACCOUNT_NAME_FIELD from '@salesforce/schema/Account.Name';

export default class ServiceRequestLauncher extends LightningElement {
  @api recordId;

  @wire(getRecord, { recordId: '$recordId', fields: [ACCOUNT_NAME_FIELD] })
  account;

  get seedJson() {
    const name = getFieldValue(this.account.data, ACCOUNT_NAME_FIELD);
    // The JSON keys must match the OmniScript field hierarchy exactly
    return JSON.stringify({
      AccountId: this.recordId,
      AccountName: name
    });
  }

  handleComplete(evt) {
    const outputData = evt.detail;
    // Handle post-submission logic: show confirmation, navigate, etc.
    console.log('OmniScript completed', outputData);
  }
}
```

**For managed package orgs**, replace `omnistudio-omni-script` with `c-omni-script` and the attribute names use camelCase:

```html
<!-- managed package variant -->
<template>
  <c-omni-script
    omni-script-type="ServiceRequest"
    omni-script-sub-type="New"
    omni-seed-json={seedJson}
    oncomplete={handleComplete}
  ></c-omni-script>
</template>
```

**Why it works:** The `seedJson` getter is computed reactively from the wired `account` data. Because it is bound as a template expression (`{seedJson}`), it is evaluated before the OmniScript component mounts, satisfying the requirement that seed data be available at connection time. The `oncomplete` handler captures the full data JSON emitted when the user submits the final step.

---

## Example 2: Custom LWC Date Picker Component Used Inside an OmniScript Screen

**Context:** An insurance intake OmniScript needs a date picker that blocks out weekends and public holidays. The standard OmniScript Date element does not support blackout dates. A custom LWC component is required to provide this UX.

**Problem:** A standard LWC date picker rendered inside an OmniScript screen does not communicate its selected value back to the OmniScript data model. The OmniScript treats the custom element as a display-only fragment. Downstream steps that depend on the selected date evaluate it as empty.

**Solution — custom LWC element with OmniStudio pubsub (native):**

```javascript
// customDatePicker.js
import { LightningElement, api } from 'lwc';
import pubsub from 'omnistudio/pubsub';

export default class CustomDatePicker extends LightningElement {
  // Receives current OmniScript data when the step renders
  @api omniJsonData;

  // Receives the output field name configured in the OmniScript designer
  @api omniOutputMap;

  _selectedDate;

  connectedCallback() {
    // Restore previously selected value if user navigated back
    if (this.omniJsonData && this.omniJsonData.SelectedAppointmentDate) {
      this._selectedDate = this.omniJsonData.SelectedAppointmentDate;
    }
  }

  disconnectedCallback() {
    // Clean up any subscriptions if needed
  }

  handleDateChange(evt) {
    this._selectedDate = evt.target.value;
    // Emit the value back to the OmniScript data model
    // The key 'SelectedAppointmentDate' must match the output field name
    // configured in the OmniScript designer custom element step exactly
    pubsub.fireEvent(this.omniOutputMap, 'omniupdatebyfield', {
      SelectedAppointmentDate: this._selectedDate
    });
  }
}
```

```html
<!-- customDatePicker.html -->
<template>
  <lightning-input
    type="date"
    label="Appointment Date"
    value={_selectedDate}
    onchange={handleDateChange}
  ></lightning-input>
</template>
```

**OmniScript designer configuration:**
In the OmniScript designer, add a Custom LWC element step and enter:
- Component Name: `c/customDatePicker` (or `omnistudio/customDatePicker` depending on namespace)
- Input Mapping: map the current `SelectedAppointmentDate` value from the OmniScript data JSON to `omniJsonData.SelectedAppointmentDate`
- Output Mapping: map `SelectedAppointmentDate` from the LWC event back to the OmniScript root data node

**Why it works:** The pubsub `fireEvent` call with `omniupdatebyfield` is the OmniScript runtime's supported mechanism for a custom element to push a value into the shared data model. The output field name must match exactly what is declared in the OmniScript designer's output mapping configuration.

---

## Anti-Pattern: Setting Seed Data After Component Mount

**What practitioners do:** Compute the seed JSON in `connectedCallback` of the parent LWC and set it imperatively using `this.template.querySelector('omnistudio-omni-script').omniSeedJson = ...` after the component has mounted.

**What goes wrong:** The OmniScript runtime initializes its internal data model at connection time. Setting seed data after the component is connected does not trigger re-initialization. The OmniScript fields remain at their default values, and the agent sees a blank form despite the data being present in the parent LWC.

**Correct approach:** Compute the seed JSON as a reactive getter or reactive property in the parent LWC JavaScript, and bind it to the `omni-seed-json` attribute as a template expression. The LWC framework evaluates template expressions before connecting child components to the DOM, ensuring the seed data is available when the OmniScript initializes.

```html
<!-- correct: seed JSON bound as template expression -->
<omnistudio-omni-script
  omni-script-type="ServiceRequest"
  omni-script-sub-type="New"
  omni-seed-json={seedJson}
></omnistudio-omni-script>
```
