# LLM Anti-Patterns — LWC Template Refs

Common mistakes AI coding assistants make when generating or advising on `lwc:ref` usage. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Putting `lwc:ref` on elements inside `<template for:each=...>`

**What the LLM generates:**

```html
<template for:each={rows} for:item="row">
    <lightning-input
        key={row.Id}
        lwc:ref="rowInput"
        label={row.Name}>
    </lightning-input>
</template>
```

**Why it happens:** The LLM sees "I need a handle to each row's input" and reaches for the most modern idiom it knows. The LWC docs explicitly forbid this — the name would collide per iteration — but the LLM does not check the directive's scope rules.

**Correct pattern:**

```html
<template for:each={rows} for:item="row">
    <lightning-input
        key={row.Id}
        data-row-id={row.Id}
        label={row.Name}
        onchange={handleRowChange}>
    </lightning-input>
</template>
```

```js
handleRowChange(event) {
    const id = event.target.closest('[data-row-id]').dataset.rowId;
    // ...
}
```

**Detection hint:** Regex: search for `lwc:ref=` lines nested within the block between `<template for:each` / `<template iterator:` and the matching closing `</template>`.

---

## Anti-Pattern 2: Accessing `this.refs.x` in `connectedCallback`

**What the LLM generates:**

```js
connectedCallback() {
    this.refs.emailInput.focus(); // TypeError: Cannot read properties of undefined
}
```

**Why it happens:** The LLM treats `connectedCallback` like React's `componentDidMount`, which runs after the DOM is in place. In LWC, `connectedCallback` runs before the first render, so `this.refs` is undefined.

**Correct pattern:**

```js
_focused = false;

renderedCallback() {
    if (!this._focused) {
        this.refs.emailInput?.focus();
        this._focused = true;
    }
}
```

**Detection hint:** Search for `this.refs.` whose enclosing method is named `connectedCallback` or `constructor`.

---

## Anti-Pattern 3: Using a ref to drill into a child component's shadow DOM

**What the LLM generates:**

```js
// "Close the dropdown inside the child combobox"
this.refs.picker.template.querySelector('.dropdown').close();
// or
this.refs.picker._internalMethod();
```

**Why it happens:** The LLM conflates "I have a reference to the child's host" with "I can reach into the child's implementation." Shadow DOM encapsulation is invisible in training data that mixes React, Vue, and pre-shadow LWC.

**Correct pattern:** Expose an `@api` method on the child and call that.

```js
// child.js
@api
close() { this._open = false; }

// parent.js
this.refs.picker.close();
```

**Detection hint:** Flag any access chain of the form `this.refs.<name>.template.` or `this.refs.<name>._<anything>`.

---

## Anti-Pattern 4: Using `lwc:ref` alongside `lwc:if` without null-checking

**What the LLM generates:**

```html
<section lwc:if={isEditing}>
    <lightning-input lwc:ref="titleInput"></lightning-input>
</section>
```

```js
handleTitleChange() {
    const value = this.refs.titleInput.value; // throws when !isEditing
}
```

**Why it happens:** The LLM treats the ref as always present because it is declared in the template, ignoring that `lwc:if={false}` removes the element from the DOM entirely.

**Correct pattern:**

```js
handleTitleChange() {
    const input = this.refs.titleInput;
    if (!input) return;
    const value = input.value;
}
```

Or with optional chaining: `const value = this.refs.titleInput?.value;`.

**Detection hint:** Any `this.refs.<name>.<member>` where the template wraps `<name>` in an `lwc:if`, `lwc:elseif`, or `lwc:else` — flag missing null check.

---

## Anti-Pattern 5: Partial migration — keeping both `lwc:ref` and `this.template.querySelector('.email')` for the same element

**What the LLM generates:**

```html
<lightning-input lwc:ref="emailInput" class="email"></lightning-input>
```

```js
renderedCallback() {
    this.refs.emailInput.focus();
}
handleBlur() {
    const v = this.template.querySelector('.email').value;  // leftover
}
```

**Why it happens:** The LLM migrates the first access it sees and leaves other accesses on the old pattern, either because it was asked to "migrate one usage" or because it forgot to search the file.

**Correct pattern:** Finish the migration for that element. Use the ref in every access and drop the `class="email"` unless it is still needed for styling.

```js
handleBlur() {
    const v = this.refs.emailInput.value;
}
```

**Detection hint:** For each element declaring `lwc:ref="x"` with `class="y"`, search the paired JS file for both `this.refs.x` and `this.template.querySelector('.y')` — the presence of both signals an incomplete migration.
