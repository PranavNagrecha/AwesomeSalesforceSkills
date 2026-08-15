# Gotchas — LWC Focus Management

Focus failures specific to Lightning Web Components. Grounded in the Lightning
Web Components Developer Guide and the Lightning Component Reference (Summer '26,
API 67.0).

The shared property of nearly every item below: **nothing throws.** `.focus()` on
a non-focusable element returns `undefined`. A comparison that can never be true
just evaluates to `false`. A query that matches nothing returns an empty
`NodeList`. Broken focus code and working focus code have identical runtime
signatures, which is why this list exists and why keyboard testing is not
optional.

---

## Gotcha 1: `document.activeElement` Retargets to the Host

**What happens:** a focus trap is written, reviewed, merged, and does nothing.
`Tab` walks straight out of the modal into the page behind it.

Shadow DOM retargeting means that when focus is on a control inside a component's
shadow tree, `document.activeElement` reports the *host* custom element, not the
control. So:

```javascript
if (document.activeElement === last) { … }   // never true
```

evaluates `<c-my-modal> === <lightning-button>`, which is `false` every time. The
trap's guard clause never fires, and because a guard that never fires produces no
output, there is nothing to notice.

**When it occurs:** in every hand-rolled focus trap ported from a non-shadow-DOM
codebase, which is most of them — the pattern is enormously represented in
general web tutorials where it is correct.

**How to avoid:** use the `ShadowRoot`'s own view, which is scoped to your
component:

```javascript
const active = this.template.activeElement;
if (active === last) { … }
```

Treat `document.activeElement` in a component bundle as a defect on sight. The
same applies to storing it: `this._opener = document.activeElement` stores a host
element (see Gotcha 8).

---

## Gotcha 2: `querySelectorAll('input, button')` Finds Nothing in a Base-Component Form

**What happens:** `focusable[0]` is `undefined`, and either the handler throws a
`TypeError` on `.focus()` or an optional chain swallows it and the trap silently
does nothing.

`this.template.querySelector()` reaches into *this* component's shadow tree and
stops there. A `<lightning-input>` in your template is a single element from your
side; the `<input>` it renders lives inside its own shadow tree, which your query
cannot cross. The classic focusable-elements selector —
`'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'` —
therefore matches zero elements in a form built entirely from base components.

**When it occurs:** the moment a form uses `lightning-input` rather than raw
HTML, which in Lightning Experience is essentially always.

**How to avoid:** enumerate the custom elements and let each focus itself. Every
relevant base component exposes a documented `focus()` — `lightning-input`'s is
"Sets focus on the input element."

```javascript
const FOCUSABLE_TAGS = [
    'lightning-input',
    'lightning-textarea',
    'lightning-combobox',
    'lightning-button',
    'lightning-button-icon'
].join(',');

const focusable = [...this.template.querySelectorAll(FOCUSABLE_TAGS)]
    .filter((el) => !el.disabled);
```

Maintaining that list is a real cost, and it is one more argument for
`lightning/modal` over a hand-rolled trap.

---

## Gotcha 3: `.focus()` Before Render Is a Silent No-op

**What happens:** focus code in `connectedCallback` does nothing, and the
component behaves as though the call were never written.

The Developer Guide is explicit about `connectedCallback`: "You can't access
child elements from the callbacks because they don't exist yet." A
`this.template.querySelector(...)` there returns `null`, and `null?.focus()` is a
no-op. With `this.refs`, the same shape: "If you call `this.refs` for a
nonexistent ref, it returns `undefined`."

**When it occurs:** whenever "focus the first field when the component loads" is
implemented in the hook whose name suggests "when the component loads".

**How to avoid:** move it to `renderedCallback`, behind a flag (Gotcha 4), or
schedule it after the state change that causes the render:

```javascript
this.isOpen = true;
Promise.resolve().then(() => this.refs.firstField?.focus());
```

`connectedCallback` also "can fire more than one time. For example, if you remove
an element and then insert it into another position, such as when you reorder a
list, the hook fires several times" — so even code that appears to work there is
running more often than the author expects.

---

## Gotcha 4: Unguarded `renderedCallback` Focus Eats Keystrokes

**What happens:** the user types into the second field, a re-render fires, focus
snaps back to the first field, and the character they typed lands somewhere they
did not intend. It reads as an input bug, not a focus bug.

`renderedCallback` runs after *every* render — "A component is usually rendered
many times during the lifespan of an application" — and it "flows from child to
parent". Any unconditional `.focus()` there re-fires on every reactive change.

**When it occurs:** as soon as the component has any other reactive state, which
is usually the sprint after the focus code was written and tested in isolation.

**How to avoid:** the documented one-time-operation pattern:

> "To use this hook to perform a one-time operation, use a boolean field like
> `hasRendered` to track whether `renderedCallback()` has been executed. The
> first time `renderedCallback()` executes, perform the one-time operation and
> set `hasRendered = true`. If `hasRendered = true`, don't perform the
> operation."

For focus specifically, a flag *per transition* is better than a
render-once flag, because focus needs to move again on the next open:

```javascript
open() {
    this._focusPending = true;   // set when the transition happens
}

renderedCallback() {
    if (this._focusPending) {
        this._focusPending = false;
        this.refs.firstField?.focus();
    }
}
```

Use a plain field, not `@track` and not an `@api` property. The same page warns
that **"Updating the state of your component in `renderedCallback()` can cause an
infinite loop"** — a non-reactive flag is safe precisely because assigning to it
does not schedule another render.

---

## Gotcha 5: `lwc:ref` Is a Compile Error Inside `for:each`

**What happens:** the build fails with a template compiler error, on the exact
construct — "focus this row" — where a named reference would be most convenient.

The Developer Guide: "If you place `lwc:ref` in a `for:each` or `iterator:*`
loop, the template compiler throws an error." Refs are also unavailable with
`lwc:dom="manual"`.

**When it occurs:** in every dynamic list — the surface where focus management
matters most, because rows appear and disappear underneath the user.

**How to avoid:** address rows by `data-*` attribute and query them:

```html
<template for:each={items} for:item="item">
    <li key={item.id}>
        <lightning-button-icon
            data-remove-id={item.id}
            onclick={handleRemove}></lightning-button-icon>
    </li>
</template>
```

```javascript
this.template.querySelector(`[data-remove-id="${nextId}"]`)?.focus();
```

Store the *selector*, not the element, when you have to survive a re-render: the
element you held a reference to before the render no longer exists after it.

---

## Gotcha 6: `tabindex` Has Exactly Two Legal Values

**What happens:** `tabindex="1"` (or `2`, or `3`) is rejected at compile time.
Developers coming from hand-authored HTML expect positive values to be a
supported, if discouraged, way to control order.

LWC supports only `0` and `-1`. `tabindex="0"` "means that the element focuses in
standard sequential keyboard" navigation; `tabindex="-1"` "removes the element
from sequential keyboard navigation" while leaving it programmatically focusable.

**When it occurs:** when someone tries to fix a bad tab order by numbering
elements instead of by fixing the DOM order.

**How to avoid:** accept the constraint as the correct one. Tab order should be
DOM order; if it is not, the DOM is wrong. Use `-1` for elements that must be
focusable programmatically but never by `Tab` — error summaries, headings you
move focus to, off-screen live regions:

```html
<div lwc:ref="errorSummary" role="alert" tabindex="-1">…</div>
```

---

## Gotcha 7: `tabindex` Plus `delegatesFocus` Fight Each Other

**What happens:** a component sets `static delegatesFocus = true` *and* carries
`tabindex="0"`, and the tab order goes strange in ways that are hard to
reproduce — the component is sometimes a stop, sometimes not, and `Shift+Tab`
behaves differently from `Tab`.

The Developer Guide states it plainly: **"Don't use `tabindex` with
`delegatesFocus` because it throws off the focus order."**

**When it occurs:** when someone applies both fixes from two different sources —
`delegatesFocus` from the LWC docs, `tabindex="0"` from a general accessibility
article — without realising they are alternatives.

**How to avoid:** pick one. `delegatesFocus` for a component that wraps a
focusable control and should hand focus to it. `tabindex="0"` in the *parent*
template for a component that should itself be a tab stop:

> "By default, focus skips the component container and moves to the elements
> inside the component. To include the component itself in navigation, add
> `tabindex="0"` to the component tag in the parent template."

Note where that `tabindex` goes: on the tag as written by the parent, not inside
the component's own template.

---

## Gotcha 8: Calling `.focus()` on a Custom Element Usually Does Nothing

**What happens:** `this._opener?.focus?.()` runs cleanly and focus ends up on
`<body>`.

A custom element is an `HTMLElement`, so `focus` exists as a method and calling it
is legal. But an element with neither `tabindex` nor `delegatesFocus` is not
focusable, so the call has no effect. Optional chaining, added defensively, makes
this indistinguishable from success.

**When it occurs:** every time focus restoration is built on a stored
`document.activeElement` (Gotcha 1) — the stored value is a host element, and the
restore call is a no-op.

**How to avoid:** make the target focusable, deliberately, by one of the two
supported routes:

```javascript
// The child declares that it delegates focus inward.
export default class CoolButton extends LightningElement {
    static delegatesFocus = true;
}
```

```javascript
// Or the child exposes an explicit focus contract it controls.
export default class AddressForm extends LightningElement {
    @api
    focus() {
        this.refs.line1?.focus();
    }
}
```

Then state which one it is in the component's JSDoc, so callers do not have to
read the implementation to know whether `.focus()` on it means anything.

---

## Gotcha 9: `role="alert"` Announces on Insertion, Not on Change

**What happens:** a user submits an invalid form twice with the same errors. The
first submit announces; the second does not. The user believes nothing happened.

Live regions announce when their contents change. A `role="alert"` node that was
never removed and whose text is byte-identical has not changed, so some screen
readers stay silent.

**When it occurs:** on repeated failures of the same validation — the exact
scenario where the user most needs the feedback.

**How to avoid:** two mechanisms, and they are not interchangeable.

For a region that stays in the DOM, blank it and re-set on the next microtask:

```javascript
announce(message) {
    this.announcement = '';
    Promise.resolve().then(() => {
        this.announcement = message;
    });
}
```

For a summary that appears and disappears, wrap it in `lwc:if` so each occurrence
is a genuine insertion. That is doing real accessibility work, not just tidying
the template.

Also pick the right urgency: `role="alert"` carries an implicit
`aria-live="assertive"` and interrupts whatever the screen reader was saying —
right for validation failures, hostile for "3 records loaded". Use
`role="status"` (`aria-live="polite"`) for progress and confirmations.

---

## Gotcha 10: A Trap With No Exit Is a WCAG Failure

**What happens:** an accessibility audit flags the modal that was built *for*
accessibility. The trap works; there is no way out of it.

WCAG 2.1.2 No Keyboard Trap requires that a keyboard user can leave any component
they can enter. A `Tab` trap with a broken or missing `Escape` handler satisfies
the letter of "trap" and fails the standard.

The Lightning Component Reference makes the same point about `lightning/modal`'s
`disableClose`, which "Prevents closing the modal by normal means like the ESC
key, the close button, or `.close()`" — it should be a state lasting "less than 5
seconds", and while it is set you must "disable any processes or UI buttons that
might call `Modal.close()`".

**When it occurs:** when `Escape` is bound but the handler is placed after an
early `return` for non-`Tab` keys, which is a natural way to write the function
and puts the exit behind the trap.

**How to avoid:** handle `Escape` first, before any other key logic, and remove
the trap when the surface closes — usually by putting the whole trapping subtree
inside `lwc:if` so the listener leaves with the DOM.

---

## Gotcha 11: Deleting the Focused Element Drops Focus to `<body>`

**What happens:** the user removes a row with the keyboard and the next `Tab`
starts from the top of the page. In a long list this is a complete loss of place
and reads as the page having reloaded.

When the focused node is removed from the DOM, focus falls to the document body.
Nothing announces it, and sighted mouse users never see it.

**When it occurs:** in every editable list, and in wizards where a step's content
is replaced rather than navigated.

**How to avoid:** compute the successor *before* the mutation, while the
neighbours are still addressable, and store a selector rather than an element —
the element will be destroyed and re-created by the re-render.

```javascript
const next = this.items[index + 1];
const prev = this.items[index - 1];
this._focusAfterRender = next
    ? `[data-remove-id="${next.id}"]`
    : prev
        ? `[data-remove-id="${prev.id}"]`
        : '[data-focus="list-heading"]';
```

The final fallback matters: when the list empties, there is no row to focus, and
a heading carrying `tabindex="-1"` is the correct landing place.

---

## Gotcha 12: Jest Cannot Tell You the Tab Order Is Wrong

**What happens:** a full green focus suite ships a component that is unusable
with a keyboard.

`sfdx-lwc-jest` runs in jsdom. jsdom has no layout, no real sequential focus
navigation, and no faithful `delegatesFocus`. A test can assert that your code
*called* focus on the element you meant, and that is worth having. It cannot
assert that `Tab` from element A reaches element B in a real browser.

**When it occurs:** on any team that treats the Jest suite as the accessibility
gate.

**How to avoid:** write the Jest tests to assert *identity*, not invocation —

```javascript
expect(element.shadowRoot.activeElement).toBe(summary);
```

— because a `jest.fn()` focus spy passes just as happily when focus went to the
wrong element. Then do the manual keyboard walk anyway, forwards and backwards,
through every row of the focus map, and record the browser and screen reader used.
The suite catches regressions in intent; the walk catches everything else.
