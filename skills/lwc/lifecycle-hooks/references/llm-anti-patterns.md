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

**Why it happens:** `if:true` and `if:false` dominated LWC documentation and Stack Overflow answers for years. LLMs reproduce them despite the guide's position: they "are no longer recommended. They may be deprecated and removed in the future. Use `lwc:if`, `lwc:elseif`, and `lwc:else` instead" (`lwc_guide reference-directives` L19500), and chained `if:true`/`if:false` "are not as performant nor as lightweight" than the `lwc:` directives (L19501). Note the guide says *not recommended*, not *removed* — existing `if:true` still compiles.

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

---

## Anti-Pattern 7: Marking a lifecycle hook `async` so it can `await`

**What the LLM generates:**

```javascript
async connectedCallback() {
    this.record = await getRecord({ recordId: this.recordId });
    this.ready = true;
}

async disconnectedCallback() {
    await this.flushPendingEdits();
    window.removeEventListener('resize', this._handler);
}
```

**Why it happens:** `async`/`await` is the default idiom for asynchronous JavaScript, and marking the enclosing function `async` is the mechanical way to use it. Nothing in the syntax signals that the caller is a framework that will not wait. The guide is explicit: "`connectedCallback()` and `disconnectedCallback()` are synchronous. The framework doesn't await a promise that's returned from a lifecycle hook. If you mark a hook as `async`, code after an `await` runs after the framework moves on, which causes unpredictable order of execution relative to rendering, parent and child callbacks, and event handlers" (`lwc_guide create-lifecycle-hooks-dom` L4117). The `disconnectedCallback` case is the dangerous one — the `removeEventListener` above runs after the element is already detached.

**Correct pattern:**

```javascript
connectedCallback() {
    this.loadRecord();                                  // fire, do not await
    this._handler = this.handleResize.bind(this);
    window.addEventListener('resize', this._handler);
}

disconnectedCallback() {
    window.removeEventListener('resize', this._handler); // synchronous, runs before detach
    this.flushPendingEdits();                            // best-effort, not awaited
}

async loadRecord() {
    try {
        this.record = await getRecord({ recordId: this.recordId });
    } catch (error) {
        this.error = error;
    }
}
```

"To run async work from a lifecycle hook, call a separate async method from the synchronous hook" (L4118).

**Detection hint:** the token `async` immediately before `connectedCallback`, `disconnectedCallback`, `renderedCallback`, or `errorCallback`. Rule **L7** in `scripts/check_lwc_lifecycle.py`.

---

## Anti-Pattern 8: Treating `render()` as a lifecycle notification

**What the LLM generates:**

```javascript
render() {
    console.log('component is rendering');
    this.updateChartData();          // side effect
    super.render();                  // and no return value
}
```

**Why it happens:** the name matches React's `render()`, and the LWC docs list it alongside the hooks, so an assistant reaches for it as "the hook that tells me a render is happening". It is not one: "The `render()` method is not technically a lifecycle hook. It is a protected method on the `LightningElement` class. A hook usually tells you that something happened… The `render()` method must exist on the prototype chain" (`lwc_guide create-lifecycle-hooks-render` L4153). Its single documented job is to choose a template, and "The method must return a valid HTML template" (L4150) — specifically a template reference, "the imported default export from an HTML file" (`create-render` L1573). Returning nothing, or performing side effects here, breaks rendering rather than observing it.

**Correct pattern:**

```javascript
import compact from './caseWatchList.html';
import detail from './caseWatchListDetail.html';

render() {
    return this.mode === 'detail' ? detail : compact;   // choose, do nothing else
}

renderedCallback() {
    if (this.hasRendered) return;                        // observe here instead
    this.hasRendered = true;
    this.updateChartData();
}
```

And prefer not to fork at all: "we recommend using the `lwc:if|elseif|else` directives to render nested templates conditionally instead" (`create-render` L1572). If you do fork, each extra template needs its own matching `.css` filename (L1579).

**Detection hint:** a `render()` body containing anything other than a `return` of an imported template reference, or a `render()` with no `return` at all.
