# Code Examples - LWC Modal And Overlay

Every claim below is grounded in the Lightning Web Components Developer Guide, cited as
`page-slug` (the page id in the URL `https://developer.salesforce.com/docs/platform/lwc/guide/<slug>.html`).
Attribute-level facts that live only in the Component Library specification tabs are marked
`UNVERIFIED (2026-09-05)` beside the claim.

The canonical bundle shape, jest config, and reusable snippets live outside this skill — do not
re-invent them:

| Canonical asset | Path |
|---|---|
| Bundle skeleton (js / html / css / `-meta.xml` / `__tests__`) | `templates/lwc/component-skeleton/` |
| Jest config with `moduleNameMapper` entries | `templates/lwc/jest.config.js` |
| Quick-action component pattern | `templates/lwc/patterns/quickActionPattern.js` |
| Imperative Apex call inside a modal body | `templates/lwc/patterns/imperativeApexPattern.js` |

---

## 1. The Modal: `queuePickerModal`

**What it does:** lets an agent pick a queue, then hands the choice back to whoever opened it.

Three facts shape this file and none of them are optional:

- `LightningModal` is a **default** export of `lightning/modal`, and you **extend** it. There is no
  `<lightning-modal>` tag to place in a template (`use-dialog-modal`, L10375, L10377).
- Import `api` from `lwc` but **not** `LightningElement` — the class already has a base
  (`use-dialog-modal`, L10379).
- `this.close(value)` both closes the modal and returns `value` to the caller
  (`use-dialog-modal`, L10379).

```javascript
// force-app/main/default/lwc/queuePickerModal/queuePickerModal.js
import { api } from 'lwc';
import LightningModal from 'lightning/modal';

export default class QueuePickerModal extends LightningModal {
    // Set by the launcher through QueuePickerModal.open({ queues: [...] }).
    // Public properties on a modal are populated from the open() config object,
    // not from parent markup (use-dialog-modal, L10387).
    @api queues = [];
    @api caseSubject = '';

    selectedQueueId;
    saving = false;

    get options() {
        return this.queues.map((q) => ({ label: q.name, value: q.id }));
    }

    get confirmDisabled() {
        return this.saving || !this.selectedQueueId;
    }

    handleChange(event) {
        this.selectedQueueId = event.detail.value;
    }

    handleCancel() {
        // Always close with an explicit shape. close() with no argument resolves
        // the caller's await with undefined and the caller cannot tell cancel
        // from an empty save.
        this.close({ status: 'cancelled' });
    }

    async handleConfirm() {
        this.saving = true;
        // disableClose is set only for the bounded save window, then released in
        // the finally block so the user is never stranded.
        // UNVERIFIED (2026-09-05): `disableClose` does not appear anywhere in the
        // LWC Developer Guide text; it is documented only on the lightning/modal
        // Component Library specification tab. Confirm the property name against
        // the Component Library before shipping.
        this.disableClose = true;
        try {
            const queue = this.queues.find((q) => q.id === this.selectedQueueId);
            this.close({ status: 'confirmed', queueId: queue.id, queueName: queue.name });
        } finally {
            this.disableClose = false;
            this.saving = false;
        }
    }
}
```

```html
<!-- force-app/main/default/lwc/queuePickerModal/queuePickerModal.html -->
<template>
    <!-- lightning-modal-body is REQUIRED; header and footer are optional
         (use-dialog-modal, L10376). -->
    <lightning-modal-header label="Reassign Case"></lightning-modal-header>

    <lightning-modal-body>
        <p class="slds-m-bottom_small">Choose the queue that should own “{caseSubject}”.</p>
        <lightning-radio-group
            name="queue"
            label="Queue"
            options={options}
            value={selectedQueueId}
            onchange={handleChange}
            required>
        </lightning-radio-group>
    </lightning-modal-body>

    <lightning-modal-footer>
        <lightning-button
            label="Cancel"
            onclick={handleCancel}
            disabled={saving}>
        </lightning-button>
        <lightning-button
            variant="brand"
            class="slds-m-left_x-small"
            label="Reassign"
            onclick={handleConfirm}
            disabled={confirmDisabled}>
        </lightning-button>
    </lightning-modal-footer>
</template>
```

**How to read it**

- No `role="dialog"`, no `aria-modal`, no backdrop `<div>`, no `slds-modal` classes. `LightningModal`
  implements the SLDS modals blueprint itself (`use-dialog-modal`, L10374) and provides the open and
  close mechanisms (`base-components-patterns`, L4778–L4779).
- No `isOpen` boolean and no `<template lwc:if>` wrapper. The modal is not rendered by the parent
  template at all; it is instantiated by the static `open()` call.
- `@api queues` has no matching attribute in any parent's HTML. That is correct for a modal and it
  is exactly what trips up a reader (and a linter) used to ordinary components.

---

## 2. The Launcher: `caseReassignPanel`

The launcher is an ordinary `LightningElement`. It imports the modal *class* and calls the static
`open()` method, which returns a promise that resolves with whatever `close()` was given
(`use-dialog-modal`, L10379, L10387).

```javascript
// force-app/main/default/lwc/caseReassignPanel/caseReassignPanel.js
import { LightningElement, api, wire } from 'lwc';
import LightningToast from 'lightning/toast';
import QueuePickerModal from 'c/queuePickerModal';
import getQueues from '@salesforce/apex/CaseRoutingController.getQueues';
import { updateRecord } from 'lightning/uiRecordApi';

export default class CaseReassignPanel extends LightningElement {
    @api recordId;
    @api caseSubject;
    queues = [];

    @wire(getQueues)
    wiredQueues({ data }) {
        if (data) {
            this.queues = data;
        }
    }

    async handleReassignClick() {
        // The promise resolves only after the modal closes. Awaiting it is the
        // whole contract - a fire-and-forget open() throws the result away.
        const result = await QueuePickerModal.open({
            // label, size and description are lightning/modal open() config keys.
            // UNVERIFIED (2026-09-05): the guide states that open() "provides data
            // to be used in the modal's properties" (use-dialog-modal, L10387) but
            // does not enumerate the built-in config keys or the allowed size
            // values; those are Component Library specification facts.
            label: 'Reassign Case',
            size: 'small',
            description: 'Choose a queue to own this case',
            // Anything else on this object lands on the modal's @api properties.
            queues: this.queues,
            caseSubject: this.caseSubject
        });

        if (result?.status !== 'confirmed') {
            // Cancel and the header X both land here. Returning focus is the
            // launcher's job, not the modal's.
            this.template.querySelector('[data-id="reassign-button"]')?.focus();
            return;
        }

        await updateRecord({ fields: { Id: this.recordId, OwnerId: result.queueId } });

        // lightning/toast is the preferred toast module; lightning/platformShowToastEvent
        // is not supported on login pages in Aura sites, in LWR sites for Experience
        // Cloud, or in standalone apps (use-toast, L10448-L10449, L10452).
        LightningToast.show(
            {
                label: 'Case reassigned',
                message: `Owner is now ${result.queueName}.`,
                variant: 'success'
            },
            this
        );
    }
}
```

```html
<!-- force-app/main/default/lwc/caseReassignPanel/caseReassignPanel.html -->
<template>
    <lightning-card title="Case Routing">
        <div class="slds-p-horizontal_small">
            <lightning-button
                data-id="reassign-button"
                label="Reassign…"
                onclick={handleReassignClick}>
            </lightning-button>
        </div>
    </lightning-card>
</template>
```

---

## 3. `-meta.xml` For The Launcher

The modal component itself needs a `-meta.xml` too, but it is never surfaced in a builder, so it
carries `isExposed=false` and no targets. Only the launcher is placed on a record page.

Setting `apiVersion` is required from Spring '25 (API v63.0) onward — saving an unversioned
component errors (`get-started-api-versioning`, L796–L798). The latest valid value is the org's
current release (`get-started-api-versioning`, L813).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/lwc/caseReassignPanel/caseReassignPanel.js-meta.xml -->
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Case Reassign Panel</masterLabel>
    <targets>
        <target>lightning__RecordPage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <objects>
                <object>Case</object>
            </objects>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/lwc/queuePickerModal/queuePickerModal.js-meta.xml -->
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <isExposed>false</isExposed>
</LightningComponentBundle>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>caseReassignPanel</members>
        <members>queuePickerModal</members>
        <name>LightningComponentBundle</name>
    </types>
    <types>
        <members>CaseRoutingController</members>
        <name>ApexClass</name>
    </types>
    <version>62.0</version>
</Package>
```

Deploy and retrieve:

```bash
# Deploy both bundles plus the controller
sf project deploy start --manifest manifest/package.xml --target-org myorg

# Pull an existing bundle back down before editing it
sf project retrieve start --metadata LightningComponentBundle:queuePickerModal --target-org myorg

# Run the Jest suite for these two bundles only
npm run test:unit -- lwc/__tests__/caseReassignPanel
```

**Verification step:** after deploying, open a Case record page, click **Reassign…**, choose a queue,
and confirm. Then check the write actually landed rather than trusting the toast:

```sql
SELECT Id, Subject, Owner.Name, Owner.Type, LastModifiedDate
FROM Case
WHERE Id = '500XXXXXXXXXXXXXXX'
```

`Owner.Type` should read `Queue`. Also press Escape on the open modal and confirm the panel's
**Reassign…** button regains focus — that is the branch nobody tests.

---

## 4. Jest: Prove `open()` Resolves With The `close()` Value

The developer guide documents a `moduleNameMapper` entry for `^lightning/modal$` pointing at a
project-local mock (`unit-testing-using-jest-create-tests`, L12448–L12449):

```javascript
// jest.config.js — see templates/lwc/jest.config.js for the full file
const { jestConfig } = require('@salesforce/sfdx-lwc-jest/config');

module.exports = {
    ...jestConfig,
    moduleNameMapper: {
        '^lightning/modal$': '<rootDir>/force-app/test/jest-mocks/lightning/modal',
        '^lightning/toast$': '<rootDir>/force-app/test/jest-mocks/lightning/toast',
        '^lightning/uiRecordApi$': '<rootDir>/force-app/test/jest-mocks/lightning/uiRecordApi'
    }
};
```

UNVERIFIED (2026-09-05): the guide states that `sfdx-lwc-jest` ships a `lightning/navigation` mock by
default (`unit-testing-using-jest-create-tests`, L12382) and it prints that mock's source, but it
never prints the body of the `lightning/modal` mock. The mock below is written to the documented
`open()` / `close()` contract, not copied from a published Salesforce file. Verify it against your
`sfdx-lwc-jest` version before relying on it.

```javascript
// force-app/test/jest-mocks/lightning/modal.js
// Records the config passed to open() and lets a test drive the resolution.
export const mockModalOpen = jest.fn();

export default class LightningModal {
    static open(config) {
        return mockModalOpen(config);
    }
    close(result) {
        this.dispatchEvent(new CustomEvent('close', { detail: result }));
    }
}
```

```javascript
// force-app/main/default/lwc/caseReassignPanel/__tests__/caseReassignPanel.test.js
import { createElement } from 'lwc';
import CaseReassignPanel from 'c/caseReassignPanel';
import QueuePickerModal from 'c/queuePickerModal';
import { updateRecord } from 'lightning/uiRecordApi';

jest.mock('c/queuePickerModal', () => ({
    __esModule: true,
    default: { open: jest.fn() }
}));

jest.mock(
    'lightning/uiRecordApi',
    () => ({ updateRecord: jest.fn(() => Promise.resolve({})) }),
    { virtual: true }
);

// Let the awaited promise chain in the click handler settle before asserting.
const flush = () => Promise.resolve();

describe('c-case-reassign-panel', () => {
    afterEach(() => {
        // jsdom is shared across tests in a file, so reset the DOM
        // (unit-testing-using-jest-create-tests, L12363).
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    function build() {
        const element = createElement('c-case-reassign-panel', { is: CaseReassignPanel });
        element.recordId = '500000000000000AAA';
        element.caseSubject = 'Printer on fire';
        document.body.appendChild(element);
        return element;
    }

    it('resolves open() with the value passed to close() and updates the record', async () => {
        // This is the assertion that matters: the promise from open() carries
        // the close() argument.
        QueuePickerModal.open.mockResolvedValue({
            status: 'confirmed',
            queueId: '00G000000000001AAA',
            queueName: 'Tier 2 Support'
        });

        const element = build();
        element.shadowRoot.querySelector('lightning-button').click();
        await flush();
        await flush();

        expect(QueuePickerModal.open).toHaveBeenCalledTimes(1);
        expect(updateRecord).toHaveBeenCalledWith({
            fields: { Id: '500000000000000AAA', OwnerId: '00G000000000001AAA' }
        });
    });

    it('writes nothing when the modal is cancelled', async () => {
        QueuePickerModal.open.mockResolvedValue({ status: 'cancelled' });

        const element = build();
        element.shadowRoot.querySelector('lightning-button').click();
        await flush();
        await flush();

        expect(updateRecord).not.toHaveBeenCalled();
    });

    it('passes the modal its @api inputs through the open() config', async () => {
        QueuePickerModal.open.mockResolvedValue({ status: 'cancelled' });

        const element = build();
        element.shadowRoot.querySelector('lightning-button').click();
        await flush();

        // @api properties on a modal are never set in markup, so this is the
        // only place a test can catch a renamed or dropped input.
        expect(QueuePickerModal.open).toHaveBeenCalledWith(
            expect.objectContaining({ caseSubject: 'Printer on fire', label: 'Reassign Case' })
        );
    });
});
```

---

## 5. Confirm / Alert / Prompt — No Component Needed

For a yes/no question, an urgent halt, or a single string of input, do not build a `LightningModal`
subclass. Three modules cover it, each imported and opened statically. None of them halts execution
the way `window.confirm()` does — they return promises (`base-components-patterns`, L4769;
`use-dialog-confirm`, L10415).

| Module | Guide-stated attributes | `open()` resolves with | Guide page |
|---|---|---|---|
| `lightning/confirm` | `message`, `variant`, `label` | `true` on OK, `false` on Cancel | `use-dialog-confirm`, L10418 |
| `lightning/alert` | `message`, `theme`, `label` | resolves when the user clicks OK | `use-dialog-alert`, L10404 |
| `lightning/prompt` | `message`, `theme`, `label`, `defaultValue` | the entered text, or `null` on Cancel | `use-dialog-prompt`, L10432 |

Note the asymmetry that costs people an afternoon: **confirm takes `variant`, alert and prompt take
`theme`.** They are not interchangeable.

```javascript
import LightningConfirm from 'lightning/confirm';
import LightningAlert from 'lightning/alert';
import LightningPrompt from 'lightning/prompt';

async handleDelete() {
    const proceed = await LightningConfirm.open({
        message: 'Deleting this case also deletes its 14 comments. Continue?',
        variant: 'header',   // confirm uses `variant` (use-dialog-confirm, L10418)
        label: 'Delete Case'
    });
    if (!proceed) {
        return;                       // resolves false on Cancel
    }

    try {
        await deleteCase({ caseId: this.recordId });
    } catch (error) {
        // A failure the user MUST acknowledge is an alert, not a toast -
        // a toast auto-dismisses and the user never sees it.
        await LightningAlert.open({
            message: 'The case was not deleted. Nothing was changed.',
            theme: 'error',  // alert uses `theme` (use-dialog-alert, L10404)
            label: 'Delete failed'
        });
    }
}

async handleRename() {
    const name = await LightningPrompt.open({
        message: 'New name for this saved view',
        theme: 'info',
        label: 'Rename view',
        defaultValue: this.viewName
    });
    // null means Cancel; empty string means the user cleared the box and hit OK.
    // Those are different outcomes (use-dialog-prompt, L10432).
    if (name === null) {
        return;
    }
    this.viewName = name.trim() || this.viewName;
}
```

UNVERIFIED (2026-09-05): the allowed values of `variant` and `theme` (`header`, `headerless`,
`error`, `warning`, `success`, `info`, and so on) are Component Library specification facts. The
guide names the attributes but not their enums.

---

## 6. BAD — Hand-Rolled SLDS Modal Markup

This is the shape an assistant reproduces from pre-Winter '23 training data. It renders. It is still
wrong.

```html
<!-- BAD: do not ship this -->
<template>
    <template lwc:if={isOpen}>
        <section role="dialog" tabindex="-1" aria-modal="true"
                 class="slds-modal slds-fade-in-open">
            <div class="slds-modal__container">
                <header class="slds-modal__header">
                    <h2 class="slds-modal__title">Reassign Case</h2>
                </header>
                <div class="slds-modal__content slds-p-around_medium">
                    <lightning-radio-group options={options} onchange={handleChange}>
                    </lightning-radio-group>
                </div>
                <footer class="slds-modal__footer">
                    <lightning-button label="Cancel" onclick={handleCancel}></lightning-button>
                    <lightning-button variant="brand" label="Reassign" onclick={handleConfirm}>
                    </lightning-button>
                </footer>
            </div>
        </section>
        <div class="slds-backdrop slds-backdrop_open"></div>
    </template>
</template>
```

Why it fails, by source:

| Problem | Grounding |
|---|---|
| It is the wrong API shape. You do not put a modal in a parent template — there is no `lightning-modal` tag and the component is used by extension, not by tagging. | `use-dialog-modal`, L10375; `base-components-patterns`, L4774–L4779 |
| It reimplements the SLDS modals blueprint by hand, which `LightningModal` already implements — so every blueprint change is now your maintenance problem. | `use-dialog-modal`, L10374 |
| There is no result contract. The parent has to invent its own `isOpen` flag plus an event or callback to learn the outcome; `close(result)` gives that for free. | `use-dialog-modal`, L10379 |
| The markup depends on `slds-modal__*` internals. The guide is explicit that you must not rely on the internal markup or CSS classes of base components, because they change between releases. | `base-components-patterns`, L4758 |
| Component styling hooks (`--slds-c-*`) that this markup will eventually need are not yet supported in SLDS 2. | `create-components-css-custom-properties`, L1718 |
| Focus trapping, Escape handling, and backdrop click-out are absent and must be hand-built on `<div>`s, where only `tabindex` values `0` and `-1` are supported and `delegatesFocus` must not be combined with `tabindex`. | `create-components-focus`, L4044, L4065 |

UNVERIFIED (2026-09-05): the guide says `LightningModal` "implements the SLDS modals blueprint" and
"blocks interaction with everything else on the page until the user acts upon or dismisses the modal"
(`use-dialog-modal`, L10372, L10374). It does not enumerate the focus-trap, Escape-key, or
focus-restoration behaviour it provides. Those specifics come from the SLDS modals blueprint and the
Component Library, not from this guide — do not tell a reviewer the guide promises them.

---

## 7. Navigating Out Of A Modal

`NavigationMixin` cannot be applied to a class that extends `LightningModal`; it is only for
components that extend `LightningElement` (`use-navigate-modal`, L10258–L10259). The documented
workaround is a three-component relay: a child inside the modal builds the `PageReference` and
dispatches it, the modal passes it up, and the **parent** — an ordinary `LightningElement` — calls
`NavigationMixin.Navigate` (`use-navigate-modal`, L10260).

```javascript
// Inside the modal: no NavigationMixin here. Hand the PageReference back
// through close() and let the launcher navigate.
handleGoToRecord(event) {
    this.close({ status: 'navigate', pageReference: event.detail });
}
```

```javascript
// In the launcher, which DOES extend NavigationMixin(LightningElement):
import { NavigationMixin } from 'lightning/navigation';

export default class CaseReassignPanel extends NavigationMixin(LightningElement) {
    async handleReassignClick() {
        const result = await QueuePickerModal.open({ label: 'Reassign Case' });
        if (result?.status === 'navigate') {
            this[NavigationMixin.Navigate](result.pageReference);
        }
    }
}
```

For deep-link and `PageReference` construction detail, read `lwc/navigation-and-routing` rather than
duplicating it here — its gotcha 10 covers `NavigationMixin` on `LightningModal` from the routing
side.
