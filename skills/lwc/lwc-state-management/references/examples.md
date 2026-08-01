# Examples — LWC State Management

Both examples are about state crossing a component boundary that `@api` cannot reach.
For the mechanics of the channel itself see `lwc/message-channel-patterns`; for
in-component reactivity see `lwc/lwc-reactive-state-patterns`.

## Example 1: A list panel that did not refresh after a sibling saved

**Context:** A record page with an edit panel and a list panel side by side. They are
siblings — neither is the other's parent — so there is no `@api` property and no event
bubbling path between them.

**Problem:** Saving in the edit panel updated the record, but the list panel kept showing
the pre-save values until the user reloaded the page. The first attempt fixed it by having
the list poll every few seconds, which moved the problem from "stale" to "stale plus a
query every five seconds per open tab".

**Solution:** The publisher announces the save; the subscriber refreshes its own wire.

```javascript
// editPanel.js — publisher
import { LightningElement, api, wire } from 'lwc';
import { publish, MessageContext } from 'lightning/messageService';
import RECORD_SAVED from '@salesforce/messageChannel/RecordSaved__c';

export default class EditPanel extends LightningElement {
    @api recordId;
    @wire(MessageContext) messageContext;

    handleSuccess(event) {
        publish(this.messageContext, RECORD_SAVED, {
            recordId: event.detail.id,
            objectApiName: 'Contact'
        });
    }
}
```

```javascript
// listPanel.js — subscriber, refreshes the wire rather than re-querying by hand
import { LightningElement, wire } from 'lwc';
import { refreshApex } from '@salesforce/apex';
import { subscribe, unsubscribe, MessageContext, APPLICATION_SCOPE }
    from 'lightning/messageService';
import RECORD_SAVED from '@salesforce/messageChannel/RecordSaved__c';
import getContacts from '@salesforce/apex/ContactListController.getContacts';

export default class ListPanel extends LightningElement {
    @wire(MessageContext) messageContext;
    @wire(getContacts) contacts;      // keep the provisioned value for refreshApex
    subscription = null;

    connectedCallback() {
        if (this.subscription) return;
        this.subscription = subscribe(
            this.messageContext,
            RECORD_SAVED,
            (message) => this.handleSaved(message),
            { scope: APPLICATION_SCOPE }
        );
    }

    disconnectedCallback() {
        unsubscribe(this.subscription);
        this.subscription = null;
    }

    handleSaved(message) {
        if (message.objectApiName === 'Contact') {
            refreshApex(this.contacts);
        }
    }
}
```

**Why it works:** neither panel imports the other, so either can be removed from the page
without breaking the other. `refreshApex` re-provisions the existing wire rather than
issuing a parallel imperative query, so the component keeps one source of truth. The
`{ scope: APPLICATION_SCOPE }` option is only available when `MessageContext` is obtained
through `@wire` — that is a documented constraint, not a style choice.

**What to watch:** if the subscriber can render *after* the publish it will never see the
message — nothing retains the last value. Where that is possible, the late-joining
component has to ask for the current state on connect instead of waiting to be told.

---

## Example 2: An app-wide "current region" that did not warrant a channel

**Context:** A region switcher in the utility bar; roughly a dozen components across the
app need to know the selected region and re-render when it changes.

**Problem:** The reads are frequent and purely client-side — the region is a filter, not a
record. Routing every read through a message channel meant every consumer needed
subscribe/unsubscribe plumbing, and a component that mounted after the switcher published
showed no region at all.

**Solution:** A module-level singleton that *retains* the current value, so a late
subscriber gets it immediately on subscribe. This is the narrow case where a hand-rolled
store beats both `@api` and a channel.

```javascript
// regionStore.js — retains last value; subscribe returns its own teardown
const subscribers = new Set();
let currentRegion = null;

export function getRegion() {
    return currentRegion;
}

export function setRegion(region) {
    if (region === currentRegion) return;    // do not notify on a no-op write
    currentRegion = region;
    subscribers.forEach((fn) => fn(currentRegion));
}

export function subscribeToRegion(fn) {
    subscribers.add(fn);
    if (currentRegion !== null) {
        fn(currentRegion);                   // late joiner is caught up immediately
    }
    return () => subscribers.delete(fn);     // caller stores this, calls it on disconnect
}
```

```javascript
// regionAwareTile.js — consumer; teardown is the thing subscribe handed back
import { LightningElement } from 'lwc';
import { subscribeToRegion } from 'c/regionStore';

export default class RegionAwareTile extends LightningElement {
    region;
    unsubscribe;

    connectedCallback() {
        this.unsubscribe = subscribeToRegion((region) => {
            this.region = region;            // reassignment triggers re-render
        });
    }

    disconnectedCallback() {
        this.unsubscribe?.();
    }
}
```

**Why it works:** returning the teardown function from `subscribe` makes the leak hard to
write — the consumer cannot subscribe without being handed the thing that unsubscribes.
Retaining `currentRegion` removes the publish-before-subscribe race that the channel
version has.

**Why this is not the default:** the store is a second source of truth. It is defensible
here only because the region is client-only state that no server record owns. The moment
the value is server-owned this pattern loses to a wire adapter, which already caches,
shares across components and invalidates itself.

**Scope caveat:** a module-level singleton is shared by everything that imports it inside
one browsing context. It does not cross an iframe boundary, so it is not a substitute for
a message channel when a component is hosted inside one.
