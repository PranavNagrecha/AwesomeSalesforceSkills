---
name: lwc-server-sent-events
description: "Use when building LWCs that must react to live server pushes — Platform Events, Change Data Capture, or streaming updates — via the lightning/empApi (CometD) subscription model. Covers lifecycle, replayId, error handling, reconnection, scale considerations, and multi-tab behavior. Does NOT cover publishing events (see platform-events or apex-platform-events)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
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

## Recommended Workflow

1. **Confirm streaming is the right tool.** For record changes, consider
   `getRecordNotifyChange` or Lightning Data Service caches first.
2. **Pick the channel.** Platform Event (`/event/<EventName>__e`), CDC
   (`/data/<ObjectName>ChangeEvent`), or Generic Streaming (`/u/...`).
3. **Subscribe in `connectedCallback`.** Always unsubscribe in
   `disconnectedCallback`. Store the subscription reference.
4. **Decide replayId.** `-1` = new events only, `-2` = retained events
   (24h), or a specific replayId if you track last-seen.
5. **Handle errors.** `onError` must log and, where appropriate, re-subscribe
   with backoff.
6. **De-duplicate across tabs.** A user with 3 tabs open will receive each
   event 3x. Decide whether that matters.
7. **Respect governor limits.** Daily event delivery allocation is finite.

## Lifecycle Template

```js
import { subscribe, unsubscribe, onError, setDebugFlag } from 'lightning/empApi';

connectedCallback() {
  this.registerErrorListener();
  this.handleSubscribe();
}

disconnectedCallback() {
  this.handleUnsubscribe();
}

handleSubscribe() {
  const channel = '/event/Order_Status__e';
  const replayId = -1; // new only
  subscribe(channel, replayId, this.onEvent.bind(this))
    .then((sub) => (this._subscription = sub))
    .catch((err) => this.handleError(err));
}

handleUnsubscribe() {
  if (this._subscription) {
    unsubscribe(this._subscription, () => {});
    this._subscription = null;
  }
}

onEvent(message) {
  // message.data.payload
}

registerErrorListener() {
  onError((err) => this.handleError(err));
}
```

## Replay Strategy

| Value | Behavior | Use When |
|---|---|---|
| `-1` | Only new events after subscribe | Best-effort UI updates |
| `-2` | All retained events (24h window) | Component needs history on open |
| specific replayId | Resume from a known point | Reliability-critical workflows |

Tracking replayId client-side requires persistence (localStorage keyed by
user) and careful cross-tab coordination.

## Error And Reconnect

- Network drop: empApi emits an error; re-subscribe with exponential
  backoff (1s, 2s, 5s, 30s cap).
- 403 on channel: permissions issue; log and give up.
- Event pool exhausted (server-side): surface the error; ops concern.

## Multi-Tab / Multi-Component

- Each LWC instance = one subscription = one delivery.
- To de-duplicate, elect a leader tab (BroadcastChannel) and forward
  events to other tabs, or accept duplicates if the handler is idempotent.
- For multi-component on one page, consider subscribing once at a parent
  and `dispatchEvent`-ing to children.

## Scale

- Platform Event daily limit varies by edition; confirm for your org.
- One component per user subscribed to a high-volume channel = linear
  multiplier on delivery counts.
- For very high volume, CDC may be cheaper than Platform Events for the
  same data shape.

## Anti-Patterns (see references/llm-anti-patterns.md)

- Subscribing in every child component.
- Forgetting `disconnectedCallback` unsubscribe (memory leak).
- Trusting `-1` for reliability-critical flows.
- Handling events without idempotency.

## Official Sources Used

- Lightning empApi — https://developer.salesforce.com/docs/platform/lwc/guide/use-comm-empapi.html
- Platform Events Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Change Data Capture — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- Streaming API — https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/intro_stream.htm
