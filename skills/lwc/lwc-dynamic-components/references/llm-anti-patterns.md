# LLM Anti-Patterns — LWC Dynamic Components

Common mistakes AI coding assistants make when generating or advising on dynamic component loading in LWC.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Passing a string to lwc:is instead of a constructor

**What the LLM generates:**

```html
<lwc:component lwc:is="c-my-component"></lwc:component>
```

```javascript
this.componentName = 'c-my-component';
```

**Why it happens:** LLMs treat `lwc:is` like a string-based component selector similar to Angular or Vue dynamic components. In LWC, `lwc:is` requires a constructor reference returned by `import()`.

**Correct pattern:**

```javascript
async loadComponent() {
    const { default: ctor } = await import('c/myComponent');
    this.componentConstructor = ctor;
}
```

```html
<lwc:component lwc:is={componentConstructor}></lwc:component>
```

**Detection hint:** `lwc:is` bound to a string variable or a string literal in the template.

---

## Anti-Pattern 2: Not handling import() failures

**What the LLM generates:**

```javascript
async connectedCallback() {
    const { default: ctor } = await import('c/myComponent');
    this.componentConstructor = ctor;
}
```

**Why it happens:** LLMs generate the happy path. Dynamic imports can fail if the component does not exist, is not deployed, or the namespace is wrong. Without error handling, the component silently shows nothing.

**Correct pattern:**

```javascript
async connectedCallback() {
    try {
        const { default: ctor } = await import('c/myComponent');
        this.componentConstructor = ctor;
    } catch (e) {
        this.loadError = `Failed to load component: ${e.message}`;
        this.componentConstructor = undefined;
    }
}
```

**Detection hint:** `import('c/` without a surrounding `try/catch` or `.catch()`.

---

## Anti-Pattern 3: Using dynamic import when lwc:if would be simpler and faster

**What the LLM generates:**

```javascript
// Dynamically imports one of two known components based on a boolean
if (this.isAdvanced) {
    const { default: ctor } = await import('c/advancedForm');
    this.formConstructor = ctor;
} else {
    const { default: ctor } = await import('c/simpleForm');
    this.formConstructor = ctor;
}
```

**Why it happens:** LLMs reach for dynamic imports whenever the word "dynamic" appears, even when the component set is known at build time and `lwc:if` would render the correct one without async overhead.

**Correct pattern:**

```html
<c-advanced-form lwc:if={isAdvanced}></c-advanced-form>
<c-simple-form lwc:else></c-simple-form>
```

**Detection hint:** Dynamic `import()` where the set of candidate components is a small, fixed list known at development time.

---

## Anti-Pattern 4: Setting @api properties before the constructor is assigned

**What the LLM generates:**

```javascript
async loadComponent() {
    this.dynamicProps = { recordId: this.recordId, mode: 'edit' };
    const { default: ctor } = await import('c/myForm');
    this.componentConstructor = ctor;
    // Props were set before the constructor — component may not pick them up
}
```

**Why it happens:** LLMs set properties eagerly. But `lwc:component` only instantiates when `lwc:is` receives a truthy constructor. Properties set before that may not propagate correctly.

**Correct pattern:**

```javascript
async loadComponent() {
    const { default: ctor } = await import('c/myForm');
    this.componentConstructor = ctor;
}
```

```html
<lwc:component lwc:is={componentConstructor}
    record-id={recordId}
    mode="edit">
</lwc:component>
```

Binding properties in the template is preferred because they are reactive.

**Detection hint:** Property assignments to a dynamic component reference before the `import()` resolves.

---

## Anti-Pattern 5: Importing from the wrong module path format

**What the LLM generates:**

```javascript
const { default: ctor } = await import('c-my-component');
// or
const { default: ctor } = await import('lightning-datatable');
```

**Why it happens:** LLMs confuse the kebab-case HTML tag format (`c-my-component`) with the module specifier format (`c/myComponent`).

**Correct pattern:**

```javascript
const { default: ctor } = await import('c/myComponent');
```

Module specifiers use `namespace/camelCaseName`, not the kebab-case tag name.

**Detection hint:** `import('c-` or `import('lightning-` in dynamic import statements.

---

## Anti-Pattern 6: Re-importing the same module on every render or interaction

**What the LLM generates:**

```javascript
handleTabChange(event) {
    // Imports the module every time the user switches tabs
    const { default: ctor } = await import(`c/${event.detail.value}`);
    this.componentConstructor = ctor;
}
```

**Why it happens:** LLMs do not cache resolved constructors. While the browser module cache prevents duplicate network requests, the async overhead and potential flicker remain.

**Correct pattern:**

```javascript
_ctorCache = {};

async handleTabChange(event) {
    const name = event.detail.value;
    if (!this._ctorCache[name]) {
        const { default: ctor } = await import(`c/${name}`);
        this._ctorCache[name] = ctor;
    }
    this.componentConstructor = this._ctorCache[name];
}
```

**Detection hint:** `import()` inside an event handler with no caching logic.
