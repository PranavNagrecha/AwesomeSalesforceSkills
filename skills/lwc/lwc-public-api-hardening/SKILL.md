---
name: lwc-public-api-hardening
description: "Use when an LWC exposes `@api` properties, `@api` methods, or design attributes in `<targetConfig>` and you need a defensive, predictable public contract. Covers runtime type coercion (the `@api` decorator does NOT enforce JS types — `recordId` is always a string even if you declared it Number), required-vs-optional `@api` validation in `connectedCallback`, getter/setter pairs for reactive normalisation, design-attribute typing in js-meta.xml (datasource picker, dataType, supported objects, default values, propertyType), kebab-case ↔ camelCase rules, and namespace prefix handling. NOT for component-to-component messaging design (see `component-communication`), NOT for App Builder exposure / surface targeting (see `lwc-app-builder-config`), NOT for Custom Property Editors for Flow (see `custom-property-editor-for-flow`)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "lwc api property comes in as string when i declared number"
  - "how to make an lwc api property required"
  - "default value on design attribute not applying when i instantiate dynamically"
  - "boolean lwc api property is a string from app builder"
  - "design attribute datasource picklist of fields apex provider"
  - "should i expose this as @api method or fire a custom event"
  - "kebab case attribute name not binding to camelcase api property"
tags:
  - lwc
  - public-api
  - api-decorator
  - design-attributes
  - target-config
  - type-coercion
  - getter-setter
  - hardening
inputs:
  - "the LWC bundle path (`force-app/.../lwc/<name>/`) being hardened"
  - "every `@api` property and `@api` method declared in the component's `.js` file"
  - "the `<targetConfig>` blocks in the component's `.js-meta.xml` (or all of them, if multi-target)"
  - "which `@api` properties are required vs optional, and what the default value should be when missing"
  - "which surfaces consume the component (record page, app page, Flow screen, Experience site, programmatic instantiation)"
outputs:
  - "an updated `<name>.js` with typed setter coercion, required-prop validation in `connectedCallback`, and JSDoc on each `@api`"
  - "an updated `<name>.js-meta.xml` with correct `dataType`, `default`, `datasource`, and `min`/`max` on each design property"
  - "a documented public-API contract using `templates/lwc-public-api-hardening-template.md`"
  - "a clean run of `scripts/check_lwc_public_api_hardening.py <bundle-path>`"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# LWC Public API Hardening

Activate this skill when an LWC ships `@api` properties, `@api` methods, or admin-facing design attributes in `<targetConfig>` and the public surface needs to be defensive, well-typed at runtime, and survivable against unexpected input from parents, App Builder admins, Flow runtime, or programmatic instantiation. The fundamental thing to internalise: **`@api` is a binding decorator, not a type checker.** Anything you declare ends up as whatever JavaScript value the host hands you — most commonly a string, even when you wrote `@api recordId;` and your IDE shows a `string` annotation.

This is NOT about choosing how components talk to each other (`component-communication` covers that), NOT about App Builder surface targeting (see `lwc-app-builder-config`), and NOT about Custom Property Editors for Flow (see `custom-property-editor-for-flow`).

---

## Before Starting

Gather this context before changing any `@api` surface:

- **Every public touchpoint.** List every `@api` property, every `@api` method, and every `<property>` block inside every `<targetConfig>` in `.js-meta.xml`. The public surface is the union of those three lists, not just the JS file.
- **The most common wrong assumption.** Authors almost always assume the LWC engine validates `@api` types at runtime. It does not. TypeScript-style annotations (whether via JSDoc `@type {number}` or a `.ts`-style comment) compile away — at runtime `@api recordId` and `@api count` are both just whatever the parent assigned, which is usually a string from HTML / App Builder / Flow.
- **Default-value scope.** `default` on a `<property>` in `<targetConfig>` is applied by **App Builder** when an admin drops the component on a page. It is NOT applied when (a) you instantiate the component programmatically via `lwc.createElement(...)`, (b) you put the component directly inside another LWC's template, or (c) you use it on a Visualforce page. In those cases the property is plain `undefined` until the parent assigns it.
- **Form-factor / container quirks.** `<lightning__FlowScreen>` design attributes use `propertyType` for object inputs (Flow only — not valid in `<lightning__AppPage>` or `<lightning__RecordPage>`). HTML attribute parsing converts `false` / `true` to **strings**, not booleans, which bites when consumers use the component declaratively.

---

## Core Concepts

### 1. `@api` does not enforce JavaScript types — only binds the property

`@api` exposes a property to the parent and (for primitive values from HTML) makes attribute writes flow into property writes. It does not coerce, validate, default, or constrain the value. The classic example is `@api recordId`: the framework documentation says it is "the record ID injected by the host page", and consumers infer the type is a Salesforce Id (a string of length 15 or 18). But on a Flow screen with a manually wired input, on a programmatically instantiated component, or in a Jest test, you can set it to a number, an object, `null`, or `undefined`. The component must tolerate every shape it can receive — a setter is the only place you can guarantee the value gets normalised before it lands in component state.

The same holds for `@api method()`. Nothing prevents a parent from calling `myMethod('not a record id')` when you expected `myMethod(['a','list'])`. The argument list is whatever the caller passes, full stop.

### 2. Design attribute types are admin-facing strings until App Builder coerces them

Inside `<property>` you declare a `type` (`String`, `Boolean`, `Integer`, `Color`). At the App Builder UI level the admin gets a typed editor and Salesforce coerces what they enter to that type before assigning it to the `@api` property. But when the same component is dropped on a Flow screen or instantiated from another LWC's template, **no coercion happens** — the value flows through verbatim. Boolean attributes from HTML markup (`<c-foo enabled="false">`) are particularly nasty: the attribute value is the string `"false"`, which is truthy, so a naive `if (this.enabled) { ... }` runs. Always coerce inside the setter.

### 3. Required-vs-optional has no enforcement layer

There is no `@api required` decorator. There is no js-meta.xml flag that fails the deploy when an admin drops the component without setting a property. The only place to enforce a required input is in `connectedCallback` (or in the setter, if you need to react before connection). Throwing during `connectedCallback` aborts the render with a stack trace in the console — that is your enforcement; choose whether you'd rather throw, log + return early, or render a fallback "configuration missing" template.

### 4. Reactive `@api` and the getter/setter trap

Plain `@api foo;` is reactive: when the parent reassigns it, the template re-renders. As soon as you replace it with a `@api get foo()` / `set foo(v)` pair, the *underlying field* the setter writes to must be tracked (decorated with `@track` or be a primitive on `this`) for re-renders to fire. A common bug is to write `set foo(v) { this._foo = normalise(v); }` and never re-render because the field `_foo` is not tracked and the getter's return value depends on it. Either keep the underlying value as a primitive on `this` (LWC tracks all primitive class fields automatically) or store complex shapes inside an `@track`-friendly structure.

---

## Common Patterns

### Pattern: Defensive setter with coercion

**When to use:** any `@api` property that receives values from HTML attributes, Flow runtime, or App Builder — i.e. the vast majority of them.

**How it works:**

```js
import { api, LightningElement } from 'lwc';

export default class HardCounter extends LightningElement {
    _count = 0;

    @api
    get count() { return this._count; }
    set count(value) {
        // App Builder may pass a string; HTML attribute parsing always does.
        const n = Number(value);
        this._count = Number.isFinite(n) ? n : 0;
    }
}
```

**Why not the alternative:** if you skip coercion and write `@api count = 0;`, then `<c-hard-counter count="3">` ends up with `this.count === '3'`. The `=== 0` falsy default looks correct in unit tests (where you assign a number) but is wrong in App Builder (where you get a string).

### Pattern: Required-prop guard in `connectedCallback`

**When to use:** any property whose absence makes the component meaningless (e.g. `recordId` on a record-context component, `topicId` on a knowledge widget).

**How it works:**

```js
connectedCallback() {
    if (!this.recordId) {
        // Hard fail — visible in console, surfaced to LWS.
        throw new Error('c-account-summary requires `record-id` to be set');
    }
}
```

For Flow screens, prefer setting an `errorMessage` property and rendering a fallback — Flow halts the screen on uncaught errors, which is harsh UX:

```js
connectedCallback() {
    if (!this.topicId) {
        this.errorMessage = 'Configure the Topic Id in the Flow screen builder.';
    }
}
```

### Pattern: Method that should be an event

**When to use:** the parent component currently calls `child.refresh()` after some user action.

**How it works:**

Replace the `@api refresh()` method with a `CustomEvent` flowing the *other direction*. The child should announce when it's ready / requesting refresh, the parent reacts:

```js
// Inside child — instead of `@api refresh()`:
handleSaveSucceeded() {
    this.dispatchEvent(new CustomEvent('saved', { detail: { id: this.recordId } }));
}
```

```html
<!-- Inside parent -->
<c-child onsaved={handleChildSaved}></c-child>
```

**Why not the alternative:** `@api refresh()` welds the parent to the child's internal lifecycle and is a recursion magnet (parent calls `refresh()`, refresh fires the event the parent listens to, parent calls `refresh()` again). Events are a one-way contract; the parent decides whether to act.

### Pattern: Design attribute with admin-facing default and datasource

**When to use:** App Builder–facing properties where the admin is choosing from a known small set, or wiring a field name from the bound SObject.

**How it works:** in `.js-meta.xml`:

```xml
<targets><target>lightning__RecordPage</target></targets>
<targetConfigs>
    <targetConfig targets="lightning__RecordPage" objects="Account,Contact">
        <property
            name="primaryField"
            label="Primary field"
            type="String"
            default="Name"
            datasource="Name,AccountNumber,Industry"
            description="Field to display as the headline." />
        <property
            name="maxRows"
            label="Max rows"
            type="Integer"
            default="5"
            min="1"
            max="50" />
    </targetConfig>
</targetConfigs>
```

Then in `.js`, still coerce inside the setter — `default` only applies when the admin uses App Builder; programmatic callers get `undefined`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Parent needs to push data into the child | `@api property` (with defensive setter) | Lowest coupling; reactive; survives parent re-renders |
| Parent needs to trigger an imperative action on the child (focus, scroll, refresh) | `@api method` only if the action is genuinely imperative and stateless; otherwise CustomEvent | Methods are appropriate for "do this now"; avoid them for "react to my state change" |
| Child needs to notify parent of an event, value change, or completion | `CustomEvent` with `dispatchEvent` | One-way contract; parent decides whether to act; survives DOM removal |
| Cross-DOM-tree communication (sibling components, deep tree) | Lightning Message Service (LMS) | `CustomEvent` only bubbles within the DOM subtree; LMS works across the page |
| Child needs admin to configure a value | Design attribute in `<targetConfig>` + defensive setter | Gives admins a typed editor with default; the setter still defends against programmatic callers |
| Child needs a "required to function" input | `@api property` + guard in `connectedCallback` | There is no `required` flag; explicit guard is the only enforcement point |
| Component instantiated programmatically AND from App Builder | Defensive setter that handles both `undefined` and string forms | App Builder defaults do not apply programmatically; setter is the only common path |

---

## Recommended Workflow

Step-by-step instructions for hardening an existing component's public API:

1. **Inventory the public surface.** Open `<name>.js` and `<name>.js-meta.xml`. List every `@api` property, every `@api` method, and every `<property>` inside every `<targetConfig>`. Note which ones currently have setters, which are bare fields, and which method names look like they should be events (`refresh`, `update`, `notify`).
2. **Classify required vs optional.** For each `@api` property, ask: does the component crash, render nothing useful, or silently misbehave when this is `undefined`? If yes, mark it required. If no, mark it optional and decide a sensible default.
3. **Convert bare `@api` fields to getter/setter pairs where coercion is needed.** Use the "Defensive setter" pattern above. Coerce strings to numbers, `"true"`/`"false"` strings to booleans, normalise nullish to a chosen default.
4. **Add a `connectedCallback` guard for required props.** Throw or render a fallback. Document the choice in a JSDoc comment on the class.
5. **Audit `@api` methods.** For each one, ask: "Could a CustomEvent in the other direction replace this?" If yes, refactor. If no, document the imperative contract in a JSDoc comment so consumers know the input shape and the side effects.
6. **Type the design attributes in `.js-meta.xml`.** Set explicit `type`, `default`, `min`/`max` (for `Integer`), and `datasource` (for fixed-set `String`). For Flow targets only, use `propertyType` if accepting an SObject. Verify kebab-case attribute names map to the camelCase JS property as expected.
7. **Run the checker.** `python3 skills/lwc/lwc-public-api-hardening/scripts/check_lwc_public_api_hardening.py <bundle-path>`. Fix every P0 and P1 finding before marking complete.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every `@api` property that can receive a string from HTML/App Builder has a setter that coerces to the intended type.
- [ ] Every required `@api` property is validated in `connectedCallback` (throw, log + early return, or fallback render).
- [ ] No `@api` method exists that could be replaced with a CustomEvent — methods are reserved for genuine imperative actions.
- [ ] No `@api` getter returns a value derived from a non-tracked, non-primitive backing field.
- [ ] Every design attribute has explicit `type`, `default` (where applicable), and `datasource` or `min`/`max` (where applicable).
- [ ] Boolean design attributes have setters that coerce string `"false"` to boolean `false`.
- [ ] No `@api` property leaks an internal mutable structure that the parent could mutate by reference.
- [ ] `python3 skills/lwc/lwc-public-api-hardening/scripts/check_lwc_public_api_hardening.py <bundle-path>` exits 0.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`@api recordId` is always a string.** Even when surrounded by code that says `Number(...)` or has a `@type {number}` comment. The host page assigns the string Id; the framework does not coerce.
2. **`default` on a design property does NOT apply to programmatic instantiation.** A unit test that does `createElement('c-foo', { is: Foo })` gets `undefined` for every property until the test explicitly assigns it. The same is true for one LWC including another in its template.
3. **Boolean attributes from HTML are strings.** `<c-foo enabled="false">` results in `this.enabled === 'false'` (truthy). HTML knows nothing about JS types.
4. **Design attribute names are kebab-case in markup, camelCase in JS.** `<property name="maxRows">` becomes `@api maxRows` (not `max-rows`). The XML attribute name is the *internal* key; it must follow the JS identifier convention except when used inline in HTML where attributes are kebab-case.
5. **Default values in `<targetConfig>` are scoped to that target.** A `default="5"` inside `<targetConfig targets="lightning__RecordPage">` does not apply when the same component is dropped on `lightning__AppPage`. Each target needs its own `<targetConfig>` block with its own defaults.
6. **`propertyType` is Flow-only.** Using `propertyType` inside a non-Flow `<targetConfig>` either deploys quietly and is ignored, or fails deploy depending on org version. Object-typed inputs only work for `<lightning__FlowScreen>`.
7. **Namespaced design attributes need the namespace prefix.** When referenced from an installed package, `c__myProperty` is the resolved name, not `myProperty`. Author components in unmanaged orgs without the prefix to avoid confusion, but be aware of the package case.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Hardened `<name>.js` | Defensive setters on every `@api` property, required-prop guards in `connectedCallback`, JSDoc on each public member |
| Typed `<name>.js-meta.xml` | Every design `<property>` has explicit `type`, default, datasource / min / max as appropriate; targets isolated to their valid set |
| Public API contract document | Filled-in `templates/lwc-public-api-hardening-template.md` documenting required-vs-optional, type coercion behaviour, events emitted, methods exposed |
| Hardening checker run | `scripts/check_lwc_public_api_hardening.py` clean exit on the bundle |

---

## Related Skills

- `lwc/component-communication` — choosing between `@api`, CustomEvent, LMS, and Pub/Sub for component-to-component communication
- `lwc/lwc-app-builder-config` — `targets`, `targetConfigs`, `supportedFormFactors`, and surface-level exposure rules in `.js-meta.xml`
- `lwc/custom-property-editor-for-flow` — when the design-attribute editor itself needs to be a custom LWC (Flow only)
- `lwc/lwc-custom-event-patterns` — naming, bubbling, composed events, and detail payload conventions
- `lwc/lifecycle-hooks` — semantics of `connectedCallback`, `renderedCallback`, and `disconnectedCallback` referenced by the hardening guards
