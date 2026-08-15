# LLM Anti-Patterns — LWC Streaming

---

## Anti-Pattern 1: Inventing `EventSource` / native SSE

**What the LLM generates:**

```javascript
const source = new EventSource('/services/data/v67.0/events/stream');
source.onmessage = (e) => this.handle(JSON.parse(e.data));
```

**Why it happens:** the request says "server-sent events", and `EventSource` *is*
the web standard for SSE. The model answers the web-platform question rather than
the Salesforce one, and the endpoint path interpolates plausibly from real
Salesforce API shapes.

**Correct pattern:** Salesforce's browser-side streaming is CometD behind
`lightning/empApi`, with `subscribe`, `unsubscribe`, `onError`, `setDebugFlag`,
and `isEmpEnabled`. There is no `EventSource` endpoint and no raw WebSocket for
this — and Lightning Web Security would not let arbitrary long-lived connections
work the way the generated code assumes.

**Detection hint:** `EventSource`, `WebSocket`, or a hand-built `fetch` polling
loop against an invented streaming endpoint.

---

## Anti-Pattern 2: No `disconnectedCallback`

**What the LLM generates:** a `connectedCallback` that subscribes and nothing
that tears down.

**Why it happens:** the request is "subscribe to a platform event", the code
subscribes, and the request is satisfied. Cleanup is a lifecycle symmetry the
model completes only when prompted for it.

**Correct pattern:** every `subscribe` has a matching `unsubscribe` in
`disconnectedCallback`, holding the subscription object returned by the promise.
In a console app where users open and close tabs continuously, the omission
accumulates subscriptions against a shared org allocation with a hard ceiling.

**Detection hint:** `subscribe(` in a file with no `disconnectedCallback`. One
grep, and it should be a lint rule.

---

## Anti-Pattern 3: Subscribing in `renderedCallback`

**What the LLM generates:** the subscription inside `renderedCallback`, often
because the surrounding example needed DOM access.

**Why it happens:** `renderedCallback` reads as "when the component is ready",
and the distinction from `connectedCallback` — that it runs after *every*
re-render — is a detail rather than a headline.

**Correct pattern:** one-time setup goes in `connectedCallback`. Nothing about
subscribing needs the DOM. In `renderedCallback` each reactive change adds
another subscription, and the handler fires N times for one event.

**Detection hint:** any `subscribe(` inside `renderedCallback`, guarded or not.

---

## Anti-Pattern 4: "Replay ids expire after 24 hours"

**What the LLM generates:** a TTL design built on a 24-hour durability window,
stated as fact.

**Why it happens:** 24 hours is the intuitive "one day" retention and appears in
older material. The correct figure is less memorable and easily displaced by the
plausible one.

**Correct pattern:** platform events and CDC events are stored on the event bus
for **72 hours**, with no guarantee beyond that (purging sometimes starts later).
Design the client TTL slightly under 72 hours with a safety margin, and fall back
to `-1` rather than subscribing with an id you cannot vouch for.

**Detection hint:** any "24 hour" or "one day" retention claim about the event
bus.

---

## Anti-Pattern 5: `getRecordNotifyChange`

**What the LLM generates:**

```javascript
import { getRecordNotifyChange } from 'lightning/uiRecordApi';
```

**Why it happens:** it was the canonical answer for years and dominates the
training corpus. Deprecation is recent relative to the volume of material using
it.

**Correct pattern:** `notifyRecordUpdateAvailable(recordIds)`. The behaviour also
differs — unlike the deprecated call it considers record data wired by *all*
instantiated components, refreshing every wire using the supplied ids and
re-emitting only where data changed.

**Detection hint:** the identifier `getRecordNotifyChange` anywhere.

---

## Anti-Pattern 6: Per-row / per-child subscriptions

**What the LLM generates:** a row component that subscribes in its own
`connectedCallback`, because each row "owns" its live data.

**Why it happens:** component encapsulation is a correct and strongly-held
principle, and each row genuinely does own its state. The model has no
representation of subscriptions as a scarce org-level resource.

**Correct pattern:** the container subscribes once and routes messages to
children as props. Note the Developer Edition ceiling of **20 concurrent CometD
clients** — a 20-row list with per-row subscriptions exhausts it on one page
render.

**Detection hint:** `subscribe(` in a component rendered inside a `for:each`.

---

## Anti-Pattern 7: Non-idempotent handlers

**What the LLM generates:**

```javascript
this.messageCount = this.messageCount + 1;
this.items = [...this.items, message.data.payload];
```

**Why it happens:** "append on receive" is the natural expression of a stream,
and the model treats delivery as exactly-once because that is how a local event
emitter behaves.

**Correct pattern:** state assignment keyed by id, so applying the same message
twice leaves the same state. Reconnects, `-2` resubscriptions, and multiple tabs
all produce duplicates, and none of them error.

**Detection hint:** an increment, a `push`, or a spread-append in a streaming
handler with no dedupe key.

---

## Anti-Pattern 8: `-1` presented as reliable

**What the LLM generates:** "use `replayId: -1` to receive events" with no
discussion of what is missed, in a design where the event is the only signal
that something happened.

**Why it happens:** `-1` is the documentation's first example and the simplest
working call. Delivery-semantics caveats are a second-order concern that the
question did not raise.

**Correct pattern:** `-1` subscribes from now; anything fired while the tab was
backgrounded, offline, or reloading is gone. Streaming is a latency optimisation
over a correct fallback — re-fetch on focus or on a slow poll. Genuine
at-least-once belongs in a server-side consumer with a committed replay
position.

**Detection hint:** a workflow whose completion is signalled only by a push, with
no re-fetch path.

---

## Anti-Pattern 9: Omitting the availability guard

**What the LLM generates:** a component that subscribes unconditionally, with no
`isEmpEnabled()` check and no fallback branch in the template.

**Why it happens:** the platform constraints (no mobile app, no iframes, no
utility-bar pop-outs, worker support required) are a paragraph in the reference
rather than part of the API shape, so they do not surface in generated code.

**Correct pattern:** `await isEmpEnabled()` in `connectedCallback`, and a
template branch that renders a working alternative when it returns false. An
unguarded component ships a blank region to every mobile user in the org, with no
error to diagnose it by.

**Detection hint:** no `isEmpEnabled` import in a component that subscribes, and
no fallback branch in the markup.

---

## Anti-Pattern 10: Unbounded retry

**What the LLM generates:**

```javascript
handleError() {
    setTimeout(() => this.handleSubscribe(), 5000);   // forever
}
```

**Why it happens:** retry-on-error is correct and well-represented, and bounding
it requires knowing which errors are permanent — context the model does not have
in a single file.

**Correct pattern:** classify first. A 403 is a permissions problem that retrying
will never fix, and every attempt spends allocation shared across the whole org
while delaying the diagnosis. Transient failures get bounded backoff and then a
visible degraded mode. Also clear the timer in `disconnectedCallback` and guard
the continuation with a `_destroyed` flag, or a pending retry resubscribes an
orphan after teardown.

**Detection hint:** a retry with no attempt ceiling, no error classification, or
no `clearTimeout` in teardown.

---

## Anti-Pattern 11: Mutating array members and expecting a re-render

**What the LLM generates:**

```javascript
const row = this.orders.find((o) => o.id === payload.Order_Id__c);
row.status = payload.Status__c;
```

**Why it happens:** find-and-mutate is the natural imperative update and works in
frameworks with deep reactivity. LWC's reactivity triggers on property
reassignment.

**Correct pattern:** reassign the array — `this.orders = this.orders.map(...)`.
This bites specifically in streaming handlers because, unlike a wire-driven
refresh, nothing else is reassigning the property for you.

**Detection hint:** a mutation of a found element inside a streaming callback,
with no subsequent assignment to the reactive property.

---

## Anti-Pattern 12: Rendering the CDC payload directly

**What the LLM generates:** a handler that reads changed fields out of the CDC
payload and renders them.

**Why it happens:** the payload contains the new values, so using them is the
obvious efficiency — one fewer round trip.

**Correct pattern:** CDC payloads are deltas containing only changed fields, and
they are delivered based on channel access rather than per-field FLS. Use
`ChangeEventHeader.recordIds` to identify what changed and
`notifyRecordUpdateAvailable` to let LDS refetch — which keeps the whole page
consistent and re-applies the running user's field security.

**Detection hint:** a template bound to values read out of
`msg.data.payload` for a `/data/*ChangeEvent` channel.
