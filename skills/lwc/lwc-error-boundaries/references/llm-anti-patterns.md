# LLM Anti-Patterns — LWC Error Boundaries

Scope: `errorCallback(error, stack)` and the wrapper-component pattern built on it. What to
do with an error once caught — user messaging, toast copy, retry UX — belongs to
`lwc/lwc-error-handling-patterns`; Apex-side exception design belongs to the apex domain.
This file is about what `errorCallback` actually catches, which is narrower than almost
every generated example assumes.

## Anti-Pattern 1: Expecting a component to catch its own errors

The single most common mistake, and it produces a boundary that appears to work in review
and does nothing in production. `errorCallback` captures errors in the **descendant**
components in its tree. Putting it on the component that throws does not give you a
handled error — the framework calls `errorCallback` and then unmounts that component during
rerender, so the "fallback" markup goes away with it.

**Wrong** — the boundary and the risk are the same component:

```javascript
import { LightningElement, wire } from 'lwc';
import getMetrics from '@salesforce/apex/DashboardController.getMetrics';

export default class RevenueTile extends LightningElement {
    hasError = false;

    errorCallback(error) {
        this.hasError = true;      // this component threw; it is being unmounted anyway
    }

    renderedCallback() {
        this.buildChart();         // throws here -> tile disappears, fallback never shows
    }
}
```

**Right** — a separate wrapper holds the boundary, and the risky component is a child of it:

```javascript
// errorBoundary.js — owns no business logic, so it has nothing of its own to break
import { LightningElement } from 'lwc';

export default class ErrorBoundary extends LightningElement {
    hasError = false;

    errorCallback(error, stack) {
        this.hasError = true;
        // eslint-disable-next-line no-console
        console.error('Boundary caught', error, stack);
    }
}
```

```html
<!-- errorBoundary.html — fallback must not depend on anything that can also fail -->
<template>
    <template lwc:if={hasError}>
        <div class="slds-box slds-theme_shade slds-text-align_center">
            This section is unavailable.
        </div>
    </template>
    <template lwc:else>
        <slot></slot>
    </template>
</template>
```

```html
<!-- dashboard.html — one boundary per widget, not one for the page -->
<template>
    <c-error-boundary><c-revenue-tile></c-revenue-tile></c-error-boundary>
    <c-error-boundary><c-pipeline-tile></c-pipeline-tile></c-error-boundary>
</template>
```

Source: errorCallback() — https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks-error.html

## Anti-Pattern 2: Assuming the boundary catches everything the child does

`errorCallback` catches errors thrown in lifecycle hooks and in event handlers **declared in
an HTML template**. It does not catch errors from handlers attached programmatically —
if the handler was wired up in JavaScript rather than in the template, `errorCallback` is
not called when it throws. Assistants generate `addEventListener` in `connectedCallback`
out of habit and then wonder why the boundary is silent.

❌ `this.template.querySelector('button').addEventListener('click', this.handleClick);`
✅ `<lightning-button onclick={handleClick}></lightning-button>` — the declarative form is
the one the boundary can see. Where a programmatic listener is genuinely required, that
handler needs its own `try/catch`; the boundary will not help it.

## Anti-Pattern 3: Treating a boundary as a substitute for handling async failures

Generated code routinely wraps an imperative Apex call in a boundary and calls it done. A
rejected promise is not a thrown render error; it never reaches `errorCallback`. The same
applies to `setTimeout` callbacks and anything else that resumes on a later tick.

**Wrong** — nothing catches this; the tile renders empty with no signal:

```javascript
connectedCallback() {
    getMetrics({ recordId: this.recordId }).then((data) => {
        this.metrics = data;
    });                                  // no .catch, no try/catch, boundary never fires
}
```

**Right** — handle the rejection where it happens, and give the component its own error
state:

```javascript
async connectedCallback() {
    try {
        this.metrics = await getMetrics({ recordId: this.recordId });
    } catch (error) {
        this.loadError = error;          // component decides what the user sees
    }
}
```

## Anti-Pattern 4: Looking for wire errors in errorCallback

A failing wire adapter does not throw into the boundary. The error is provisioned onto the
wired property's own `error` member, and the component has to read it. Assistants that
learned React's boundary model miss this entirely, so a 404 or a `NoAccessException` from a
wire shows as a permanently empty component with a clean console.

❌ Rely on the boundary to surface a wire failure.
✅ Read the provisioned error and branch on it:

```javascript
@wire(getRecord, { recordId: '$recordId', fields: FIELDS })
wiredRecord({ data, error }) {
    if (error) {
        // FetchResponse: error.status (e.g. 404), error.statusText (e.g. NOT_FOUND),
        // error.body defined by the underlying API
        this.message = error.body?.message ?? error.statusText;
    } else if (data) {
        this.record = data;
    }
}
```

Source: Handle Errors (wire `error` property, `FetchResponse` shape) — https://developer.salesforce.com/docs/platform/lwc/guide/data-error.html

## Anti-Pattern 5: One boundary around the whole application

The pattern looks tidier with a single wrapper at the root, and it converts every localised
failure into a blank page — the exact outcome boundaries exist to prevent. Because the
framework unmounts the erroring subtree, a root-level boundary unmounts the application.

❌ `<c-error-boundary>` wrapping the entire dashboard.
✅ One boundary per independently-failing unit. The test is: if this subtree disappears,
can the user still do something useful on this page? If not, the boundary is too high.

## Anti-Pattern 6: A fallback that can fail as hard as the thing it replaces

Generated fallbacks reach for `lightning-card`, a spinner, an illustration, sometimes
another custom component. Everything the fallback depends on is a new way for the fallback
itself to throw — inside a component that is already in an error state.

❌ A fallback that renders `<c-fancy-empty-state>` with its own wire adapter.
✅ Static markup and a base class or two. No wires, no imperative calls, no child custom
components, no formatting that depends on data that may be the reason you are here.

## Anti-Pattern 7: Catching silently, so production failures are invisible

`hasError = true` and nothing else is the default generated body. The user sees a polite
grey box; nobody is told. This is strictly worse than the blank page it replaced, because
the blank page at least got reported.

❌ `errorCallback(error) { this.hasError = true; }`
✅ Record it. Send the component name, the reduced message and the `stack` string — `error`
is a native JavaScript error object and `stack` is a string, so both serialise — to whatever
the org already uses for logging. Send from the boundary, not from each widget, so
instrumentation arrives with the wrapper rather than being remembered per component. Guard
the reporting call itself with `try/catch`: a logger that throws inside `errorCallback` is
a failure inside the failure handler.
