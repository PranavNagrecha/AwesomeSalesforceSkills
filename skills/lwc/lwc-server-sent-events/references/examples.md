# Examples — LWC Streaming (`lightning/empApi`)

The `lightning/empApi` module exports exactly five functions
([Emp API](https://developer.salesforce.com/docs/component-library/bundle/lightning-emp-api/documentation)):

| Function | Signature | Returns |
|---|---|---|
| `subscribe` | `subscribe(channel, replayId, onMessageCallback)` | `Promise<subscription>` |
| `unsubscribe` | `unsubscribe(subscription, callback)` | `Promise` — callback receives a result with a `successful` boolean |
| `onError` | `onError(callback)` | `void` — **call once per component lifespan**; a second call overwrites the first |
| `setDebugFlag` | `setDebugFlag(boolean)` | `void` — console logging on/off |
| `isEmpEnabled` | `isEmpEnabled()` | `Promise<boolean>` — is EmpJs usable in this context |

Requires API version 44.0+. Supported in desktop browsers with web worker or
shared worker support. **Not supported in the Salesforce mobile app**, and not
usable in child windows, utility-bar pop-outs, or iframes.

---

## Example 1 — WRONG vs RIGHT: the subscription lifecycle

### WRONG — three defects that ship together

```javascript
import { LightningElement, api } from 'lwc';
import { subscribe, onError } from 'lightning/empApi';

export default class OrderTicker extends LightningElement {
    @api recordId;
    orders = [];

    renderedCallback() {                     // (1) runs on EVERY re-render
        subscribe('/event/Order_Status__e', -1, (msg) => {
            this.orders = [...this.orders, msg.data.payload];
        });
        onError((e) => console.error(e));    // (2) re-registers each render
    }
                                             // (3) no disconnectedCallback
}
```

1. **`renderedCallback` runs on every re-render.** Each subscription pushes
   another delivery against the org's 24-hour allocation, and every message is
   then handled N times where N is the number of renders so far.
2. **`onError` must be called once.** Calling it repeatedly overwrites the
   previous handler; the documentation is explicit that multiple calls replace
   the earlier one.
3. **No `unsubscribe`.** The subscription outlives the component. In a console
   app where users open and close tabs all day, this accumulates silently.

### RIGHT — one-time setup, guarded, torn down

```javascript
import { LightningElement, api } from 'lwc';
import {
    subscribe,
    unsubscribe,
    onError,
    isEmpEnabled
} from 'lightning/empApi';

const CHANNEL = '/event/Order_Status__e';

export default class OrderTicker extends LightningElement {
    @api recordId;

    orders = [];
    empUnavailable = false;

    _subscription = null;
    _errorRegistered = false;

    // One-time setup belongs here, not in renderedCallback.
    async connectedCallback() {
        // empApi is unavailable in the mobile app, in iframes, and in
        // utility-bar pop-outs. Degrade deliberately instead of failing.
        const enabled = await isEmpEnabled();
        if (!enabled) {
            this.empUnavailable = true;
            return;
        }

        if (!this._errorRegistered) {
            onError((error) => this.handleStreamingError(error));
            this._errorRegistered = true;
        }

        try {
            this._subscription = await subscribe(
                CHANNEL,
                -1,
                (message) => this.handleEvent(message)
            );
        } catch (error) {
            this.handleStreamingError(error);
        }
    }

    disconnectedCallback() {
        if (!this._subscription) {
            return;
        }
        unsubscribe(this._subscription, (result) => {
            if (!result || result.successful !== true) {
                // Not fatal, but worth surfacing — a failed unsubscribe means
                // the subscription may still be consuming the org allocation.
                this.dispatchEvent(new CustomEvent('streamingwarning', {
                    detail: { stage: 'unsubscribe', result }
                }));
            }
        });
        this._subscription = null;
    }

    handleEvent(message) {
        // Message shape: message.data.payload holds the event fields;
        // message.data.event.replayId is the position in the stream.
        const payload = message?.data?.payload;
        const replayId = message?.data?.event?.replayId;
        if (!payload) {
            return;
        }
        // Handlers MUST be idempotent — see gotcha 6.
        this.applyOrderUpdate(payload, replayId);
    }

    handleStreamingError(error) {
        this.dispatchEvent(new CustomEvent('streamingerror', {
            detail: { error }
        }));
    }
}
```

```html
<!-- orderTicker.html -->
<template>
    <template lwc:if={empUnavailable}>
        <!-- Never a blank component. Streaming is unavailable on mobile and in
             iframes; the user needs a working path, not a silent no-op. -->
        <div role="status" class="slds-text-color_weak">
            Live updates aren't available here.
            <lightning-button
                label="Refresh"
                onclick={handleManualRefresh}>
            </lightning-button>
        </div>
    </template>
    <template lwc:else>
        <!-- live list -->
    </template>
</template>
```

The `isEmpEnabled()` guard is the part most implementations omit, and it is the
difference between a component that degrades and one that appears broken on
every mobile device in the org.

---

## Example 2 — CDC auto-refresh, with the current API

### Context

A Case detail page should refresh when the record changes server-side.

### WRONG — the deprecated refresh call

```javascript
import { getRecordNotifyChange } from 'lightning/uiRecordApi';   // DEPRECATED
// ...
getRecordNotifyChange([{ recordId: this.recordId }]);
```

`getRecordNotifyChange(recordIds)` is deprecated. Use
`notifyRecordUpdateAvailable(recordIds)` instead — and note the behavioural
difference: unlike the deprecated call, `notifyRecordUpdateAvailable` *"considers
the record data wired by all instantiated components"*, refreshing every wire
that uses data from the supplied record ids and re-emitting only where the data
actually changed
([notifyRecordUpdateAvailable](https://developer.salesforce.com/docs/platform/lwc/guide/reference-notify-record-update.html)).

### RIGHT — CDC tells you *which* record; LDS fetches *what* changed

```javascript
import { LightningElement, api, wire } from 'lwc';
import { subscribe, unsubscribe, onError } from 'lightning/empApi';
import { getRecord, notifyRecordUpdateAvailable } from 'lightning/uiRecordApi';
import CASE_STATUS from '@salesforce/schema/Case.Status';
import CASE_SUBJECT from '@salesforce/schema/Case.Subject';

const CDC_CHANNEL = '/data/CaseChangeEvent';
const FIELDS = [CASE_STATUS, CASE_SUBJECT];

export default class CaseLiveDetail extends LightningElement {
    @api recordId;

    _subscription = null;

    @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
    caseRecord;

    async connectedCallback() {
        onError((e) => this.handleError(e));
        this._subscription = await subscribe(CDC_CHANNEL, -1, (msg) => {
            // CDC payloads are DELTAS. ChangeEventHeader.recordIds tells you
            // WHICH records changed; the changed values are not guaranteed to
            // be a complete record. Let LDS fetch the truth.
            const header = msg?.data?.payload?.ChangeEventHeader;
            const ids = header?.recordIds ?? [];
            if (ids.includes(this.recordId)) {
                notifyRecordUpdateAvailable([{ recordId: this.recordId }]);
            }
        });
    }

    disconnectedCallback() {
        if (this._subscription) {
            unsubscribe(this._subscription, () => {});
            this._subscription = null;
        }
    }

    handleError(error) {
        this.dispatchEvent(new CustomEvent('streamingerror', { detail: { error } }));
    }
}
```

### Why this shape rather than rendering the CDC payload directly

- **Consistency.** LDS is the cache the rest of the page reads from. Rendering
  the CDC payload in one component and leaving the rest of the page on stale
  cached data produces a page that contradicts itself.
- **Security.** The CDC payload is delivered based on the *subscriber's* channel
  access. Refetching through LDS re-applies the running user's FLS and sharing
  to each field.
- **Completeness.** A CDC delta contains only changed fields. A component that
  renders it directly must merge, and merge logic drifts.

---

## Example 3 — One subscription per page, fanned out to children

### Context

A list of 100 order rows, each of which should update live.

### WRONG — subscribe per row

```javascript
// orderRow.js — 100 instances = 100 subscriptions
connectedCallback() {
    subscribe('/event/Order_Status__e', -1, this.handle.bind(this));
}
```

Each subscribed client counts against the org's concurrent-CometD-client limit
and each delivered event counts against the 24-hour delivery allocation. In a
Developer Edition org the concurrent client ceiling is **20**, so this component
exhausts it with a single page render.

### RIGHT — container subscribes, children receive props

```javascript
// orderList.js
import { LightningElement } from 'lwc';
import { subscribe, unsubscribe, onError } from 'lightning/empApi';

export default class OrderList extends LightningElement {
    orders = [];
    _subscription = null;

    async connectedCallback() {
        onError((e) => this.handleError(e));
        this._subscription = await subscribe(
            '/event/Order_Status__e',
            -1,
            (msg) => this.route(msg)
        );
    }

    disconnectedCallback() {
        if (this._subscription) {
            unsubscribe(this._subscription, () => {});
            this._subscription = null;
        }
    }

    route(message) {
        const payload = message?.data?.payload;
        if (!payload?.Order_Id__c) {
            return;
        }
        // Reassign the array so LWC's reactivity picks it up. Mutating an
        // element in place does not trigger a re-render.
        this.orders = this.orders.map((o) =>
            o.id === payload.Order_Id__c
                ? { ...o, status: payload.Status__c, updatedAt: Date.now() }
                : o
        );
    }
}
```

```html
<!-- orderList.html — children are pure, no subscriptions -->
<template>
    <template for:each={orders} for:item="order">
        <c-order-row
            key={order.id}
            order={order}>
        </c-order-row>
    </template>
</template>
```

One subscription serves all 100 rows. The children become pure presentational
components, which also makes them trivially testable — the usual second benefit
of this refactor.

---

## Example 4 — Replay strategy, with the correct retention window

### The option values

| `replayId` | Behaviour | Use when |
|---|---|---|
| `-1` | New events only, from the moment of subscription | Best-effort UI updates |
| `-2` | All retained events in the durability window | Component needs recent history on open |
| specific | Resume from a known position | Reliability-critical flows |

### The retention window is 72 hours, not 24

Platform events and change data capture events are published to the event bus,
where they are **stored for 72 hours**. Salesforce does not guarantee storage
beyond that, though purging sometimes starts later so older events can still be
available
([Event Message
Durability](https://developer.salesforce.com/docs/platform/pub-sub-api/guide/event-message-durability.html)).

A stored replay id older than the retention window cannot be resumed from.

### Persisting a replay id across reloads

```javascript
const REPLAY_KEY = 'orderTicker.replayId';

async connectedCallback() {
    onError((e) => this.handleError(e));

    const stored = Number(window.localStorage.getItem(REPLAY_KEY));
    const storedAt = Number(window.localStorage.getItem(REPLAY_KEY + '.at'));

    // Treat a stored replay id as having a TTL shorter than the platform's
    // 72-hour retention. If it may have aged out, fall back to -1 rather than
    // subscribing with an id the bus can no longer resolve.
    const RETENTION_MS = 72 * 60 * 60 * 1000;
    const SAFETY_MARGIN_MS = 60 * 60 * 1000;   // 1 hour
    const isFresh = storedAt &&
        (Date.now() - storedAt) < (RETENTION_MS - SAFETY_MARGIN_MS);

    const replayId = (stored && isFresh) ? stored : -1;

    this._subscription = await subscribe('/event/Order_Status__e', replayId,
        (msg) => {
            const rid = msg?.data?.event?.replayId;
            if (rid) {
                window.localStorage.setItem(REPLAY_KEY, String(rid));
                window.localStorage.setItem(REPLAY_KEY + '.at', String(Date.now()));
            }
            this.handleEvent(msg);
        });
}
```

**Two honest caveats on this pattern.** First, `localStorage` in LWC is
namespaced per namespace by Lightning Web Security, which is what you want but
means the key is not shared with other namespaces. Second, and more importantly,
if the user has three tabs open, all three write to the same key and the
last-writer wins — so a resumed subscription may skip events another tab already
consumed. If exactly-once matters, the replay id belongs on the server, not in
the browser.

**When `-1` is honest and sufficient:** a live dashboard where the next event
corrects any gap, or any UI that re-fetches on focus. Reach for replay
persistence only when a missed event has a durable consequence.

---

## Example 5 — Reconnect with bounded backoff

### Context

Laptop lid closes. Network drops. `onError` fires.

### The shape

```javascript
const BACKOFF_MS = [1000, 2000, 5000, 15000, 30000];   // capped, not infinite

export default class ResilientTicker extends LightningElement {
    _subscription = null;
    _attempt = 0;
    _timerId = null;
    _destroyed = false;

    async connectedCallback() {
        onError((error) => this.onStreamError(error));
        await this.doSubscribe();
    }

    disconnectedCallback() {
        this._destroyed = true;            // stop any pending retry
        window.clearTimeout(this._timerId);
        if (this._subscription) {
            unsubscribe(this._subscription, () => {});
            this._subscription = null;
        }
    }

    onStreamError(error) {
        // 403 on the channel is a permissions problem. Retrying will never fix
        // it and every attempt burns allocation. Fail loudly instead.
        if (this.isAuthFailure(error)) {
            this.showPermanentError(
                'You do not have access to live updates for this object.');
            return;
        }
        this.scheduleReconnect();
    }

    scheduleReconnect() {
        if (this._destroyed) {
            return;
        }
        if (this._attempt >= BACKOFF_MS.length) {
            // Give up on push and tell the user how to get current data.
            this.showDegradedMode();
            return;
        }
        const delay = BACKOFF_MS[this._attempt++];
        this._timerId = window.setTimeout(() => this.doSubscribe(), delay);
    }

    async doSubscribe() {
        if (this._destroyed) {
            return;
        }
        try {
            this._subscription = await subscribe(CHANNEL, -1,
                (m) => this.handleEvent(m));
            this._attempt = 0;                  // reset only on success
            this.hideDegradedMode();
        } catch (e) {
            this.scheduleReconnect();
        }
    }

    isAuthFailure(error) {
        const text = JSON.stringify(error ?? {});
        return text.includes('403') || text.includes('403::');
    }
}
```

### Three properties that make this correct rather than merely present

- **The `_destroyed` flag.** Without it, a pending `setTimeout` fires after the
  component is gone and resubscribes an orphan. This is the leak that survives
  adding `disconnectedCallback`.
- **Bounded attempts, then a visible degraded mode.** Infinite retry against a
  down service silently consumes the org's shared allocation on behalf of every
  user who has the page open.
- **Permanent errors are not retried.** A 403 is a configuration problem. Every
  retry is wasted allocation and a delayed diagnosis.

---

## Anti-Pattern — treating streaming as a reliable transport

**What practitioners do:** build a workflow where the *only* signal that an
approval completed is a platform event, subscribed with `-1`.

**What goes wrong:** `-1` subscribes from now. Events fired while the browser was
backgrounded, the network was down, or the page was mid-reload are simply not
delivered. The user sees a pending approval indefinitely, and the failure is
invisible — nothing errored.

Delivery is also capped: the 24-hour allocation of delivered event notifications
to CometD clients is shared across all clients in the org, and is finite by
edition. Under a burst, the events you needed may be the ones not delivered.

**Correct approach:** treat streaming as a **latency optimisation over a
correct fallback**, never as the source of truth. The page re-fetches state on
focus, on a slow poll, or when the user acts. A missed push then means a few
seconds of staleness rather than a stuck workflow. Reliability-critical flows
that genuinely need at-least-once delivery belong on a server-side consumer with
a committed replay position — see `integration/platform-events-integration` and
the Pub/Sub API's managed subscriptions, not in a browser tab.
