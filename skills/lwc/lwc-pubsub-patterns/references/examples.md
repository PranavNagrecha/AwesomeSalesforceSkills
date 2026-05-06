# Examples — LWC Pub/Sub Patterns

## Example 1 — Parent-child should NOT use LMS

**Wrong.**

```javascript
// Parent
@wire(MessageContext) messageContext;
publish(this.messageContext, REFRESH_CHANNEL, { id });

// Child
subscribe(this.messageContext, REFRESH_CHANNEL, (msg) => {...});
```

**Why it's wrong.** The components have a parent-child
relationship; LMS adds indirection (channel definition, message
context, subscribe lifecycle) where a single `@api` property or
`CustomEvent` would do the same job in less code.

**Right.**

```javascript
// Parent template
<c-child record-id={recordId} onselect={handleSelect}></c-child>

// Child
@api recordId;
fireSelect() {
    this.dispatchEvent(new CustomEvent('select', {
        detail: { id: this.recordId }
    }));
}
```

LMS is for **siblings** with no parent-child relationship.

---

## Example 2 — Sibling LMS with subscribe / unsubscribe

**Channel.**

```xml
<!-- force-app/main/default/messageChannels/RecordSelected.messageChannel-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Record Selected</masterLabel>
    <isExposed>true</isExposed>
    <description>Search -> details sibling sync.</description>
    <lightningMessageFields>
        <fieldName>recordId</fieldName>
        <description>Selected record Id.</description>
    </lightningMessageFields>
</LightningMessageChannel>
```

**Publisher (search component).**

```javascript
import { LightningElement, wire } from 'lwc';
import { publish, MessageContext } from 'lightning/messageService';
import RECORD_SELECTED from '@salesforce/messageChannel/RecordSelected__c';

export default class Search extends LightningElement {
    @wire(MessageContext) messageContext;

    handleClick(evt) {
        publish(this.messageContext, RECORD_SELECTED, {
            recordId: evt.target.dataset.id
        });
    }
}
```

**Subscriber (details component).**

```javascript
import { LightningElement, wire } from 'lwc';
import {
    subscribe, unsubscribe, MessageContext, APPLICATION_SCOPE
} from 'lightning/messageService';
import RECORD_SELECTED from '@salesforce/messageChannel/RecordSelected__c';

export default class Details extends LightningElement {
    @wire(MessageContext) messageContext;
    subscription = null;
    recordId;

    connectedCallback() {
        this.subscription = subscribe(
            this.messageContext,
            RECORD_SELECTED,
            (msg) => { this.recordId = msg.recordId; },
            { scope: APPLICATION_SCOPE }
        );
    }

    disconnectedCallback() {
        unsubscribe(this.subscription);
        this.subscription = null;
    }
}
```

---

## Example 3 — The leaked subscription bug

**Wrong.**

```javascript
connectedCallback() {
    this.subscription = subscribe(this.messageContext, CH, this.handle);
}
// Forgot disconnectedCallback
```

**What happens.** User navigates away from the page. The component
is destroyed. The subscription is not removed. The handler is now
attached to a destroyed component — depending on browser timing,
this may be a memory leak, a duplicate-handler bug (next visit
double-fires), or a noisy console error.

**Right.**

```javascript
disconnectedCallback() {
    unsubscribe(this.subscription);
    this.subscription = null;
}
```

Always pair every subscribe with an unsubscribe. Treat it like
opening a file: close it.

---

## Example 4 — APPLICATION_SCOPE for utility bar

**Context.** Utility-bar component needs to publish "user is busy"
to any page-level component listening.

**Configuration.** Subscriber sets `{ scope: APPLICATION_SCOPE }`
so it receives messages regardless of which app / page it's on
within the Lightning session.

**Why it matters.** Default scope (`ACTIVE`) only delivers to
subscribers in the active navigation context. Utility-bar
components live outside the navigation context; subscribers using
default scope would never receive their messages.

---

## Example 5 — Migrating from `c/pubsub` to LMS

**Before.**

```javascript
import { fireEvent, registerListener } from 'c/pubsub';
registerListener('searchSelected', this.handleSelect, this);
fireEvent(this.pageRef, 'searchSelected', { id });
```

**After.**

```javascript
import { publish, subscribe, MessageContext } from 'lightning/messageService';
import SEARCH_SELECTED from '@salesforce/messageChannel/SearchSelected__c';
@wire(MessageContext) messageContext;

connectedCallback() {
    this.subscription = subscribe(
        this.messageContext, SEARCH_SELECTED, this.handleSelect.bind(this)
    );
}
publish(this.messageContext, SEARCH_SELECTED, { id });
```

**Migration steps.**

1. Define a Message Channel for each pubsub event.
2. Replace `fireEvent` with `publish`.
3. Replace `registerListener` with `subscribe`.
4. Add `disconnectedCallback` with `unsubscribe`.
5. Remove the `c/pubsub` utility once no consumers remain.

---

## Example 6 — Choosing between LMS, parent-child, and Platform Events

| Communication shape | Right tool |
|---|---|
| Parent passes data to child | `@api` props |
| Child notifies parent | `CustomEvent` (bubbles="false" default; set composed=true to cross shadow boundary) |
| Sibling notifies sibling on the same page | LMS |
| Utility-bar notifies pages | LMS with `APPLICATION_SCOPE` |
| Cross-tab / cross-user / cross-org | Platform Events |
| LWC subscribes to Apex change | `@wire` to Apex method, or CDC, or Platform Events |
| Aura page hosting an LWC | LMS (or Aura's Application Events bridge) |
