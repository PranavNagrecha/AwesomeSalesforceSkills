# Gotchas — LWC Error Boundaries

Every claim below cites the crawled Lightning Web Components Developer Guide as
`lwc_guide <page-slug> L<n>`, or carries an UNVERIFIED marker.

The hook's own contract — what `errorCallback` captures, and where it sits in the
lifecycle — is owned by `lwc/lifecycle-hooks`. The gotchas here are about the boundary
*component*: what its fallback can and cannot do, what shape the error arrives in, and how
retry, telemetry and slots interact.

## Gotcha 1: Async errors uncaught

**What happens:** A rejected promise never reaches `errorCallback`. The tile renders empty
with a clean console and the boundary stays silent.

**When it occurs:** `fetch`, an imperative Apex call, or a `setTimeout` callback inside
`connectedCallback`. The guide's own worked example: a `throw` inside a `setTimeout`
callback is not caught by the surrounding `try/catch`, because "the try-catch block can
handle exceptions in synchronous code only … only errors within a single transaction are
caught" (`lwc_guide data-error L6513`, L6524).

**How to avoid:** Put the `try/catch` *inside* the callback, not around the call that
schedules it (`lwc_guide data-error L6525`), and give the component its own error state.

---

## Gotcha 2: A boundary above the whole app is legal and still costs the whole app

**What happens:** Every localised failure blanks everything below the boundary.

**When it occurs:** One wrapper at the page root. This is not a rule violation — the guide
says placement is yours: "You can wrap the entire app, or every individual component. Most
likely, your architecture falls somewhere in between" (`lwc_guide
create-lifecycle-hooks-error L4160`). What makes it expensive is the unmount: when an error
is thrown the throwing subtree "is unmounted and removed from the DOM" (`L4162`), and the
framework "unmounts the component during rerender" (`L4165`).

**How to avoid:** Size the boundary to what you are willing to lose in one go. The test is
whether the user can still do something useful on the page after that subtree disappears.

---

## Gotcha 3: A fallback with dependencies fails inside the failure handler

**What happens:** The fallback throws while rendering, and there is no second boundary
above this one to catch it, so the error propagates to the parent and then to the enclosing
app — which shows the "A Component Error has occurred!" or "Something went wrong" modal
(`lwc_guide data-error-types L7732`).

**When it occurs:** A fallback that renders another custom component, calls a wire adapter,
or formats the very data that may be the reason the boundary fired.

**How to avoid:** Static markup, SLDS classes, at most a base component or two. Wrap the
telemetry call in its own `try/catch` for the same reason.

---

## Gotcha 4: `error.body` is an array for a UI API read and an object for everything else

**What happens:** `error.body.message` returns `undefined` for a `getRecord` failure — the
message exists, but one level down inside an array element — so the user sees a blank error
box while the real message sits in memory.

**When it occurs:** Any code that reads `error.body.message` without checking the shape
first. The four cases are stated explicitly: UI API **read** operations such as `getRecord`
return `error.body` as an **array of objects**; UI API **write** operations such as
`createRecord` return an **object**, often with object-level and field-level errors; Apex
read and write operations return an **object**; network errors such as offline return an
**object** (`lwc_guide data-error L6568–L6571`).

**How to avoid:** Branch on `Array.isArray(error.body)` before reading `.message` — the
guide's own snippet does exactly that (`lwc_guide data-error L6555–L6557`). Normalise once
in a shared module (`references/code-examples.md`, Bundle 1) rather than at each call site.

---

## Gotcha 5: An unhandled Apex exception ships the Apex class name to the browser

**What happens:** `error.body.stackTrace` arrives at the client containing the Apex class
and line number. A boundary that renders `error.body` for debugging puts internal class
names on a customer-facing page.

**When it occurs:** The Apex method threw without a `try/catch`, so "the error is returned
directly from Apex and surfaces the … class name in the `body.stackTrace` property"
(`lwc_guide apex-error-handling L7518`). Throwing `AuraHandledException` instead produces a
message that "includes your custom message and the one returned from Apex … But the error
doesn't include the `body.stackTrace` property" (`L7521`).

**How to avoid:** Have Apex throw `AuraHandledException`, and on the client keep
`body.stackTrace` in the telemetry payload only, never in the rendered message. The Apex
side of this is `apex/exception-handling`.

---

## Gotcha 6: `lwc:if` cannot evaluate an expression, so `lwc:if={!hasError}` silently fails

**What happens:** The negated branch never renders — or the template fails to compile —
because the directive is not evaluating what the author thinks it is.

**When it occurs:** Writing the boundary's healthy branch as `lwc:if={!hasError}` instead of
`lwc:else`. "The expression passed in to `lwc:if` and `lwc:elseif` supports simple dot
notation. Complex expressions like `!condition`, `object?.property?.condition` or
`sum % 2 === 1` aren't supported. To compute such expressions, use a getter in the
JavaScript class" (`lwc_guide reference-directives L19510`). Two more constraints bite the
same template: `lwc:elseif` and `lwc:else` must be *immediately* preceded by a sibling
conditional, with no text or element between them (`L19506`, `L19512`), and the outer
`<template>` root must carry no directive at all — the symptom is `LWC1077: Invalid
template tag` (`lwc_guide create-conditional L1519`).

**How to avoid:** `lwc:if={hasError}` / `lwc:else`, and a getter for anything that is not a
plain property lookup.

---

## Gotcha 7: A conditional slot renders correctly with `lwc:if` and warns with `if:true`

**What happens:** With the legacy directives, the compiler warns about duplicate slots and
the retry re-mount is unreliable, because the compiler cannot prove the `<slot>` renders
only once.

**When it occurs:** Wrapping `<slot>` in `<template if:true={...}>`. "The template compiler
treats the conditional directives as a valid use case, and it knows that `<slot>` isn't
rendered twice. If you use the legacy `if:true` and `if:false` directives, the compiler
warns you about duplicate slots because it's not clear if `<slot>` will only render once"
(`lwc_guide create-components-slots L2169–L2172`). `if:true` / `if:false` are no longer
recommended generally (`lwc_guide create-conditional L1504`).

**How to avoid:** Nest the `<slot>` inside a `<template>` carrying `lwc:if` / `lwc:else`.

---

## Gotcha 8: The boundary cannot query the component it is wrapping

**What happens:** `this.template.querySelector('c-revenue-tile')` returns `null` inside the
boundary, so a boundary that tries to inspect or reset its child by DOM lookup does nothing
and reports success.

**When it occurs:** Any boundary that reaches into slotted content. "The `<slot></slot>`
element is part of a component's shadow tree. To access elements in its shadow tree, a
component calls `this.template.querySelector()` … However, the DOM elements that are passed
into the slot aren't part of the component's shadow tree. To access elements passed via
slots, a component calls `this.querySelector()` and `this.querySelectorAll()`"
(`lwc_guide create-components-slots L2160–L2161`). And never query by `id`: "When an HTML
template is rendered, `id` values can be transformed into globally unique values"
(`L2168`).

**How to avoid:** Do not reach into the child at all. Re-mount it by toggling the
conditional that wraps the `<slot>`, which the framework handles, and let the child rebuild
its own state.

---

## Gotcha 9: Toggling the retry flag twice in one synchronous block is a no-op

**What happens:** The Retry button appears to do nothing. The child is never torn down, so
its `connectedCallback` never runs again and the stale error state survives.

**When it occurs:** `this.showChild = false; this.showChild = true;` in one handler.
Rerendering on a property change is asynchronous — "Component rerendering upon a property
change is asynchronous, so the order in which something is added to the DOM isn't always
predictable" (`lwc_guide unit-testing-using-jest-patterns L12590`), and a state mutation
enqueues "a microtask rerender" rather than rendering immediately (`lwc_guide
create-lifecycle-hooks-rendered L4131`). Both writes land in the same microtask, so the
engine sees no change. The re-mount itself is real: `lwc:if` "removes and inserts DOM
elements based on whether the data is a truthy or falsy value" (`lwc_guide create-conditional
L1506`), and a reinserted component runs `connectedCallback` again — the hook "can fire more
than one time" (`lwc_guide create-lifecycle-hooks-dom L4111`).

**How to avoid:** Set the flag false, then set it true from a resolved promise so the two
writes fall in different rerender passes. Cap the attempts; a deterministic failure will
otherwise loop.

UNVERIFIED (2026-09-05): the guide does not document a canonical remount idiom for
`lwc:if`, and `key`-driven diffing is documented only for `for:each` iteration elements
(`lwc_guide create-lifecycle-hooks-rendered L4134`). The two-tick toggle is derived from the
rerender and conditional-directive behaviour cited above, not stated as a pattern anywhere
in the guide.

---

## Gotcha 10: `platformShowToastEvent` is silent on an LWR Experience Cloud site

**What happens:** The boundary catches, the telemetry lands, and the user is told nothing,
because the toast module the code imported does not work in that container.

**When it occurs:** A boundary or tile that imports `lightning/platformShowToastEvent` and
is placed on an Experience Cloud page. That module "uses an event-based mechanism to display
a toast, and it's not supported in environments like LWR sites for Experience Cloud or
standalone apps" (`lwc_guide base-components-patterns L4773`), and is also unsupported "on
login pages in Aura sites" (`lwc_guide use-toast L10449`). `lightning/toast` is "the
preferred method to display a toast" (`use-toast L10448`).

**How to avoid:** Import `lightning/toast` and call `show()`. If a bundle's
`.js-meta.xml` lists `lightningCommunity__Default` (`lwc_guide
reference-configuration-tags L18722`), treat any `platformShowToastEvent` import in that
bundle as a defect — the checker in `scripts/check_lwc_error_boundaries.py` flags exactly
this pair. Toast copy, variants and container limits belong to
`lwc/lwc-toast-and-notifications`.
