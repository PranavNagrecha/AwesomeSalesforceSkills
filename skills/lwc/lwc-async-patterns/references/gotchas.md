# Gotchas — LWC Async Patterns

Five behaviors of async / Promise code in LWC that surprise
practitioners after the first `await` works. These are the
second-order issues that compound the basics in `SKILL.md` —
the things that go wrong once you try to combine `@wire`,
imperative Apex, lifecycle hooks, and global timers in a real
component.

---

## Gotcha 1: `@wire` cannot be awaited — it's reactive provisioning, not a Promise

**What happens:** A practitioner who knows `await fetch(...)` and
`await getData()` tries to write
`const account = await this.wiredAccount;` to "wait for the wire to
resolve before calling the next service." The expression evaluates
to whatever the field currently holds (often `undefined` on first
render) and the `await` resolves immediately — the next line runs
with no account data. The component appears to load random subsets
of data depending on timing.

**When it occurs:** Any time a developer tries to chain "wire fires
→ pass that data to another call." Common shapes: a wired
`getRecord` followed by an imperative Apex call that needs the
wired record's `AccountId`, or a wired user-info call feeding a
permission-check service. The wire decorator returns its value into
a property (or a `{ data, error }` parameter object on a function
target) — it's a reactive *push* primitive subscribed by the LWC
engine, not a Promise the developer can `await`.

**How to avoid:** For "do X *then* call Y with X's result," skip
`@wire` entirely on the leading call and use imperative Apex for
both steps — that's the shape `await` was designed for. Per the
official wire-service docs, "Don't depend on receiving data from a
wire adapter at any specific point in your component lifecycle"
and "The wire service delegates control flow to the Lightning Web
Components engine" — which is exactly the wrong tradeoff when you
need control flow. Keep `@wire` for the case it's actually good at:
reactive read-only data that should auto-refresh when a `$reactive`
variable changes. The moment the data feeds another call, switch to
imperative.

If you must mix the two (e.g., wired record on the page plus an
imperative action that needs its `Id`), watch the wired property
inside a getter and only kick off the imperative work when the
wired data has actually arrived. The cleanest version uses a
function-target wire:

```javascript
@wire(getRecord, { recordId: '$recordId', fields: [ACCOUNT_ID_FIELD] })
wiredAccount({ data, error }) {
    if (error) { this.error = error.body?.message; return; }
    if (data && !this._didFetchRelated) {
        this._didFetchRelated = true;
        this.loadRelatedRecords(data.fields.Id.value);
    }
}
```

The `_didFetchRelated` guard prevents the imperative call from
re-firing every time the wire re-provisions (which it will, every
time the parent passes a new `recordId` or invalidates the cache).

---

## Gotcha 2: Returning a Promise from `connectedCallback` is allowed but errors are silently swallowed unless `.catch()`'d

**What happens:** A practitioner writes
`async connectedCallback() { this.data = await getData(); }`. The
`getData()` call rejects (server is down, validation fires, FLS
denial). The component renders nothing, no spinner ever clears
because none was set, no error banner appears, and the browser
console shows a vague "Uncaught (in promise)" warning that doesn't
include the LWC component name. The user sees a blank panel and
files a ticket; the developer can't reproduce it because the local
dev org has no issue with the call.

**When it occurs:** Any LWC where an `async` lifecycle hook lacks a
`try`/`catch` around the awaited work. Hits hardest in production —
the local org's record-data, FLS, and validation rules all align
with the developer's expectations; the rejection only happens for
some user populations. Also fires when a wired function-target
callback dispatches an `await`-bearing helper without catching
inside the helper.

**How to avoid:** Treat every `async` lifecycle hook
(`connectedCallback`, `renderedCallback`, `disconnectedCallback`)
as a place where rejections will be lost without explicit handling.
Wrap the awaited work in `try`/`catch`/`finally` exactly as
`SKILL.md` Example 1 shows. The framework does NOT promote
uncaught Promise rejections from a lifecycle hook into
`errorCallback`. The official `errorCallback` docs scope coverage
to errors in descendant components' lifecycle hooks and template-
declared event handlers; it explicitly does not catch errors from
programmatically-assigned handlers, and the docs do not document
coverage of unhandled Promise rejections at all. Treating
`errorCallback` as a safety net for missing `.catch()` is wishful
thinking — surface the error yourself.

If a helper method is awaited from a lifecycle hook and that helper
already has its own try/catch, you're fine. If the lifecycle hook
directly awaits a Promise-returning function without catching,
you'll lose every server-side error to the browser console.

---

## Gotcha 3: Server calls inside `renderedCallback` without a one-shot guard fire on EVERY re-render — infinite loop common

**What happens:** A practitioner moves their data-loading code into
`renderedCallback` because `connectedCallback` was firing before
`@api` properties had been hydrated by the parent. The call now
fires when the data arrives — but it also fires every time anything
in the template re-renders. The call's success path assigns to a
`@track` field, which causes a re-render, which re-fires the call,
which re-assigns, which re-renders. Either the org's per-transaction
limits kill it after a few hundred invocations or the browser tab
becomes unresponsive.

**When it occurs:** Practitioners migrating from Aura's
`{!v.recordId}` reactive pattern who reach for `renderedCallback`
as a "load data once the DOM is ready" hook. Per the official
lifecycle docs, `renderedCallback()` "fires multiple times" and
"components rerender whenever tracked state changes" — including
state the callback itself sets. The docs recommend "using a boolean
field like `hasRendered` to track whether `renderedCallback()` has
been executed."

**How to avoid:** Guard every `renderedCallback` server call with a
one-shot boolean:

```javascript
renderedCallback() {
    if (this._didLoad) return;
    this._didLoad = true;
    this.loadData();        // async helper with its own try/catch
}
```

For data that should refetch when an `@api` property changes,
prefer a property setter:

```javascript
_recordId;
@api
get recordId() { return this._recordId; }
set recordId(value) {
    this._recordId = value;
    if (value) this.loadData();
}
```

The setter fires once per real change, not once per re-render —
exactly the semantic the developer wanted. `renderedCallback` is
the right place for DOM-measurement work (computing a child's
height, integrating a third-party canvas library) where you genuinely
do need to react to every paint; it is the wrong place for
single-shot server calls.

---

## Gotcha 4: `setTimeout` / `setInterval` are not blanket-blocked, but they ARE constrained — and ESLint will complain

**What happens:** A practitioner writes
`setTimeout(() => this.refresh(), 5000);` and ESLint (under the
recommended `@salesforce/eslint-plugin-lwc` config) flags it as
restricted global usage. Depending on the project's rule set, the
build either fails outright or emits a warning the developer
silently ignores. The runtime behavior under Lightning Web Security
(LWS) is also subtly different from native — the timer fires in a
sandboxed context that wraps DOM access through LWS proxies, so any
callback that touches the parent window or top-frame surface
behaves unexpectedly.

**When it occurs:** Custom polling loops, debounced search inputs
written without a helper utility, integrations with third-party
libraries that schedule callbacks. The ESLint rule names to know:
`@lwc/lwc/no-async-operation` (the canonical name from
`@salesforce/eslint-plugin-lwc`) flags `setTimeout`, `setInterval`,
`setImmediate`, and `requestAnimationFrame` as discouraged inside
LWC.

**How to avoid:** Two acceptable routes. First, use
`window.setTimeout` / `window.setInterval` explicitly so the call
is namespaced under the LWS-virtualized `window` object — this is
the form most teams reach for when the rule fires, paired with an
ESLint suppress comment on the specific line:

```javascript
// eslint-disable-next-line @lwc/lwc/no-async-operation
this._refreshTimer = window.setTimeout(
    () => this.refresh(),
    5000
);
```

Second, and usually better, refactor away from the timer. For
debounced inputs, a 300ms `setTimeout` is fine and conventional,
but always clear the prior timer on each call and clear it again in
`disconnectedCallback` so the timer doesn't fire against an
unmounted component. For polling, `lightning/empApi` (Streaming API
subscription) or `lightning/refresh.RefreshEvent` is almost always
the right primitive — neither requires timers, and both integrate
with the LWC cache invalidation story. If you must keep a timer,
treat the cleanup hook as mandatory: cancel from
`disconnectedCallback` and inside the timer callback itself check
that `this` is still attached before touching state.

The exact restrictions on global APIs differ between Lightning
Locker (legacy) and Lightning Web Security (modern). LWS imposes
fewer restrictions than Locker in many cases but uses namespace
isolation that changes how proxies wrap DOM-touching callbacks.
Per the LWS-vs-Locker docs, "your code already abides by the
security practices that Lightning Locker also requires" — so most
working Locker code works under LWS, but assume any global timer or
event handler runs in a sandboxed context, not the raw window.

---

## Gotcha 5: Errors thrown in async event handlers don't bubble to LWC's error boundary unless dispatched as `CustomEvent('error')` — silent failure mode

**What happens:** A practitioner places an `errorCallback` in a
parent component expecting it to catch any error from child
components ("we have an error boundary now, we're covered"). A
child's `onclick` handler does
`async handleClick() { await callApi(); }` and the API rejects.
`errorCallback` does NOT fire. The error logs to the browser
console with no LWC component context; the user-facing toast or
banner the team relied on for visibility never appears.

**When it occurs:** Any async event handler — `onclick`, `onchange`,
`oninput`, `onsubmit` — that awaits server work without catching
locally. Common in forms with imperative save handlers, in
button-driven search components, in any "fire and forget" pattern.
Per the official errorCallback docs, the hook catches errors
"occurring in lifecycle hooks" and errors "in event handlers
declared in the HTML template" — but explicitly does not catch
"errors from programmatically assigned event handlers" and does not
document coverage of unhandled Promise rejections from any kind of
handler. Treating `errorCallback` as a safety net for missing
`.catch()` inside async event handlers is a misread of what the
boundary covers.

**How to avoid:** Two patterns work. First, the standard one — wrap
every async event handler in try/catch and surface the error
explicitly via `ShowToastEvent` or an inline banner. This is the
same pattern as `SKILL.md`'s `handleLoad` example; it must be
applied per handler, not delegated to a parent boundary.

Second, when you genuinely want a parent to handle the error (e.g.,
a reusable form component should let its parent decide how to
display save failures), catch in the child and dispatch an `error`
custom event the parent listens to:

```javascript
// child
async handleSubmit() {
    try {
        await saveRecord(this.payload);
        this.dispatchEvent(new CustomEvent('success'));
    } catch (err) {
        this.dispatchEvent(new CustomEvent('error', {
            detail: {
                message: err.body?.message ?? 'Save failed.',
                cause: err
            }
        }));
    }
}

// parent template
<c-record-form onsuccess={handleSuccess}
               onerror={handleError}></c-record-form>
```

The parent's `handleError` then decides the UX — toast, modal, log,
retry button. The async error never silently disappears because the
child always either dispatches `success` or dispatches `error`; the
parent has both contracts and can rely on them.
