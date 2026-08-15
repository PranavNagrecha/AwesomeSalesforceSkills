# Well-Architected Notes — LWC Streaming

## Relevant Pillars

### Reliability

The central design decision is what happens when a push does **not** arrive, and
the honest answer is that this will happen routinely: `-1` subscribes from now,
so anything fired while the tab was backgrounded, offline, or mid-reload is
simply absent. Nothing errors.

That makes streaming a **latency optimisation over a correct fallback**, never a
transport. The architectural test is one question: *if every push were dropped
for the next ten minutes, would the UI eventually become correct?* If the answer
is no, the design has made a browser subscription load-bearing, and no amount of
reconnect logic fixes that — the tab can be closed.

Two supporting properties:

- **Idempotent handlers.** Reconnects, `-2` resubscriptions, and multiple tabs
  all produce duplicate delivery. State assignment keyed by id makes duplicates
  harmless; increments and appends make them corruption.
- **Bounded retry with error classification.** A 403 is permanent; retrying it
  spends a shared org resource and delays a five-minute fix.

Genuine at-least-once requirements belong on a server-side consumer with a
committed replay position — see `integration/platform-events-integration` and
the Pub/Sub API's managed subscriptions.

### Scalability

Subscription count is an **org-level architectural concern**, not a component
decision, because both relevant allocations are shared across every CometD
client in the org — your components, other teams' components, and any middleware
subscribing over CometD.

| Edition | Concurrent CometD clients | 24-hour delivery to CometD clients |
|---|---|---|
| Performance & Unlimited | 2,000 | 50,000 |
| Enterprise | 1,000 | 25,000 |
| Developer | 20 | 10,000 |
| Professional (API add-on) | 20 | 25,000 |

([Platform Event
Allocations](https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm))

Two multipliers turn a reasonable component into an org-wide problem: one
subscription per row rather than per page, and one subscription per component
rather than per page. Both are encapsulation instincts, and both multiply a
scarce shared resource by a number nobody bounded.

The Developer Edition ceiling of 20 concurrent clients is worth knowing
specifically because it is where the pattern is usually first exercised — a
per-row list exhausts it on one page render, which is a cheap place to learn.

### User Experience

Push beats polling when latency is visible to the user — a progress bar, a
queue, an approval status. It is worth nothing when the user would not notice a
30-second delay, and in that case a poll is simpler, has no allocation cost, and
degrades to nothing on mobile.

The UX failure specific to this API is the **silent blank region**.
`lightning/empApi` is unavailable in the Salesforce mobile app, in iframes, and
in utility-bar pop-outs. Without an `isEmpEnabled()` guard and a fallback branch,
every mobile user sees an empty panel with no error to explain it. Guarding is
three lines and is the difference between graceful degradation and a component
that appears broken.

### Security

Two considerations that are easy to skip:

- **CDC payload vs. LDS refetch.** CDC delivery is governed by channel access.
  Rendering the payload directly can surface field values the running user's FLS
  would otherwise hide. Using `notifyRecordUpdateAvailable` to refetch through
  LDS re-applies per-field security on the way back.
- **`localStorage` replay ids.** Lightning Web Security namespaces browser
  storage per namespace, so the key is isolated from other namespaces — but it is
  shared across your own tabs, which is why multi-tab replay tracking races.
  Sensitive positional state does not belong in browser storage regardless.

---

## Architectural Tradeoffs

### Push vs. poll vs. refetch-on-focus

| | Push (`empApi`) | Poll | Refetch on focus |
|---|---|---|---|
| Latency | Sub-second | Interval | On user attention |
| Org allocation cost | Delivery + client slots | API calls | Minimal |
| Works on mobile | **No** | Yes | Yes |
| Complexity | Lifecycle, reconnect, idempotency | Low | Very low |
| Correct when a message is missed | Only with a fallback | Self-healing | Self-healing |

Most "live" requirements are satisfied by refetch-on-focus plus a slow poll. Push
earns its complexity when a human is watching the value change in real time.
Combining push with refetch-on-focus is the shape that is both fast and correct.

### Platform Events vs. CDC

CDC is the cheaper answer to "this record changed" — no Apex, no trigger to
maintain, no publishing allocation. Platform Events are right for domain events
with their own schema, for progress on a long-running job where there is no
record to watch, and for objects CDC does not cover.

Both consume the same subscriber-side delivery allocation, so the choice is
about publishing cost and semantic fit. Publishing a custom event from a trigger
solely to say "record changed" is reimplementing CDC. See
`standards/decision-trees/integration-pattern-selection.md`.

### `-1` vs. `-2` vs. tracked replay id

`-1` is simplest and misses everything before subscription. `-2` replays the
retained window and requires idempotent handlers, since the component will
re-see events it already processed. A tracked replay id is the most precise and
the most fragile — it races across tabs, needs a TTL under the 72-hour retention
window, and puts positional state in the browser.

Default to `-1` plus a fallback refetch. Take `-2` when the component genuinely
needs recent history on open. Take a tracked id only when you have already
concluded that a server-side consumer is not an option, and then be honest that
it is best-effort.

### One subscription per page vs. per component

Per-component is simpler to write and multiplies a shared org resource.
Per-page requires fan-out plumbing — a container that subscribes and passes data
down as props — and has the side benefit of making children pure and trivially
testable.

For multiple independent streaming components on one page, a single container
owning both the subscription and the `onError` registration is the cleaner
answer, because `onError` can only be registered once without overwriting.

### Accepting duplicates vs. leader-tab election

If handlers are idempotent, duplicate delivery across tabs is harmless and
accepting it is free. Leader-tab election adds coordination machinery for a
problem that idempotency already solves. Reach for it only when the handler has a
genuine side effect that cannot be made idempotent — and in that case, ask why a
browser tab is performing a non-idempotent side effect at all.

---

## Anti-Patterns

1. **Streaming as the source of truth.** `-1` misses events with no error; a
   closed tab misses all of them. Always have a path back to correctness.

2. **Subscription per row or per component.** Multiplies an org-level shared
   allocation with a hard ceiling.

3. **Non-idempotent handlers.** Turns a routine reconnect into a data
   corruption event.

4. **No availability guard.** Ships a silent blank region to every mobile user
   in the org.

5. **Unbounded retry.** Spends shared allocation against a permanent failure and
   delays its diagnosis.

6. **Rendering the CDC payload directly.** Deltas are incomplete, and the
   refetch is what re-applies field security.

7. **Timers that outlive the component.** The leak that survives adding
   `disconnectedCallback`.

---

## Related

- `integration/platform-events-integration` — publishing, and server-side
  consumers with committed replay positions.
- `lwc/message-channel-patterns` — in-page component communication, which is
  what most "sibling components need to know" questions actually want.
- `lwc/lwc-performance-budgets` — a streaming component's re-render rate is a
  budget item.
- `lwc/common-lwc-runtime-errors` — the reactivity and lifecycle errors that
  surface here.
- `standards/decision-trees/integration-pattern-selection.md` — Platform Events
  vs. CDC vs. Pub/Sub vs. polling.

---

## Official Sources Used

- Emp API (`lightning/empApi`) — https://developer.salesforce.com/docs/component-library/bundle/lightning-emp-api/documentation
- Platform Event Allocations — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
- Event Message Durability (Pub/Sub API) — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/event-message-durability.html
- Message Durability (Streaming API) — https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/using_streaming_api_durability.htm
- notifyRecordUpdateAvailable(recordIds) — https://developer.salesforce.com/docs/platform/lwc/guide/reference-notify-record-update.html
- getRecordNotifyChange (Deprecated) — https://developer.salesforce.com/docs/platform/lwc/guide/reference-get-record-notify.html
- Subscribe to Platform Event Notifications in a Lightning Component — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_subscribe_lc.htm
- Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
