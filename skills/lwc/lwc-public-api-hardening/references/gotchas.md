# Gotchas — LWC Public API Hardening

Subtle traps when designing or hardening an LWC's public surface. Each gotcha includes the concrete repro that bit a real component.

---

## 1. `@api recordId` is always a string, regardless of declared "type"

**What happens:** developers declare `@api recordId;` with a JSDoc `@type {number}` or even a `.ts`-style annotation, then later write `if (this.recordId > 0)` or pass `this.recordId` straight into a wire that expects a string. At runtime, `recordId` arrives from the host page as a string Id (e.g. `"001..."`), so numeric comparisons silently coerce or NaN.

**When it occurs:** any `@api recordId` consumer outside a Jest test, where the host (Lightning App Builder, Experience Cloud page, Flow with a record context) injects the live Id.

**How to avoid:** treat `recordId` as a string Id for all comparisons. If you want a numeric value, declare a separate `@api numericThing` with a setter that calls `Number(value)` and validates `Number.isFinite`.

---

## 2. `default` in `<targetConfig>` does NOT apply to programmatic instantiation

**What happens:**

```xml
<property name="maxRows" type="Integer" default="10" />
```

```js
@api maxRows;
```

Then in a Jest test:

```js
const el = createElement('c-foo', { is: Foo });
document.body.appendChild(el);
console.log(el.maxRows); // undefined, NOT 10
```

The same is true when a parent LWC includes `<c-foo>` inline without setting `max-rows` — `default` is an App-Builder-only convenience.

**When it occurs:** unit tests, component composition (one LWC inside another), and `lwc.createElement(...)` callers.

**How to avoid:** mirror the default in JS as well, ideally in a setter:

```js
_maxRows = 10;
@api
get maxRows() { return this._maxRows; }
set maxRows(v) {
    const n = Number(v);
    this._maxRows = Number.isFinite(n) ? n : 10;
}
```

---

## 3. Boolean attributes from HTML markup are *strings*, not booleans

**What happens:**

```html
<c-foo enabled="false"></c-foo>
```

In the child:

```js
@api enabled;
// ...
if (this.enabled) {
    // RUNS — because the string "false" is truthy.
}
```

**When it occurs:** any boolean `@api` declared as a bare field instead of a setter that coerces. HTML knows nothing about JS types — every attribute value is a string until something coerces it.

**How to avoid:** always wrap booleans in a setter that coerces explicitly:

```js
_enabled = false;
@api
get enabled() { return this._enabled; }
set enabled(v) {
    this._enabled = v === true || v === 'true';
}
```

LWC App Builder coerces a `type="Boolean"` design property correctly when an admin uses the toggle, but HTML markup, programmatic callers, and Flow inputs do not.

---

## 4. Reactive re-render breaks when you swap a bare `@api` for a getter/setter pair

**What happens:** the change from

```js
@api foo;
```

to

```js
_foo;
@api
get foo() { return this._foo; }
set foo(v) { this._foo = normalise(v); }
```

stops triggering re-renders for some consumers because they relied on the parent reassigning the bare field. With the setter form, the underlying `_foo` field is the reactive source — and if `_foo` is a non-primitive (object, array) and the setter mutates it in place, the template never re-renders.

**When it occurs:** when the setter mutates an object/array stored in `_foo` rather than reassigning it.

**How to avoid:** in the setter, **reassign** the backing field with a new value rather than mutating the existing one:

```js
// WRONG
set rows(v) { this._rows.length = 0; this._rows.push(...v); }

// RIGHT
set rows(v) { this._rows = Array.isArray(v) ? [...v] : []; }
```

LWC's reactivity tracks reassignment of class fields and primitive mutations; in-place object mutation is not tracked.

---

## 5. `propertyType` only works inside a `<lightning__FlowScreen>` `<targetConfig>`

**What happens:** an author copies a Flow `<propertyType name="T" extends="SObject"/>` block into a `<lightning__RecordPage>` `<targetConfig>`. Depending on org version, the deploy either fails with a confusing schema error or succeeds but the type is silently treated as `String`, producing very strange admin UX.

**When it occurs:** any time a multi-target component is generalising "accept an SObject" across surfaces.

**How to avoid:** keep `<propertyType>` strictly inside Flow target configs. For non-Flow surfaces, accept a string Id (or a JSON blob) and document the contract.

---

## 6. Kebab-case attribute / camelCase property mapping is not symmetric

**What happens:** a developer writes `@api maxRows` in JS and `<c-foo maxRows="3">` in markup. The attribute does not bind because HTML attribute names are case-insensitive and LWC requires kebab-case in markup: `<c-foo max-rows="3">`. Conversely, in `<targetConfig>` the `<property name="maxRows">` uses **camelCase** — that is the JS property name, and App Builder maps it correctly without kebab conversion.

**When it occurs:** mixing the two conventions or copy-pasting between markup, design XML, and JS.

**How to avoid:** remember the rule: **markup is kebab-case, JS and design XML are camelCase.** The framework converts the markup attribute name to the JS property name on assignment.

---

## 7. Default values are scoped per `<targetConfig>` block

**What happens:** you have one component used in both `lightning__RecordPage` and `lightning__AppPage`. You set `default="5"` only in the record page block. On an App Page, the property is undefined unless the admin sets it.

**When it occurs:** multi-target components where the author copy-pasted only one `<targetConfig>`.

**How to avoid:** every `<targetConfig>` block needs its own `<property>` declarations and its own defaults. They are not inherited across targets. If the property semantics are the same across targets, mirror the default in a JS setter so it works regardless of which target rendered the component.

---

## 8. `@api` getter/setter with a default value initialiser breaks the setter

**What happens:**

```js
@api foo = 'default';
get foo() { return this._foo; }
set foo(v) { this._foo = v; }
```

This is a syntax / decorator error or a silent no-op depending on tooling — `@api` cannot be applied to both a class field and an accessor pair with the same name. The intent (set a default) must move into the constructor or the backing field.

**When it occurs:** during refactor, when an author converts a bare `@api foo = 'default';` into a getter/setter and forgets to remove the original line.

**How to avoid:** initialise the backing field, not the public accessor:

```js
_foo = 'default';
@api
get foo() { return this._foo; }
set foo(v) { this._foo = v ?? 'default'; }
```

---

## 9. Public method on a removed component throws "this.template is null"

**What happens:** parent calls `child.refresh()` from a `setTimeout`. By the time the timer fires, the child has been removed from the DOM (e.g. user navigated). `this.template` is now null, and the method throws an unhandled exception that bubbles to the LWS error boundary.

**When it occurs:** any `@api` method that touches `this.template` and is called via deferred work (timeouts, promises, async callbacks) from outside the component.

**How to avoid:** events, not methods, where possible. When a method is genuinely required, guard it: `if (!this.isConnected) return;` (custom flag set in `connectedCallback` / `disconnectedCallback`) or `if (!this.template) return;` as a defensive check.

---

## 10. Namespaced design attributes need the namespace prefix in installed packages

**What happens:** a managed-package component declares `<property name="primaryField">`. Inside the package org it resolves as `primaryField`. After install in a subscriber org, the property is exposed as `c__primaryField` (or `<ns>__primaryField`). Any documentation that says "set `primaryField` to ..." is wrong for the subscriber.

**When it occurs:** publishing an LWC in a managed package.

**How to avoid:** test in a subscriber org, document the namespaced name, and avoid hand-editing FlexiPages or programmatic property writes that assume the unprefixed name.
