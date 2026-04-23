# Examples — LWC Template Refs

## Example 1: Focus an input on modal open with a render guard

**Context:** An edit-contact modal opens in response to a row click. The UX requirement is that the email field receives focus the first time the modal renders, but not on every subsequent rerender (which would steal focus while the user is typing).

**Problem:** Reaching for `this.template.querySelector('.email-input')` in `connectedCallback` races the first render and can return `null`. Running focus on every `renderedCallback` steals focus during typing.

**Solution:**

```html
<!-- editContactModal.html -->
<template>
    <section lwc:if={isOpen}>
        <lightning-input
            lwc:ref="emailInput"
            label="Email"
            type="email"
            value={email}>
        </lightning-input>
    </section>
</template>
```

```js
// editContactModal.js
import { LightningElement, api } from 'lwc';

export default class EditContactModal extends LightningElement {
    @api email;
    isOpen = false;
    _focused = false;

    @api open() {
        this.isOpen = true;
        this._focused = false; // reset so the next open focuses again
    }

    renderedCallback() {
        if (this.isOpen && !this._focused) {
            // refs.emailInput may still be undefined if the lwc:if hasn't rendered yet
            this.refs.emailInput?.focus();
            if (this.refs.emailInput) {
                this._focused = true;
            }
        }
    }
}
```

**Why it works:** The ref is accessed after render, null-checked for the `lwc:if` case, and flipped to a one-shot flag so the user keeps focus during normal typing. The template declares intent ("this is the email input") without relying on a class name.

---

## Example 2: Validate a small set of required form fields via named refs

**Context:** A short onboarding form has exactly three required inputs: email, phone, and start date. The component's submit handler must call `reportValidity()` on each before calling Apex.

**Problem:** `querySelectorAll('lightning-input')` returns every input in the template — including optional ones added later — which silently broadens the validation contract. Class-based selectors require hunting across the HTML on every refactor.

**Solution:**

```html
<!-- onboardingForm.html -->
<template>
    <lightning-input lwc:ref="emailInput"     label="Email"      required></lightning-input>
    <lightning-input lwc:ref="phoneInput"     label="Phone"      required></lightning-input>
    <lightning-input lwc:ref="startDateInput" label="Start Date" type="date" required></lightning-input>
    <lightning-input                          label="Notes"></lightning-input>
    <lightning-button label="Submit" onclick={handleSubmit}></lightning-button>
</template>
```

```js
// onboardingForm.js
import { LightningElement } from 'lwc';

const REQUIRED_REFS = ['emailInput', 'phoneInput', 'startDateInput'];

export default class OnboardingForm extends LightningElement {
    handleSubmit() {
        const allValid = REQUIRED_REFS
            .map((name) => this.refs[name])
            .filter((el) => el) // null-safe for lwc:if branches
            .reduce((valid, el) => el.reportValidity() && valid, true);

        if (!allValid) {
            return;
        }
        this.submitToApex();
    }

    submitToApex() { /* ... */ }
}
```

**Why it works:** The required-field contract is visible in the JS as a named list. Non-required inputs (like "Notes") are explicitly excluded. The template names carry intent and will not silently drift if the HTML classes are renamed.

---

## Anti-Pattern: `lwc:ref` on the container of a `for:each` expecting per-row refs

**What practitioners do:** They try to tag each row in an iterator with a ref:

```html
<!-- WRONG — refs inside for:each are unsupported -->
<template for:each={contacts} for:item="contact">
    <lightning-input
        key={contact.Id}
        lwc:ref="contactRow"
        label={contact.Name}>
    </lightning-input>
</template>
```

Then reach for `this.refs.contactRow` expecting an array.

**What goes wrong:** The LWC docs explicitly state that `lwc:ref` must not appear inside `for:each` or `iterator` templates because the name collides for every iteration. Depending on the compiler version this either errors at build time or resolves to an unpredictable single element.

**Correct approach:** Use `data-*` attributes and event delegation, or `querySelectorAll`.

```html
<template for:each={contacts} for:item="contact">
    <lightning-input
        key={contact.Id}
        data-contact-id={contact.Id}
        label={contact.Name}
        onchange={handleRowChange}>
    </lightning-input>
</template>
```

```js
handleRowChange(event) {
    const row = event.target.closest('[data-contact-id]');
    const contactId = row.dataset.contactId;
    // ...
}
```

This keeps per-row identity in `data-*` where the platform supports it, and reserves `lwc:ref` for single owned elements.
