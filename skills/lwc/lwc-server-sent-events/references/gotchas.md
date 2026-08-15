# Gotchas — LWC Streaming (`lightning/empApi`)

---

## 1. Event retention is **72 hours**, not 24

**What happens:** a design persists a replay id and assumes a one-day resume
window. A user returns after a long weekend, the component subscribes with a
stale id, and the subscription errors — or worse, the design over-conservatively
discards ids that were still valid.

**The documented behaviour:** platform events and change data capture events are
published to the event bus where they are **stored for 72 hours**. Salesforce
does not guarantee storage beyond the retention period, though the purge
sometimes starts later so older events can still be available
([Event Message
Durability](https://developer.salesforce.com/docs/platform/pub-sub-api/guide/event-message-durability.html)).

**How to avoid:** treat a stored replay id as having a TTL slightly shorter than
72 hours — subtract an hour of safety margin — and fall back to `-1` when it may
have aged out. Never subscribe with an id you cannot vouch for; the failure is
an error, not a graceful degradation.

---

## 2. `empApi` is not available everywhere the component renders

**What happens:** the component works perfectly on desktop and shows an empty
panel in the Salesforce mobile app, in an iframe, and in a utility-bar pop-out.
No error, no console message — just nothing.

**The documented constraints:** `lightning/empApi` is supported in desktop
browsers with web worker or shared worker support. It is **not supported in the
Salesforce mobile app**, and it cannot be used in child windows, utility bar
pop-outs, or iframes. One user per browser session. API version 44.0+
([Emp API](https://developer.salesforce.com/docs/component-library/bundle/lightning-emp-api/documentation)).

**How to avoid:** call `isEmpEnabled()` in `connectedCallback` and branch the
template. Streaming unavailable must render a working alternative — a refresh
button, a poll — never a blank region. Components that appear on both a record
page and a mobile-visible page need this or they ship a silent failure to every
mobile user in the org.

---

## 3. Concurrent CometD client limits are lower than teams expect

**What happens:** a per-row subscription pattern, or a widely-deployed component
on a heavily-used page, exhausts the org's concurrent subscriber ceiling. New
subscriptions start failing for everyone, including unrelated integrations.

**The documented allocations** (defaults; add-on licences raise them):

| Edition | Concurrent CometD clients | 24-hour event delivery to CometD clients |
|---|---|---|
| Performance & Unlimited | 2,000 | 50,000 |
| Enterprise | 1,000 | 25,000 |
| Developer | **20** | 10,000 |
| Professional (with API add-on) | 20 | 25,000 |

([Platform Event
Allocations](https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm))

**How to avoid:** one subscription per page, fanned out to children. Note the
Developer Edition ceiling of 20 concurrent clients — a per-row subscription in a
20-row list exhausts it on a single page render, which is why this pattern is
usually discovered in the developer's own scratch org.

The delivery allocation is **shared across all CometD clients in the org**, so
your component competes with every other subscriber including middleware. That
makes subscription count an org-level architectural concern, not a
component-level one.

---

## 4. Subscribing in `renderedCallback` multiplies subscriptions

**What happens:** the handler fires two, then three, then N times for one event.
Memory climbs. The allocation drains.

**Why:** `renderedCallback` runs after *every* re-render, not once. Any reactive
property change re-invokes it.

**How to avoid:** one-time setup belongs in `connectedCallback`. If you
genuinely need a post-render hook, guard with a flag — but for `empApi` there is
no reason to; nothing about subscribing requires the DOM.

---

## 5. `onError` called more than once silently replaces the handler

**What happens:** two components each call `onError`. The second registration
overwrites the first, and the first component's errors go nowhere.

**The documented behaviour:** *"Make sure that you call `onError` only once in
your component's lifespan. Calling `onError` multiple times overwrites the
previous error handler."*

**How to avoid:** register once, guarded by an instance flag, and route errors
outward via a custom event so a parent can aggregate. In a page with several
streaming components this is an argument for a single container that owns both
the subscription and the error handler.

---

## 6. Handlers must be idempotent — delivery is not exactly-once

**What happens:** the handler increments a counter or appends to a list. A
reconnect with `-2`, a duplicate delivery, or a second tab produces double
counts.

**How to avoid:** write handlers as **state assignments keyed by id**, not as
mutations:

```javascript
// WRONG — not idempotent
this.count = this.count + 1;
this.rows = [...this.rows, payload];

// RIGHT — replaying the same event twice yields the same state
this.rowsById = { ...this.rowsById, [payload.Order_Id__c]: payload };
this.count = Object.keys(this.rowsById).length;
```

The test for idempotency: applying the same message twice must leave the
component in the same state as applying it once. If it does not, a reconnect is
a data corruption event.

---

## 7. `-1` means "from now", which is not "reliable"

**What happens:** an approval workflow whose only completion signal is a
platform event delivered to a subscription opened with `-1`. Events fired while
the tab was backgrounded, the network was down, or the page was reloading are
never delivered. The UI is stuck and nothing errored.

**How to avoid:** treat streaming as a latency optimisation over a correct
fallback. Re-fetch on focus, on a slow poll, or on user action. A missed push
then costs seconds of staleness rather than a stuck workflow. Genuine
at-least-once requirements belong on a server-side consumer with a committed
replay position, not in a browser tab.

---

## 8. CDC payloads are deltas, and `getRecordNotifyChange` is deprecated

**What happens:** a component renders the CDC payload directly and shows partial
records — or calls the deprecated refresh API and gets inconsistent behaviour
across components on the page.

**Two corrections:**

- `ChangeEventHeader.recordIds` tells you *which* records changed. The payload
  carries changed fields only; it is not a complete record.
- `getRecordNotifyChange(recordIds)` is **deprecated**. Use
  `notifyRecordUpdateAvailable(recordIds)`, which *"considers the record data
  wired by all instantiated components"* — it refreshes every wire using data
  from the supplied ids and re-emits only where data actually changed
  ([notifyRecordUpdateAvailable](https://developer.salesforce.com/docs/platform/lwc/guide/reference-notify-record-update.html)).

**How to avoid:** CDC identifies, LDS fetches. That also re-applies the running
user's FLS and sharing on the refetch, which rendering the payload directly does
not.

---

## 9. A pending reconnect timer outlives the component

**What happens:** `disconnectedCallback` unsubscribes correctly. A backoff timer
scheduled moments earlier still fires, resubscribes, and creates a subscription
with no component behind it. This is the leak that survives adding the teardown.

**How to avoid:** a `_destroyed` flag checked at the top of every async
continuation, and `clearTimeout` in `disconnectedCallback`. Any `setTimeout`,
`setInterval`, or `.then()` that can outlive the component needs the same guard.

---

## 10. Retrying a 403 forever

**What happens:** the running user lacks read access to the platform event
object. `onError` fires, the backoff loop retries indefinitely, and every attempt
consumes shared org allocation while masking a five-minute permissions fix.

**How to avoid:** classify errors before retrying. Auth and permission failures
are permanent — surface them and stop. Transient failures get bounded backoff
and then a visible degraded mode. Unbounded retry against a permanent failure is
an availability problem for the whole org, because the allocation is shared.

---

## 11. Mutating an array element does not trigger a re-render

**What happens:** the handler runs, the data is correct in the debugger, and the
UI does not update.

```javascript
// WRONG — LWC does not observe deep mutation of array members
const row = this.orders.find((o) => o.id === payload.Order_Id__c);
row.status = payload.Status__c;

// RIGHT — reassign, so the reactive property changes identity
this.orders = this.orders.map((o) =>
    o.id === payload.Order_Id__c ? { ...o, status: payload.Status__c } : o);
```

**Why it bites specifically here:** streaming handlers are the natural place to
write "find the row and update it", and unlike a wire-driven refresh there is no
framework machinery reassigning the property for you.

---

## 12. Multiple tabs multiply deliveries and race on stored replay ids

**What happens:** a user with three tabs open receives each event three times,
and all three tabs write the same `localStorage` replay key — so a resumed
subscription may skip events another tab already consumed.

**How to avoid:** decide explicitly. If handlers are idempotent (gotcha 6),
duplicate delivery is harmless and the simplest answer is to accept it. If it is
not harmless, elect a leader tab and forward events to the others. And if
exactly-once genuinely matters, the replay position belongs on the server —
`localStorage` cannot arbitrate between tabs.

Note that Lightning Web Security namespaces `localStorage` per namespace, so the
key is isolated from other namespaces but shared across your own tabs — which is
precisely the race described.

---

## 13. Platform event field API names are exact, and typos return `undefined`

**What happens:** the handler reads `payload.OrderStatus__c` where the field is
`Order_Status__c`. No error. The value is `undefined` and the UI renders blank.

**How to avoid:** destructure with a default and assert early:

```javascript
const { Order_Id__c: orderId, Status__c: status } = message?.data?.payload ?? {};
if (!orderId) {
    // Loud in development, silent-but-counted in production.
    return;
}
```

A Jest test with a realistic payload fixture catches this at build time, which is
the only place it is cheap to catch.

---

## 14. Choosing Platform Events when CDC is the right tool (or vice versa)

**What happens:** a custom platform event is published from a trigger purely to
say "this record changed" — reimplementing CDC in Apex, with a trigger to
maintain and publishing allocation to spend.

**How to choose:**

| Need | Use |
|---|---|
| "This record changed" for UI refresh | **CDC** — no Apex, no publishing allocation |
| A domain event with its own schema and semantics | **Platform Event** |
| Progress of a long-running job | **Platform Event** — there is no record to watch |
| Change notification for an object CDC does not support | **Platform Event** |

Both consume the same delivery allocation on the subscriber side, so the choice
is about publishing cost and semantic fit rather than about delivery. See
`standards/decision-trees/integration-pattern-selection.md`.
