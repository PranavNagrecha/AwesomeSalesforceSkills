# LLM Anti-Patterns — LWC Conditional Rendering

Common mistakes AI coding assistants make when generating or advising on LWC conditional rendering.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating `if:true={...}` In A Modern-API Template

**What the LLM generates:**

```html
<template if:true={isLoading}>
  <lightning-spinner></lightning-spinner>
</template>
<template if:false={isLoading}>
  <c-ready-view record={record}></c-ready-view>
</template>
```

**Why it happens:** Training-data bias — `if:true` / `if:false` dominated LWC samples for years before `lwc:if` landed. LLMs default to the older idiom even when the target component is clearly on a recent API version and the surrounding code already uses `lwc:if` elsewhere.

**Correct pattern:**

```html
<template lwc:if={isLoading}>
  <lightning-spinner></lightning-spinner>
</template>
<template lwc:else>
  <c-ready-view record={record}></c-ready-view>
</template>
```

**Detection hint:** grep for `if:true=` or `if:false=` — both are on Salesforce's "no longer recommended, may be removed" list.

---

## Anti-Pattern 2: Putting Template Expressions In `lwc:if`

**What the LLM generates:**

```html
<template lwc:if={isReady && !hasError}>
  <c-ready-view></c-ready-view>
</template>
<template lwc:if={items.length > 0}>
  <c-list items={items}></c-list>
</template>
```

**Why it happens:** React/Vue bleed — those frameworks allow richer in-template JS. LWC intentionally restricts template expressions to property and member access. The template will not compile.

**Correct pattern:**

```html
<template lwc:if={canShowReadyView}>
  <c-ready-view></c-ready-view>
</template>
<template lwc:if={hasItems}>
  <c-list items={items}></c-list>
</template>
```

```javascript
get canShowReadyView() {
    return this.isReady && !this.hasError;
}
get hasItems() {
    return (this.items?.length ?? 0) > 0;
}
```

**Detection hint:** any `&&`, `||`, `!==`, `>`, `<`, or `.length` inside `lwc:if={...}`. The skill checker flags these automatically.

---

## Anti-Pattern 3: Expecting State To Survive A `lwc:if` False → True Transition

**What the LLM generates:**

```javascript
// Component keeps a filter panel with partial user input.
// The LLM advises: "Use lwc:if to show/hide the panel."
// User then reports their typed text disappears every time they close and reopen.
```

**Why it happens:** The LLM treats `lwc:if` as a visibility toggle (like CSS `display`), missing that it unmounts the subtree and discards child state. This is a core mental-model error carried over from other frameworks where conditional rendering preserves state by default.

**Correct pattern:** If state must survive the toggle, keep the subtree mounted and hide with CSS:

```html
<div class={filterPanelClass}>
  <c-advanced-filter-panel></c-advanced-filter-panel>
</div>
```

```javascript
get filterPanelClass() {
    return this.isOpen ? 'filter-panel' : 'filter-panel slds-hide';
}
```

Use `lwc:if` only when reset-on-close is the intended behavior.

**Detection hint:** review any `lwc:if` gating a form, wizard step, drawer, or panel and ask whether a user's partial input should survive toggling. If yes, switch to CSS hide.

---

## Anti-Pattern 4: Accessing `this.refs.x` Inside `connectedCallback` Of A Component Whose Top-Level Branch May Be False

**What the LLM generates:**

```javascript
connectedCallback() {
    // Refs are not yet populated, AND the ref may live inside a lwc:if that is currently false.
    this.refs.input.focus();
}
```

**Why it happens:** The LLM confuses `connectedCallback` (fires when the component is inserted) with `renderedCallback` (fires after the DOM is rendered), and does not account for `lwc:if` unmounting the ref's target element when the branch is false.

**Correct pattern:**

```javascript
renderedCallback() {
    // Null-check — the ref is undefined if the branch is currently false.
    const input = this.refs?.input;
    if (input && !this._focused) {
        input.focus();
        this._focused = true;
    }
}
```

**Detection hint:** any `this.refs.*` access inside `connectedCallback`, or any unconditional `.focus()` / `.scrollIntoView()` on a ref without a null check.

---

## Anti-Pattern 5: Writing Two `lwc:if` Blocks As A Fake Else

**What the LLM generates:**

```html
<template lwc:if={isLoggedIn}>
  <c-dashboard></c-dashboard>
</template>
<template lwc:if={isNotLoggedIn}>
  <c-login-prompt></c-login-prompt>
</template>
```

...with `get isNotLoggedIn() { return !this.isLoggedIn; }`. The LLM has the modern directive half-right but invents a negated getter instead of using `lwc:else`.

**Why it happens:** LLM completes the first `lwc:if` confidently, then defaults to the familiar "write another if with a negation" pattern rather than reaching for the chain primitive.

**Correct pattern:**

```html
<template lwc:if={isLoggedIn}>
  <c-dashboard></c-dashboard>
</template>
<template lwc:else>
  <c-login-prompt></c-login-prompt>
</template>
```

Drop the `isNotLoggedIn` getter entirely. `lwc:else` takes no expression and makes the exclusivity explicit in the template.

**Detection hint:** look for a negated getter (`isNot*`, `!this.*`) used as the sole condition on a second `lwc:if` block that immediately follows the positive one. Almost always means `lwc:else` is the intended primitive.
