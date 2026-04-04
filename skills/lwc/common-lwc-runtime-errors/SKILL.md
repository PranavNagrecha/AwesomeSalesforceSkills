---
name: common-lwc-runtime-errors
description: "Diagnose and fix runtime errors in Lightning Web Components including wire adapter failures, shadow DOM boundary violations, event propagation mistakes, async rendering timing bugs, NavigationMixin errors, Lightning Locker vs Lightning Web Security conflicts, and slot projection problems. Triggers: 'wire adapter returns undefined', 'querySelector returns null in LWC', 'custom event not received by parent', 'LWC component not rendering after connected callback', 'NavigationMixin page reference error'. NOT for LWC fundamentals, build/deployment errors, or Aura component debugging."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - User Experience
triggers:
  - "wire adapter data is undefined even though the record exists"
  - "querySelector returns null inside a connected LWC component"
  - "custom event dispatched but parent component never receives it"
  - "LWC component shows nothing after connectedCallback completes"
  - "NavigationMixin navigate throws an error or does nothing"
  - "third-party JavaScript library throws access denied in LWC"
  - "slot content is not rendering or is missing in the child component"
  - "error boundary not catching exceptions thrown in child LWC"
  - "LWC debug mode console errors how to interpret them"
  - "shadow DOM cannot find element across component boundary"
tags:
  - lwc-runtime-errors
  - wire-adapter
  - shadow-dom
  - navigation-mixin
  - lwc-debugging
  - lightning-locker
  - lightning-web-security
  - event-propagation
  - slot-projection
  - error-boundary
inputs:
  - "the browser console error message or stack trace"
  - "whether Lightning Web Security (LWS) or legacy Locker Service is active in the org (Setup > Session Settings)"
  - "whether debug mode is enabled for the org (Setup > Lightning Components)"
  - "the component's lifecycle phase where the error first appears (connectedCallback, renderedCallback, wire handler, event handler)"
  - "any third-party JavaScript libraries the component loads"
  - "the component's shadow access mode if it overrides the default (open vs closed vs any)"
outputs:
  - "root cause identification and fix for the specific runtime error"
  - "corrected wire adapter usage pattern with proper error/data destructuring"
  - "event propagation configuration (bubbles, composed) for the target boundary"
  - "shadow-boundary-safe DOM traversal approach"
  - "checker report from scripts/check_common_lwc_runtime_errors.py"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Common LWC Runtime Errors

Use this skill when a Lightning Web Component compiles and deploys successfully but fails at runtime — producing console errors, blank UI areas, missing data, or unhandled exceptions. The skill covers the eight highest-frequency LWC runtime error categories: wire adapter failures, shadow DOM boundary violations, event propagation misconfiguration, async rendering timing bugs, NavigationMixin errors, Locker vs LWS conflicts, slot projection problems, and missing error boundaries.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Enable debug mode** — Setup > Lightning Components > Enable Debug Mode. Without it, minified stack traces make root-cause analysis impractical. Debug mode also surfaces additional LWC framework warnings in the console.
- **Identify the security model** — Is the org using Lightning Web Security (LWS) or legacy Locker Service? LWS allows more permissive DOM operations and broader third-party library compatibility. Locker Service blocks many native DOM APIs. Check Setup > Session Settings.
- **Identify the lifecycle phase** — Most runtime errors occur in a specific hook: `connectedCallback`, `renderedCallback`, a `@wire` handler, or an event handler. Knowing the phase narrows the cause immediately.
- **Collect the full console error** — LWC runtime errors from the framework often include a component stack alongside the JS stack. Both are needed to locate the failing component boundary.
- **Check if a wire adapter is involved** — Wire errors surface as `undefined` data rather than thrown exceptions. The `error` property of the wire object is the primary diagnostic signal.

---

## Core Concepts

### Wire Adapter Response Structure

`@wire` adapters return a reactive object with two properties: `data` and `error`. Neither is available synchronously on component initialization — both are `undefined` until the wire service resolves or rejects the request. This is the source of the most common LWC runtime error: accessing `this.wiredResult.data.fields` before the response arrives.

The correct pattern is to guard every access on both properties:

```js
@wire(getRecord, { recordId: '$recordId', fields: FIELDS })
wiredRecord({ data, error }) {
    if (data) {
        this.record = data;
    } else if (error) {
        this.errorMessage = reduceErrors(error);
    }
}
```

The wire handler fires twice on first load for many adapters: once with `{ data: undefined, error: undefined }` and once with the resolved result. Template expressions must handle the undefined state without throwing.

Wire responses are also cached by the Lightning Data Service. A wire adapter may return a cached (potentially stale) result before fetching fresh data. If the component needs to force a refresh, use `refreshApex` (for LDS-backed adapters) — do not recreate the component.

### Shadow DOM and Component Boundaries

LWC enforces the shadow DOM specification: a component's template is encapsulated in its own shadow root. External components cannot reach into another component's shadow tree using standard DOM APIs. `this.template.querySelector` searches only within the current component's own shadow, not into child component shadows. Calling `document.querySelector` or `this.template.querySelector` to find an element owned by a child component returns `null` at runtime.

The correct approach is to communicate across component boundaries using the public API (`@api` properties and methods) or events — not DOM queries. If a parent genuinely needs to call a method on a child, use `@api` to expose that method and call it via a ref obtained from `this.template.querySelector` (which can reach the child's host element, not its internals).

`querySelector` on `this` (not `this.template`) is also commonly misused. `this.querySelector` is not a standard LWC API.

### Lightning Locker vs Lightning Web Security

Legacy Locker Service wraps all DOM elements in a SecureElement proxy that blocks direct prototype access, limits `eval`, and restricts access to native globals. Many third-party JavaScript libraries (jQuery, Chart.js, etc.) break under Locker because they probe the prototype chain or use restricted APIs.

Lightning Web Security (LWS), available since Winter '23 and the default for new orgs, uses a different isolation model: it distorts the JS runtime in the module scope rather than wrapping the DOM. LWS is more permissive and compatible with a wider set of libraries, but it has its own restrictions — global object access, cross-origin iframes, and unrecognized APIs may still fail.

Errors from Locker violations appear as `TypeError: Cannot read properties of undefined` or `Access check failed!` in the console. Errors from LWS violations have similar shapes but different stack frames. Identifying which model is active in the org is the first step in diagnosing any third-party library failure.

### Event Propagation and Shadow Boundaries

Custom events in LWC do not cross shadow boundaries by default. An event dispatched inside a child component's shadow with `bubbles: true` will bubble up through the child's shadow root but stop at the host element boundary — it will not reach the parent's event listener.

To cross shadow boundaries, the event must also set `composed: true`. However, `composed: true` events retarget: the `event.target` seen by the parent is the host element of the innermost shadow that dispatched it, not the original element. Code that relies on `event.target` being a specific internal element will break when `composed: true` is added.

The rule: use `bubbles: true, composed: true` only when the event genuinely needs to cross shadow boundaries. Use `bubbles: true, composed: false` (or no options) for events meant to stay within the component tree.

### NavigationMixin Page References

`NavigationMixin` requires a valid `pageReference` object. The most common failure modes are:

1. Missing or misspelled `type` property — `"standard__recordPage"` not `"standard_recordPage"`.
2. Navigating before the component is connected — `NavigationMixin.Navigate` can only be called after `connectedCallback`.
3. Using a `recordId` that is `undefined` when navigation is attempted (typically because a wire adapter hasn't resolved yet).
4. Using `standard__webPage` with a relative URL — this type requires a fully qualified URL.

Navigation failures in Experience Cloud pages have an additional constraint: the target page type must exist in the Experience Builder site map. Navigating to a page type not configured in the site produces a silent no-op.

---

## Common Patterns

### Pattern 1: Defensive Wire Handler with Error Normalization

**When to use:** Any `@wire` call where the component renders wire data in the template. This is the correct baseline for every wire usage.

**How it works:**

```js
import { LightningElement, wire, api } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import ACCOUNT_NAME from '@salesforce/schema/Account.Name';
import ACCOUNT_INDUSTRY from '@salesforce/schema/Account.Industry';

const FIELDS = [ACCOUNT_NAME, ACCOUNT_INDUSTRY];

export default class AccountDetail extends LightningElement {
    @api recordId;

    accountName;
    accountIndustry;
    errorMessage;
    isLoading = true;

    @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
    handleAccount({ data, error }) {
        this.isLoading = false;
        if (data) {
            this.accountName = getFieldValue(data, ACCOUNT_NAME);
            this.accountIndustry = getFieldValue(data, ACCOUNT_INDUSTRY);
            this.errorMessage = undefined;
        } else if (error) {
            // error is an array of error objects when using LDS wire adapters
            this.errorMessage = Array.isArray(error.body)
                ? error.body.map(e => e.message).join(', ')
                : error.body?.message ?? 'Unknown error';
        }
    }
}
```

Template guards:

```html
<template>
    <template lwc:if={isLoading}>
        <lightning-spinner alternative-text="Loading"></lightning-spinner>
    </template>
    <template lwc:elseif={errorMessage}>
        <p class="slds-text-color_error">{errorMessage}</p>
    </template>
    <template lwc:else>
        <p>{accountName} — {accountIndustry}</p>
    </template>
</template>
```

**Why not the alternative:** Accessing `this.wiredResult.data.fields.Name.value` directly without guards throws `TypeError: Cannot read properties of undefined` on initial render because the wire hasn't resolved. This is the single most common LWC runtime error.

### Pattern 2: Cross-Boundary Event with Composed Flag

**When to use:** A deeply nested child component needs to notify an ancestor outside its shadow tree.

**How it works:**

In the child component that originates the event:

```js
// Child dispatches with composed so the event crosses shadow boundaries
handleSave() {
    this.dispatchEvent(new CustomEvent('recordsaved', {
        bubbles: true,
        composed: true,
        detail: { recordId: this.recordId }
    }));
}
```

In the parent template (event listener on the child host element):

```html
<c-child-form onrecordsaved={handleRecordSaved}></c-child-form>
```

In the parent JS:

```js
handleRecordSaved(event) {
    // event.target is the child host element (c-child-form), not the button inside it
    const { recordId } = event.detail;
    // use event.detail, not event.target, to get payload data
}
```

**Why not the alternative:** Omitting `composed: true` means the event stops at the child's shadow boundary. The parent's `onrecordsaved` listener never fires. No error is thrown — the parent silently receives nothing.

### Pattern 3: Safe DOM Access Across Component Lifecycle

**When to use:** A component needs to read or write DOM state (dimensions, focus, third-party widget initialization) after rendering.

**How it works:**

```js
import { LightningElement } from 'lwc';

export default class ChartWrapper extends LightningElement {
    chart;

    renderedCallback() {
        // renderedCallback fires after every render cycle.
        // Guard against re-initialization on subsequent renders.
        if (this.chart) return;

        // this.template.querySelector is scoped to this component's shadow only.
        const canvas = this.template.querySelector('canvas');
        if (!canvas) return; // element not yet in DOM on this render cycle

        // Initialize third-party chart library on the canvas element.
        // Under LWS the canvas element is accessible; under legacy Locker it may be wrapped.
        this.chart = new window.Chart(canvas, { type: 'bar', data: this.chartData });
    }

    disconnectedCallback() {
        // Always clean up resources when the component is removed.
        if (this.chart) {
            this.chart.destroy();
            this.chart = undefined;
        }
    }
}
```

**Why not the alternative:** Initializing a third-party library in `connectedCallback` fails because the template has not rendered yet — `this.template.querySelector` returns `null`. DOM elements are only guaranteed to exist in `renderedCallback`.

---

## Decision Guidance

| Symptom | Likely Cause | First Check |
|---|---|---|
| `TypeError: Cannot read properties of undefined` on wire data | Wire not resolved yet; no guard on `data` | Add `if (data)` guard in wire handler |
| `querySelector` returns `null` | Querying across a shadow boundary or before render | Use `this.template.querySelector`; move to `renderedCallback` |
| Custom event not received by parent | Missing `composed: true` | Add `composed: true` if event must cross shadow boundary |
| NavigationMixin does nothing | Invalid pageReference `type` or undefined `recordId` | Log `pageReference` before calling Navigate; check `type` spelling |
| Third-party library throws `Access check failed` | Locker Service restriction | Confirm which security model is active; consider LWS migration |
| Slot content missing or blank | Named slot mismatch or reactive data not passed | Verify `slot="name"` attribute matches template `<slot name="name">` |
| Error in child component not caught | No error boundary (`errorCallback`) in parent | Implement `errorCallback` in the parent LWC |
| Blank UI after `connectedCallback` | Async work not triggering reactivity | Assign result to a reactive property; use `@track` or class field |
| `refreshApex` does nothing | Called on a non-LDS wire result | Only `refreshApex` works for LDS-backed adapters; use imperative call for Apex wires |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner diagnosing a runtime error:

1. **Enable debug mode and collect the full error** — Setup > Lightning Components > Enable Debug Mode for the user. Capture the complete console output including component stack, not just the JS error line. Note the lifecycle hook where the error occurs.
2. **Identify the error category** — Map the error to one of the eight categories: wire failure, shadow DOM violation, event propagation, async timing, NavigationMixin, Locker/LWS conflict, slot projection, or missing error boundary. The Decision Guidance table above is the fastest path to categorization.
3. **Apply the category-specific fix** — Use the pattern for that category from the Common Patterns section. Wire errors need defensive handlers and template guards. Event errors need `bubbles`/`composed` audit. DOM errors need lifecycle and boundary audit.
4. **Check the security model** — If the error involves DOM access or a third-party library, confirm whether LWS or Locker is active. Under Locker, native DOM API behavior is different. The fix may differ depending on the active model.
5. **Validate with the checker script** — Run `python3 scripts/check_common_lwc_runtime_errors.py --manifest-dir path/to/lwc` to catch common anti-patterns across all LWC files in the project.
6. **Test in debug mode** — Reload the page with debug mode still enabled. Confirm the error is gone and no new warnings appear. Test the error path (e.g., wire failure, navigation to a missing record) to confirm graceful handling.
7. **Review the checklist** — Run through the Review Checklist below before marking the fix complete.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All `@wire` handlers guard against `undefined` data and surface the `error` property when set.
- [ ] Template expressions that read wire data are guarded with `lwc:if` or optional chaining.
- [ ] No `querySelector` calls attempt to reach into a child component's shadow tree.
- [ ] DOM access that requires rendered elements is performed in `renderedCallback`, not `connectedCallback`.
- [ ] Custom events that must cross shadow boundaries set `composed: true`.
- [ ] `event.detail` is used for event payload data; `event.target` is not used to reach internal elements across boundaries.
- [ ] NavigationMixin `pageReference` uses the correct `type` string and all required properties are defined before navigation is called.
- [ ] Third-party library initialization is guarded against the security model (LWS vs Locker).
- [ ] Slot names in the parent template match the `name` attribute on `<slot>` elements in the child template.
- [ ] Parent components that render child components implement `errorCallback` to catch and surface child errors.
- [ ] `disconnectedCallback` cleans up timers, third-party instances, and event listeners added outside the LWC event system.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Wire fires with `undefined, undefined` before it resolves** — The wire handler is called at least once with `{ data: undefined, error: undefined }` before the adapter returns a result. Code that checks `if (!data && !error)` to show a spinner must also handle the case where neither is set yet. Failing to do so causes a flash of incorrect state.
2. **`refreshApex` only works with LDS-backed wires** — `refreshApex` accepts the wired property object. If the wire calls an Apex method directly (not an LDS adapter like `getRecord`), `refreshApex` silently does nothing. The correct approach for Apex-wired data is to use an imperative Apex call or re-trigger the wire by changing a reactive `$property`.
3. **`renderedCallback` fires on every re-render, not just once** — Any DOM initialization code in `renderedCallback` without a guard will run on every render cycle, potentially creating duplicate instances of third-party widgets or causing memory leaks. Always guard with an instance check or a boolean flag.
4. **`composed: true` retargets `event.target`** — When a `composed: true` event crosses a shadow boundary, the listener receives the host element as `event.target`, not the originating element inside the shadow. Payload data must be passed via `event.detail`, not read from `event.target`.
5. **Slot content reactivity is limited** — Data passed to slotted content via the parent template is reactive in the parent, but the child component cannot observe changes to slotted content after initial render without using `slotchange` event listeners. A common bug is expecting slot content to update reactively in response to child state changes that are not propagated via `@api`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Wire handler fix | Corrected wire handler with `data`/`error` guard and template guards for each access |
| Event configuration | `CustomEvent` constructor options (`bubbles`, `composed`) correct for the target boundary |
| Shadow-safe DOM pattern | `renderedCallback`-based initialization with `this.template.querySelector` scoped correctly |
| NavigationMixin fix | Corrected `pageReference` object with valid `type` and all required state properties |
| Checker report | Per-file findings from `scripts/check_common_lwc_runtime_errors.py` |

---

## Related Skills

- `lwc/lwc-dynamic-components` — use when the runtime error involves `lwc:component`, `lwc:is`, or dynamic `import()` patterns specifically.
- `lwc/lwc-performance` — use when the issue is sluggish rendering or excessive re-renders rather than hard errors.
