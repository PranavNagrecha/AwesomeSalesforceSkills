# Examples — Aura to LWC Migration

## Example 1: Translating Aura Component Events to LWC CustomEvent

**Context:** An Aura child component fires a component event carrying a record ID when the user selects an item. The parent Aura component handles the event to refresh a panel. Both components are being migrated to LWC simultaneously.

**Problem:** The Aura component event definition and `component.fire()` API have no direct equivalent in LWC. Developers unfamiliar with LWC try to call `this.fire()` or look for a `CustomEvent` constructor analog that matches Aura naming conventions.

**Solution:**

Aura child — original:
```javascript
// accountSelected.evt (Aura event definition)
// <aura:event type="COMPONENT">
//   <aura:attribute name="recordId" type="String"/>
// </aura:event>

// In Aura child controller:
var event = component.getEvent("accountSelected");
event.setParams({ recordId: selectedId });
event.fire();
```

LWC child — migrated:
```javascript
// accountTile.js
import { LightningElement, api } from 'lwc';

export default class AccountTile extends LightningElement {
    @api recordId;

    handleSelect() {
        const selectedId = this.recordId;
        this.dispatchEvent(
            new CustomEvent('accountselected', {
                detail: { recordId: selectedId },
                bubbles: false,   // component events did not bubble by default
                composed: false
            })
        );
    }
}
```

LWC parent — migrated:
```html
<!-- accountPanel.html -->
<template>
    <c-account-tile record-id={tileRecordId}
                    onaccountselected={handleAccountSelected}>
    </c-account-tile>
</template>
```

```javascript
// accountPanel.js
import { LightningElement } from 'lwc';

export default class AccountPanel extends LightningElement {
    handleAccountSelected(event) {
        const selectedId = event.detail.recordId;
        // refresh logic here
    }
}
```

**Why it works:** LWC uses standard DOM `CustomEvent` dispatched with `dispatchEvent`. The parent listens with an `on<eventname>` handler in the template. The event name must be all lowercase in the template attribute (`onaccountselected`), matching the lowercase string passed to the `CustomEvent` constructor.

---

## Example 2: Replacing Aura Application Events with Lightning Message Service

**Context:** An Aura sidebar component fires an application event `c:CaseContextChanged` whenever the agent selects a case. Multiple Aura components on the same App Builder page subscribe to this event to update their views. During migration, some subscriber components are rewritten to LWC while the sidebar publisher remains Aura temporarily.

**Problem:** LWC components cannot register as handlers of Aura application events. The migrated LWC subscribers silently stop receiving updates. There is no error — the LWC event listener simply does not exist in the Aura event registry.

**Solution:**

Step 1 — Create the LMS channel:
```xml
<!-- force-app/main/default/messageChannels/CaseContext.messageChannel-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>CaseContext</masterLabel>
    <isExposed>true</isExposed>
    <description>Broadcasts the selected case context across components</description>
    <lightningMessageFields>
        <fieldName>caseId</fieldName>
        <description>Salesforce ID of the selected Case record</description>
    </lightningMessageFields>
    <lightningMessageFields>
        <fieldName>caseNumber</fieldName>
        <description>Human-readable case number for display</description>
    </lightningMessageFields>
</LightningMessageChannel>
```

Step 2 — Update the Aura publisher to also publish on the LMS channel (coexistence period):
```javascript
// In Aura sidebar controller — publish on LMS while Aura event is still fired
var messageService = component.find("messageService");
messageService.publish({
    caseId: selectedCaseId,
    caseNumber: selectedCaseNumber
});
// Also fire legacy Aura event for any remaining Aura subscribers
var evt = $A.get("e.c:CaseContextChanged");
evt.setParams({ caseId: selectedCaseId });
evt.fire();
```

```html
<!-- In Aura sidebar component markup — add LMS reference -->
<lightning:messageChannel type="CaseContext__c" aura:id="messageService"/>
```

Step 3 — LWC subscriber uses the LMS channel:
```javascript
// caseDetails.js (migrated LWC)
import { LightningElement, wire } from 'lwc';
import { subscribe, MessageContext, unsubscribe } from 'lightning/messageService';
import CASE_CONTEXT_CHANNEL from '@salesforce/messageChannel/CaseContext__c';

export default class CaseDetails extends LightningElement {
    @wire(MessageContext) messageContext;
    subscription = null;
    caseId;

    connectedCallback() {
        this.subscription = subscribe(
            this.messageContext,
            CASE_CONTEXT_CHANNEL,
            (message) => this.handleMessage(message)
        );
    }

    disconnectedCallback() {
        unsubscribe(this.subscription);
        this.subscription = null;
    }

    handleMessage(message) {
        this.caseId = message.caseId;
    }
}
```

**Why it works:** LMS is the only supported cross-framework messaging mechanism in Salesforce. Both Aura and LWC can publish and subscribe to the same LMS channel, enabling incremental migration without breaking communication. The Aura application event can be removed once all publishers and subscribers are migrated to LWC.

---

## Example 3: Replacing force:navigateToSObject with NavigationMixin

**Context:** An Aura component fires `force:navigateToSObject` to redirect the user to a Case record detail page. The component is being rewritten as LWC.

**Problem:** Developers attempt to fire `force:navigateToSObject` from LWC JavaScript, or look for a `$A.get("e.force:navigateToSObject")` equivalent. Neither works in LWC.

**Solution:**

Aura original:
```javascript
var navEvent = $A.get("e.force:navigateToSObject");
navEvent.setParams({ recordId: this.caseId });
navEvent.fire();
```

LWC migrated:
```javascript
// caseNavigator.js
import { LightningElement, api } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';

export default class CaseNavigator extends NavigationMixin(LightningElement) {
    @api caseId;

    navigateToCase() {
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: {
                recordId: this.caseId,
                objectApiName: 'Case',
                actionName: 'view'
            }
        });
    }
}
```

**Why it works:** `NavigationMixin` is the LWC-native navigation API. The class extends `NavigationMixin(LightningElement)` rather than directly extending `LightningElement`. Navigation calls use `this[NavigationMixin.Navigate](pageRef)` where the page reference object type (`standard__recordPage`, `standard__webPage`, etc.) replaces the Aura event name.

---

## Anti-Pattern: Attempting to Access $A in LWC

**What practitioners do:** Port Aura controller code verbatim into an LWC `.js` file, leaving `$A.enqueueAction`, `$A.getCallback`, or `$A.get("e.force:*")` calls intact.

**What goes wrong:** `$A` is not defined in the LWC JavaScript context. The browser throws `ReferenceError: $A is not defined` at runtime. The component renders but all server calls and navigation events fail.

**Correct approach:** Replace `$A.enqueueAction(action)` with either a `@wire` adapter or an imported Apex function called imperatively with `async/await`. Replace `$A.getCallback(fn)` by removing it entirely — LWC reactive properties trigger re-render from any async context without needing a re-entry wrapper. Replace `$A.get("e.force:*")` events with `NavigationMixin` calls.
