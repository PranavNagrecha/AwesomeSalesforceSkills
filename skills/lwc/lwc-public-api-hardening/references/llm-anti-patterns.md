# LLM Anti-Patterns — LWC Public API Hardening

Common mistakes AI coding assistants make when generating or hardening LWC public APIs. These help the consuming agent self-check its own output against the patterns in `SKILL.md`.

---

## Anti-Pattern 1: Adding type annotations as if they're enforced

**What the LLM generates:**

```js
/** @type {number} */
@api recordId;

/** @type {boolean} */
@api enabled = false;
```

…and then writes downstream code that does `this.recordId > 0` or `if (this.enabled)`.

**Why it happens:** training data is full of TypeScript-style code where the annotation is enforced. The LLM imports that mental model into LWC, where annotations are *documentation only* and the framework binds whatever the parent assigned.

**Correct pattern:** treat annotations as documentation, defend at the boundary with a setter:

```js
_enabled = false;
@api
get enabled() { return this._enabled; }
set enabled(v) { this._enabled = v === true || v === 'true'; }
```

**Detection hint:** any `@api` field with a JSDoc `@type` annotation but no setter, especially for `boolean` or `number` types. Coerce explicitly.

---

## Anti-Pattern 2: Treating `@api` properties as immutable by default

**What the LLM generates:** assumes `@api` properties cannot change after initial assignment, so the component caches derived state in `connectedCallback` and never reacts:

```js
@api recordId;
connectedCallback() {
    this.computedKey = `record-${this.recordId}`; // captured once
}
```

When the parent later changes `record-id`, `computedKey` is stale.

**Why it happens:** the LLM reads "public API" as "Java-style final input" and forgets LWC `@api` properties are reactive — parent reassignments trigger re-renders.

**Correct pattern:** derive in a getter, not in `connectedCallback`:

```js
@api recordId;
get computedKey() {
    return `record-${this.recordId}`;
}
```

Or, if expensive, use a setter that recomputes:

```js
_recordId;
@api
get recordId() { return this._recordId; }
set recordId(v) {
    this._recordId = v;
    this.computedKey = `record-${v}`;
}
```

**Detection hint:** any `@api` property whose derived state is computed only in `connectedCallback`.

---

## Anti-Pattern 3: Exposing every internal helper as `@api`

**What the LLM generates:** the user said "make this component reusable", so the LLM marks every method `@api`:

```js
@api computeRowKey(row) { ... }
@api flushBuffer() { ... }
@api validate() { ... }
@api setRows(rows) { ... }
```

**Why it happens:** the LLM optimises for "more public surface = more flexible" without considering coupling cost or security boundary.

**Correct pattern:** the public API should be the *intent* of the component, not its internals. Most "make it reusable" requests are better served by:

- One or two `@api` properties that configure the component
- One or two `@api` methods that perform genuine imperative actions (focus, scroll, reset)
- CustomEvents for everything that says "I did X, do you care?"

```js
// Probably enough:
@api recordId;
@api maxRows = 5;

handleClick() {
    this.dispatchEvent(new CustomEvent('rowselect', { detail: { rowId } }));
}
```

**Detection hint:** more than ~4 `@api` methods on a single component, especially with names like `set*`, `get*`, `compute*`, `flush*`, `update*`. Replace with reactive properties + events.

---

## Anti-Pattern 4: Using `@api` methods where a CustomEvent is the right primitive

**What the LLM generates:**

```js
// Child
@api refresh() {
    this.runWire();
}

// Parent
this.template.querySelector('c-child').refresh();
```

Then in a follow-up bug, the parent calls `refresh()` after the child has been removed and `template` is null.

**Why it happens:** the LLM sees "parent needs to tell child to do X" and reaches for the imperative method, skipping the design conversation about whether the child should announce a state change instead.

**Correct pattern:** flip the contract. If the parent has new data, push it as a property change. If the parent has a state change, announce it via an LMS message or via a property the child reacts to. If the child needs to announce work-completed, dispatch an event.

```js
// Child announces, parent reacts.
this.dispatchEvent(new CustomEvent('saved', { detail: { id } }));
```

```html
<!-- Parent listens. -->
<c-child onsaved={handleSaved}></c-child>
```

**Detection hint:** any `@api` method named `refresh`, `update`, `notify`, `set*`, `forceX`, or anything imperative — interrogate whether a CustomEvent or property change replaces it.

---

## Anti-Pattern 5: Trusting `default` in `<targetConfig>` as the runtime default

**What the LLM generates:**

```xml
<property name="maxRows" type="Integer" default="10" />
```

```js
@api maxRows; // no default initialiser, no setter
```

Then a Jest test:

```js
const el = createElement('c-foo', { is: Foo });
expect(el.maxRows).toBe(10); // FAILS — undefined
```

**Why it happens:** the LLM reads `<property default="10">` as "the runtime default" rather than "the App Builder admin-UI default."

**Correct pattern:** mirror the default in JS too:

```js
_maxRows = 10;
@api
get maxRows() { return this._maxRows; }
set maxRows(v) {
    const n = Number(v);
    this._maxRows = Number.isFinite(n) ? n : 10;
}
```

**Detection hint:** any `@api` field that appears in a `<targetConfig>` `<property default="...">` but has no JS-side initialiser or setter-side fallback.

---

## Anti-Pattern 6: Mutating an `@api`-tracked object in place inside a setter

**What the LLM generates:**

```js
_rows = [];
@api
get rows() { return this._rows; }
set rows(v) {
    this._rows.length = 0;
    if (Array.isArray(v)) for (const r of v) this._rows.push(r);
}
```

**Why it happens:** the LLM treats array reuse as a perf optimisation and forgets LWC reactivity tracks reassignment, not in-place mutation.

**Correct pattern:** reassign:

```js
set rows(v) {
    this._rows = Array.isArray(v) ? [...v] : [];
}
```

**Detection hint:** any setter that calls `.length = 0`, `.splice(0)`, `Object.assign(this._foo, v)`, or any in-place mutation of a backing field. Replace with reassignment.

---

## Anti-Pattern 7: Over-validating in `connectedCallback` and breaking unit tests

**What the LLM generates:**

```js
connectedCallback() {
    if (!this.recordId) throw new Error('record-id required');
    if (!this.maxRows) throw new Error('max-rows required');
    if (!this.label) throw new Error('label required');
    if (!this.onCallback) throw new Error('callback required');
    // ... 8 more requireds
}
```

**Why it happens:** the LLM reads "validate required props in connectedCallback" and applies it to every property, not just the ones whose absence breaks the component.

**Correct pattern:** mark *truly required* props (those whose absence makes the component meaningless or unsafe) with a guard. Optional props get a default. Coerce-and-default in the setter handles 90% of cases:

```js
connectedCallback() {
    // Only the things that genuinely break the component if missing.
    if (!this.recordId) throw new Error('c-foo requires `record-id`');
}

// Optional with default:
_maxRows = 5;
@api
get maxRows() { return this._maxRows; }
set maxRows(v) { /* coerce or fall back to 5 */ }
```

**Detection hint:** more than 2-3 throws in `connectedCallback`, or throws on properties that have a sensible default.

---

## Anti-Pattern 8: Mixing kebab-case and camelCase between markup, JS, and design XML

**What the LLM generates:**

```xml
<property name="max-rows" type="Integer" />
```

```js
@api maxRows;
```

Or:

```html
<c-foo maxRows="5"></c-foo>
```

Both forms produce silent binding failures.

**Why it happens:** the LLM has seen both conventions in different framework training data and isn't sure which applies where in LWC.

**Correct pattern:** **markup is kebab-case, JS and design XML are camelCase.**

```xml
<property name="maxRows" type="Integer" /> <!-- design XML: camelCase -->
```

```js
@api maxRows;                              // JS: camelCase
```

```html
<c-foo max-rows="5"></c-foo>               <!-- markup: kebab-case -->
```

**Detection hint:** kebab-case in `<property name="...">`, or camelCase as an HTML attribute in markup.
