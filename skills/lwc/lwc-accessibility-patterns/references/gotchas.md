# Gotchas — LWC Accessibility Patterns

## Gotcha 1: ARIA IDREF Attributes Silently Break Across Shadow Boundaries

**What happens:** `aria-controls`, `aria-owns`, `aria-activedescendant`, and `aria-describedby` all take an IDREF value — an `id` string that the browser resolves in the DOM. In standard HTML this works globally. In LWC with Lightning Locker or Lightning Web Security, each component has its own shadow root. The browser resolves the IDREF only within the current shadow scope. If the referenced `id` belongs to an element inside a child component's shadow, the attribute resolves to nothing and the ARIA relationship is silently absent. No browser warning, no console error, no runtime exception.

**When it occurs:** Any time the interactive controller (e.g., a button with `aria-controls`) and the target region (e.g., an expandable panel) are in different LWC component files. Common cases: disclosure buttons controlling panels in child components, comboboxes pointing to listboxes in sibling components, tab lists referencing tab panels rendered by a loop over child components.

**How to avoid:** Keep IDREF-linked elements in the same component template. When the architecture genuinely requires separate components, replace IDREF relationships with state management: expose `@api` methods on the child for `open()`, `close()`, and `focus()`, and manage `aria-expanded` or `aria-selected` state attributes on the controller element in the parent.

---

## Gotcha 2: `this.template.querySelector()` Cannot Penetrate Child Component Shadow Roots

**What happens:** A parent component tries to call `.focus()` on an element inside a child LWC component using `this.template.querySelector('c-child-component input')`. The selector returns `null` even though the input visually exists in the page.

**When it occurs:** Any focus management code in a parent that tries to query inside a child component's DOM. This is the correct and intended shadow encapsulation behavior, but it surprises developers accustomed to standard querySelector traversal.

**How to avoid:** The child component must expose a public `@api` method that internally calls `this.template.querySelector('input').focus()`. The parent calls `this.template.querySelector('c-child-component').focusInput()` instead of trying to reach the input directly. For LWC components using `lwc:ref`, use `this.refs.childRef.focusMethod()` for cleaner syntax available from API version 59.0+.

---

## Gotcha 3: `aria-live` Regions Must Be In The DOM Before Content Changes

**What happens:** A developer conditionally renders the live region with `if:true={hasResults}`, then sets the message text after results load. The announcement never fires. Alternatively, they render the live region and immediately set the text in the same JS microtask — the browser only announces changes to a live region after it has been observed, so rapid insert-and-fill also fails.

**When it occurs:** Any time `aria-live` is wrapped in a conditional template directive, or when the live region text is set in the same synchronous operation that inserts the region into the DOM.

**How to avoid:** Always render the `aria-live` container unconditionally. Initialise its text content to an empty string. Update the text only after the async operation completes. If you need to clear the message and set a new one in sequence, clear it in one microtask and set the new message in a subsequent one so the browser registers the change:

```javascript
// Clear first so screen readers pick up the new value as a change
this.statusMessage = '';
// eslint-disable-next-line @locker/locker/distorted-promise-resolve
Promise.resolve().then(() => {
    this.statusMessage = `${this.results.length} results loaded`;
});
```

---

## Gotcha 4: `renderedCallback` Runs On Every Rerender — Focus Calls Need A Guard

**What happens:** A developer places a `focus()` call inside `renderedCallback` to move focus to a newly visible element. It works on first render but then fires again on every property change, stealing focus from wherever the user is typing or navigating.

**When it occurs:** Any `focus()` call in `renderedCallback` without a flag to track whether focus has already been placed for the current interaction.

**How to avoid:** Use a boolean flag on the component instance. Set it to `true` before the state change that should trigger focus, check it in `renderedCallback`, call `.focus()` once, then immediately reset the flag to `false`.

```javascript
connectedCallback() {
    this._focusOnRender = false;
}

openPanel() {
    this._focusOnRender = true;
    this.isOpen = true;
}

renderedCallback() {
    if (this._focusOnRender) {
        this._focusOnRender = false;
        const target = this.template.querySelector('[data-focus-first]');
        if (target) target.focus();
    }
}
```

---

## Gotcha 5: `role="button"` Without `tabindex="0"` Is Unreachable By Keyboard

**What happens:** A developer adds `role="button"` to a `div` or `span` to fix screen reader announcements. Keyboard testing reveals the element is skipped entirely during Tab navigation because divs have no native tab stop. Alternatively, the developer adds `tabindex="0"` but only adds `onclick`. Space key press does nothing because browsers do not synthesize a click event for Space on non-native buttons.

**When it occurs:** Any custom interactive element that is not a native `<button>`, `<a href>`, `<input>`, or `<select>`. Common cases: custom toggle tiles, clickable card surfaces, icon-triggered inline actions.

**How to avoid:** A fully accessible custom button requires all three: `role="button"`, `tabindex="0"`, and a `keydown` handler that calls the action on both Enter and Space. Enter alone is not sufficient because native buttons also fire on Space, and users who have learned that pattern will expect it.

```html
<div
    role="button"
    tabindex="0"
    onclick={handleAction}
    onkeydown={handleButtonKey}
>Activate</div>
```

```javascript
handleButtonKey(event) {
    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        this.handleAction();
    }
}
```

The `event.preventDefault()` on Space is required to prevent the page from scrolling, which is the default browser behavior for Space outside a text input.
