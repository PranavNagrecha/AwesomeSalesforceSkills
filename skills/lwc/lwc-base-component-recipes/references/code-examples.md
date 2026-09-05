# Code Examples — LWC Base Component Recipes

One complete, deployable composite: a record-page panel built entirely from base components.
It is deliberately the *everyday* shape — a card with an action menu, a responsive grid, a picklist
driven by object metadata, a loading state, and a read-only field summary — because that is what
most "add a panel to the Account page" requests actually are.

> **The Component Library is the authority for attribute contracts.** The LWC Developer Guide
> documents which base components exist, how they compose, and how they behave in containers; it
> does not publish per-component attribute tables
> (`lwc_guide base-components-considerations` L4727, `base-components-patterns-global` L4804, L4812).
> Attributes below that the guide never prints are marked `UNVERIFIED (2026-09-05)` inline. Check
> each on the component's **Specification** tab before shipping.

Canonical starting points, by relative path — copy these rather than re-inventing them:

- `templates/lwc/component-skeleton/` — bundle skeleton (`.html`, `.js`, `.css`, `.js-meta.xml`, `__tests__/`)
- `templates/lwc/jest.config.js` — the Jest harness base
- `templates/lwc/patterns/wireServicePattern.js` — wire-with-error-handling shape
- `templates/lwc/patterns/slotsCompositionPattern.html` — slot composition reference
- `templates/lwc/patterns/ldsRecordEditForm.html` — the edit-form counterpart to the view form below

---

## The bundle: `accountSummaryPanel`

```text
force-app/main/default/lwc/accountSummaryPanel/
├── accountSummaryPanel.html
├── accountSummaryPanel.js
├── accountSummaryPanel.js-meta.xml
└── __tests__/
    ├── accountSummaryPanel.test.js
    └── data/
        ├── getObjectInfo.json
        └── getPicklistValues.json
```

### `accountSummaryPanel.html`

```html
<template>
  <lightning-card title="Account Summary" icon-name="standard:account">
    <!-- Card actions go in a NAMED SLOT. In LWC (unlike Aura) `title` and `footer` are
         text-only attributes and there is no `actions` attribute — lwc_guide L11674. -->
    <lightning-button-menu
      slot="actions"
      alternative-text="Panel actions"
      menu-alignment="auto"
      onselect={handleMenuSelect}
    >
      <lightning-menu-item value="refresh" label="Refresh"></lightning-menu-item>
      <lightning-menu-divider></lightning-menu-divider>
      <lightning-menu-item value="clear" label="Clear rating"></lightning-menu-item>
    </lightning-button-menu>

    <div class="slds-var-p-horizontal_medium slds-var-p-bottom_medium">
      <!-- Loading state. lwc:if is a conditional directive; base component tags are
           valid targets for it — lwc_guide L1507. -->
      <template lwc:if={isLoading}>
        <div class="slds-is-relative slds-var-p-vertical_large">
          <lightning-spinner
            alternative-text="Loading account summary"
            size="small"
          ></lightning-spinner>
        </div>
      </template>

      <template lwc:if={hasError}>
        <!-- lightning-badge surfaces icon hover text through icon-alternative-text,
             NOT through the global `title` attribute — lwc_guide L4794-L4801. -->
        <lightning-badge
          label="Metadata unavailable"
          icon-name="utility:warning"
          icon-alternative-text="Warning"
        ></lightning-badge>
        <p class="slds-text-color_error slds-var-m-top_x-small">{errorMessage}</p>
      </template>

      <template lwc:if={isReady}>
        <!-- lightning-layout allows only lightning-layout-item, plain HTML tags and text
             between its items — no expressions, no other components — lwc_guide L11707. -->
        <lightning-layout multiple-rows="true" horizontal-align="spread">
          <lightning-layout-item size="12" small-device-size="6" padding="around-small">
            <!-- Flat structure: options is an array of {label, value} — lwc_guide L4875, L6614.
                 `label` on an input component is the a11y contract — lwc_guide L3987-L3988. -->
            <lightning-combobox
              label="Rating"
              name="rating"
              value={rating}
              placeholder="Select a rating"
              options={ratingOptions}
              onchange={handleRatingChange}
            ></lightning-combobox>
          </lightning-layout-item>

          <lightning-layout-item size="12" small-device-size="6" padding="around-small">
            <!-- The FORM sits in the layout item. The OUTPUT FIELDS stay direct children of
                 the form: lightning-output-field must not be nested in another element such
                 as lightning-layout — lwc_guide L11727. -->
            <lightning-record-view-form
              record-id={recordId}
              object-api-name="Account"
              density="compact"
            >
              <lightning-output-field field-name="Industry"></lightning-output-field>
              <lightning-output-field field-name="AnnualRevenue"></lightning-output-field>
              <lightning-output-field field-name="Owner.Name"></lightning-output-field>
            </lightning-record-view-form>
          </lightning-layout-item>
        </lightning-layout>

        <lightning-button-group>
          <lightning-button
            label="Save rating"
            variant="brand"
            disabled={isSaveDisabled}
            onclick={handleSave}
          ></lightning-button>
          <lightning-button label="Reset" onclick={handleReset}></lightning-button>
        </lightning-button-group>
      </template>
    </div>
  </lightning-card>
</template>
```

**UNVERIFIED (2026-09-05)** — attribute names above that the LWC Developer Guide never prints, and
that must be confirmed on the Component Library Specification tab:
`lightning-card` `icon-name`;
`lightning-button-menu` `alternative-text`, `menu-alignment`, `onselect` (the guide records only
that `lightning:buttonMenu` lacks `onclick`/`onclose`, L11672);
`lightning-menu-item` `value`, `label`;
`lightning-spinner` `alternative-text`, `size`;
`lightning-badge` `label`, `icon-name` (only `icon-alternative-text` is printed, L4799);
`lightning-layout` `multiple-rows`, `horizontal-align`;
`lightning-layout-item` `padding` (`size` and `small-device-size` **are** printed, L1768);
`lightning-combobox` `label`, `name`, `value`, `placeholder`, `onchange` (`options` is printed,
L4875; `onchange` as the base-component change handler is printed generically, L4822, L5095);
`lightning-record-view-form` `record-id`, `object-api-name` (`density` **is** printed, L6329–L6331);
`lightning-output-field` `field-name`;
`lightning-button` `label`, `disabled`, `onclick` (`variant` and its value list **are** printed,
L1620, L1683).

### `accountSummaryPanel.js`

```js
import { LightningElement, api, wire } from 'lwc';
import { getObjectInfo, getPicklistValues } from 'lightning/uiObjectInfoApi';
import { updateRecord } from 'lightning/uiRecordApi';
import Toast from 'lightning/toast';

import ACCOUNT_OBJECT from '@salesforce/schema/Account';
import RATING_FIELD from '@salesforce/schema/Account.Rating';
import ID_FIELD from '@salesforce/schema/Account.Id';

// getPicklistValues requires a recordTypeId. When an object has no default record type,
// the master record type is 012000000000000AAA — lwc_guide L14949.
const MASTER_RECORD_TYPE_ID = '012000000000000AAA';

export default class AccountSummaryPanel extends LightningElement {
  @api recordId;

  // Reactive variable that carries defaultRecordTypeId into the second wire.
  // The guide prescribes exactly this two-step chain — lwc_guide L14960.
  recordTypeId = MASTER_RECORD_TYPE_ID;

  rating;
  originalRating;
  ratingOptions = [];
  objectInfoSettled = false;
  picklistSettled = false;
  errorMessage;

  @wire(getObjectInfo, { objectApiName: ACCOUNT_OBJECT })
  wiredObjectInfo({ data, error }) {
    if (data) {
      // defaultRecordTypeId is documented as the value to feed getPicklistValues — L14949.
      this.recordTypeId = data.defaultRecordTypeId || MASTER_RECORD_TYPE_ID;
    } else if (error) {
      this.errorMessage = this.reduceError(error);
    }
    this.objectInfoSettled = true;
  }

  @wire(getPicklistValues, {
    recordTypeId: '$recordTypeId',
    fieldApiName: RATING_FIELD
  })
  wiredRatingValues({ data, error }) {
    if (data) {
      // data.values is a list of picklist labels and values — lwc_guide L14962.
      // label is TRANSLATED into the running user's language; value is always the
      // untranslated API name. Save `value`, display `label` — lwc_guide L14963-L14964.
      this.ratingOptions = data.values.map((item) => ({
        label: item.label,
        value: item.value
      }));
      this.errorMessage = undefined;
    } else if (error) {
      this.ratingOptions = [];
      this.errorMessage = this.reduceError(error);
    }
    this.picklistSettled = true;
  }

  get isLoading() {
    return !(this.objectInfoSettled && this.picklistSettled);
  }

  get hasError() {
    return !this.isLoading && !!this.errorMessage;
  }

  get isReady() {
    return !this.isLoading && !this.errorMessage;
  }

  get isSaveDisabled() {
    return !this.recordId || this.rating === this.originalRating;
  }

  handleRatingChange(event) {
    // Base components dispatch change; read the new value from the event, not the DOM.
    // lwc_guide L4822 (oneventname handlers), L5095 (onchange on input components).
    this.rating = event.detail.value;
    this.dispatchEvent(
      new CustomEvent('ratingchange', { detail: { value: this.rating } })
    );
  }

  handleMenuSelect(event) {
    const action = event.detail.value;
    if (action === 'refresh') {
      this.dispatchEvent(new CustomEvent('refreshrequest'));
    } else if (action === 'clear') {
      this.rating = undefined;
    }
  }

  handleReset() {
    this.rating = this.originalRating;
  }

  async handleSave() {
    const fields = {};
    fields[ID_FIELD.fieldApiName] = this.recordId;
    // The API name, never the translated label — lwc_guide L14964.
    fields[RATING_FIELD.fieldApiName] = this.rating;
    try {
      await updateRecord({ fields });
      this.originalRating = this.rating;
      // lightning/toast is a module import whose configuration is passed to a method on
      // the module — lwc_guide L4735. It is recommended over platformShowToastEvent because
      // platformShowToastEvent is not supported in LWR sites — lwc_guide L4649, L4773.
      // UNVERIFIED (2026-09-05): the Toast.show(config, source) signature is in the
      // Component Library, not the Developer Guide.
      Toast.show({ label: 'Rating saved', variant: 'success' }, this);
    } catch (error) {
      Toast.show(
        { label: 'Save failed', message: this.reduceError(error), variant: 'error' },
        this
      );
    }
  }

  reduceError(error) {
    if (Array.isArray(error?.body)) {
      return error.body.map((e) => e.message).join(', ');
    }
    return error?.body?.message || error?.message || 'Unknown error';
  }
}
```

### `accountSummaryPanel.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Account Summary Panel</masterLabel>
    <description>Card with a metadata-driven rating combobox and a read-only account summary.</description>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <objects>
                <object>Account</object>
            </objects>
            <supportedFormFactors>
                <supportedFormFactor type="Large" />
                <supportedFormFactor type="Small" />
            </supportedFormFactors>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

How to read it:

- `apiVersion` is the framework version *your* component runs against. Base components are not
  versioned, so lowering it does not roll a base component back; anything below 58.0 is treated as
  58.0 (`lwc_guide base-components-min-version` L4697, L4701).
- `lightning__RecordPage` is available from API 58.0 and `isExposed` must be `true`
  (`lwc_guide targets-lightning-record-page` L19335–L19336).
- `<objects>` restricts the component to Account; the tag set works only inside a `targetConfig`
  configured for `lightning__RecordPage` and may appear once (L19363–L19364).
- `<supportedFormFactor type="…">` accepts `Large` (desktop) and `Small` (phone), and Salesforce
  strongly recommends declaring it (L19373–L19376). **`Small` is safe here only because this bundle
  contains no `lightning-datatable` and no `lightning-tree-grid` — neither is supported on mobile
  devices (`lwc_guide data-table-vs-tree-grid` L5600).** Add a datatable to this bundle and `Small`
  has to come out.

### `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>accountSummaryPanel</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>62.0</version>
</Package>
```

---

## The Jest suite

The `sfdx-lwc-jest` package ships mock components in its `lightning-stubs` directory. They match the
API of the real components but implement none of the behaviour, **fire no events, and do not reflect
every property as a DOM attribute** — you can still query them and call `dispatchEvent()` against
them (`lwc_guide unit-testing-using-jest-patterns` L12622, L12626–L12627). Every assertion below
therefore reads a *property* off the stub and simulates interaction by dispatching at it.

### `__tests__/data/getObjectInfo.json`

```json
{
  "apiName": "Account",
  "defaultRecordTypeId": "012000000000000AAA",
  "label": "Account",
  "fields": {}
}
```

### `__tests__/data/getPicklistValues.json`

```json
{
  "controllerValues": {},
  "defaultValue": null,
  "url": "/services/data/v62.0/ui-api/object-info/Account/picklist-values/012000000000000AAA/Rating",
  "values": [
    { "attributes": null, "label": "Hot", "validFor": [], "value": "Hot" },
    { "attributes": null, "label": "Warm", "validFor": [], "value": "Warm" },
    { "attributes": null, "label": "Cold", "validFor": [], "value": "Cold" }
  ]
}
```

### `__tests__/accountSummaryPanel.test.js`

```js
import { createElement } from 'lwc';
import AccountSummaryPanel from 'c/accountSummaryPanel';
import { getObjectInfo, getPicklistValues } from 'lightning/uiObjectInfoApi';

import mockObjectInfo from './data/getObjectInfo.json';
import mockPicklistValues from './data/getPicklistValues.json';

const RECORD_ID = '001000000000001AAA';

// Emitting after appendChild is required: a component receives wire updates only once it is
// connected to the DOM — lwc_guide unit-testing-using-wire-utility L12548.
function build() {
  const element = createElement('c-account-summary-panel', {
    is: AccountSummaryPanel
  });
  element.recordId = RECORD_ID;
  document.body.appendChild(element);
  return element;
}

// One awaited microtask per rerender — lwc_guide L12590, L12593, L12556.
function flush() {
  return Promise.resolve();
}

describe('c-account-summary-panel', () => {
  afterEach(() => {
    // The jsdom instance is shared across tests in a file — reset it — lwc_guide L12361-L12363.
    while (document.body.firstChild) {
      document.body.removeChild(document.body.firstChild);
    }
    jest.clearAllMocks();
  });

  it('shows a spinner until both wire adapters have settled', async () => {
    const element = build();
    await flush();

    expect(element.shadowRoot.querySelector('lightning-spinner')).not.toBeNull();
    expect(element.shadowRoot.querySelector('lightning-combobox')).toBeNull();
  });

  it('builds combobox options from the picklist values', async () => {
    const element = build();
    getObjectInfo.emit(mockObjectInfo);
    getPicklistValues.emit(mockPicklistValues);
    await flush();

    const combobox = element.shadowRoot.querySelector('lightning-combobox');
    // Read the PROPERTY off the stub. `options` is an array — it is never reflected as an
    // attribute, so getAttribute('options') would return null on both a passing and a
    // failing component — lwc_guide L12626.
    expect(combobox.options).toEqual([
      { label: 'Hot', value: 'Hot' },
      { label: 'Warm', value: 'Warm' },
      { label: 'Cold', value: 'Cold' }
    ]);
    // The label attribute is the accessibility contract — lwc_guide L3987-L3988.
    expect(combobox.label).toBe('Rating');
    expect(element.shadowRoot.querySelector('lightning-spinner')).toBeNull();
  });

  it('re-reads picklist values against the default record type from getObjectInfo', async () => {
    const element = build();
    getObjectInfo.emit({ ...mockObjectInfo, defaultRecordTypeId: '012ABCDEFGHIJKLMNO' });
    getPicklistValues.emit(mockPicklistValues);
    await flush();

    // getPicklistValues requires BOTH recordTypeId and fieldApiName — lwc_guide L14960.
    expect(getPicklistValues.getLastConfig()).toEqual({
      recordTypeId: '012ABCDEFGHIJKLMNO',
      fieldApiName: { objectApiName: 'Account', fieldApiName: 'Rating' }
    });
  });

  it('dispatches ratingchange with the API value when the combobox changes', async () => {
    const element = build();
    const handler = jest.fn();
    element.addEventListener('ratingchange', handler);

    getObjectInfo.emit(mockObjectInfo);
    getPicklistValues.emit(mockPicklistValues);
    await flush();

    const combobox = element.shadowRoot.querySelector('lightning-combobox');
    // The stub fires nothing on its own; dispatch the event yourself — lwc_guide L12627.
    combobox.dispatchEvent(new CustomEvent('change', { detail: { value: 'Warm' } }));
    await flush();

    expect(handler).toHaveBeenCalledTimes(1);
    expect(handler.mock.calls[0][0].detail.value).toBe('Warm');
    expect(element.shadowRoot.querySelector('lightning-combobox').value).toBe('Warm');
  });

  it('dispatches refreshrequest when the Refresh menu item is selected', async () => {
    const element = build();
    const handler = jest.fn();
    element.addEventListener('refreshrequest', handler);

    getObjectInfo.emit(mockObjectInfo);
    getPicklistValues.emit(mockPicklistValues);
    await flush();

    const menu = element.shadowRoot.querySelector('lightning-button-menu');
    menu.dispatchEvent(new CustomEvent('select', { detail: { value: 'refresh' } }));
    await flush();

    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('keeps every output field a direct child of the record view form', async () => {
    const element = build();
    getObjectInfo.emit(mockObjectInfo);
    getPicklistValues.emit(mockPicklistValues);
    await flush();

    const form = element.shadowRoot.querySelector('lightning-record-view-form');
    expect(form.recordId).toBe(RECORD_ID);
    expect(form.objectApiName).toBe('Account');

    const fields = element.shadowRoot.querySelectorAll('lightning-output-field');
    expect(fields).toHaveLength(3);
    // lightning-output-field must be a direct child of the form — lwc_guide L11727.
    fields.forEach((field) => expect(field.parentElement).toBe(form));
  });

  it('renders an error badge and no combobox when object info fails', async () => {
    const element = build();
    getObjectInfo.error();
    getPicklistValues.error();
    await flush();

    expect(element.shadowRoot.querySelector('lightning-badge')).not.toBeNull();
    expect(element.shadowRoot.querySelector('lightning-combobox')).toBeNull();
  });
});
```

**UNVERIFIED (2026-09-05):** `getLastConfig()` and `error()` on an emitted LDS test wire adapter are
`@salesforce/sfdx-lwc-jest` APIs; the Developer Guide documents `emit()` only (L12554). Confirm both
against the sfdx-lwc-jest repo before relying on that third test.

If you need a custom stub — for example to add properties to the toast event object — map it in
`jest.config.js` with `moduleNameMapper`; without an entry the import resolves to the default
`lightning-stubs` implementation (`lwc_guide` L12637, L12646–L12647). Start from
`templates/lwc/jest.config.js`.

---

## Deploy order

| # | Step | Command |
|---|---|---|
| 1 | Confirm the fields exist and the running user can read them | `sf sobject describe --sobject Account --target-org <alias>` |
| 2 | Run the Jest suite locally — it needs no org | `npm run test:unit -- accountSummaryPanel` |
| 3 | Run the base-component checker | `python3 skills/lwc/lwc-base-component-recipes/scripts/check_lwc_base_component_recipes.py --manifest-dir force-app/main/default/lwc --strict` |
| 4 | Validate the deployment without committing it | `sf project deploy start --manifest package.xml --dry-run --target-org <alias>` |
| 5 | Deploy | `sf project deploy start --manifest package.xml --target-org <alias>` |
| 6 | Retrieve back to confirm what actually landed | `sf project retrieve start --metadata LightningComponentBundle:accountSummaryPanel --target-org <alias>` |

Deploy the bundle before adding it to a Lightning page — App Builder only lists components whose
`isExposed` is `true` and whose `targets` include the page type.

## Verification

| Check | How | Pass |
|---|---|---|
| Component is available in App Builder | Setup → Object Manager → Account → Lightning Record Pages → Edit | "Account Summary Panel" appears in the Custom components list |
| Picklist options match the org | Compare the combobox against Setup → Object Manager → Account → Fields → Rating → Values | Same active values, same order the record type exposes |
| Values, not labels, are saved | Change the rating, save, then run the SOQL below | `Rating` holds the API name (`Hot`), not a translated label |
| Record type scoping is right | Open the panel on records of two different record types | The option list changes with the record type (`lwc_guide` L14958) |
| Read-only summary respects FLS | Log in as a user without read access to `AnnualRevenue` | That output field is absent; nothing else breaks |
| Mobile behaviour | Open the record in the Salesforce mobile app | The layout stacks to full width (`size="12"`); no datatable is present to fail |

```sql
SELECT Id, Name, Rating, Industry, AnnualRevenue
FROM Account
WHERE Id = '001000000000001AAA'
```

Run it with `sf data query --query "<the SOQL above>" --target-org <alias>`.
