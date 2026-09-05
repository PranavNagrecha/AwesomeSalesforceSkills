# LLM Anti-Patterns — LWC Error Boundaries

Scope: `errorCallback(error, stack)` and the wrapper-component pattern built on it. What to
do with an error once caught — toast copy, variants, notification containers — belongs to
`lwc/lwc-toast-and-notifications`; the runtime error messages themselves are catalogued in
`lwc/common-lwc-runtime-errors`; Apex-side exception design belongs to
`apex/exception-handling`.
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
✅ Read the provisioned error and branch on it — and branch on the *body shape* too,
because `getRecord` is a UI API read and its `error.body` is an array
(`lwc_guide data-error L6568`):

```javascript
@wire(getRecord, { recordId: '$recordId', fields: FIELDS })
wiredRecord({ data, error }) {
    if (error) {
        // FetchResponse: error.status (e.g. 404), error.statusText (e.g. NOT_FOUND),
        // error.body defined by the underlying API (lwc_guide data-error L6548-L6551)
        this.messages = Array.isArray(error.body)
            ? error.body.map((e) => e.message)
            : [error.body?.message ?? error.statusText];
    } else if (data) {
        this.record = data;
    }
}
```

Source: Handle Errors (wire `error` property, `FetchResponse` shape) — https://developer.salesforce.com/docs/platform/lwc/guide/data-error.html

## Anti-Pattern 5: Choosing the boundary's height by tidiness rather than by blast radius

Generated code reaches for a single wrapper at the root because it reads cleanly. The guide
does not forbid that — "You can wrap the entire app, or every individual component. Most
likely, your architecture falls somewhere in between" (`lwc_guide
create-lifecycle-hooks-error L4160`). What the guide *does* fix is the cost: when an error
is thrown the subtree below the boundary "is unmounted and removed from the DOM" (`L4162`),
and the framework "unmounts the component during rerender" (`L4165`). So a root-level
boundary is a decision to lose the whole page on any single failure, and an assistant that
picks it for symmetry has made that decision without noticing.

❌ `<c-error-boundary>` wrapping the entire dashboard because it is one tag instead of six.
✅ Size the boundary to what you are willing to lose in one go. The test is: if this subtree
disappears, can the user still do something useful on this page? If not, the boundary is
too high — not because the guide forbids it, but because the unmount takes everything with
it.

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
✅ Record it. Send the component name, the reduced message and the `stack` string to
whatever the org already uses for logging. `error` is a native JavaScript error object and
`stack` is a string (`lwc_guide create-lifecycle-hooks-error L4164`) — pull the fields out
by name rather than handing the whole object to a serialiser, because a native `Error`'s own
properties are non-enumerable and `JSON.stringify(error)` produces `{}`. Send from the boundary, not from each widget, so
instrumentation arrives with the wrapper rather than being remembered per component. Guard
the reporting call itself with `try/catch`: a logger that throws inside `errorCallback` is
a failure inside the failure handler.

## Anti-Pattern 8: Reading `error.body.message` without checking whether `body` is an array

The single most common way a boundary reports nothing useful. `error.body` is an **array of
objects** for a UI API read such as `getRecord`, and an **object** for a UI API write, for
Apex, and for a network failure (`lwc_guide data-error L6568–L6571`). Assistants write one
accessor for all four, and the `getRecord` case silently yields `undefined`.

❌ `this.message = error.body.message;`
✅ Branch on the shape, the way the guide's own snippet does (`lwc_guide data-error
L6555–L6557`):

```javascript
if (Array.isArray(error.body)) {
    this.messages = error.body.map((e) => e.message);
} else if (typeof error.body?.message === 'string') {
    this.messages = [error.body.message];
} else {
    this.messages = [error.statusText];   // FetchResponse fallback (L6551)
}
```

Better still, normalise once in a shared module and import it from the boundary and from
every child — see `references/code-examples.md`, Bundle 1.

## Anti-Pattern 9: Rethrowing from `errorCallback` to "let something upstream handle it"

There is nothing upstream that improves the outcome. An unhandled error propagates to the
parent component and then to the enclosing app, which shows the "A Component Error has
occurred!" or "Something went wrong" popup with the message and stack trace (`lwc_guide
data-error-types L7732`) — the blank-page failure the boundary was added to prevent. The
framework has already unmounted the throwing subtree by this point (`lwc_guide
create-lifecycle-hooks-error L4165`), so the rethrow buys no cleanup either.

❌ `errorCallback(error) { this.log(error); throw error; }`
✅ Set state, report, and stop. If a *higher* boundary genuinely needs to know, dispatch a
custom event — the guide's own recommendation is to "propagate errors from child components
and then handle errors in parent components" via `throw` **or** a custom event (`lwc_guide
data-error-types L7743–L7744`), and the event version does not unmount anything.

UNVERIFIED (2026-09-05): the guide never states whether rethrowing from `errorCallback`
specifically is permitted. The position above is derived from what an unhandled error does
(L7732) and from the unmount already having happened (L4165), not from a direct statement
about rethrow.

## Anti-Pattern 10: A fallback that shows the raw error object

`error.body.stackTrace` names the Apex class and line that threw when the Apex method did
not catch (`lwc_guide apex-error-handling L7518`). A fallback that renders
`{JSON.stringify(error)}` for "debuggability" puts internal class names in front of whoever
loads the page, including on an Experience Cloud site.

❌ `<pre>{errorJson}</pre>` in the fallback template.
✅ Render the normalised messages; send `body.stackTrace` and the `stack` string to
telemetry. Have Apex throw `AuraHandledException`, which omits `body.stackTrace` entirely
(`lwc_guide apex-error-handling L7521`) — see `apex/exception-handling`.
