# LLM Anti-Patterns — LWC Accessibility

Common mistakes AI coding assistants make when generating or advising on LWC accessibility.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using div and span with click handlers instead of semantic interactive elements

**What the LLM generates:**

```html
<div class="clickable-card" onclick={handleSelect}>
    <span>{record.Name}</span>
</div>
```

**Why it happens:** LLMs optimize for visual output and use generic containers with click handlers. This creates elements that are invisible to keyboard users and screen readers.

**Correct pattern:**

```html
<button class="clickable-card" onclick={handleSelect}>
    <span>{record.Name}</span>
</button>
```

Or if a non-button semantic is needed:

```html
<div class="clickable-card" role="button" tabindex="0"
     onclick={handleSelect} onkeydown={handleKeydown}>
    <span>{record.Name}</span>
</div>
```

**Detection hint:** `onclick=` on `<div>` or `<span>` elements without `role="button"` and `tabindex`.

---

## Anti-Pattern 2: Adding redundant aria-label on elements that already have visible text

**What the LLM generates:**

```html
<lightning-button label="Save" aria-label="Save button"></lightning-button>
```

**Why it happens:** LLMs over-apply ARIA attributes as a "safety" measure. Screen readers already use the `label` attribute of base components, so the `aria-label` creates duplicate announcements.

**Correct pattern:**

```html
<lightning-button label="Save"></lightning-button>
```

Use `aria-label` only when there is no visible text or when the visible text is ambiguous (e.g., an icon-only button).

**Detection hint:** `aria-label` on `lightning-button`, `lightning-input`, or other base components that already have a `label` attribute with the same or similar text.

---

## Anti-Pattern 3: Building a custom modal without focus trapping

**What the LLM generates:**

```html
<template lwc:if={showModal}>
    <div class="slds-modal slds-fade-in-open">
        <div class="slds-modal__container">
            <!-- No focus management -->
            <lightning-input label="Name" value={name}></lightning-input>
            <lightning-button label="Close" onclick={closeModal}></lightning-button>
        </div>
    </div>
    <div class="slds-backdrop slds-backdrop_open"></div>
</template>
```

**Why it happens:** LLMs produce visually correct modal markup using SLDS classes but omit focus trapping, initial focus placement, and Escape key handling. Use `LightningModal` instead.

**Correct pattern:**

```javascript
import LightningModal from 'lightning/modal';

export default class MyModal extends LightningModal {
    handleClose() {
        this.close('cancelled');
    }
}
```

`LightningModal` handles focus trap, Escape key, and return-to-trigger focus automatically.

**Detection hint:** `slds-modal` class in HTML template without `LightningModal` base class in the JS file.

---

## Anti-Pattern 4: Using aria-hidden="true" on interactive or informational content

**What the LLM generates:**

```html
<div aria-hidden="true">
    <lightning-input label="Email" value={email}></lightning-input>
</div>
```

**Why it happens:** LLMs sometimes apply `aria-hidden` to hide content from screen readers when they mean to hide it visually, or they copy it from decorative icon patterns and apply it too broadly.

**Correct pattern:**

To hide visually but keep accessible: use the SLDS `slds-assistive-text` class.
To hide from screen readers only: use `aria-hidden="true"` only on purely decorative elements.
To hide both: use `lwc:if` to remove from the DOM entirely.

```html
<!-- Decorative icon — ok to hide from screen reader -->
<lightning-icon icon-name="utility:info" aria-hidden="true"></lightning-icon>

<!-- Input must NEVER be aria-hidden -->
<lightning-input label="Email" value={email}></lightning-input>
```

**Detection hint:** `aria-hidden="true"` on or around `lightning-input`, `lightning-button`, `lightning-combobox`, or any interactive element.

---

## Anti-Pattern 5: Missing labels on icon-only buttons

**What the LLM generates:**

```html
<lightning-button-icon icon-name="utility:delete" onclick={handleDelete}>
</lightning-button-icon>
```

**Why it happens:** The code looks complete visually — the icon conveys meaning to sighted users. LLMs skip the `alternative-text` attribute because the icon name seems self-documenting.

**Correct pattern:**

```html
<lightning-button-icon
    icon-name="utility:delete"
    alternative-text="Delete record"
    onclick={handleDelete}>
</lightning-button-icon>
```

**Detection hint:** `<lightning-button-icon` without `alternative-text` attribute.

---

## Anti-Pattern 6: Not managing focus after dynamic content changes

**What the LLM generates:**

```javascript
handleSave() {
    saveRecord().then(() => {
        this.showSuccess = true; // Success message appears but focus stays on Save button
    });
}
```

**Why it happens:** LLMs handle the data flow but ignore that screen reader users will not know new content appeared unless focus is moved to it or a live region announces it.

**Correct pattern:**

```javascript
handleSave() {
    saveRecord().then(() => {
        this.showSuccess = true;
        // Move focus to the success message or use a live region
        Promise.resolve().then(() => {
            this.template.querySelector('.success-message')?.focus();
        });
    });
}
```

```html
<div class="success-message" tabindex="-1" role="status" lwc:if={showSuccess}>
    Record saved successfully.
</div>
```

**Detection hint:** Dynamic content toggled via boolean flag with no subsequent `focus()` call or `role="status"` / `role="alert"` on the container.
