---
name: lwc-server-sent-events
description: "Use when building LWCs that must react to live server pushes — Platform Events, Change Data Capture, or streaming updates — via the lightning/empApi (CometD) subscription model. Covers lifecycle, replayId, error handling. NOT for publishing events (see platform-events or apex-platform-events) — use integration/platform-events-integration."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - User Experience
  - Scalability
triggers:
  - "lwc subscribe to platform event"
  - "lightning empapi example"
  - "cdc to lwc"
  - "replay id lwc subscription"
  - "realtime lwc push"
tags:
  - lwc
  - streaming
  - empapi
  - platform-events
  - cdc
  - realtime
inputs:
  - Platform Event or CDC channel LWC must listen to
  - Expected event volume and latency tolerance
  - Concurrent tabs / components listening
outputs:
  - Subscription lifecycle implementation
  - Replay strategy (MAX, -2, specific replayId)
  - Error / reconnect plan
  - Fan-out pattern across components and tabs
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# LWC Server-Sent / Streaming Events

## Purpose

Salesforce's streaming model — CometD under `lightning/empApi` — is the
closest thing LWCs get to Server-Sent Events. Teams reach for it when a
record page should "auto-refresh" on server changes, when a custom
dashboard needs near-real-time data, or when a long-running job needs to
stream progress to the user. The shape is simple but the failure modes
(disconnection, missed events, replay storms, memory leaks) are not. This
skill codifies subscription lifecycle, replayId strategy, error handling,
and coordination across components and tabs.

## The API Surface

`lightning/empApi` exports exactly five functions: `subscribe(channel, replayId,
onMessageCallback)` returning a `Promise<subscription>`; `unsubscribe(subscription,
callback)` whose result carries a `successful` boolean; `onError(callback)`;
`setDebugFlag(boolean)`; and `isEmpEnabled()` returning a `Promise<boolean>`.

Requires API 44.0+. **Not supported in the Salesforce mobile app**, and not
usable in child windows, utility-bar pop-outs, or iframes — it needs web worker
or shared worker support. Call `onError` **once** per component lifespan; a
second call overwrites the first handler.

## Recommended Workflow

1. **Confirm streaming is the right tool.** Most "live" requirements are met by
   refetch-on-focus plus a slow poll, which work on mobile and cost no
   allocation. Push earns its complexity when a human is watching a value change
   in real time.
2. **Pick the channel.** Platform Event (`/event/<EventName>__e`), CDC
   (`/data/<ObjectName>ChangeEvent`), or Generic Streaming (`/u/...`). Publishing
   a custom event from a trigger just to say "record changed" is reimplementing
   CDC.
3. **Guard, then subscribe in `connectedCallback`.** `await isEmpEnabled()` and
   render a working fallback when it returns false — otherwise every mobile user
   gets a silent blank region. Never subscribe in `renderedCallback`, which runs
   on every re-render.
4. **Always `unsubscribe` in `disconnectedCallback`,** and clear any pending
   reconnect timer with a `_destroyed` flag — a timer that outlives the component
   resubscribes an orphan.
5. **Choose the replay value.** `-1` (new only), `-2` (retained window), or a
   tracked id. Event bus retention is **72 hours**, so a stored id needs a TTL
   under that with a safety margin.
6. **Make handlers idempotent.** Assign state keyed by id; never increment or
   append. Reconnects, `-2`, and multiple tabs all produce duplicates and none of
   them error. Remember that mutating an array member does not trigger a
   re-render — reassign the property.
7. **Bound the retry and classify the error.** A 403 is permanent; retrying it
   spends a shared org allocation and delays the fix. Transient failures get
   capped backoff, then a visible degraded mode.

## Replay Strategy

| Value | Behavior | Use When |
|---|---|---|
| `-1` | Only new events after subscribe | Best-effort UI updates (default) |
| `-2` | All retained events (**72-hour** window) | Component needs recent history on open |
| specific replayId | Resume from a known point | Reliability-critical — but see below |

Tracking a replay id client-side races across tabs (`localStorage` is namespaced
per namespace by Lightning Web Security but shared across your own tabs) and
puts positional state in the browser. If exactly-once matters, the replay
position belongs on a server-side consumer.

## Scale — Subscriptions Are An Org-Level Resource

Both allocations are **shared across every CometD client in the org**, including
other teams' components and middleware:

| Edition | Concurrent CometD clients | 24-hour delivery to CometD clients |
|---|---|---|
| Performance & Unlimited | 2,000 | 50,000 |
| Enterprise | 1,000 | 25,000 |
| Developer | 20 | 10,000 |
| Professional (API add-on) | 20 | 25,000 |

One subscription per page, fanned out to children as props — never one per row.
A 20-row list with per-row subscriptions exhausts a Developer Edition org on a
single page render.

## Refreshing A Record From CDC

`getRecordNotifyChange(recordIds)` is **deprecated**. Use
`notifyRecordUpdateAvailable(recordIds)`, which considers record data wired by
all instantiated components and re-emits only where data actually changed.

CDC payloads are **deltas** — `ChangeEventHeader.recordIds` says *which* records
changed; the payload is not a complete record. Identify with CDC, refetch with
LDS. That keeps the whole page consistent and re-applies the running user's FLS,
which rendering the payload directly does not.

## Anti-Patterns (see references/llm-anti-patterns.md)

- Inventing `EventSource` or a WebSocket — the Salesforce answer is CometD
  behind `lightning/empApi`.
- Subscribing per row or per child component.
- Missing `disconnectedCallback` unsubscribe, or a reconnect timer that outlives
  the component.
- Trusting `-1` as a transport rather than as a latency optimisation.
- Non-idempotent handlers (increment / append).
- No `isEmpEnabled()` guard — a silent blank region on mobile.

## Official Sources Used

- Emp API (`lightning/empApi`) — https://developer.salesforce.com/docs/component-library/bundle/lightning-emp-api/documentation
- Platform Event Allocations — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
- Event Message Durability (Pub/Sub API) — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/event-message-durability.html
- notifyRecordUpdateAvailable(recordIds) — https://developer.salesforce.com/docs/platform/lwc/guide/reference-notify-record-update.html
- Subscribe to Platform Event Notifications in a Lightning Component — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_subscribe_lc.htm
- Change Data Capture — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
