# Well-Architected Notes — LWC Async Patterns

## Relevant Pillars

Async logic in LWC looks like a JavaScript detail, but the
architectural weight comes from how the choice between `@wire`,
imperative Apex, push subscriptions, and message-channel
broadcasting shapes the component's failure modes, the parent /
child coupling, and the latency profile under realistic data
volumes. Three pillars carry weight; the dominant one is
Operational Excellence because the difference between a polished
component and a flaky one is whether errors surface at all.

- **Operational Excellence (debuggability)** — `try`/`catch`/
  `finally` around every imperative `await`, with an
  `@track`-decorated loading flag reset in `finally`, is the
  difference between "spinner clears, banner shows, ticket is
  diagnosable" and "page is frozen, console shows
  `Uncaught (in promise)`, ticket says 'doesn't work'." The
  framework's `errorCallback` does not catch unhandled Promise
  rejections (the official docs scope it to lifecycle-hook errors
  and template-declared event handlers), so async errors that
  escape a handler land in the browser console with no LWC
  component context. Operational excellence here is the discipline
  of treating every awaited call as a place where an exception
  WILL eventually fire in production.
- **Reliability (error visibility)** — Silent failures are the
  highest-volume source of LWC support tickets in any mature org.
  A component that "works" but eats errors degrades trust faster
  than a component that throws a visible toast — users learn to
  retry the visible-error component, and learn to file tickets for
  the silent one. The `disconnectedCallback` cleanup contract is
  the other reliability lever: pending timers, in-flight
  `AbortController`s, and `lightning/empApi` subscriptions left
  alive after the component unmounts fire against a dead `this`,
  produce console warnings, and on tab-heavy pages leak memory
  until the user refreshes.
- **Performance (parallelism)** — `Promise.all` over independent
  Apex calls collapses serial round-trip latency into the cost of
  the slowest call. For three lightweight server calls at ~200ms
  apiece, that's a 600ms → 200ms win every user notices on first
  paint. The performance discipline isn't "use `Promise.all`
  everywhere" — it's classifying each call as
  *dependent on prior result* (must serialize) or *independent*
  (parallelize). The default in unrefactored code is serial
  because `await` is one keystroke and `Promise.all` is several;
  the architectural correction is to look at every chain of two or
  more awaits and ask whether the second actually needs the first.

## Architectural Tradeoffs

The defining tradeoff is **which data-fetching primitive to use**,
since LWC ships several overlapping mechanisms with very different
control-flow semantics:

| Dimension | Imperative Apex + `async`/`await` | `@wire` (reactive provisioning) | `@api` parent-controlled refresh | `lightning/empApi` (Streaming push) | `lightning/messageService` (LMS) |
|---|---|---|---|---|---|
| Initiated by | Explicit method call | LWC engine, reactively | Parent setting an `@api` property | Server pushing a Platform Event | Sibling/sister component publishing |
| Returns Promise | Yes — `await`-able | No — pushes into property | No — pushes via setter | No — fires a callback per event | No — fires subscriber callbacks |
| Cancellable | Yes (`AbortController` for fetch; request-id guard for Apex) | No (engine owns lifecycle) | Conceptually, via parent | Yes (`unsubscribe`) | Yes (`unsubscribe`) |
| Errors surface where | Local `try`/`catch` | `{ data, error }` payload | Parent's catch path | Subscribe `onError` callback | Per-message envelope |
| Caches automatically | No | Yes (Lightning Data Service / Apex cache) | No | No (live stream) | No (broadcast) |
| Best for | User-initiated actions, button clicks, on-demand fetches | Read-only reactive data tied to `$reactive` keys | Component-shaped wizards where the parent owns flow | Server-pushed events (long-running job done, record changed elsewhere) | Decoupled siblings on the same page sharing state |
| Worst for | Reactive auto-refresh on context change | "Do X then call Y with X's result" (can't await) | Anything with cross-page persistence | Synchronous user feedback right after a click | One-to-one parent/child contracts |

The handoff rule that works in practice: **use imperative Apex with
`async`/`await` for any user-initiated action (button, submit,
selection change). Use `@wire` for read-only reactive data that
should auto-refresh when a parameter changes and that doesn't feed
another server call. Use `@api` setter-based refresh when the
parent owns the workflow and the child is a dumb panel. Use
`lightning/empApi` when the trigger is server-side and the user
happens to be on the page. Use `lightning/messageService` when
unrelated components on the same page need to react to each other
without parent / child wiring.** Mixing primitives is normal and
healthy — a typical record-page LWC might wire its primary record,
imperatively load related data on user request, and subscribe via
empApi for inbound updates from other users.

A second tradeoff: **`Promise.all` vs `Promise.allSettled`**. The
two differ by failure semantics — `Promise.all` is fail-fast (first
rejection aborts the whole batch and the resolved values are lost
to the catch handler); `Promise.allSettled` always resolves with an
array of per-call status objects regardless of failures. Use
`Promise.all` when all calls are required for the component to be
useful (the dashboard tile in `examples.md` Example 2 first
variant: no account, no tile). Use `Promise.allSettled` when
partial render is better than no render (a multi-section page where
each section is independent) or when one of the calls is best-effort
(a permission check that should default to "denied" on failure
without aborting the surrounding data load).

A third tradeoff: **`AbortController` vs request-id guard for
stale-response races**. `AbortController` cancels the in-flight
fetch and produces an `AbortError` rejection that's easy to
distinguish from real failures; it works for `fetch()` and any API
that accepts an `AbortSignal`, but does NOT work for imperative
Apex calls (they don't expose a signal parameter). The request-id
counter pattern works for ANY async call regardless of
cancellation support — assign `const id = ++this._latest;` before
the await, then guard `if (id !== this._latest) return;` after,
discarding stale results without canceling the request. Use
`AbortController` when the underlying API supports it (cleaner
semantics, server gets to short-circuit work it doesn't need to
finish). Use the request-id guard for Apex (where AbortController
isn't an option) and for libraries that don't accept a signal.

## Anti-Patterns

1. **Awaiting an Apex call without try/catch.** A rejected Promise
   throws past every line below the `await` until something catches
   it; if nothing does, the rejection lands in the browser console
   as an "Uncaught (in promise)" with no LWC component name. The
   loading state never clears, the error never shows. See
   `references/llm-anti-patterns.md` for the same anti-pattern from
   the LLM-generation angle.
2. **Trying to `await` a `@wire`-decorated property.** Wire is
   reactive push, not Promise-based — the await resolves
   immediately to whatever the field happens to hold (often
   `undefined` on first paint). For "do X then call Y with X's
   result," skip wire on the leading call and use imperative Apex
   for both steps. See `gotchas.md` Gotcha 1.
3. **Server calls inside `renderedCallback` without a one-shot
   guard.** The hook fires on every re-render; an unguarded server
   call that assigns to a `@track` field becomes an infinite loop
   that ends only when the platform or browser intervenes. Guard
   with `if (this._didLoad) return; this._didLoad = true;` or move
   the call to an `@api` setter. See `gotchas.md` Gotcha 3.
4. **No `disconnectedCallback` cleanup for timers, subscriptions,
   and `AbortController`s.** LWC has NO `componentWillUnmount`
   equivalent under another name; `disconnectedCallback` is the
   only teardown hook. Without it, `setInterval` keeps firing
   against a dead `this`, `empApi` keeps pushing events into a
   detached component, and in-flight fetches keep running until
   they resolve and assign to nothing.
5. **Sequential chains of `.then().then().then()` for independent
   calls.** Each `.then()` callback hides the dependency graph:
   are these calls truly sequential, or could the second and third
   run in parallel? Refactoring to `async`/`await` makes the data
   dependencies explicit and almost always reveals at least one
   `Promise.all` opportunity. See `examples.md` anti-pattern.

## Official Sources Used

- LWC Developer Guide — Call Apex Methods Imperatively:
  https://developer.salesforce.com/docs/platform/lwc/guide/apex-call-imperative.html
- LWC Developer Guide — Understand the Wire Service:
  https://developer.salesforce.com/docs/platform/lwc/guide/data-wire-service-about.html
- LWC Developer Guide — Work with Salesforce Data (`data-apex`):
  https://developer.salesforce.com/docs/platform/lwc/guide/data-apex.html
- LWC Developer Guide — Handle the Wire Service Result:
  https://developer.salesforce.com/docs/platform/lwc/guide/data-wire-service-result.html
- LWC Developer Guide — Lifecycle Hooks (renderedCallback,
  errorCallback, disconnectedCallback):
  https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks.html
- Lightning Web Security overview (constraints on global APIs like
  `setTimeout` / `setInterval`):
  https://developer.salesforce.com/docs/platform/lwc/guide/security-lwsec-intro.html
- Salesforce Well-Architected — Resilient:
  https://architect.salesforce.com/well-architected/adaptable/resilient
