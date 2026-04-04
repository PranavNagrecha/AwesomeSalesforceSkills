# Message Channel Patterns — Work Template

Use this template when implementing or reviewing Lightning Message Service in a Salesforce org.

## Scope

**Skill:** `message-channel-patterns`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer these before starting:

- **UI technologies involved:** [ ] LWC only  [ ] LWC + Aura  [ ] LWC + Visualforce
- **Subscriber location:** [ ] Inline page region  [ ] Utility bar  [ ] Workspace tab  [ ] Console nav item
- **Channel already deployed?** [ ] Yes  [ ] No — must deploy first
- **Cross-namespace required?** [ ] Yes (`isExposed: true`)  [ ] No (`isExposed: false`)
- **Scope decision:** [ ] Default (active tab only)  [ ] APPLICATION_SCOPE (required for VF iframe or inactive tab)

---

## Message Channel Metadata

File path: `force-app/main/default/messageChannels/<ChannelName>.messageChannel-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel><!-- Human-readable label --></masterLabel>
    <isExposed>false</isExposed>
    <description><!-- What event this channel represents --></description>
    <lightningMessageFields>
        <fieldName><!-- fieldName1 --></fieldName>
        <description><!-- What this field carries --></description>
    </lightningMessageFields>
    <!-- Add more lightningMessageFields as needed -->
</LightningMessageChannel>
```

**Deployment command:**
```bash
sf project deploy start --source-dir force-app/main/default/messageChannels
```

---

## Publisher Component (LWC)

```javascript
// <componentName>.js
import { LightningElement, wire } from 'lwc';
import { publish, MessageContext } from 'lightning/messageService';
import CHANNEL_NAME from '@salesforce/messageChannel/<ChannelName>__c';
// For namespaced channel: import CHANNEL_NAME from '@salesforce/messageChannel/namespace__ChannelName__c';

export default class PublisherComponentName extends LightningElement {
    @wire(MessageContext)
    messageContext;

    handleUserAction(event) {
        const payload = {
            // fieldName1: value,
            // fieldName2: value
        };
        publish(this.messageContext, CHANNEL_NAME, payload);
    }
}
```

**Checklist:**
- [ ] `@wire(MessageContext)` is declared (not called in constructor)
- [ ] Payload contains only serializable JSON values (no functions, no class instances)
- [ ] Publish is triggered by a user action or lifecycle event, not a constructor call

---

## Subscriber Component (LWC)

```javascript
// <componentName>.js
import { LightningElement, wire, track } from 'lwc';
import {
    subscribe,
    unsubscribe,
    MessageContext,
    APPLICATION_SCOPE   // Remove if default (active tab) scope is sufficient
} from 'lightning/messageService';
import CHANNEL_NAME from '@salesforce/messageChannel/<ChannelName>__c';

export default class SubscriberComponentName extends LightningElement {
    @wire(MessageContext)
    messageContext;

    subscription = null;

    // Add @track properties for message payload fields
    // @track fieldName1;

    connectedCallback() {
        this.subscription = subscribe(
            this.messageContext,
            CHANNEL_NAME,
            (message) => this.handleMessage(message),
            { scope: APPLICATION_SCOPE }   // Remove options object if using default scope
        );
    }

    disconnectedCallback() {
        unsubscribe(this.subscription);
        this.subscription = null;
    }

    handleMessage(message) {
        // Process message fields
        // this.fieldName1 = message.fieldName1;
    }
}
```

**Checklist:**
- [ ] `subscribe()` is called in `connectedCallback`, not constructor
- [ ] Subscription handle is stored in `this.subscription`
- [ ] `unsubscribe()` is called in `disconnectedCallback`
- [ ] `this.subscription` is set to `null` after unsubscribing
- [ ] Scope is explicitly set to `APPLICATION_SCOPE` if cross-tab or cross-iframe delivery is needed

---

## Aura Subscriber Reference (if Aura component is a subscriber)

```html
<!-- myAuraSubscriber.cmp -->
<aura:component>
    <!-- lightning:messageChannel must be a DIRECT child of aura:component -->
    <lightning:messageChannel
        type="ChannelName__c"
        aura:id="channelRef"
        onMessage="{!c.handleMessage}"
        scope="APPLICATION"
    />
    <!-- scope="APPLICATION" is optional; omit for active-tab-only delivery -->
</aura:component>
```

```javascript
// myAuraSubscriberController.js
({
    handleMessage: function(cmp, message, helper) {
        var fieldValue = message.getParam('fieldName1');
        // process fieldValue
    }
})
```

**Checklist:**
- [ ] `lightning:messageChannel` is an immediate child of `aura:component` (not nested in card or layout)
- [ ] `aura:id` is set to access the component in the controller
- [ ] `onMessage` handler is in the controller file, not in helper

---

## LMS Contract Summary

| Field | Value |
|---|---|
| Channel name | `<ChannelName>__c` |
| Channel file | `messageChannels/<ChannelName>.messageChannel-meta.xml` |
| Publisher component(s) | |
| Subscriber component(s) | |
| Payload fields | |
| Scope | `APPLICATION_SCOPE` / Default |
| Cross-namespace | Yes / No (`isExposed`: true/false) |
| Subscription lifecycle owner | `connectedCallback` / `disconnectedCallback` |

---

## Deployment Order Reminder

1. Deploy message channel metadata first.
2. Deploy publisher and subscriber components after the channel is confirmed in the org.
3. Validate with `sf project deploy validate` before production deployment.

---

## Notes

(Record any deviations from the standard pattern and why.)
