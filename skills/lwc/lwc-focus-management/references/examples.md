# Examples — LWC Focus Management

Working focus code for the surfaces that actually need it. Every framework
construct below is from the Lightning Web Components Developer Guide or the
Lightning Component Reference (Summer '26, API 67.0): `lwc:ref` / `this.refs`,
`static delegatesFocus`, `renderedCallback`, `lightning/modal`, and the
documented `focus()` method on the base components.

Templates use `lwc:if` / `lwc:else` rather than the legacy `if:true` / `if:false`
directives.

---

## Example 1: The dialog you should almost always write

**Context:** a destructive action needs a confirmation dialog.

**Problem:** a hand-rolled modal has to place initial focus somewhere sensible,
trap `Tab` in both directions, exit on `Escape`, remove its trap on close, and
hand focus back to the button that opened it. That is five separate things to get
right and there is no error when you get any of them wrong.

**`lightning/modal` already does four of the five.** The Lightning Component
Reference documents its initial-focus rule in priority order: the step subtitle
when the modal has multiple steps, otherwise the title in the header, otherwise
"the first interactive element in the modal body", otherwise the close button.

```javascript
// force-app/main/default/lwc/confirmDeleteModal/confirmDeleteModal.js
import { api } from 'lwc';
import LightningModal from 'lightning/modal';

export default class ConfirmDeleteModal extends LightningModal {
    // Custom @api properties are passed through LightningModal.open().
    @api recordName;

    handleCancel() {
        this.close('cancel');
    }

    handleConfirm() {
        this.close('confirm');
    }
}
```

```html
<!-- confirmDeleteModal.html -->
<template>
    <!-- lightning-modal-body is required; header and footer are optional but
         recommended. They render in the order they appear in the template. -->
    <lightning-modal-header label="Delete record"></lightning-modal-header>

    <lightning-modal-body>
        <p>Delete <strong>{recordName}</strong>? This can't be undone.</p>
    </lightning-modal-body>

    <lightning-modal-footer>
        <lightning-button
            label="Cancel"
            onclick={handleCancel}></lightning-button>
        <lightning-button
            variant="destructive"
            label="Delete"
            onclick={handleConfirm}></lightning-button>
    </lightning-modal-footer>
</template>
```

The fifth thing — **returning focus to the trigger** — is the opener's job,
because the opener is the only component that knows which button was pressed:

```javascript
// recordActions.js
import { LightningElement, api } from 'lwc';
import ConfirmDeleteModal from 'c/confirmDeleteModal';

export default class RecordActions extends LightningElement {
    @api recordId;
    @api recordName;

    async handleDeleteClick() {
        const result = await ConfirmDeleteModal.open({
            // label is required — it is the modal's accessible name.
            label: 'Delete record',
            size: 'small',
            description: 'Confirm permanent deletion of this record',
            recordName: this.recordName
        });

        if (result === 'confirm') {
            await this.deleteRecord();
        }

        // Restoration. The modal has left the DOM by the time open() resolves,
        // so focus is currently on <body>. Put it back where the user left it.
        this.refs.deleteButton.focus();
    }

    async deleteRecord() {
        /* deleteRecord from lightning/uiRecordApi, omitted */
    }
}
```

```html
<!-- recordActions.html -->
<template>
    <lightning-button
        lwc:ref="deleteButton"
        variant="destructive"
        label="Delete"
        onclick={handleDeleteClick}></lightning-button>
</template>
```

**Why it works:** `lwc:ref="deleteButton"` names the trigger without a selector,
and `this.refs.deleteButton` resolves it in the opener's own shadow tree — the
only tree in which that button is visible. `lightning-button` exposes a
documented `focus()`, so no reaching into its internals is needed.

**Note on `disableClose`:** the modal supports it, but the reference is blunt
about the risk — it "Prevents closing the modal by normal means like the ESC key,
the close button, or `.close()`", it should be a state lasting "less than 5
seconds", and misusing it is a keyboard trap. If you set it, also disable every
UI path that would call `close()` while it is set.

---

## Example 2: A hand-rolled trap, done correctly

**Context:** a non-modal disclosure surface — an inline editor panel that must
keep `Tab` inside itself while open, where `lightning/modal` is the wrong shape.

**Problem:** the standard implementation found in most codebases does not work
in LWC, for two independent reasons.

### The version that does not work

```javascript
// WRONG — both bugs, in six lines.
const FOCUSABLE = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

handleKeyDown(event) {
    if (event.key !== 'Tab') return;
    const focusable = [...this.template.querySelectorAll(FOCUSABLE)];
    const first = focusable[0];
    const last  = focusable[focusable.length - 1];

    if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
    }
}
```

1. **`this.template.querySelectorAll(FOCUSABLE)` returns an empty list** for a
   panel built from base components. `<lightning-input>` is not an `input`; the
   real `<input>` is inside *its* shadow tree, which this query cannot reach.
   `focusable[0]` is `undefined` and the handler throws or silently does nothing.

2. **`document.activeElement === first` is never true.** With focus on a control
   inside a shadow tree, `document.activeElement` retargets to the host custom
   element. The comparison fails even when the element genuinely is focused.

The combination is worse than either bug alone: the code is unreachable, so it
never throws in a way anyone notices, and the trap simply is not there.

### The version that works

```javascript
import { LightningElement, api } from 'lwc';

/**
 * Focusable things in THIS template are custom elements, so enumerate those.
 * Each one owns a documented focus() that reaches its own internals.
 * Extend this list when the panel gains a new kind of control.
 */
const FOCUSABLE_TAGS = [
    'lightning-input',
    'lightning-textarea',
    'lightning-combobox',
    'lightning-button',
    'lightning-button-icon'
].join(',');

export default class InlineEditorPanel extends LightningElement {
    @api recordId;

    _open = false;
    _focusPending = false;

    @api
    open() {
        this._open = true;
        this._focusPending = true;
    }

    close() {
        this._open = false;
        this._focusPending = false;
        // The opener restores focus; this component only reports that it closed.
        this.dispatchEvent(new CustomEvent('close'));
    }

    get isOpen() {
        return this._open;
    }

    renderedCallback() {
        // Guarded: renderedCallback fires after EVERY render, and re-focusing on
        // each one steals the caret from a user who has started typing.
        if (this._focusPending) {
            this._focusPending = false;
            this.refs.firstField?.focus();
        }
    }

    handleKeyDown(event) {
        if (!this._open) {
            return;
        }

        // WCAG 2.1.2 No Keyboard Trap: a trap without an exit is a failure, not
        // a feature. Escape is the exit, and it must be handled before Tab.
        if (event.key === 'Escape') {
            event.stopPropagation();
            this.close();
            return;
        }

        if (event.key !== 'Tab') {
            return;
        }

        const focusable = this.focusableElements();
        if (focusable.length === 0) {
            return;
        }

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        // this.template.activeElement is the ShadowRoot's own view of focus,
        // scoped to this component. document.activeElement would be the host.
        const active = this.template.activeElement;

        if (event.shiftKey && active === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && active === last) {
            event.preventDefault();
            first.focus();
        }
    }

    /**
     * Document order is tab order here because no element in this template
     * carries a tabindex. If that changes, this ordering assumption breaks —
     * which is one more reason not to sprinkle tabindex around.
     */
    focusableElements() {
        return [...this.template.querySelectorAll(FOCUSABLE_TAGS)]
            .filter((el) => !el.disabled);
    }
}
```

```html
<!-- inlineEditorPanel.html -->
<template>
    <template lwc:if={isOpen}>
        <!-- The keydown listener lives on the container, so it sees Tab from
             every descendant regardless of which shadow tree fired it. -->
        <section
            class="slds-box"
            role="dialog"
            aria-label="Edit record inline"
            onkeydown={handleKeyDown}>

            <lightning-input
                lwc:ref="firstField"
                label="Name"
                value={name}></lightning-input>

            <lightning-textarea
                label="Description"
                value={description}></lightning-textarea>

            <lightning-button
                label="Done"
                onclick={close}></lightning-button>
        </section>
    </template>
</template>
```

**Why it works:**

- The query targets custom elements, so it finds the controls that exist.
- The comparison uses `this.template.activeElement`, which is scoped to this
  shadow tree and therefore actually matches.
- `Escape` is handled before `Tab`, so the trap always has an exit.
- The trap is inside `lwc:if`, so closing the panel removes the listener with the
  DOM instead of leaving a keydown handler attached to a hidden subtree.
- Focus is placed once, behind `_focusPending`, rather than on every render.

**Known limitation, stated rather than hidden:** `focusableElements()` assumes
document order equals tab order and that `disabled` is the only reason an element
is skipped. A control hidden by CSS, or one inside a collapsed section, is still
returned. If the panel gains conditional content, filter on visibility too — or
reconsider whether this should have been a `lightning/modal`.

---

## Example 3: Validation errors — summary first

**Context:** a multi-field form where submit runs client-side validation.

**Problem:** the intuitive fix is to focus the first invalid field. That
announces one error to a screen-reader user who has three, and gives no sense of
how much work is left.

```javascript
import { LightningElement } from 'lwc';

const FIELD_TAGS = 'lightning-input, lightning-combobox, lightning-textarea';

export default class ApplicationForm extends LightningElement {
    errors = [];
    _focusSummaryPending = false;

    // Options for the combobox; source omitted.
    countryOptions = [];

    get hasErrors() {
        return this.errors.length > 0;
    }

    get errorCount() {
        return this.errors.length;
    }

    handleSubmit() {
        // reportValidity() "Displays the error messages and returns false if the
        // input is invalid" — so it both renders the inline messages and gives
        // us the per-field result in one pass.
        const fields = [...this.template.querySelectorAll(FIELD_TAGS)];

        this.errors = fields
            .filter((field) => !field.reportValidity())
            .map((field) => ({
                name: field.name,
                message: `${field.label} is required or invalid`
            }));

        if (this.hasErrors) {
            // Focus moves in renderedCallback, because the summary does not
            // exist in the DOM until this assignment causes a re-render.
            this._focusSummaryPending = true;
            return;
        }

        this.save();
    }

    renderedCallback() {
        if (this._focusSummaryPending) {
            this._focusSummaryPending = false;
            this.refs.errorSummary?.focus();
        }
    }

    handleErrorClick(event) {
        event.preventDefault();
        const fieldName = event.currentTarget.dataset.field;
        // lwc:ref is a compile error inside for:each, so dynamic targets are
        // addressed by data-* attribute instead.
        this.template
            .querySelector(`[data-field-name="${fieldName}"]`)
            ?.focus();
    }

    save() {
        /* imperative Apex call, omitted — see templates/lwc/patterns/imperativeApexPattern.js */
    }
}
```

```html
<!-- applicationForm.html -->
<template>
    <template lwc:if={hasErrors}>
        <!-- tabindex="-1" makes this programmatically focusable without adding
             it to the tab order. 0 and -1 are the only values LWC accepts.
             role="alert" carries an implicit aria-live="assertive". -->
        <div
            lwc:ref="errorSummary"
            role="alert"
            tabindex="-1"
            class="slds-notify slds-notify_alert slds-theme_error">
            <h2>Fix {errorCount} problems before saving</h2>
            <ul>
                <template for:each={errors} for:item="err">
                    <li key={err.name}>
                        <a
                            href="#"
                            data-field={err.name}
                            onclick={handleErrorClick}>{err.message}</a>
                    </li>
                </template>
            </ul>
        </div>
    </template>

    <lightning-input
        name="firstName"
        data-field-name="firstName"
        label="First name"
        required></lightning-input>

    <lightning-combobox
        name="country"
        data-field-name="country"
        label="Country"
        options={countryOptions}
        required></lightning-combobox>

    <lightning-button label="Submit" onclick={handleSubmit}></lightning-button>
</template>
```

**Why it works:** the summary is focused once per submit, `role="alert"`
announces it on insertion, and each error is a link into the field it describes —
so a keyboard user gets the count first and a direct route to each problem
second.

**The subtle part:** `role="alert"` announces when the node is *inserted*. If a
second submit produces an identically worded summary and the node was never
removed, some screen readers will not announce it again. The `lwc:if` wrapper is
doing real work here — it removes the node between submits, so each submit is a
fresh insertion.

---

## Example 4: Deleting the focused row

**Context:** an editable list where each row has a Remove button.

**Problem:** removing the focused row destroys the focused element. Focus falls
to `<body>`, and the next `Tab` starts from the top of the page — a keyboard user
loses their place entirely.

```javascript
import { LightningElement, track } from 'lwc';

export default class LineItemList extends LightningElement {
    @track items = [];
    _focusAfterRender = null;

    handleRemove(event) {
        const removedId = event.currentTarget.dataset.id;
        const index = this.items.findIndex((i) => i.id === removedId);
        if (index === -1) {
            return;
        }

        // Decide the successor BEFORE the mutation, while the neighbours still
        // exist: next row, else previous row, else the list heading.
        const next = this.items[index + 1];
        const prev = this.items[index - 1];
        this._focusAfterRender = next
            ? `[data-remove-id="${next.id}"]`
            : prev
                ? `[data-remove-id="${prev.id}"]`
                : '[data-focus="list-heading"]';

        // Reassign rather than splice in place — LWC reactivity triggers on
        // assignment to the property, not on mutation of the array it holds.
        this.items = this.items.filter((i) => i.id !== removedId);

        this.announce(`Removed line item. ${this.items.length} remaining.`);
    }

    renderedCallback() {
        if (this._focusAfterRender) {
            const selector = this._focusAfterRender;
            this._focusAfterRender = null;
            this.template.querySelector(selector)?.focus();
        }
    }

    /**
     * A live region announces only when its text CHANGES. Two identical
     * consecutive messages announce once unless the region is blanked between
     * them, so blank now and set on the next microtask.
     */
    announce(message) {
        this.announcement = '';
        Promise.resolve().then(() => {
            this.announcement = message;
        });
    }
}
```

```html
<!-- lineItemList.html -->
<template>
    <h2 data-focus="list-heading" tabindex="-1">Line items</h2>

    <ul>
        <template for:each={items} for:item="item">
            <li key={item.id}>
                <span>{item.label}</span>
                <lightning-button-icon
                    icon-name="utility:delete"
                    alternative-text={item.removeLabel}
                    data-id={item.id}
                    data-remove-id={item.id}
                    onclick={handleRemove}></lightning-button-icon>
            </li>
        </template>
    </ul>

    <!-- role="status" is aria-live="polite": it waits for a pause rather than
         interrupting. Correct for confirmations; wrong for validation errors. -->
    <div role="status" class="slds-assistive-text">{announcement}</div>
</template>
```

**Why it works:** the successor is computed while it is still addressable, the
selector is stashed rather than the element (the element is about to be
destroyed and re-created by the re-render), and `renderedCallback` applies it
once. The heading carries `tabindex="-1"` so it can receive focus when the list
empties without becoming a tab stop.

---

## Example 5: Testing focus in Jest, and what the test cannot prove

```javascript
import { createElement } from 'lwc';
import ApplicationForm from 'c/applicationForm';

describe('c-application-form focus behaviour', () => {
    let element;

    beforeEach(() => {
        element = createElement('c-application-form', { is: ApplicationForm });
        document.body.appendChild(element);
    });

    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
    });

    it('moves focus to the error summary after a failed submit', async () => {
        const inputs = element.shadowRoot.querySelectorAll('lightning-input');
        inputs.forEach((i) => {
            i.reportValidity = jest.fn(() => false);
        });

        element.shadowRoot
            .querySelector('lightning-button')
            .dispatchEvent(new CustomEvent('click'));

        // Two microtask flushes: one for the state assignment, one for the
        // re-render that creates the summary and the renderedCallback that
        // focuses it.
        await Promise.resolve();
        await Promise.resolve();

        const summary = element.shadowRoot.querySelector('[role="alert"]');
        expect(summary).not.toBeNull();

        // Assert the IDENTITY of the focused element. A spy that merely records
        // "focus was called" passes just as happily when focus went to the
        // wrong element, which is the failure this test exists to catch.
        expect(element.shadowRoot.activeElement).toBe(summary);
    });

    it('does not re-focus the summary on an unrelated re-render', async () => {
        /* … trigger the failure, then change an unrelated property, then assert
           activeElement is unchanged. This is the test that catches an
           unguarded renderedCallback. … */
    });
});
```

Config: [`templates/lwc/jest.config.js`](../../../../templates/lwc/jest.config.js).

**What this proves:** that the component *intends* to focus the right element,
and that it does not re-focus on every render.

**What it does not prove:** that the real tab order is correct. jsdom is not a
browser — it has no layout, no real sequential focus navigation, and no
`delegatesFocus` behaviour to speak of. A green suite here plus a manual
keyboard walk is the working standard; the suite alone is not.

---

## Anti-Pattern: `this._opener = document.activeElement`

**What almost every LWC modal does:**

```javascript
@api open() {
    this._opener = document.activeElement;   // the host, not the button
    this._isOpen = true;
}

handleClose() {
    this._isOpen = false;
    Promise.resolve().then(() => this._opener?.focus?.());
}
```

**What goes wrong:** when the trigger button lives inside another component's
shadow tree — which it does, always, in Lightning — `document.activeElement`
retargets to that component's *host* element. `this._opener` is a
`<c-record-actions>`, not a `<lightning-button>`.

The `?.focus?.()` then makes the failure invisible in two layers. The host is an
`HTMLElement`, so `focus` exists and the optional call succeeds. But a custom
element with no `tabindex` and no `delegatesFocus` is not focusable, so the call
is a no-op. No error, no warning, and focus quietly ends up on `<body>`.

**Correct approach:** the opener restores its own trigger, because it is the only
component that can see it.

```javascript
// Opener component — it knows what was clicked.
async handleOpen() {
    this.showDialog = true;
    await this.dialogClosed();          // or await SomeModal.open({...})
    this.showDialog = false;
    this.refs.openButton.focus();       // its own shadow tree, its own element
}
```

**Detection hint:** `document.activeElement` anywhere in a component bundle. In
LWC it is almost never the element you want, and there is a scoped alternative
(`this.template.activeElement`) for the one case — comparing against a known
element in your own shadow tree — where you legitimately need to ask.
