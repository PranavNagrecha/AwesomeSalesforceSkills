# LLM Anti-Patterns — Lifecycle Hooks

Common mistakes AI coding assistants make when generating or advising on LWC lifecycle hooks.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Performing data fetches or heavy logic in the constructor

**What the LLM generates:**

```javascript
constructor() {
    super();
    this.loadData(); // Imperative Apex call in constructor
    this.template.querySelector('div'); // DOM not available yet
}
```

**Why it happens:** In many JS frameworks, the constructor is the natural place for initialization. LLMs carry that habit into LWC, where the component is not connected to the DOM and `@api` properties are not yet set during construction.

**Correct pattern:**

```javascript
constructor() {
    super();
    // Only initialize local state that does not depend on @api or DOM
    this.items = [];
}

connectedCallback() {
    this.loadData(); // Safe — component is in the DOM, @api props are set
}
```

**Detection hint:** Any method call or DOM query inside `constructor()` other than `super()` and simple property initialization.

---

## Anti-Pattern 2: Running DOM-dependent logic in connectedCallback instead of renderedCallback

**What the LLM generates:**

```javascript
connectedCallback() {
    const el = this.template.querySelector('.my-element');
    el.focus(); // el is null — DOM is not rendered yet
}
```

**Why it happens:** `connectedCallback` fires when the component enters the DOM tree, but the shadow DOM content has not rendered yet. LLMs confuse "connected" with "rendered."

**Correct pattern:**

```javascript
renderedCallback() {
    if (this._hasInitialized) return; // Guard against re-runs
    const el = this.template.querySelector('.my-element');
    if (el) {
        el.focus();
        this._hasInitialized = true;
    }
}
```

**Detection hint:** `this.template.querySelector` inside `connectedCallback`.

---

## Anti-Pattern 3: Missing the guard flag in renderedCallback causing infinite loops

**What the LLM generates:**

```javascript
renderedCallback() {
    this.template.querySelector('.chart').initialize(this.data);
    // Runs every render cycle — can trigger re-render and loop
}
```

**Why it happens:** `renderedCallback` fires after every render, including rerenders caused by reactive state changes. LLMs treat it like `componentDidMount` (fires once) rather than `componentDidUpdate` (fires repeatedly).

**Correct pattern:**

```javascript
_chartInitialized = false;

renderedCallback() {
    if (this._chartInitialized) return;
    const chartEl = this.template.querySelector('.chart');
    if (chartEl) {
        chartEl.initialize(this.data);
        this._chartInitialized = true;
    }
}
```

**Detection hint:** `renderedCallback` body that lacks a boolean guard or early-return check.

---

## Anti-Pattern 4: Adding event listeners in connectedCallback without removing them in disconnectedCallback

**What the LLM generates:**

```javascript
connectedCallback() {
    window.addEventListener('resize', this.handleResize);
}
// No disconnectedCallback cleanup
```

**Why it happens:** Cleanup is omitted because training data frequently shows only the setup side. Memory leaks are invisible in short-lived demos.

**Correct pattern:**

```javascript
connectedCallback() {
    this._resizeHandler = this.handleResize.bind(this);
    window.addEventListener('resize', this._resizeHandler);
}

disconnectedCallback() {
    window.removeEventListener('resize', this._resizeHandler);
}
```

**Detection hint:** `addEventListener` in `connectedCallback` without a matching `removeEventListener` in `disconnectedCallback`.

---

## Anti-Pattern 5: Using the deprecated `if:true` directive instead of `lwc:if`

**What the LLM generates:**

```html
<template if:true={isLoading}>
    <lightning-spinner></lightning-spinner>
</template>
```

**Why it happens:** `if:true` and `if:false` dominated LWC documentation and Stack Overflow answers for years. LLMs reproduce this pattern despite its deprecation in favor of `lwc:if`, `lwc:elseif`, and `lwc:else`.

**Correct pattern:**

```html
<template lwc:if={isLoading}>
    <lightning-spinner></lightning-spinner>
</template>
<template lwc:else>
    <slot></slot>
</template>
```

**Detection hint:** Regex `if:true=` or `if:false=` in HTML template files.

---

## Anti-Pattern 6: Treating connectedCallback as firing only once

**What the LLM generates:**

```javascript
connectedCallback() {
    this.subscription = subscribe(this.messageContext, CHANNEL, this.handler);
    // Assumes this runs exactly once per component lifetime
}
```

**Why it happens:** LLMs assume `connectedCallback` behaves like a singleton initializer. In reality, if a component is removed and re-inserted (e.g., behind `lwc:if`), `connectedCallback` fires again, causing duplicate subscriptions.

**Correct pattern:**

```javascript
connectedCallback() {
    if (!this.subscription) {
        this.subscription = subscribe(this.messageContext, CHANNEL, this.handler);
    }
}

disconnectedCallback() {
    unsubscribe(this.subscription);
    this.subscription = null;
}
```

**Detection hint:** `connectedCallback` that creates subscriptions, intervals, or event listeners without checking for existing ones.
