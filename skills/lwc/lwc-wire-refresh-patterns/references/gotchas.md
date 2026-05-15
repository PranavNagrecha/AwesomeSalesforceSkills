# Gotchas — LWC Wire Refresh Patterns

Non-obvious platform behaviors that surface when refreshing
LWC `@wire`'d data. These extend (rather than duplicate) the
high-level rules in `SKILL.md`.

## Gotcha 1: `refreshApex` returns a Promise that resolves before the wire's data property updates

**What happens:** Code awaits `refreshApex(this._wiredFoo)` and
then immediately reads `this.foo` (or `this._wiredFoo.data`)
expecting the new values. The Promise resolution and the wire
callback fire on different microtask queues — `refreshApex`
resolves once the network call returns, but the wire callback that
writes `data` into your component property runs in a separate tick.
Code that reads the wired property in the same async function
after the await sees the *old* value.

**When it occurs:** Patterns like "save → refresh → reuse the
refreshed data immediately":

```javascript
await refreshApex(this._wiredFoo);
const top = this.foo[0];  // still old data
```

Or test code (Jest) that awaits `refreshApex` and then asserts on
DOM state — the DOM hasn't re-rendered yet either.

**How to avoid:** Wait one more microtask: `await Promise.resolve();`
or use the wire callback (function-form `@wire`) to drive the
post-refresh logic — the wire fires after the data lands. In tests,
use `flushPromises()` (the standard helper:
`return Promise.resolve();` in a chain) to push past the wire
callback. The cleanest production pattern is to put the
"post-refresh logic" inside the wire's function body, not after
the `refreshApex` call.

---

## Gotcha 2: `RefreshEvent` performance scales with the number of `@wire(RefreshView)` listeners

**What happens:** Dispatching `new RefreshEvent()` triggers every
component in the active view that has wired `RefreshView` or
listens to the refresh signal. On a record page with 12 components
(highlights, related lists, custom LWCs, Path, etc.) and each of
those re-running 2–3 wires, a single `RefreshEvent` can produce
36+ network round-trips. Users see a multi-second loading state
even if their actual change only affected one field.

**When it occurs:** Heavy record pages with many wires, common
on Account/Opportunity pages in mature orgs. Also: components
that fire `RefreshEvent` on every keystroke (don't do this)
multiply the effect.

**How to avoid:** For targeted updates, prefer
`notifyRecordUpdateAvailable([{ recordId }])` — it invalidates only
the entries that name a specific record. Use `RefreshEvent` only
when:
- The change has unknown downstream effects (Flow side-effects,
  parallel rollups), OR
- The component genuinely doesn't know which records changed.

For high-frequency triggers (search filters, infinite scroll), do
**not** use `RefreshEvent` — drive the refresh through a reactive
parameter on the specific wire that needs updating, leaving other
components' caches intact.

---

## Gotcha 3: A wire that returns `data: undefined, error: undefined` is in the LOADING state — refresh won't change that

**What happens:** Code does
`if (!this._wiredFoo.data && !this._wiredFoo.error) refreshApex(this._wiredFoo);`
to "kick off a re-fetch when there's no data yet." The pattern
appears to do nothing — the wire stays in the loading state,
`data` never populates, and the component never finishes rendering.

**When it occurs:** Component initialization races where the
developer added a "warm up the wire" call in `connectedCallback`
or `renderedCallback`. The wire is already pending its first
invocation; `refreshApex` against a pending wire is a no-op (you
can't refresh data that hasn't arrived yet) and may produce
warnings in Lightning Inspector but no error.

**How to avoid:** Don't call `refreshApex` on a wire that hasn't
yet produced data. Use the wire callback's `result.data ||
result.error` check to detect first-data arrival, and only then
arm refresh logic. If the wire is genuinely not firing, the issue
is the reactive-parameter binding — verify the `$paramName`
expression refers to a defined property, not a method or
computed value.

---

## Gotcha 4: Cached wires across navigation can return stale data even after `refreshApex`

**What happens:** A user navigates to record page A, edits a Case
inline, navigates to record page B, navigates BACK to record page
A. The component on A's page renders with the *pre-edit* values
even though the user just changed them. Calling `refreshApex` in
`connectedCallback` doesn't help — the data returned is still
stale.

**When it occurs:** Records modified through LDS / UI API are
refreshed correctly. Records modified through custom Apex
`@AuraEnabled(cacheable=true)` methods are cached by the Lightning
client per the cache control headers — and the cache is shared
across navigations within the same browser tab. The cached value
returns instantly on revisit; `refreshApex` triggers a network
refresh, but the wire's first callback emits the cached value
*before* the network refresh completes.

**How to avoid:** For data that must be fresh on every page visit,
do NOT use `@AuraEnabled(cacheable=true)`. Use imperative Apex
calls (`@AuraEnabled` without `cacheable=true`) and manage the
data shape yourself. The performance cost is real (no client-side
cache) but the alternative — debugging stale-cache reports from
sales reps — is worse. Alternatively, structure the wire to
re-fetch on a reactive parameter that changes with navigation
(e.g., `'$recordId'` already does this for record pages, but a
custom "tab session ID" can force refresh in other contexts).

---

## Gotcha 5: `notifyRecordUpdateAvailable` does NOT refresh related-list components

**What happens:** A custom LWC calls `notifyRecordUpdateAvailable`
after inserting a new Contact on the current Account. The Account
record page's `getRecord` wires refresh — but the related-list
component "Contacts" still shows the old contact count and the new
Contact is invisible until the user clicks the related list's
refresh button.

**When it occurs:** Whenever the change adds or removes a related
record (vs. updating a field on the current record). The standard
related-list components subscribe to a different cache key than
the parent record's UI API wires. `notifyRecordUpdateAvailable`
only invalidates the records you name in the parameter array — and
naming the *parent* doesn't refresh the related-list adapter
because it's keyed by `parentId + relationship + filter`, not by
`parentId` alone.

**How to avoid:** For related-list refreshes after insert/delete,
use `RefreshEvent` (broad scope) — it propagates through the
related-list adapter as well. Alternatively, use the specific
`getRelatedListRecords` adapter directly in your component and
call `refreshApex` against that wire's result. There is no
narrowly-scoped equivalent of `notifyRecordUpdateAvailable` for
related-list changes; the platform doesn't expose enough cache
key information to make one feasible.
