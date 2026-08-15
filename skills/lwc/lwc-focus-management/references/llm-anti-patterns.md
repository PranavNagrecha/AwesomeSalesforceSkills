# LLM Anti-Patterns — LWC Focus Management

Mistakes AI assistants make specifically when writing focus code for Lightning
Web Components. The common cause is that the correct general-web answer is
*almost* correct in LWC — the shadow boundary changes one detail, and the detail
is not visible in the code.

---

## Anti-Pattern 1: `document.activeElement` as the focus-trap comparison

**What the LLM generates:**

```javascript
handleKeyDown(event) {
    if (event.key !== 'Tab') return;
    const focusable = [...this.template.querySelectorAll(FOCUSABLE)];
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
    }
}
```

**Why it happens:** this is the canonical focus-trap snippet. It is correct on
the open web, it appears in hundreds of accessibility articles, and nothing in
the LWC-specific parts of the code (`this.template.querySelectorAll`) signals
that the `document.activeElement` half needs to change too.

**Correct pattern:** shadow DOM retargets `document.activeElement` to the *host*
custom element, so the comparison evaluates `<c-my-modal> === <lightning-button>`
and is `false` every time. Use the `ShadowRoot`'s own view:

```javascript
const active = this.template.activeElement;
if (event.shiftKey && active === first) { … }
```

**Detection hint:** `document.activeElement` anywhere in a `.js` file under
`lwc/`. There is no legitimate use of it inside a component.

---

## Anti-Pattern 2: The focusable-elements selector from every accessibility blog

**What the LLM generates:**

```javascript
const FOCUSABLE =
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
const focusable = [...this.template.querySelectorAll(FOCUSABLE)];
```

**Why it happens:** it is *the* focusable-elements selector, it is correct HTML,
and it is what the training distribution contains. Recognising that it returns
zero matches requires knowing that `<lightning-input>` is a custom element whose
`<input>` lives in a shadow tree the query cannot enter.

**Correct pattern:** query the custom elements and let each focus itself. Every
relevant base component publishes a `focus()` method —
`lightning-input`'s is documented as "Sets focus on the input element."

```javascript
const FOCUSABLE_TAGS = [
    'lightning-input', 'lightning-textarea', 'lightning-combobox',
    'lightning-button', 'lightning-button-icon'
].join(',');

const focusable = [...this.template.querySelectorAll(FOCUSABLE_TAGS)]
    .filter((el) => !el.disabled);
```

**Detection hint:** a selector string containing bare `input` or `button` inside
a component whose template contains `lightning-`. The generated code will not
throw; it will find nothing.

---

## Anti-Pattern 3: Storing `document.activeElement` as "the opener"

**What the LLM generates:**

```javascript
@api open() {
    this._opener = document.activeElement;
    this._isOpen = true;
}

handleClose() {
    this._isOpen = false;
    Promise.resolve().then(() => this._opener?.focus?.());
}
```

**Why it happens:** "save the active element, restore it on close" is the textbook
restoration pattern and is correct without shadow DOM. The defensive `?.focus?.()`
is added because it is good hygiene — and it is what hides the failure.

**Correct pattern:** the stored value is the host component, not the button.
Custom elements without `tabindex` or `delegatesFocus` are not focusable, so the
restore call succeeds and does nothing, and focus lands on `<body>`.

Restoration belongs to the opener, which is the only component that can see its
own trigger:

```javascript
async handleOpen() {
    const result = await ConfirmModal.open({ label: 'Confirm' });
    this.handleResult(result);
    this.refs.openButton.focus();   // its own ref, its own shadow tree
}
```

**Detection hint:** the pair `_opener = document.activeElement` … `_opener.focus()`
in the same class, or any restoration logic living inside the overlay rather than
inside the thing that opened it.

---

## Anti-Pattern 4: Hand-rolling a modal that `lightning/modal` already implements

**What the LLM generates:** a complete custom modal — backdrop `div`, `role="dialog"`,
a focus trap, an `Escape` handler, first-element focus in `renderedCallback` — in
response to "build a confirmation dialog".

**Why it happens:** the request is for a dialog, a dialog is a well-known
component shape, and generating one from primitives is a satisfying complete
answer. `lightning/modal` is a Salesforce-specific module that has to be recalled
rather than derived.

**Correct pattern:** import `LightningModal` and compose
`lightning-modal-header` / `-body` / `-footer`. It has a documented initial-focus
rule (multi-step subtitle → header title → "the first interactive element in the
modal body" → close button), maintained trapping, and `Escape` handling. What
remains yours is restoration in the opener — the one part the module cannot do,
because it cannot see your trigger.

Hand-rolling is defensible when the surface genuinely is not a modal — an inline
disclosure panel, a popover. Say which it is, and why, rather than defaulting.

**Detection hint:** `role="dialog"` plus a hand-written `Tab` handler in a bundle
that has no `import LightningModal from 'lightning/modal'`.

---

## Anti-Pattern 5: `.focus()` in `connectedCallback`

**What the LLM generates:**

```javascript
connectedCallback() {
    this.template.querySelector('lightning-input')?.focus();
}
```

**Why it happens:** `connectedCallback` is the LWC analogue of `componentDidMount`,
and `componentDidMount` runs after the DOM exists. The names line up and the
semantics do not.

**Correct pattern:** "You can't access child elements from the callbacks because
they don't exist yet." The query returns `null`, the optional chain swallows it,
and nothing happens. Move it to `renderedCallback` behind a flag, or schedule it
after the state change:

```javascript
renderedCallback() {
    if (this._focusPending) {
        this._focusPending = false;
        this.refs.firstField?.focus();
    }
}
```

**Detection hint:** any `querySelector`, `this.refs`, or `.focus()` inside
`connectedCallback`. The optional chaining that usually accompanies it is what
makes the bug silent.

---

## Anti-Pattern 6: Unguarded `renderedCallback` focus

**What the LLM generates:**

```javascript
renderedCallback() {
    this.template.querySelector('[data-focus="first"]').focus();
}
```

**Why it happens:** `renderedCallback` was correctly identified as the hook where
the DOM exists, and the guard is a second, separate piece of knowledge — that the
hook fires after *every* render, not once.

**Correct pattern:** the Developer Guide prescribes a boolean field: "To use this
hook to perform a one-time operation, use a boolean field like `hasRendered`…".
For focus, flag per transition rather than per lifetime, so focus moves again the
next time the surface opens.

Use a plain field, never `@track` and never an `@api` property — the same page
warns that **"Updating the state of your component in `renderedCallback()` can
cause an infinite loop."**

**Detection hint:** a `.focus()` call in `renderedCallback` with no enclosing
`if`. Symptom in the wild: "typing in the form jumps back to the first field."

---

## Anti-Pattern 7: `lwc:ref` inside `for:each`

**What the LLM generates:**

```html
<template for:each={rows} for:item="row">
    <li key={row.id}>
        <lightning-button-icon
            lwc:ref="removeButton"
            onclick={handleRemove}></lightning-button-icon>
    </li>
</template>
```

**Why it happens:** refs are the documented modern way to address an element, and
generalising "use a ref" to every element is the obvious move. The loop
restriction is a specific carve-out.

**Correct pattern:** "If you place `lwc:ref` in a `for:each` or `iterator:*` loop,
the template compiler throws an error." Refs are also unavailable with
`lwc:dom="manual"`. Inside iterations, use a `data-*` attribute and
`this.template.querySelector`. Store the *selector* rather than the element when
the target has to survive a re-render — the node you captured before the render
does not exist after it.

**Detection hint:** `lwc:ref` and `for:each` in the same template subtree. This
one at least fails loudly, at build time.

---

## Anti-Pattern 8: `aria-live` on a node whose text never changes identity

**What the LLM generates:**

```javascript
this.statusMessage = `${this.items.length} items remaining.`;
```

against a permanently rendered `<div aria-live="polite">{statusMessage}</div>`.

**Why it happens:** assigning the message is the complete implementation of
"announce it", and the requirement that the *text must change* for a screen
reader to speak is a screen-reader behaviour rather than a DOM one.

**Correct pattern:** blank the region, then set on the next microtask, so two
consecutive identical messages both announce:

```javascript
announce(message) {
    this.announcement = '';
    Promise.resolve().then(() => {
        this.announcement = message;
    });
}
```

And choose urgency deliberately: `role="alert"` implies `aria-live="assertive"`
and interrupts — correct for validation failures, hostile for "3 records loaded".
`role="status"` implies `polite` and waits.

**Detection hint:** a direct assignment to a live-region property with no
intervening reset, or `role="alert"` on a region carrying progress messages.

---

## Anti-Pattern 9: `tabindex` as a tab-order control

**What the LLM generates:**

```html
<lightning-input tabindex="1" label="First"></lightning-input>
<lightning-input tabindex="2" label="Second"></lightning-input>
```

**Why it happens:** positive `tabindex` is legal HTML, it is what "control the tab
order" means outside a framework, and the request usually is exactly "make it tab
in this order".

**Correct pattern:** LWC supports only `0` and `-1`; the template compiler
rejects the rest. That is the framework enforcing the accessibility rule rather
than recommending it. Tab order should be DOM order — if the desired order
differs from the DOM, reorder the DOM. Reserve `-1` for elements that must be
focusable programmatically but never by `Tab`: error summaries, headings you move
focus to, off-screen live regions.

**Detection hint:** any `tabindex` whose value is not `0` or `-1`. Also flag
`tabindex` co-occurring with `static delegatesFocus = true`, which the docs warn
"throws off the focus order".

---

## Anti-Pattern 10: A `jest.fn()` focus spy presented as a focus test

**What the LLM generates:**

```javascript
const input = element.shadowRoot.querySelector('lightning-input');
input.focus = jest.fn();
element.openPanel();
await Promise.resolve();
expect(input.focus).toHaveBeenCalled();
```

**Why it happens:** spying on a method is the standard way to test that a method
was called, and the assertion is true. It is just not the assertion that matters.

**Correct pattern:** assert the *identity* of the focused element, so the test
fails when focus goes to the wrong place rather than merely to nowhere:

```javascript
expect(element.shadowRoot.activeElement).toBe(expectedElement);
```

And say what the test cannot prove. jsdom has no layout, no real sequential focus
navigation, and no faithful `delegatesFocus`, so a green suite is evidence about
intent, not about tab order. The manual keyboard walk is not optional, and an
answer that presents the Jest suite as the accessibility gate is wrong in a way
that costs a user rather than a build.

**Detection hint:** `toHaveBeenCalled()` on a `focus` spy with no accompanying
`activeElement` assertion, or a testing recommendation that stops at Jest.

---

## Anti-Pattern 11: Reaching into a child component's shadow tree

**What the LLM generates:**

```javascript
this.template
    .querySelector('c-address-form')
    .shadowRoot.querySelector('lightning-input')
    .focus();
```

**Why it happens:** it is the shortest path from "I have the child" to "I have
the input", `shadowRoot` is a real property, and in a dev console it appears to
work.

**Correct pattern:** the child owns its internals. Either it declares
`static delegatesFocus = true`, so `child.focus()` delegates to the first
focusable element inside, or it publishes an explicit contract:

```javascript
export default class AddressForm extends LightningElement {
    /** Focuses the first editable line. Part of this component's public API. */
    @api
    focus() {
        this.refs.line1?.focus();
    }
}
```

The parent then calls `this.refs.addressForm.focus()` and stays correct when the
child's internal markup changes.

**Detection hint:** `.shadowRoot.` appearing in component code rather than in a
test. In production code it is a coupling to another component's private
structure; in a Jest test against your own component it is normal.
