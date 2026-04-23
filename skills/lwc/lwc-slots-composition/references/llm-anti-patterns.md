# LLM Anti-Patterns — LWC Slots Composition

Common mistakes AI coding assistants make when generating or reviewing LWC slot composition.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Putting `slot="name"` Inside The Child's Template

**What the LLM generates:**

```html
<!-- WRONG: child template -->
<template>
    <header>
        <slot name="header" slot="header"></slot>
    </header>
    <footer>
        <slot slot="footer"></slot>
    </footer>
</template>
```

**Why it happens:** LLMs see `slot="..."` in examples and conflate "naming a slot" with "placing the slot." They add it to the child's `<slot>` element for symmetry, not realizing the `slot` attribute on `<slot>` is interpreted as an assignment instruction, which is meaningless inside the child.

**Correct pattern:**

```html
<!-- Child template declares names -->
<template>
    <header><slot name="header"></slot></header>
    <footer><slot name="footer"></slot></footer>
</template>

<!-- Parent template assigns children -->
<c-child>
    <h2 slot="header">Title</h2>
    <button slot="footer">Save</button>
</c-child>
```

**Detection hint:** Search for `\bslot\s+[^>]*slot="` in `lwc/**/*.html` — a `<slot>` tag carrying both `name` and `slot` attributes is almost always a bug.

---

## Anti-Pattern 2: `::slotted()` Selectors In Shadow-DOM Child CSS

**What the LLM generates:**

```css
/* WRONG: child.css in a shadow-DOM component */
::slotted(h2) {
    font-size: 1.25rem;
    color: var(--lwc-colorTextDefault);
}
::slotted(.muted) {
    opacity: 0.6;
}
```

**Why it happens:** LLMs trained on open Web Components examples treat `::slotted()` as standard. They forget that LWC's shadow DOM intentionally does not support it.

**Correct pattern:** Style slotted content from the parent's CSS, or convert the child to light DOM. Inside the child, expose CSS custom properties as the documented styling hook.

```css
/* Parent styles what the parent owns */
c-child h2 { font-size: 1.25rem; }

/* Or in a light-DOM child, normal selectors just work */
```

**Detection hint:** `grep -RIn "::slotted" lwc/` — any hit in a component that is not declared as light DOM in `.js-meta.xml` is a finding.

---

## Anti-Pattern 3: Polling The DOM Instead Of Handling `slotchange`

**What the LLM generates:**

```javascript
// WRONG: polling in renderedCallback
renderedCallback() {
    const slot = this.template.querySelector('slot[name="actions"]');
    if (slot && slot.assignedNodes().length > 0) {
        this.hasActions = true;
    } else {
        this.hasActions = false;
    }
}
```

**Why it happens:** `renderedCallback` is the most commonly demonstrated lifecycle hook in training data, so LLMs reach for it even when an event-driven primitive exists.

**Correct pattern:**

```html
<slot name="actions" lwc:ref="actionsSlot" onslotchange={handleActionsSlotChange}></slot>
```

```javascript
handleActionsSlotChange() {
    const assigned = this.refs.actionsSlot.assignedNodes({ flatten: true });
    this.hasActions = assigned.some(
        (n) => n.nodeType !== Node.TEXT_NODE || n.textContent.trim().length > 0
    );
}
```

**Detection hint:** A `renderedCallback` that calls `querySelector('slot')` and sets a reactive boolean is the red flag — the right approach uses `onslotchange` in the template.

---

## Anti-Pattern 4: Using `<slot>` To Pass Structured Data

**What the LLM generates:**

```html
<!-- WRONG: parent serializing data into a slot -->
<c-record-viewer>
    <span slot="record">{recordJson}</span>
</c-record-viewer>
```

```javascript
// child tries to parse the slotted JSON
const slot = this.template.querySelector('slot[name="record"]');
const text = slot.assignedNodes()[0].textContent;
const record = JSON.parse(text);
```

**Why it happens:** LLMs see slots as a general "prop" mechanism and conflate them with Vue/React-style prop passing. They forget that slots carry DOM, not values.

**Correct pattern:**

```javascript
// child.js
import { api, LightningElement } from 'lwc';
export default class RecordViewer extends LightningElement {
    @api record;
}
```

```html
<c-record-viewer record={record}></c-record-viewer>
```

**Detection hint:** A `slot` paired with `JSON.parse`, `JSON.stringify`, or `textContent` reads in the child is almost always this mistake.

---

## Anti-Pattern 5: Case Mismatch Between Slot Declaration And Assignment

**What the LLM generates:**

```html
<!-- child template -->
<slot name="slotName"></slot>

<!-- parent -->
<c-child>
    <div slot="slot-name">Content</div>
</c-child>
```

**Why it happens:** LLMs sometimes auto-convert names to kebab-case for HTML attributes because that is the idiomatic casing for HTML; but slot names are string identifiers and must match exactly between declaration and assignment.

**Correct pattern:** Use kebab-case on both sides (recommended for HTML consistency), and match exactly:

```html
<!-- child -->
<slot name="slot-name"></slot>

<!-- parent -->
<c-child>
    <div slot="slot-name">Content</div>
</c-child>
```

**Detection hint:** Collect every `<slot name="...">` declaration and every `slot="..."` assignment across the pair of templates and diff the set. A mismatched name leaves the slot empty and the assigned element unrendered — no error is raised.
