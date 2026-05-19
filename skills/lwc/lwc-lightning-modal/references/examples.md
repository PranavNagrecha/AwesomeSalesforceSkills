# Examples — LWC Lightning Modal

Two worked scenarios and one anti-pattern showing how to use
`LightningModal` correctly. The scenarios target the two most common
shapes: a confirmation that returns a value to the caller, and a
size-variant modal with a `disableClose` guard during async work.
The anti-pattern shows what breaks when practitioners build a "modal"
out of raw `slds-modal` markup instead of the platform base class.

---

## Example 1: Confirmation modal that returns a typed result to the parent

**Context:** A record page LWC ("Delete Account") needs to ask the
user "Are you sure?" before issuing a delete via UI API. The parent
must know whether the user clicked Delete or Cancel, and must NOT
proceed if the user dismissed the modal via Esc or the close (X)
button. The codebase already standardizes on `lightning/modal`.

**Problem:** A common first attempt uses `dispatchEvent(new
CustomEvent('confirm'))` from inside the modal to notify the parent.
That doesn't work — the parent does not subscribe to events on a
modal opened with `Modal.open()` because the modal renders in a
separate portal outside the parent's template. The parent has no
element handle to attach a listener to. The result is that the modal
"works" (it opens and the buttons render) but the parent never sees
the click.

**Solution:** Use `this.close(value)` from the modal — the value is
the resolution of the Promise returned by `Modal.open()`. Pass a
typed sentinel ('confirm' / 'cancel') so the parent can distinguish
explicit dismissal from passive dismissal (Esc / X → `undefined`).

```javascript
// confirmDelete.js — the modal component
import { api } from 'lwc';
import LightningModal from 'lightning/modal';

export default class ConfirmDelete extends LightningModal {
    @api recordName;

    handleConfirm() {
        this.close('confirm');
    }

    handleCancel() {
        this.close('cancel');
    }
}
```

```html
<!-- confirmDelete.html -->
<template>
    <lightning-modal-header label="Delete Account"></lightning-modal-header>
    <lightning-modal-body>
        <p>
            Delete account <strong>{recordName}</strong>?
            This action cannot be undone.
        </p>
    </lightning-modal-body>
    <lightning-modal-footer>
        <lightning-button
            label="Cancel"
            onclick={handleCancel}>
        </lightning-button>
        <lightning-button
            label="Delete"
            variant="destructive"
            onclick={handleConfirm}>
        </lightning-button>
    </lightning-modal-footer>
</template>
```

```javascript
// accountActions.js — the parent that opens the modal
import { LightningElement, api } from 'lwc';
import { deleteRecord } from 'lightning/uiRecordApi';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import ConfirmDelete from 'c/confirmDelete';

export default class AccountActions extends LightningElement {
    @api recordId;
    @api recordName;

    async handleDeleteClick() {
        const result = await ConfirmDelete.open({
            size: 'small',
            description: 'Confirm deletion of an Account record',
            recordName: this.recordName
        });

        // Esc, outside-click, or X all resolve with undefined.
        // Explicit Cancel resolves with the string 'cancel'.
        if (result !== 'confirm') {
            return;
        }

        try {
            await deleteRecord(this.recordId);
            this.dispatchEvent(new ShowToastEvent({
                title: 'Deleted',
                variant: 'success'
            }));
        } catch (e) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'Delete failed',
                message: e.body?.message ?? 'Unknown error',
                variant: 'error'
            }));
        }
    }
}
```

**Why it works:** `Modal.open()` returns a Promise; `this.close(value)`
resolves that Promise with `value`. Custom events don't cross the
modal boundary because the modal isn't in the parent's template tree —
return values do. The three-way distinction (`'confirm'` vs
`'cancel'` vs `undefined`) lets the parent code reason about user
intent: only `'confirm'` proceeds, both explicit cancel and passive
dismissal short-circuit. Passing `recordName` via `@api` works because
`Modal.open()` assigns the options object's properties onto the modal
instance before the first render — exactly like passing `@api` props
through a template binding, just keyed off the options object.

---

## Example 2: Wizard modal with size variant, disableClose, and async work

**Context:** A "Create Opportunity Bundle" wizard collects three
screens of data (account, line items, terms), then submits via Apex.
Submission may take 2–4 seconds. While the submission is in flight,
the modal must NOT close — the user pressing Esc would orphan the
in-progress callout. The wizard needs more horizontal space than the
default, so it uses `size: 'large'`. On successful submit, the modal
returns the new Opportunity Id so the parent can navigate to it.

**Problem:** Practitioners often try to set `disableClose` once at
`Modal.open({ disableClose: true, ... })`. That locks the modal for
its entire lifetime — the user can't close even on screen 1 of 3
before they've started any work. They also try to call `this.close()`
while a submit is in flight and hit race conditions where the close
fires twice (once from the button, once from a finally-block).

**Solution:** Make `disableClose` reactive via an `@api` getter that
the LightningModal instance reads on each render. Toggle it `true`
only while the submission Promise is unresolved. Guard `this.close()`
with a `_isClosing` flag so it can't fire twice.

```javascript
// opportunityBundleWizard.js
import { api, track } from 'lwc';
import LightningModal from 'lightning/modal';
import submitBundle from '@salesforce/apex/OppBundleController.submitBundle';

export default class OpportunityBundleWizard extends LightningModal {
    @api accountId;

    @track step = 1;          // 1, 2, or 3
    @track payload = {};
    @track isSubmitting = false;

    _isClosing = false;

    // LightningModal reads disableClose on each render — toggling
    // isSubmitting flips the close-disabled state mid-flight.
    get disableClose() {
        return this.isSubmitting;
    }

    handleNext(e) {
        Object.assign(this.payload, e.detail);
        this.step += 1;
    }

    handleBack() {
        this.step -= 1;
    }

    handleCancel() {
        if (this._isClosing) return;
        this._isClosing = true;
        this.close(undefined);    // explicit user cancel
    }

    async handleSubmit() {
        this.isSubmitting = true;
        try {
            const opportunityId = await submitBundle({
                accountId: this.accountId,
                payload: JSON.stringify(this.payload)
            });
            if (this._isClosing) return;
            this._isClosing = true;
            this.close({ status: 'created', opportunityId });
        } catch (e) {
            this.isSubmitting = false;     // re-enable close on failure
            this.dispatchEvent(new CustomEvent('submiterror', {
                detail: e.body?.message ?? 'Submit failed'
            }));
        }
    }

    get isStep1() { return this.step === 1; }
    get isStep2() { return this.step === 2; }
    get isStep3() { return this.step === 3; }
}
```

```html
<!-- opportunityBundleWizard.html -->
<template>
    <lightning-modal-header label="New Opportunity Bundle"></lightning-modal-header>
    <lightning-modal-body>
        <template lwc:if={isStep1}>
            <c-bundle-step-account onnext={handleNext}></c-bundle-step-account>
        </template>
        <template lwc:elseif={isStep2}>
            <c-bundle-step-line-items onnext={handleNext} onback={handleBack}></c-bundle-step-line-items>
        </template>
        <template lwc:elseif={isStep3}>
            <c-bundle-step-terms onnext={handleNext} onback={handleBack}></c-bundle-step-terms>
        </template>
        <template lwc:if={isSubmitting}>
            <lightning-spinner alternative-text="Submitting"></lightning-spinner>
        </template>
    </lightning-modal-body>
    <lightning-modal-footer>
        <lightning-button
            label="Cancel"
            disabled={isSubmitting}
            onclick={handleCancel}>
        </lightning-button>
        <template lwc:if={isStep3}>
            <lightning-button
                label="Create Bundle"
                variant="brand"
                disabled={isSubmitting}
                onclick={handleSubmit}>
            </lightning-button>
        </template>
    </lightning-modal-footer>
</template>
```

```javascript
// parent that launches the wizard
import { LightningElement, api } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';
import OpportunityBundleWizard from 'c/opportunityBundleWizard';

export default class AccountBundleLauncher extends NavigationMixin(LightningElement) {
    @api recordId;

    async handleLaunch() {
        const result = await OpportunityBundleWizard.open({
            size: 'large',
            label: 'New Opportunity Bundle',
            description: 'Three-step wizard to create a bundled opportunity',
            accountId: this.recordId
        });

        if (result?.status === 'created') {
            this[NavigationMixin.Navigate]({
                type: 'standard__recordPage',
                attributes: {
                    recordId: result.opportunityId,
                    objectApiName: 'Opportunity',
                    actionName: 'view'
                }
            });
        }
    }
}
```

**Why it works:** `disableClose` is documented as an option on
`Modal.open()`, but the platform also reads it from the instance on
each render — so making it a reactive getter that depends on
`isSubmitting` (tracked) gives mid-lifetime control. The
`_isClosing` flag prevents the double-close race that happens when
both a button handler and an error handler can call `this.close()`.
Returning a structured object `{ status, opportunityId }` rather than
a bare Id keeps the parent's success/cancel/failure branching
exhaustive: `undefined` from passive dismissal, `undefined` from
explicit Cancel, the object on success. The `size: 'large'` value
matches the platform's enum (`small | medium | large | full`) — any
other string is silently ignored and the modal falls back to
`medium`.

---

## Anti-Pattern: Building a "modal" with raw `slds-modal` CSS classes

**What practitioners do:**

```html
<!-- DON'T DO THIS — handRolledModal.html -->
<template>
    <template lwc:if={isOpen}>
        <section
            role="dialog"
            tabindex="-1"
            aria-modal="true"
            class="slds-modal slds-fade-in-open">
            <div class="slds-modal__container">
                <header class="slds-modal__header">
                    <h2 class="slds-modal__title slds-hyphenate">{title}</h2>
                </header>
                <div class="slds-modal__content slds-p-around_medium">
                    <slot></slot>
                </div>
                <footer class="slds-modal__footer">
                    <button class="slds-button slds-button_neutral" onclick={handleCancel}>Cancel</button>
                    <button class="slds-button slds-button_brand" onclick={handleOk}>OK</button>
                </footer>
            </div>
        </section>
        <div class="slds-backdrop slds-backdrop_open"></div>
    </template>
</template>
```

**What goes wrong:**

1. **No focus trap.** Pressing Tab walks the user out of the modal
   and into the underlying page. Keyboard-only users lose their place
   instantly. The accessibility audit (axe, Lighthouse) flags
   `dialog-without-focusable-element` or `focus-trap-missing`
   depending on the tool.
2. **Esc does nothing.** Users expect Esc to close any modal — this
   one requires a manual `keydown` listener on `window`, which most
   implementations forget. Even when added, the listener leaks across
   modal lifetimes if not torn down.
3. **No portal rendering.** The "modal" lives inside its parent's
   shadow tree, so a parent with `overflow: hidden` or a CSS
   `transform` becomes the modal's containing block — z-index
   stacking breaks, and the modal renders behind page chrome on
   record pages.
4. **`role="dialog"` without `aria-labelledby` is incomplete.**
   Screen readers announce "dialog" but no name. The handrolled
   version above sets a `<h2>` but doesn't link it via
   `aria-labelledby`, so VoiceOver / NVDA users hear "dialog, group"
   instead of "Delete Account, dialog".
5. **No `dismissOnEscape` semantics for `disableClose` use cases.**
   The official `LightningModal` lets you set `disableClose: true`
   to suppress Esc-to-close during async work; the handrolled version
   either always closes on Esc or never does — no middle ground
   without rewriting the keydown handler.

**Correct approach:** Use `LightningModal` from `lightning/modal`.
The base class provides focus trap, Esc-to-close (with `disableClose`
opt-out), portal rendering outside the parent shadow tree,
`aria-labelledby` wiring from the `lightning-modal-header` label,
SLDS Global Focus Guidelines, and a Promise-based close result.
Every one of the five issues above is solved by the platform — the
correct line count to maintain a custom modal is zero. The only
legitimate reason to build a custom dialog is if you're targeting an
org pinned below Winter '23 (when `lightning/modal` went GA), in
which case the documented migration path is `lightning/overlayLib`
in Aura with an LWC `<c:lwcContainer>` — not raw `slds-modal` CSS.
