# Examples — LWC Cross-Tab State Sync

## Example 1: BroadcastChannel record-update fan-out

**Context:** Customer-service team uses two browser tabs simultaneously — one for the case detail, one for the parent account. When the rep saves the case, the account view must reflect the new "Last Activity" stamp.

**Problem:** Without sync, the account tab is stale until manual refresh.

**Solution:**

```javascript
// recordSyncBus.js
const CHANNEL = 'sf-record-updates';
const channel = typeof BroadcastChannel !== 'undefined'
    ? new BroadcastChannel(CHANNEL)
    : null;

export function publishRecordUpdate(recordId) {
    if (!channel) return;
    channel.postMessage({ type: 'record-updated', recordId, ts: Date.now() });
}

export function subscribeRecordUpdate(handler) {
    if (!channel) return () => {};
    const wrapped = (e) => {
        if (e.data?.type === 'record-updated') handler(e.data);
    };
    channel.addEventListener('message', wrapped);
    return () => channel.removeEventListener('message', wrapped);
}
```

```javascript
// accountSummary.js
import { LightningElement, wire, api } from 'lwc';
import { getRecord, refreshApex } from 'lightning/uiRecordApi';
import { subscribeRecordUpdate } from 'c/recordSyncBus';

const FIELDS = ['Account.LastActivityDate'];

export default class AccountSummary extends LightningElement {
    @api recordId;
    wired;
    unsubscribe;

    @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
    handle(result) {
        this.wired = result;
    }

    connectedCallback() {
        this.unsubscribe = subscribeRecordUpdate(({ recordId }) => {
            // Refresh the account if the saved record was its own case child
            if (recordId === this.recordId) refreshApex(this.wired);
        });
    }

    disconnectedCallback() {
        this.unsubscribe?.();
    }
}
```

**Why it works:** `BroadcastChannel` does not echo to the sender; only other tabs receive the message. The `unsubscribe` returned from `subscribe` is the cleanup the `disconnectedCallback` needs.

---

## Example 2: Logout fan-out using the storage event (universal fallback)

**Context:** Org has not migrated to Lightning Web Security; some users on older browsers without `BroadcastChannel`.

**Problem:** Need cross-tab logout broadcast that works on every browser.

**Solution:**

```javascript
// sessionBus.js
const KEY = 'sf-session-event';

export function publishLogout() {
    localStorage.setItem(KEY, JSON.stringify({ type: 'logout', ts: Date.now() }));
    // Setting and removing in the same tick fires the storage event
    // in every other tab once.
    localStorage.removeItem(KEY);
}

export function subscribeLogout(handler) {
    const onStorage = (e) => {
        if (e.key !== KEY || !e.newValue) return;
        const data = JSON.parse(e.newValue);
        if (data.type === 'logout') handler(data);
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
}
```

**Why it works:** The `storage` event fires only in *other* tabs — same-tab self-fires are suppressed by the API. Setting and immediately removing the key triggers a single notification in each peer tab without leaving residue.

---

## Anti-Pattern: subscribing without cleanup

**What practitioners do:** `connectedCallback` subscribes to the channel; no `disconnectedCallback`.

**What goes wrong:** Each time the component is rerendered (e.g., a parent's `if:true` toggles), a new subscription is added but the old one is never removed. After a few minutes in a long-lived workspace tab, the same `record-updated` message triggers 20 `refreshApex` calls and the API limit warnings start.

**Correct approach:** Always pair subscribe + unsubscribe in lifecycle hooks. The subscribe function should return a cleanup function the component stores and calls on disconnect.
