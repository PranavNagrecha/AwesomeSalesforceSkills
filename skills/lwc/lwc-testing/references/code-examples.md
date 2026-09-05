# Code Examples: LWC Jest Harness

One component bundle that exercises every boundary this skill mocks — an LDS
`@wire`, an imperative Apex call, a custom event, and a custom label — plus the
full Jest suite that proves all four, including the failure paths.

Line citations are to the crawled Lightning Web Components Developer Guide
(`lwc_guide <page-slug> L<line>`); each page lives at
`https://developer.salesforce.com/docs/platform/lwc/guide/<page-slug>.html`.

Do not re-invent the shell or the config. Copy:

- `templates/lwc/component-skeleton/` — the bundle shape (`.js`, `.html`, `.css`,
  `.js-meta.xml`, `__tests__/`) and the loading / error / ready state model.
- `templates/lwc/component-skeleton/__tests__/componentSkeleton.test.js` — the
  render / state-transition / error-event trio this suite extends.
- `templates/lwc/jest.config.js` — the base config. This file only lists the
  **delta** you add on top of it.
- `templates/lwc/patterns/imperativeApexPattern.js` and
  `templates/lwc/patterns/wireServicePattern.js` — the production-side call shapes.

---

## What the suite proves

| Requirement | Test in `contactQuickEditor.test.js` |
|---|---|
| Wire provisions data → DOM renders it | `renders the wired contact name` |
| Wire provisions an error → error region renders | `renders the error region when the wire errors` |
| Imperative Apex resolves → success state + event | `dispatches contactsaved when the Apex save resolves` |
| Imperative Apex rejects → error state, no event | `renders the Apex error and dispatches nothing when save rejects` |
| Custom event payload is asserted, not just the call | `dispatches contactsaved …` (`detail.contactId`) |
| Label import is mocked, not asserted against the org | `jest.mock('@salesforce/label/…')` at module scope |
| Negative path: no `recordId` → nothing is wired or saved | `does not call Apex when recordId is missing` |
| Every mounted element is torn down | `afterEach` |

---

## The bundle

### `force-app/main/default/lwc/contactQuickEditor/contactQuickEditor.js`

```js
import { LightningElement, api, wire } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import saveContact from '@salesforce/apex/ContactController.saveContact';
import SAVE_ERROR_LABEL from '@salesforce/label/c.Contact_Save_Error';
import NAME_FIELD from '@salesforce/schema/Contact.Name';
import TITLE_FIELD from '@salesforce/schema/Contact.Title';

const FIELDS = [NAME_FIELD, TITLE_FIELD];

/**
 * contactQuickEditor — one component, four testable boundaries.
 *
 *  @wire(getRecord)   -> the test emits into the imported adapter
 *  saveContact(...)   -> the test resolves / rejects a jest.fn()
 *  `contactsaved`     -> the test asserts the CustomEvent detail
 *  SAVE_ERROR_LABEL   -> the test substitutes a known string
 *
 * A @wire function receives an object with a `data` property or an `error`
 * property; those names are hardcoded in the API and must be used verbatim
 * (lwc_guide apex-wire-method L7106-L7107).
 */
export default class ContactQuickEditor extends LightningElement {
    @api recordId;

    contact;
    wireError;
    apexError;
    saving = false;

    // `$recordId` makes the config reactive. When recordId is undefined the
    // parameter is undefined, and an undefined parameter means the adapter is
    // not invoked (lwc_guide apex-wire-method L7104).
    @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
    wiredContact({ data, error }) {
        if (data) {
            this.contact = data;
            this.wireError = undefined;
        } else if (error) {
            this.wireError = this.reduceError(error);
            this.contact = undefined;
        }
    }

    get name() {
        return getFieldValue(this.contact, NAME_FIELD);
    }

    get title() {
        return getFieldValue(this.contact, TITLE_FIELD);
    }

    get isReady() {
        return Boolean(this.contact) && !this.saving;
    }

    async handleSave() {
        if (!this.recordId) {
            return;
        }
        this.saving = true;
        this.apexError = undefined;
        try {
            const savedId = await saveContact({
                contactId: this.recordId,
                title: this.template.querySelector('[data-id="title-input"]').value
            });
            // bubbles and composed both default to false, so this event is
            // observable on the host element only (lwc_guide events-propagation
            // L5119-L5121). The test listens on `element`, which IS the host.
            this.dispatchEvent(
                new CustomEvent('contactsaved', { detail: { contactId: savedId } })
            );
        } catch (error) {
            // Prefer the org's custom label over the raw Apex text so the
            // message is translatable (lwc_guide create-labels L3766).
            this.apexError = `${SAVE_ERROR_LABEL}: ${this.reduceError(error)}`;
        } finally {
            this.saving = false;
        }
    }

    reduceError(error) {
        if (Array.isArray(error?.body)) {
            return error.body.map((e) => e.message).join(', ');
        }
        if (typeof error?.body?.message === 'string') {
            return error.body.message;
        }
        return error?.message ?? 'Unknown error';
    }
}
```

### `force-app/main/default/lwc/contactQuickEditor/contactQuickEditor.html`

```html
<template>
    <lightning-card title="Quick Edit">
        <template lwc:if={wireError}>
            <p data-id="wire-error" role="alert">{wireError}</p>
        </template>

        <template lwc:elseif={isReady}>
            <p data-id="name">{name}</p>
            <lightning-input
                data-id="title-input"
                label="Title"
                value={title}
            ></lightning-input>
            <lightning-button
                data-id="save"
                label="Save"
                onclick={handleSave}
            ></lightning-button>
        </template>

        <template lwc:if={apexError}>
            <p data-id="apex-error" role="alert">{apexError}</p>
        </template>
    </lightning-card>
</template>
```

`data-id` attributes are the test's selectors on purpose. LWC adds its own
scoping attributes and classes to every element, and those "are internal
implementation details that can change at any time… Don't rely on internal
attributes and classes in your code **or tests**"
(`lwc_guide create-components-css-antipatterns L1915, L1920`).

### `force-app/main/default/lwc/contactQuickEditor/contactQuickEditor.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordPage</target>
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

`63.0` is the LWC API version that maps to Spring '25 (`lwc_guide
create-version-alignment L855-L856`). Versioning support began at 58.0; anything
lower is silently treated as 58.0, and a version later than the org's latest
fails on save (`lwc_guide create-version-considerations L872-L873`). The
version table in the guide stops at Spring '25 / 63.0 — **UNVERIFIED
(2026-09-05): the LWC API version for Summer '26 is not in the crawled guide.
Pin the version your org actually reports rather than copying a newer number
from a template.**

---

## The Jest suite

### `force-app/main/default/lwc/contactQuickEditor/__tests__/contactQuickEditor.test.js`

```js
import { createElement } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';
import ContactQuickEditor from 'c/contactQuickEditor';
import saveContact from '@salesforce/apex/ContactController.saveContact';

// --- Imperative Apex -------------------------------------------------------
// `{ virtual: true }` is mandatory. `@salesforce/apex/...` is generated by the
// LWC compiler and has no file on disk, so without the flag Jest throws
// "Cannot find module" while collecting the suite. The guide shows this exact
// three-argument shape for the sibling scoped module @salesforce/label
// (lwc_guide unit-testing-using-jest-patterns L12650-L12655).
jest.mock(
    '@salesforce/apex/ContactController.saveContact',
    () => ({ default: jest.fn() }),
    { virtual: true }
);

// --- Custom label ----------------------------------------------------------
// A jest-transformer rewrites the @salesforce/label import into a variable
// whose value is the label PATH — by default `c.Contact_Save_Error`, never the
// org's translated text. Mock it so the assertion has a known string
// (lwc_guide unit-testing-using-jest-patterns L12650).
jest.mock(
    '@salesforce/label/c.Contact_Save_Error',
    () => ({ default: 'Could not save' }),
    { virtual: true }
);

const RECORD_ID = '003000000000001AAA';

const MOCK_GET_RECORD = {
    apiName: 'Contact',
    id: RECORD_ID,
    fields: {
        Name: { value: 'Amy Taylor', displayValue: null },
        Title: { value: 'VP of Engineering', displayValue: null }
    }
};

function buildElement(props = {}) {
    const element = createElement('c-contact-quick-editor', {
        is: ContactQuickEditor
    });
    // Properties set BEFORE appendChild render synchronously; properties set
    // after it need a microtask (lwc_guide unit-testing-using-jest-create-tests
    // L12505-L12506). Setting here keeps the first render deterministic.
    Object.assign(element, props);
    document.body.appendChild(element);
    return element;
}

describe('c-contact-quick-editor', () => {
    afterEach(() => {
        // Each test file shares ONE jsdom instance and it is not reset between
        // tests, so anything left mounted leaks forward
        // (lwc_guide unit-testing-using-jest-create-tests L12362-L12363).
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    it('renders the wired contact name', async () => {
        const element = buildElement({ recordId: RECORD_ID });

        // The component receives wire updates only once it is connected to the
        // DOM, so emit AFTER appendChild
        // (lwc_guide unit-testing-using-wire-utility L12548).
        getRecord.emit(MOCK_GET_RECORD);
        await Promise.resolve();

        expect(element.shadowRoot.querySelector('[data-id="name"]').textContent).toBe(
            'Amy Taylor'
        );
        expect(element.shadowRoot.querySelector('[data-id="wire-error"]')).toBeNull();
    });

    it('renders the error region when the wire errors', async () => {
        const element = buildElement({ recordId: RECORD_ID });

        // UNVERIFIED (2026-09-05): the crawled guide documents only emit() on
        // the imported adapter; the error() method is documented in the
        // wire-service-jest-util README, not in the Developer Guide.
        getRecord.error({ body: { message: 'Record not found' }, status: 404 });
        await Promise.resolve();

        const errorEl = element.shadowRoot.querySelector('[data-id="wire-error"]');
        expect(errorEl).not.toBeNull();
        expect(errorEl.textContent).toBe('Record not found');
        expect(element.shadowRoot.querySelector('[data-id="name"]')).toBeNull();
    });

    it('dispatches contactsaved when the Apex save resolves', async () => {
        saveContact.mockResolvedValue(RECORD_ID);

        const element = buildElement({ recordId: RECORD_ID });
        const handler = jest.fn();
        // `contactsaved` is dispatched with bubbles:false / composed:false — the
        // defaults (lwc_guide events-propagation L5119-L5121). A listener on
        // document.body would never fire; the host element is the only place.
        element.addEventListener('contactsaved', handler);

        getRecord.emit(MOCK_GET_RECORD);
        await Promise.resolve();

        element.shadowRoot.querySelector('[data-id="save"]').click();
        // Two boundaries to cross: the awaited Apex promise, then the rerender.
        await Promise.resolve();
        await Promise.resolve();

        expect(saveContact).toHaveBeenCalledTimes(1);
        expect(saveContact).toHaveBeenCalledWith({
            contactId: RECORD_ID,
            title: 'VP of Engineering'
        });
        expect(handler).toHaveBeenCalledTimes(1);
        expect(handler.mock.calls[0][0].detail).toEqual({ contactId: RECORD_ID });
    });

    it('renders the Apex error and dispatches nothing when save rejects', async () => {
        saveContact.mockRejectedValue({ body: { message: 'FIELD_CUSTOM_VALIDATION' } });

        const element = buildElement({ recordId: RECORD_ID });
        const handler = jest.fn();
        element.addEventListener('contactsaved', handler);

        getRecord.emit(MOCK_GET_RECORD);
        await Promise.resolve();

        element.shadowRoot.querySelector('[data-id="save"]').click();
        await Promise.resolve();
        await Promise.resolve();

        const errorEl = element.shadowRoot.querySelector('[data-id="apex-error"]');
        expect(errorEl).not.toBeNull();
        // Proves the LABEL mock is in play, not the raw `c.Contact_Save_Error`
        // path string the transformer would otherwise substitute.
        expect(errorEl.textContent).toBe('Could not save: FIELD_CUSTOM_VALIDATION');
        expect(handler).not.toHaveBeenCalled();
    });

    it('does not call Apex when recordId is missing', async () => {
        const element = buildElement();

        getRecord.emit(MOCK_GET_RECORD);
        await Promise.resolve();

        // The guard runs before any await, so nothing is queued.
        element.shadowRoot.querySelector('[data-id="save"]')?.click();
        await Promise.resolve();

        expect(saveContact).not.toHaveBeenCalled();
        expect(element.shadowRoot.querySelector('[data-id="apex-error"]')).toBeNull();
    });
});
```

### Reading the suite

- **`getRecord` is imported, not registered.** The test imports the same adapter
  the component imports and calls `.emit()` on it. Registering the adapter under
  test was the Spring '21-and-earlier shape: "That code still works, but it isn't
  recommended" (`lwc_guide unit-testing-using-wire-utility L12562`). If you see
  `registerLdsTestWireAdapter` or `registerApexTestWireAdapter` in a suite, it is
  legacy — the checker WARNs on it.
- **`await Promise.resolve()` is the whole flush story.** The guide's own examples
  use `return Promise.resolve().then(...)` (`L12556`, `L12600`) and
  `await Promise.resolve()` (`L12485`). **UNVERIFIED (2026-09-05): `flushPromises`
  does not appear anywhere in the crawled guide** — it is a community helper name.
  `templates/lwc/component-skeleton/__tests__/componentSkeleton.test.js` defines
  one; that is a local convention wrapping `Promise.resolve()`, not a platform API.
- **One `await` per async boundary.** A click that triggers an awaited Apex call
  needs two: one to settle the promise, one for the rerender it schedules.
- **`element.shadowRoot` is a test-only API.** It "lets you peek across the shadow
  boundary… the test equivalent of `this.template`"
  (`lwc_guide unit-testing-using-jest-create-tests L12379`).
- **`lightning-button` / `lightning-input` are stubs.** They come from the
  `lightning-stubs` directory in sfdx-lwc-jest, they "match the API of the actual
  components but don't have all the functionality", and **no events are fired from
  these mocks — you can still call `dispatchEvent()` against them**
  (`lwc_guide unit-testing-using-jest-patterns L12622, L12627`). Base-component
  properties are also not always reflected as DOM attributes (`L12626`).

---

## The `jest.config.js` delta

`templates/lwc/jest.config.js` is the base. It already spreads
`@salesforce/sfdx-lwc-jest/config`, maps `lightning/navigation` and
`lightning/platformShowToastEvent`, and sets an 80% `coverageThreshold`. Add only
what this component needs:

```js
const { jestConfig } = require('@salesforce/sfdx-lwc-jest/config');

module.exports = {
    ...jestConfig,
    moduleNameMapper: {
        // --- already in templates/lwc/jest.config.js ---
        '^lightning/navigation$':
            '<rootDir>/force-app/test/jest-mocks/lightning/navigation',
        '^lightning/platformShowToastEvent$':
            '<rootDir>/force-app/test/jest-mocks/lightning/platformShowToastEvent',

        // --- the delta this component adds ---
        // Point these at a custom stub ONLY when the sfdx-lwc-jest stub is not
        // enough. Mapping uiRecordApi replaces the stub adapter, which means
        // getRecord.emit() no longer exists unless your stub provides it.
        '^lightning/uiRecordApi$':
            '<rootDir>/force-app/test/jest-mocks/lightning/uiRecordApi',
        '^@salesforce/apex$': '<rootDir>/force-app/test/jest-mocks/apex'
    },
    coverageThreshold: {
        global: { branches: 80, functions: 80, lines: 80, statements: 80 }
    },
    testTimeout: 10000
};
```

- `moduleNameMapper` for `@salesforce/apex` is the guide's documented route for
  Apex mocks (`lwc_guide unit-testing-using-jest-create-tests L12461-L12465`); the
  per-test `jest.mock(..., { virtual: true })` used above is the alternative when
  one test needs a different resolve value than another.
- Without a `moduleNameMapper` entry, an import resolves to the sfdx-lwc-jest stub;
  with one, it resolves to your custom stub (`lwc_guide unit-testing-using-jest-patterns L12646-L12647`).
- "If you override the default `jest.config.js` file with a custom
  `setupFilesAfterEnv` option, merge the values with those defined in
  `@salesforce/sfdx-lwc-jest/config`" (`lwc_guide unit-testing-using-jest-patterns L12648`) — spreading `...jestConfig` and
  then re-declaring `setupFilesAfterEnv` silently drops the platform's own setup.
- The guide's sample config also carries `setupFiles: ['jest-canvas-mock']` and
  `testTimeout: 10000` (`lwc_guide unit-testing-using-jest-create-tests L12455-L12457`).
- **UNVERIFIED (2026-09-05): `coverageThreshold` is Jest's own option, not
  documented in the LWC guide.** The guide never names a coverage percentage for
  Jest — 80% is this repo's convention from `templates/lwc/jest.config.js`, not a
  Salesforce requirement. (The 75% figure people quote is the Apex deployment
  gate, which has nothing to do with Jest.)

---

## `.forceignore`

Jest tests are local-only and are never saved to Salesforce
(`lwc_guide unit-testing-using-jest-create-tests L12325`). Keep the folder out of
every push, pull and deploy:

```text
**/__tests__/**
```

`sf force lightning lwc test setup` writes this entry for you
(`lwc_guide unit-testing-using-jest-create-tests L12329`). **UNVERIFIED
(2026-09-05): the crawled page states that a glob pattern must be added but the
extraction dropped the literal pattern.** `**/__tests__/**` is the widely used
form; confirm against the file the CLI generates in your own project.

---

## Commands

Deploy order is **N/A** — nothing in this file is deployable except the bundle
itself, and the tests never reach the org. What matters is CI order:

```bash
# 1. One-time, from the top-level directory of the DX project.
#    Creates the config files, installs @salesforce/sfdx-lwc-jest, and adds the
#    .forceignore entry (lwc_guide unit-testing-using-jest-installation L12250).
sf force lightning lwc test setup

# 2. Scaffold the __tests__ folder and a boilerplate test for a component
#    (lwc_guide unit-testing-using-jest-create-tests L12327).
sf force lightning lwc test create -f force-app/main/default/lwc/contactQuickEditor/contactQuickEditor.js

# 3. Local loop — re-runs the relevant tests on every save
#    (lwc_guide unit-testing-using-jest-run-tests L12263).
npm run test:unit:watch

# 4. Whole project, once (lwc_guide unit-testing-using-jest-run-tests L12262).
sf force lightning lwc test run

# 5. CI gate — run the Jest suite BEFORE the deploy, never after.
npm run test:unit:coverage
sf project deploy start --source-dir force-app/main/default/lwc \
    --test-level RunLocalTests --wait 30

# 6. Harness audit (this skill's checker).
python3 skills/lwc/lwc-testing/scripts/check_lwc_testing.py \
    --manifest-dir force-app/main/default/lwc --strict
```

**UNVERIFIED (2026-09-05): `npm run test:unit:coverage` and the underlying
`sfdx-lwc-jest --coverage` / `--skipApiVersionCheck` flags are not documented in
the crawled guide.** The guide names only `--watch` (`L12263`) and `--debug`
(`L12292`), and says the script entries live in `package.json` (`L12253`) — read
your project's `scripts` block for the exact names rather than assuming them.

---

## Verification

The suite is not "done" because it is green. Check all four:

| Check | Command | Passing looks like |
|---|---|---|
| Coverage floor | `npm run test:unit:coverage` | branches/functions/lines/statements all ≥ the `coverageThreshold` in `jest.config.js` |
| The failure paths run | grep the report for `contactQuickEditor.js` | the `catch` block and the `error` branch of `wiredContact` are both covered — a suite that only emits success leaves them at 0 |
| The suite can actually fail | temporarily change `'Amy Taylor'` to `'Nobody'` in the component | `renders the wired contact name` goes red; if it stays green the assertion is not reaching the DOM |
| Harness hygiene | `check_lwc_testing.py --manifest-dir <lwc dir> --strict` | 0 ERROR, 0 WARN |

The third row is the one people skip. A test that appends the element, never
awaits, and asserts `not.toBeNull()` on a `<template lwc:if>` region will pass on
both branches and prove nothing.
