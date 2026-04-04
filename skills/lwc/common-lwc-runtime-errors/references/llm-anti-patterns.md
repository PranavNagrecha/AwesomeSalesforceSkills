# LLM Anti-Patterns — Common LWC Runtime Errors

Common mistakes AI coding assistants make when generating or advising on LWC runtime error diagnosis and fixes. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Accessing Wire Data Without Guarding Against Undefined

**What the LLM generates:**

```js
@wire(getRecord, { recordId: '$recordId', fields: FIELDS })
wiredRecord;

get accountName() {
    return this.wiredRecord.data.fields.Name.value;
}
```

**Why it happens:** LLMs are trained on code snippets where the author assumed the wire had resolved. The chained property access looks idiomatic and compact. The LLM does not model the asynchronous wire lifecycle — it treats `wiredRecord.data` as if it were synchronously available.

**Correct pattern:**

```js
@wire(getRecord, { recordId: '$recordId', fields: FIELDS })
handleRecord({ data, error }) {
    if (data) {
        this.accountName = getFieldValue(data, ACCOUNT_NAME);
    } else if (error) {
        this.errorMessage = error.body?.message ?? 'Error loading record';
    }
}
```

**Detection hint:** Look for property chains like `.wiredX.data.fields.` or `.wiredX.data.` without an `if (data)` guard upstream. Also flag getter functions that access wire properties without null-checking.

---

## Anti-Pattern 2: Using `document.querySelector` to Find Component-Internal Elements

**What the LLM generates:**

```js
renderedCallback() {
    const input = document.querySelector('.my-input');
    input.focus();
}
```

**Why it happens:** LLMs trained on general JavaScript naturally use `document.querySelector` as the standard DOM access pattern. Shadow DOM encapsulation is a web-components-specific concept that many training examples predate or ignore. The LLM does not know that LWC shadow roots are opaque to `document.querySelector`.

**Correct pattern:**

```js
renderedCallback() {
    // this.template.querySelector is scoped to this component's shadow only
    const input = this.template.querySelector('.my-input');
    if (input) {
        input.focus();
    }
}
```

**Detection hint:** Flag any `document.querySelector`, `document.getElementById`, or `window.document.querySelector` usage inside an LWC JavaScript file. These should almost always be `this.template.querySelector`.

---

## Anti-Pattern 3: Dispatching Custom Events Without `composed: true` for Cross-Boundary Communication

**What the LLM generates:**

```js
// In a child component, expecting parent to receive this event
this.dispatchEvent(new CustomEvent('save', { bubbles: true, detail: { id: this.recordId } }));
```

And then puzzled why the parent's `onsave` handler never fires.

**Why it happens:** LLMs know that `bubbles: true` makes events bubble through the DOM, but they conflate the DOM tree with the shadow tree. The distinction between shadow-tree bubbling and composed event propagation is a shadow DOM concept that is not prominent in general JavaScript training data.

**Correct pattern:**

```js
// When the event must cross shadow boundaries to reach a parent component:
this.dispatchEvent(new CustomEvent('save', {
    bubbles: true,
    composed: true,   // required to cross shadow boundaries
    detail: { id: this.recordId }
}));

// When the event is handled within the same component's own template:
this.dispatchEvent(new CustomEvent('stepchange', {
    bubbles: false,
    composed: false,
    detail: { step: this.currentStep }
}));
```

**Detection hint:** Look for `CustomEvent` constructor calls with `bubbles: true` but without `composed: true`. Flag these when the event listener is on a different component than the dispatcher (i.e., the listener is in a parent template, not the same template).

---

## Anti-Pattern 4: Calling `refreshApex` on an Apex-Wired Method

**What the LLM generates:**

```js
import { refreshApex } from '@salesforce/apex';
import getOpportunities from '@salesforce/apex/OpportunityController.getOpportunities';

export default class OpportunityList extends LightningElement {
    @wire(getOpportunities)
    wiredOpps;

    async handleSave() {
        await saveRecord(/* ... */);
        // LLM suggests this to "refresh" the wire — it does nothing for Apex wires
        refreshApex(this.wiredOpps);
    }
}
```

**Why it happens:** `refreshApex` is prominently documented as the way to "refresh wire data" in LWC, and LLMs apply it broadly without distinguishing LDS-backed wires from Apex-backed wires. The LWC documentation does state the limitation, but training data skews toward the pattern's usage, not its constraints.

**Correct pattern:**

```js
// Option A: Use imperative Apex instead of @wire when you need to refresh after mutations
async handleSave() {
    await saveRecord(/* ... */);
    // Re-fetch imperatively after save
    try {
        this.opportunities = await getOpportunities();
    } catch (error) {
        this.errorMessage = error.body?.message;
    }
}

// Option B: Change a reactive wire parameter to force re-evaluation
// (only works if the wire has a parameter)
handleSave() {
    this._refreshToken = Date.now(); // triggers wire re-evaluation
}
@wire(getOpportunities, { token: '$_refreshToken' })
wiredOpps({ data, error }) { /* ... */ }
```

**Detection hint:** Look for `refreshApex(this.wiredX)` where `wiredX` is populated by a wire that imports from `@salesforce/apex/`. `refreshApex` is only effective for wires using LDS adapters (`getRecord`, `getRelatedListRecords`, etc.).

---

## Anti-Pattern 5: Initializing Third-Party Libraries in `connectedCallback`

**What the LLM generates:**

```js
connectedCallback() {
    // Will fail — template not yet rendered
    const container = this.template.querySelector('.chart-container');
    this.chart = new Chart(container, this.chartConfig);
}
```

**Why it happens:** `connectedCallback` is the natural analog of `componentDidMount` in React and `ngOnInit` in Angular, both of which fire after the initial DOM render. LLMs trained on cross-framework patterns assume the same timing in LWC. But in LWC, `connectedCallback` fires when the component class is connected to the DOM host, before the component's own shadow template is rendered. `this.template.querySelector` returns `null` at this point.

**Correct pattern:**

```js
_chartInstance;

// connectedCallback: template NOT rendered yet. Do not query the DOM.
connectedCallback() {
    // Set up non-DOM state here: load configuration, subscribe to pub/sub, etc.
}

// renderedCallback: template IS rendered. Safe to query DOM and init third-party libs.
renderedCallback() {
    if (this._chartInstance) return; // guard: init once
    const container = this.template.querySelector('.chart-container');
    if (!container) return;
    this._chartInstance = new Chart(container, this.chartConfig);
}

disconnectedCallback() {
    if (this._chartInstance) {
        this._chartInstance.destroy();
        this._chartInstance = undefined;
    }
}
```

**Detection hint:** Flag any `this.template.querySelector` call inside `connectedCallback`. All DOM queries must be in `renderedCallback`. Also flag any third-party library constructor call (`new SomeLib(...)`) in `connectedCallback` that takes a DOM element as its first argument.

---

## Anti-Pattern 6: Assuming `event.target` Contains the Originating Child Element Across Shadow Boundaries

**What the LLM generates:**

```js
// Parent listening to a composed event from a child
handleChildAction(event) {
    // LLM assumes event.target is the button inside the child shadow — it is not
    const buttonLabel = event.target.label;
    this.doSomething(buttonLabel);
}
```

**Why it happens:** In standard DOM event handling without shadow DOM, `event.target` is always the originating element. LLMs trained on general DOM programming apply this assumption to LWC composed events without accounting for shadow boundary retargeting.

**Correct pattern:**

```js
// In the child component: put all payload data in event.detail
handleButtonClick() {
    this.dispatchEvent(new CustomEvent('childaction', {
        bubbles: true,
        composed: true,
        detail: {
            label: this.buttonLabel,
            action: 'primary'
        }
    }));
}

// In the parent: use event.detail, not event.target
handleChildAction(event) {
    // event.target is the child host element (e.g., <c-child-component>)
    // event.detail is the payload set by the child
    const { label, action } = event.detail;
    this.doSomething(label, action);
}
```

**Detection hint:** Flag `event.target.someProperty` (other than `.tagName`, `.dataset`, or `.id`) inside a parent event handler that listens for an event dispatched by a child component. Cross-boundary event payload should always come from `event.detail`.

---

## Anti-Pattern 7: Omitting `errorCallback` in Parent Components That Render Complex Child Trees

**What the LLM generates:**

A parent component that renders multiple child components without implementing `errorCallback`:

```js
// parentContainer.js — no errorCallback
export default class ParentContainer extends LightningElement {
    // handles no child errors — a child runtime error will propagate to the platform
}
```

**Why it happens:** LLMs generate the happy-path component structure by default. Error boundary patterns are defensive code that does not appear in tutorials or quick-start examples, so LLMs underweight them.

**Correct pattern:**

```js
// parentContainer.js
export default class ParentContainer extends LightningElement {
    childError;

    // errorCallback catches errors thrown in child component lifecycle hooks and handlers
    errorCallback(error, stack) {
        console.error('ParentContainer caught child error:', error.message, stack);
        this.childError = error.message;
    }
}
```

```html
<!-- parentContainer.html -->
<template>
    <template lwc:if={childError}>
        <div class="slds-text-color_error">
            Something went wrong: {childError}
        </div>
    </template>
    <template lwc:else>
        <c-child-component></c-child-component>
    </template>
</template>
```

**Detection hint:** Flag parent components that render `<c-*>` child components but do not implement `errorCallback`. This is especially important for container components, page layouts, and anything that renders third-party or community-contributed child components.
