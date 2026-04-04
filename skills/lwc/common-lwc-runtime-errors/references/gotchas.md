# Gotchas — Common LWC Runtime Errors

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Wire Delivers `{ data: undefined, error: undefined }` Before Resolving

**What happens:** The `@wire` handler fires at least once before the adapter returns any data. On that initial call, both `data` and `error` are `undefined`. Code that checks only `if (error)` to show an error state and `if (data)` to show content is correct, but code that checks `if (!this.wiredResult)` or accesses `this.wiredResult.data` directly will evaluate against undefined on that first call, causing a `TypeError` or incorrect UI state.

**When it occurs:** On every component mount, for every wire adapter, before the Lightning Data Service or Apex wire has had time to respond. It also occurs after a `refreshApex` call — the wire briefly returns to the `{ undefined, undefined }` state before the fresh response arrives.

**How to avoid:** Always handle three states in wire handlers — loading (both undefined), success (data defined), and error (error defined). Use an explicit `isLoading` flag initialized to `true` and set to `false` in the wire handler once either `data` or `error` arrives. Never access properties through the wire result without a guard.

---

## Gotcha 2: `renderedCallback` Runs on Every Re-Render

**What happens:** `renderedCallback` is not a one-time initialization hook — it fires after every render cycle caused by reactive property changes. Third-party library instances, event listeners attached imperatively, and any setup code placed in `renderedCallback` without a guard will execute multiple times, creating duplicate widget instances, stacking event listeners, or consuming excessive memory.

**When it occurs:** Any time a reactive property (`@track`, `@api`, or plain class field) changes after the component is connected. Frequent triggers include wire responses arriving, parent property updates, and user interactions that change local state. In a busy component, `renderedCallback` may fire dozens of times per session.

**How to avoid:** Protect any one-time initialization inside `renderedCallback` with an instance check or a boolean flag:

```js
renderedCallback() {
    if (this._initialized) return;
    this._initialized = true;
    // safe to initialize once here
}
```

Clean up in `disconnectedCallback` to release resources when the component is removed from the DOM.

---

## Gotcha 3: `refreshApex` Silently Does Nothing for Non-LDS Wire Adapters

**What happens:** Developers use `@wire` with an imported Apex method (e.g., `@wire(getMyRecords)`) and then call `refreshApex(this.wiredResult)` expecting it to re-fetch data. For Apex-backed wires, `refreshApex` has no effect — the wire cache is not refreshed and the Apex call is not re-issued. No error is thrown and no warning appears in the console.

**When it occurs:** Whenever a component uses a wired Apex method and needs to reload data after a create, update, or delete operation. This is one of the top "data doesn't update after save" complaints for LWC.

**How to avoid:** `refreshApex` only works for Lightning Data Service wires (e.g., `getRecord`, `getRelatedListRecords`). For Apex-backed wires, use one of two patterns: (1) call the Apex method imperatively (not via `@wire`) in a `handleSave` function and update the component state directly, or (2) change the value of a reactive `$property` used as a wire parameter, which forces the wire to re-evaluate.

---

## Gotcha 4: Shadow DOM Retargets `event.target` on Composed Events

**What happens:** A `CustomEvent` dispatched with `composed: true` crosses shadow boundaries as it bubbles up. At each shadow boundary, the browser retargets `event.target` to the host element of the shadow that enclosed the original target. A parent component listening for the event will see `event.target` as the child host element (`<c-child-form>`), not the internal button or input that originally dispatched it.

**When it occurs:** Whenever a parent component's event handler reads `event.target` to identify which sub-element triggered the action. This is especially confusing when a generic handler uses `event.target.dataset` or `event.target.name` to route behavior.

**How to avoid:** Never rely on `event.target` for payload data in cross-boundary events. Put all relevant data in `event.detail` in the dispatching component. Use `event.target` only for its tag name or dataset when you know the event will not cross a shadow boundary (i.e., when it originates from a base HTML element within the current component's own shadow, with `composed: false`).

---

## Gotcha 5: Slot Name Mismatch Renders Nothing Without Errors

**What happens:** A parent component passes content to a named slot in a child component. If the `slot` attribute value in the parent template does not exactly match the `name` attribute on the `<slot>` element in the child template, the content is not rendered anywhere. The child shows its fallback slot content (if any), or just renders blank. No console error is thrown.

**When it occurs:** When a child component has `<slot name="actions">` but the parent uses `<template slot="action">` (typo — missing 's'). Also occurs when a developer renames a slot in the child during refactoring but forgets to update the parent template.

**How to avoid:** Verify slot names end-to-end by checking both the child's `<slot name="...">` and the parent's `slot="..."` attribute on the content element. Default slots (unnamed) receive any content not assigned to a named slot — content intended for a named slot that has a typo will fall into the default slot if one exists, making the bug harder to spot because some content still renders (in the wrong place).

---

## Gotcha 6: `connectedCallback` Fires Before `@api` Properties Are Set by the Parent

**What happens:** A component reads an `@api` property in `connectedCallback` expecting it to have the value the parent passed. But `connectedCallback` fires when the component is inserted into the DOM, which happens before the parent has had a chance to set property values via the public API. The property is `undefined` in `connectedCallback`.

**When it occurs:** Any time a component's initialization logic in `connectedCallback` depends on an `@api` property — for example, making an imperative Apex call using `this.recordId` before the parent has finished setting it.

**How to avoid:** Do not depend on `@api` properties being set in `connectedCallback`. Use a getter/setter pattern on the `@api` property that triggers initialization when the value is first assigned, or use `@wire` with the property as a reactive parameter (`'$recordId'`) which automatically defers and re-evaluates when the value changes. Alternatively, use `getters` in the template that handle the undefined state gracefully.

---

## Gotcha 7: Lightning Locker Breaks Many Third-Party Libraries That Work in LWS

**What happens:** A third-party JavaScript library (Chart.js, Flatpickr, Quill, etc.) works correctly in a sandbox or scratch org using Lightning Web Security but fails in a production org that still uses legacy Locker Service. Errors appear as `TypeError: Cannot read properties of undefined`, `Cannot set property of null`, or `Access check failed` in the console.

**When it occurs:** When a production org has not enabled Lightning Web Security (still on legacy Locker Service). Locker wraps DOM elements in SecureElement proxies that intercept and block certain prototype chain lookups and native global accesses that many JavaScript libraries rely on. The same code can work in LWS because LWS uses module-scope distortion rather than DOM proxy wrapping.

**How to avoid:** Check Setup > Session Settings > Use Lightning Web Security to confirm the active model. If Locker is active, test every third-party library against Locker restrictions before deployment. For Locker-incompatible libraries, the resolution options are: (1) migrate the org to LWS (recommended), (2) find a Locker-compatible alternative library, or (3) avoid using the library in LWC and render the feature in a Visualforce page loaded inside a `<lightning-iframe>`.
