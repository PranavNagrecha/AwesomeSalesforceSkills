# Code Examples — LWC Forms and Validation

Two deployable bundles plus their Jest tests. Bundle 1 is the **hybrid** shape:
`lightning-record-edit-form` keeps LDS field wiring and server-error surfacing, while one
`lightning-input` carries a rule the platform cannot express. Bundle 2 is the **fully custom**
shape: `lightning/uiRecordApi` `createRecord`, with the write-error body mapped back onto fields.

Grounding for the design choice, from the LWC Developer Guide
(`/scratchpad/lwc_guide.txt`, cite as `<page-slug>:<line>`):

| Claim | Source |
|---|---|
| `lightning-input-field` does not support client-side custom validation; nest `lightning-input` in the form instead | `data-edit-record`:5513 |
| Wiring is automatic for `lightning-input-field`, **not** for `lightning-input` — wire it with `getRecord` and supply your own label; submit through `onsubmit` and validate with `setCustomValidity()` | `data-edit-record`:5516 |
| `lightning-input-field` stays the preferred component; use `lightning-input` only when validation-rule errors don't meet the requirement | `data-edit-record`:5518 |
| Include `lightning-messages` before or after the fields for automatic error display | `data-edit-record`:5489, 5499; `data-create-record`:5530 |
| The form fires `error`, `load`, `submit`, `success` | `data-edit-record`:5501–5504 |
| `event.detail.message` is the general description; `event.detail.output.fieldErrors` carries field-specific validation-rule errors | `data-edit-record`:5509 |
| `createRecord` takes a `recordInput` of `apiName` + `fields` | `reference-create-record`:15028–15029, 15033 |
| UI API **write** errors return `error.body` as an object, often with object-level and field-level errors (reads return an array) | `data-error`:6568–6569 |
| With `updateRecord`, requiredness is **not** enforced client-side — call `reportValidity()` to show field-level errors | `reference-update-record`:15403 |

---

## Bundle 1 — `contactQuickEdit` (record-edit-form + one custom-validated input)

### `contactQuickEdit.html`

```html
<!-- force-app/main/default/lwc/contactQuickEdit/contactQuickEdit.html -->
<template>
    <lightning-card title="Edit Contact" icon-name="standard:contact">
        <div class="slds-var-p-around_medium">
            <!--
              onsubmit intercepts, onsuccess/onerror report.
              lightning-messages renders platform errors above the fields
              (data-edit-record:5489).
            -->
            <lightning-record-edit-form
                object-api-name="Contact"
                record-id={recordId}
                density="auto"
                onload={handleLoad}
                onsubmit={handleSubmit}
                onsuccess={handleSuccess}
                onerror={handleError}
            >
                <lightning-messages></lightning-messages>

                <!-- LDS-wired fields: labels, type, requiredness and FLS come from
                     the field metadata via UI API (data-ui-api:5393). -->
                <lightning-input-field field-name="FirstName"></lightning-input-field>
                <lightning-input-field field-name="LastName"></lightning-input-field>
                <lightning-input-field field-name="Email"></lightning-input-field>
                <lightning-input-field
                    field-name="Phone"
                    variant="label-inline"
                ></lightning-input-field>

                <!-- Not LDS-wired. lightning-input-field cannot carry a client-side
                     custom rule (data-edit-record:5513), so this control is a plain
                     lightning-input with its own label, and handleSubmit folds its
                     value back into the submitted fields (data-edit-record:5516). -->
                <lightning-input
                    data-field="ConfirmEmail"
                    type="email"
                    label="Confirm Email"
                    value={confirmEmail}
                    onblur={handleConfirmEmailBlur}
                    onchange={handleConfirmEmailChange}
                ></lightning-input>

                <div class="slds-var-m-top_medium">
                    <lightning-button
                        label="Cancel"
                        onclick={handleCancel}
                    ></lightning-button>
                    <lightning-button
                        class="slds-var-m-left_x-small"
                        variant="brand"
                        type="submit"
                        label="Save"
                        disabled={saving}
                    ></lightning-button>
                </div>
            </lightning-record-edit-form>
        </div>
    </lightning-card>
</template>
```

### `contactQuickEdit.js`

```js
// force-app/main/default/lwc/contactQuickEdit/contactQuickEdit.js
import { LightningElement, api, track } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

import EMAIL_FIELD from '@salesforce/schema/Contact.Email';

const CONFIRM_SELECTOR = 'lightning-input[data-field="ConfirmEmail"]';
const MISMATCH = 'Confirm Email must match Email.';

export default class ContactQuickEdit extends LightningElement {
    @api recordId;

    confirmEmail = '';
    saving = false;
    @track fieldErrorSummary = [];

    handleLoad() {
        // `load` fires when the form loads record data (data-edit-record:5502).
        this.saving = false;
    }

    handleConfirmEmailChange(event) {
        this.confirmEmail = event.target.value;
    }

    handleConfirmEmailBlur() {
        this.validateConfirmEmail(this.currentEmailValue());
    }

    /**
     * Intercept the submit, run the rule the platform cannot express, then hand
     * the augmented field map back to the form.
     *
     * UNVERIFIED (2026-09-05): `event.preventDefault()` on the form's `submit`
     * event and the `submit(fields)` method on lightning-record-edit-form are
     * documented in the Component Library, not in the LWC Developer Guide. The
     * guide states only that you "submit the record data using the onsubmit
     * event handler" and update the fields with the user input value
     * (data-edit-record:5516). The shape of `event.detail.fields` is likewise
     * Component-Library-only.
     */
    handleSubmit(event) {
        event.preventDefault();

        const fields = { ...event.detail.fields };

        if (!this.validateConfirmEmail(fields[EMAIL_FIELD.fieldApiName])) {
            // Stop here. No submit() call means no server round trip and no
            // half-saved record.
            return;
        }

        // Augment: normalise before the record leaves the browser.
        const email = fields[EMAIL_FIELD.fieldApiName];
        if (typeof email === 'string') {
            fields[EMAIL_FIELD.fieldApiName] = email.trim().toLowerCase();
        }

        this.saving = true;
        this.fieldErrorSummary = [];
        this.template.querySelector('lightning-record-edit-form').submit(fields);
    }

    handleSuccess(event) {
        // The record Id is not available on the submit event; it arrives on
        // success (data-considerations:6376).
        this.saving = false;
        this.dispatchEvent(
            new ShowToastEvent({
                title: 'Saved',
                message: `Contact ${event.detail.id} updated.`,
                variant: 'success'
            })
        );
        this.dispatchEvent(
            new CustomEvent('saved', { detail: { recordId: event.detail.id } })
        );
    }

    handleError(event) {
        // event.detail.message is the general description; validation-rule
        // failures land in event.detail.output.fieldErrors as a list of fields
        // and record exception errors (data-edit-record:5509-5510).
        this.saving = false;
        const detail = event.detail || {};
        const fieldErrors = (detail.output && detail.output.fieldErrors) || {};

        this.fieldErrorSummary = Object.keys(fieldErrors).map((fieldApiName) => ({
            field: fieldApiName,
            messages: fieldErrors[fieldApiName].map((e) => e.message).join(' ')
        }));

        this.dispatchEvent(
            new ShowToastEvent({
                title: 'Save failed',
                message: this.fieldErrorSummary.length
                    ? this.fieldErrorSummary
                          .map((f) => `${f.field}: ${f.messages}`)
                          .join('\n')
                    : detail.message || 'An error occurred.',
                variant: 'error',
                mode: 'sticky'
            })
        );
    }

    handleCancel() {
        // lightning-record-edit-form ships no Cancel button of its own; reset()
        // on each input field reverts the values (data-edit-record:5490-5492).
        this.template
            .querySelectorAll('lightning-input-field')
            .forEach((field) => field.reset());
        this.confirmEmail = '';
        this.clearConfirmEmail();
    }

    // --- validation helpers -------------------------------------------------

    currentEmailValue() {
        const emailField = this.template.querySelector(
            'lightning-input-field[field-name="Email"]'
        );
        return emailField ? emailField.value : undefined;
    }

    /**
     * Set-then-report. setCustomValidity() only stores the message; the field
     * renders nothing until reportValidity() runs, and the empty string is what
     * clears a stale message (flow-custom-property-editor example,
     * lwc_guide:9206-9214; reference-update-record:15403).
     */
    validateConfirmEmail(emailValue) {
        const input = this.template.querySelector(CONFIRM_SELECTOR);
        if (!input) {
            return true;
        }
        const mismatch =
            (emailValue || '').trim().toLowerCase() !==
            (this.confirmEmail || '').trim().toLowerCase();

        input.setCustomValidity(mismatch ? MISMATCH : '');
        return input.reportValidity();
    }

    clearConfirmEmail() {
        const input = this.template.querySelector(CONFIRM_SELECTOR);
        if (input) {
            input.setCustomValidity('');
            input.reportValidity();
        }
    }
}
```

### `contactQuickEdit.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Contact Quick Edit</masterLabel>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <objects>
                <object>Contact</object>
            </objects>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

Every component must have a configuration file named `componentName.js-meta.xml`
(`create-components-meta-file`:716). The guide's minimal sample shows `apiVersion` and
`isExposed` (`create-components-meta-file`:718–720); `67.0` matches
`templates/lwc/component-skeleton/componentSkeleton.js-meta.xml` in this repo. Placing the
component on a Contact record page lets it inherit `record-id` and `object-api-name`
(`data-edit-record`:5480).

---

## Bundle 2 — `contactCustomCreate` (uiRecordApi `createRecord` + field-error map)

Reach for this only when the `lightning-record*form` components cannot carry the UX; the guide
says to check for an easier way first (`reference-create-record`:15032). Note the cost you take
on: `createRecord`/`updateRecord` are **independent transactions** — multi-record atomicity
needs Apex (`data-guidelines`:5347).

### `contactCustomCreate.html`

```html
<!-- force-app/main/default/lwc/contactCustomCreate/contactCustomCreate.html -->
<template>
    <lightning-card title="New Contact" icon-name="standard:contact">
        <div class="slds-var-p-around_medium">
            <template lwc:if={pageError}>
                <div class="slds-text-color_error slds-var-m-bottom_small" role="alert">
                    {pageError}
                </div>
            </template>

            <lightning-input
                data-field="FirstName"
                label="First Name"
                value={firstName}
                onchange={handleChange}
            ></lightning-input>

            <lightning-input
                data-field="LastName"
                label="Last Name"
                required
                value={lastName}
                onchange={handleChange}
            ></lightning-input>

            <lightning-input
                data-field="Email"
                type="email"
                label="Email"
                value={email}
                onchange={handleChange}
            ></lightning-input>

            <lightning-combobox
                data-field="LeadSource"
                label="Lead Source"
                value={leadSource}
                options={leadSourceOptions}
                onchange={handleChange}
            ></lightning-combobox>

            <div class="slds-var-m-top_medium">
                <lightning-button
                    variant="brand"
                    label="Create Contact"
                    disabled={saving}
                    onclick={handleCreate}
                ></lightning-button>
            </div>
        </div>
    </lightning-card>
</template>
```

### `contactCustomCreate.js`

```js
// force-app/main/default/lwc/contactCustomCreate/contactCustomCreate.js
import { LightningElement, wire } from 'lwc';
import { createRecord, getRecordCreateDefaults } from 'lightning/uiRecordApi';
import { getObjectInfo, getPicklistValues } from 'lightning/uiObjectInfoApi';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

import CONTACT_OBJECT from '@salesforce/schema/Contact';
import LEADSOURCE_FIELD from '@salesforce/schema/Contact.LeadSource';

export default class ContactCustomCreate extends LightningElement {
    firstName = '';
    lastName = '';
    email = '';
    leadSource = '';
    saving = false;
    pageError = '';

    recordTypeId;
    leadSourceOptions = [];

    // getPicklistValues needs BOTH recordTypeId and fieldApiName; take the
    // recordTypeId from getObjectInfo's defaultRecordTypeId, which falls back to
    // the master record type 012000000000000AAA when there is no default
    // (reference-wire-adapters-picklist-values:14949, 14960).
    @wire(getObjectInfo, { objectApiName: CONTACT_OBJECT })
    handleObjectInfo({ data, error }) {
        if (data) {
            this.recordTypeId = data.defaultRecordTypeId;
        } else if (error) {
            this.pageError = this.reduceError(error);
        }
    }

    @wire(getPicklistValues, {
        recordTypeId: '$recordTypeId',
        fieldApiName: LEADSOURCE_FIELD
    })
    handlePicklist({ data, error }) {
        if (data) {
            this.leadSourceOptions = data.values.map((v) => ({
                label: v.label,
                value: v.value
            }));
        } else if (error) {
            this.pageError = this.reduceError(error);
        }
    }

    // Defaults for a create form come from getRecordCreateDefaults; ignored here
    // beyond proving the wire is available, but wire it when the object has
    // meaningful defaults you would otherwise hardcode.
    @wire(getRecordCreateDefaults, { objectApiName: CONTACT_OBJECT })
    createDefaults;

    handleChange(event) {
        const field = event.target.dataset.field;
        this[field.charAt(0).toLowerCase() + field.slice(1)] = event.detail.value;
        // Clear the server-side message this control was carrying, or the user
        // stays blocked after fixing the value.
        event.target.setCustomValidity('');
        event.target.reportValidity();
    }

    async handleCreate() {
        this.pageError = '';

        // Requiredness is NOT enforced client-side on a custom form; the sweep
        // below is what surfaces it (reference-update-record:15403, 15405-15410).
        const inputs = [
            ...this.template.querySelectorAll('lightning-input, lightning-combobox')
        ];
        const allValid = inputs.reduce((validSoFar, input) => {
            input.reportValidity();
            return validSoFar && input.checkValidity();
        }, true);

        if (!allValid) {
            return;
        }

        // recordInput takes exactly two properties: apiName and fields
        // (reference-create-record:15028-15029, 15033).
        const recordInput = {
            apiName: CONTACT_OBJECT.objectApiName,
            fields: {
                FirstName: this.firstName,
                LastName: this.lastName,
                Email: this.email,
                LeadSource: this.leadSource
            }
        };

        this.saving = true;
        try {
            const contact = await createRecord(recordInput);
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Contact created',
                    message: `Record ${contact.id} created.`,
                    variant: 'success'
                })
            );
            this.dispatchEvent(
                new CustomEvent('created', { detail: { recordId: contact.id } })
            );
            this.reset();
        } catch (error) {
            this.applyServerErrors(error);
        } finally {
            this.saving = false;
        }
    }

    /**
     * A UI API write error returns error.body as an OBJECT, often carrying
     * object-level and field-level errors — unlike a read error, whose body is
     * an array (data-error:6568-6569).
     *
     * UNVERIFIED (2026-09-05): the exact key names inside that object
     * (`output.fieldErrors`, `output.errors`) are documented for the
     * record-edit-form `onerror` event detail (data-edit-record:5509) but the
     * LWC Developer Guide does not restate them for the createRecord rejection
     * body. The reader below therefore probes defensively and always falls back
     * to error.body.message.
     */
    applyServerErrors(error) {
        const body = (error && error.body) || {};
        const output = body.output || {};
        const fieldErrors = output.fieldErrors || {};
        const pageErrors = output.errors || [];

        let mappedAny = false;
        Object.keys(fieldErrors).forEach((fieldApiName) => {
            const input = this.template.querySelector(
                `[data-field="${fieldApiName}"]`
            );
            if (input && typeof input.setCustomValidity === 'function') {
                input.setCustomValidity(
                    fieldErrors[fieldApiName].map((e) => e.message).join(' ')
                );
                input.reportValidity();
                mappedAny = true;
            }
        });

        const leftovers = pageErrors.map((e) => e.message);
        if (!mappedAny || leftovers.length) {
            this.pageError = leftovers.join(' ') || this.reduceError(error);
        }

        this.dispatchEvent(
            new ShowToastEvent({
                title: 'Create failed',
                message: this.pageError || 'Check the highlighted fields.',
                variant: 'error',
                mode: 'sticky'
            })
        );
    }

    reduceError(error) {
        const body = (error && error.body) || {};
        if (Array.isArray(body)) {
            return body.map((e) => e.message).join(', ');
        }
        if (typeof body.message === 'string') {
            return body.message;
        }
        return error && error.statusText ? error.statusText : 'Unknown error';
    }

    reset() {
        this.firstName = '';
        this.lastName = '';
        this.email = '';
        this.leadSource = '';
        this.pageError = '';
    }
}
```

### `contactCustomCreate.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Contact Custom Create</masterLabel>
    <targets>
        <target>lightning__AppPage</target>
        <target>lightning__HomePage</target>
    </targets>
</LightningComponentBundle>
```

---

## Jest tests

`__tests__` lives at the top of the bundle directory, test files end in `.test.js`, and the
folder is `.forceignore`d so it never deploys (`unit-testing-using-jest-create-tests`:12328–12331).
`element.shadowRoot` is the test-only API for peeking across the shadow boundary
(`unit-testing-using-jest-create-tests`:12379). Rerenders after a property or DOM change are
asynchronous — return or await `Promise.resolve()` before asserting
(`unit-testing-using-jest-create-tests`:12494, 12501).

### `__tests__/contactQuickEdit.test.js`

```js
// force-app/main/default/lwc/contactQuickEdit/__tests__/contactQuickEdit.test.js
import { createElement } from 'lwc';
import ContactQuickEdit from 'c/contactQuickEdit';

const CONFIRM = 'lightning-input[data-field="ConfirmEmail"]';
const FORM = 'lightning-record-edit-form';

/** The sfdx-lwc-jest base-component stubs render but implement no constraint
 *  validation, so the test supplies the validity contract it is asserting on. */
function stubInput(input, { valid }) {
    input.setCustomValidity = jest.fn();
    input.reportValidity = jest.fn(() => valid);
    input.checkValidity = jest.fn(() => valid);
    return input;
}

describe('c-contact-quick-edit', () => {
    afterEach(() => {
        // The jsdom instance is shared across test cases in a file, so reset it.
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    function render() {
        const element = createElement('c-contact-quick-edit', {
            is: ContactQuickEdit
        });
        element.recordId = '003000000000001AAA';
        document.body.appendChild(element);
        return element;
    }

    it('blocks submit and reports a message when the emails do not match', async () => {
        const element = render();
        const form = element.shadowRoot.querySelector(FORM);
        form.submit = jest.fn();

        const confirm = stubInput(
            element.shadowRoot.querySelector(CONFIRM),
            { valid: false }
        );
        confirm.dispatchEvent(
            new CustomEvent('change', { detail: { value: 'other@example.com' } })
        );
        await Promise.resolve();

        form.dispatchEvent(
            new CustomEvent('submit', {
                detail: { fields: { Email: 'real@example.com', LastName: 'Ada' } }
            })
        );
        await Promise.resolve();

        // The custom message was set, reported, and the save never left the browser.
        expect(confirm.setCustomValidity).toHaveBeenCalledWith(
            'Confirm Email must match Email.'
        );
        expect(confirm.reportValidity).toHaveBeenCalled();
        expect(form.submit).not.toHaveBeenCalled();
    });

    it('clears the custom message and submits normalised fields when valid', async () => {
        const element = render();
        const form = element.shadowRoot.querySelector(FORM);
        form.submit = jest.fn();

        const confirm = stubInput(
            element.shadowRoot.querySelector(CONFIRM),
            { valid: true }
        );
        confirm.dispatchEvent(
            new CustomEvent('change', { detail: { value: 'Real@Example.com' } })
        );
        await Promise.resolve();

        form.dispatchEvent(
            new CustomEvent('submit', {
                detail: { fields: { Email: '  Real@Example.com ', LastName: 'Ada' } }
            })
        );
        await Promise.resolve();

        expect(confirm.setCustomValidity).toHaveBeenLastCalledWith('');
        expect(form.submit).toHaveBeenCalledTimes(1);
        expect(form.submit.mock.calls[0][0].Email).toBe('real@example.com');
    });

    it('surfaces field-level validation-rule errors from the error event', async () => {
        const element = render();
        const form = element.shadowRoot.querySelector(FORM);
        const toast = jest.fn();
        element.addEventListener('lightning__showtoast', toast);

        form.dispatchEvent(
            new CustomEvent('error', {
                detail: {
                    message: 'An error occurred while trying to update the record.',
                    output: {
                        fieldErrors: {
                            Email: [
                                {
                                    message: 'Email must be on the corporate domain.',
                                    fieldLabel: 'Email'
                                }
                            ]
                        }
                    }
                }
            })
        );
        await Promise.resolve();

        expect(toast).toHaveBeenCalled();
        expect(toast.mock.calls[0][0].detail.message).toContain(
            'Email must be on the corporate domain.'
        );
        expect(toast.mock.calls[0][0].detail.variant).toBe('error');
    });
});
```

### `__tests__/contactCustomCreate.test.js`

```js
// force-app/main/default/lwc/contactCustomCreate/__tests__/contactCustomCreate.test.js
import { createElement } from 'lwc';
import ContactCustomCreate from 'c/contactCustomCreate';
import { createRecord } from 'lightning/uiRecordApi';

jest.mock(
    'lightning/uiRecordApi',
    () => ({
        createRecord: jest.fn(),
        getRecordCreateDefaults: jest.fn()
    }),
    { virtual: true }
);

describe('c-contact-custom-create', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    function render() {
        const element = createElement('c-contact-custom-create', {
            is: ContactCustomCreate
        });
        document.body.appendChild(element);
        return element;
    }

    function stubAll(element, valid) {
        return [
            ...element.shadowRoot.querySelectorAll(
                'lightning-input, lightning-combobox'
            )
        ].map((input) => {
            input.setCustomValidity = jest.fn();
            input.reportValidity = jest.fn(() => valid);
            input.checkValidity = jest.fn(() => valid);
            return input;
        });
    }

    it('does not call createRecord when a required input is invalid', async () => {
        const element = render();
        const inputs = stubAll(element, false);

        element.shadowRoot
            .querySelector('lightning-button')
            .dispatchEvent(new CustomEvent('click'));
        await Promise.resolve();

        inputs.forEach((i) => expect(i.reportValidity).toHaveBeenCalled());
        expect(createRecord).not.toHaveBeenCalled();
    });

    it('maps a rejected write body onto the offending field', async () => {
        createRecord.mockRejectedValue({
            body: {
                message: 'An error occurred while trying to create the record.',
                output: {
                    errors: [],
                    fieldErrors: {
                        Email: [{ message: 'Duplicate email address.' }]
                    }
                }
            },
            status: 400,
            statusText: 'BAD_REQUEST'
        });

        const element = render();
        const inputs = stubAll(element, true);
        const emailInput = inputs.find(
            (i) => i.dataset.field === 'Email'
        );

        element.shadowRoot
            .querySelector('lightning-button')
            .dispatchEvent(new CustomEvent('click'));
        await Promise.resolve();
        await Promise.resolve();

        expect(createRecord).toHaveBeenCalledTimes(1);
        expect(createRecord.mock.calls[0][0].apiName).toBe('Contact');
        expect(emailInput.setCustomValidity).toHaveBeenCalledWith(
            'Duplicate email address.'
        );
        expect(emailInput.reportValidity).toHaveBeenCalled();
    });
});
```

`jest.config.js` — copy `templates/lwc/jest.config.js`. It already maps
`lightning/platformShowToastEvent` and `lightning/navigation` to the repo mocks; the guide's
own config maps `lightning/uiRecordApi` the same way
(`unit-testing-using-jest-create-tests`:12442–12443).

---

## Deploy manifest

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>contactQuickEdit</members>
        <members>contactCustomCreate</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>67.0</version>
</Package>
```

## Commands

```bash
# Retrieve an existing bundle before you edit it
sf project retrieve start -m "LightningComponentBundle:contactQuickEdit" -o my-sandbox

# Run the Jest suite locally — no org needed, tests never deploy
npm run test:unit -- contactQuickEdit
npx sfdx-lwc-jest -- --coverage

# Deploy both bundles
sf project deploy start -x manifest/package.xml -o my-sandbox

# Dry run only (nothing is saved)
sf project deploy start -x manifest/package.xml -o my-sandbox --dry-run
```

## Verification after deploy

1. **Setup check** — Setup → Quick Find → *Lightning Components* lists every LWC in the org;
   click the component to see its details (`use-setup`:7783–7785). Confirm both bundles appear.
2. **Behaviour check** — put `contactQuickEdit` on a Contact record page, enter a mismatched
   Confirm Email, and press Save. The field-level message must appear and **no** save should
   occur; then create a Contact validation rule (for example `NOT(ISBLANK(Email)) &&
   NOT(CONTAINS(Email, "@corp.example"))`), save a violating value, and confirm the message
   arrives through `onerror` rather than as a blank failure.
3. **Query check** — after a successful save, confirm the write landed and was normalised:

   ```sql
   SELECT Id, Email, LastModifiedDate
   FROM Contact
   WHERE Id = '003000000000001AAA'
   ```

   `Email` should be lower-cased and trimmed, which proves `handleSubmit` augmented the field
   map rather than letting the raw form value through.

## How to read these bundles

- **`onsubmit` is the only place a hybrid form can intervene.** Once the form submits, the
  field map is what the server sees; the guide's own instruction is to validate and update the
  fields inside that handler (`data-edit-record`:5516).
- **`lightning-input-field` and `lightning-input` are not interchangeable.** The first is
  LDS-wired but carries no custom client rule (`data-edit-record`:5513); the second needs its
  own label and value wiring (`data-edit-record`:5516) but accepts `min`, `max`, and `pattern`
  (`data-edit-record`:5517).
- **`lightning-messages` is not decoration.** It is the supported surface for automatic error
  display in the form (`data-edit-record`:5489); `onerror` is for behaviour you add on top.
- **Bundle 2 pays for its freedom.** It re-implements requiredness
  (`reference-update-record`:15403), the record-type-aware picklist
  (`reference-wire-adapters-picklist-values`:14949), and the error mapping the form does for
  free — and it is still one transaction per call (`data-guidelines`:5347).
- **Both bundles keep the save button gated.** `disabled={saving}` is the state that stops the
  second click during latency; nothing in the platform does this for you.
