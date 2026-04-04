---
name: message-channel-patterns
description: "Use when implementing Lightning Message Service (LMS) to enable cross-DOM communication between LWC, Aura, and Visualforce components on the same Lightning page, using message channels. Triggers: 'communicate between unrelated LWC components', 'send data between Visualforce and LWC', 'lightning message service not working', 'APPLICATION_SCOPE vs default scope', 'message channel metadata deployment'. NOT for parent-child component communication (use component-communication) or server-side events."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Reliability
triggers:
  - "communicate between unrelated LWC components on the same page"
  - "send data between Visualforce and LWC or Aura on a Lightning page"
  - "lightning message service messages not received across DOM boundaries"
  - "how to use APPLICATION_SCOPE for message channels"
  - "how to unsubscribe from a message channel to prevent memory leaks"
tags:
  - lightning-message-service
  - message-channel
  - lms
  - cross-dom-communication
  - lwc-interop
  - application-scope
inputs:
  - "Which UI technologies are involved: LWC only, LWC + Aura, or LWC + Visualforce"
  - "Whether subscribers live in utility bar, workspace tabs, or inline page regions"
  - "The message payload shape: fields, types, and whether it crosses namespace boundaries"
  - "Whether the channel is already deployed or needs to be created from scratch"
outputs:
  - "Message channel XML metadata file (messageChannelName.messageChannel-meta.xml)"
  - "Publisher component with correct MessageContext and publish() wiring"
  - "Subscriber component with connectedCallback subscription and disconnectedCallback cleanup"
  - "Scope recommendation: APPLICATION_SCOPE vs default (active-tab-only)"
  - "Review findings for missing unsubscribe, wrong scope, or iframe boundary issues"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Message Channel Patterns

This skill activates when components that have no parent-child relationship must share state or events across DOM boundaries on a Lightning page. It covers creating message channels, wiring up publishers and subscribers in LWC and Aura, choosing the correct scope, and ensuring lifecycle cleanup.

---

## Before Starting

Gather this context before working on anything in this domain:

- Are the communicating components in a direct ownership chain, or are they truly unrelated (utility bar, workspace tab, sidebar, inline region)? If they are directly related, use `@api` / custom events from `component-communication` instead.
- What UI technologies are involved? LWC-to-LWC, LWC-to-Aura, and LWC-to-Visualforce all use LMS but the subscriber wiring syntax differs per technology.
- Is the subscriber inside a navigation tab (inactive-able) or always-on utility? This determines whether `APPLICATION_SCOPE` is required.
- Is the message channel already deployed? Channels must exist in the org before components that reference them can be deployed.

---

## Core Concepts

### Message Channel Metadata

A Lightning Message Channel is a platform metadata artifact — not a custom object, even though it uses the `__c` suffix. It lives in `force-app/main/default/messageChannels/` as a file named `channelName.messageChannel-meta.xml`. The file declares the channel's label, description, whether it can be used outside its defining namespace (`isExposed`), and optional typed field declarations (`lightningMessageFields`). Channels are deployed like any other metadata via `sf project deploy start`. A component that imports a channel that has not been deployed will fail at load time.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>ProductSelected</masterLabel>
    <isExposed>true</isExposed>
    <description>Published when a product record is selected in the catalog.</description>
    <lightningMessageFields>
        <fieldName>productId</fieldName>
        <description>Salesforce record ID of the selected product</description>
    </lightningMessageFields>
    <lightningMessageFields>
        <fieldName>productName</fieldName>
        <description>Display name of the selected product</description>
    </lightningMessageFields>
</LightningMessageChannel>
```

### Publishing on a Channel (LWC)

LWC components use the `lightning/messageService` wire adapter alongside two imports: the channel symbol and `MessageContext`. `MessageContext` is injected via `@wire` and must be present before calling `publish`. The payload is a plain serializable JavaScript object — functions and symbols are not allowed.

```javascript
// productCatalog.js
import { LightningElement, wire } from 'lwc';
import { publish, MessageContext } from 'lightning/messageService';
import PRODUCT_SELECTED_CHANNEL from '@salesforce/messageChannel/ProductSelected__c';

export default class ProductCatalog extends LightningElement {
    @wire(MessageContext)
    messageContext;

    handleProductClick(event) {
        const payload = {
            productId: event.currentTarget.dataset.id,
            productName: event.currentTarget.dataset.name
        };
        publish(this.messageContext, PRODUCT_SELECTED_CHANNEL, payload);
    }
}
```

### Subscribing and the Subscription Lifecycle (LWC)

Subscribers call `subscribe()` in `connectedCallback` and **must** call `unsubscribe()` in `disconnectedCallback`. Failing to unsubscribe causes the handler to continue firing even after the component is removed from the DOM because LMS holds a strong reference to the subscription object. Each `subscribe()` call returns a subscription handle — store it and pass it to `unsubscribe()` later.

```javascript
// productDetail.js
import { LightningElement, wire } from 'lwc';
import { subscribe, unsubscribe, MessageContext, APPLICATION_SCOPE } from 'lightning/messageService';
import PRODUCT_SELECTED_CHANNEL from '@salesforce/messageChannel/ProductSelected__c';

export default class ProductDetail extends LightningElement {
    @wire(MessageContext)
    messageContext;

    subscription = null;

    connectedCallback() {
        this.subscription = subscribe(
            this.messageContext,
            PRODUCT_SELECTED_CHANNEL,
            (message) => this.handleMessage(message),
            { scope: APPLICATION_SCOPE }
        );
    }

    disconnectedCallback() {
        unsubscribe(this.subscription);
        this.subscription = null;
    }

    handleMessage(message) {
        // message.productId and message.productName are available
        this.selectedProductId = message.productId;
    }
}
```

### Scope: APPLICATION_SCOPE vs Default

By default, LMS only delivers messages to subscribers in the **currently active navigation tab or item**. Utility bar items are always active. If a subscriber component lives in a tab that the user has not yet visited or has navigated away from, it will not receive the message unless `APPLICATION_SCOPE` is specified. Use `APPLICATION_SCOPE` when:

- The subscriber is in a workspace tab that might not be the active tab.
- The publisher and subscriber could be on different console navigation items at the same time.
- You want to ensure all live component instances receive the message regardless of visibility.

Do not use `APPLICATION_SCOPE` as a blanket default — it increases coupling and can trigger stale subscriber logic in components that are technically rendered but not visible.

---

## Common Patterns

### Pattern 1: Master-Detail Page Coordination

**When to use:** A list (master) component and a detail panel (detail) component live in separate regions of a Lightning App page and share no common ancestor in the LWC hierarchy.

**How it works:**
1. Create `RecordSelected__c` message channel with a `recordId` field.
2. The master component publishes on row click.
3. The detail component subscribes with `APPLICATION_SCOPE` if either component could be in a non-active tab; otherwise use the default scope for active-tab-only delivery.
4. The detail component unsubscribes in `disconnectedCallback`.

**Why not the alternative:** A Pub/Sub utility helper (legacy pattern) is not supported, not type-safe, and has no lifecycle guarantees. Custom events cannot cross the DOM boundary between independent page regions.

### Pattern 2: Visualforce-to-LWC Bridge

**When to use:** A Visualforce page is embedded in a Lightning page alongside LWC components, and the VF page must notify LWC components of user actions.

**How it works:**
1. Create the message channel and deploy it to the org.
2. In the Visualforce page, use the `sforce.one` LMS API to publish:
   ```javascript
   // Inside Visualforce page JavaScript
   sforce.one.publish('MyChannel__c', { action: 'refresh', context: 'vf' });
   ```
3. LWC subscriber uses `subscribe()` with `APPLICATION_SCOPE` — the VF page is inside an iframe and scope must be `APPLICATION` for messages to cross the iframe boundary.
4. Note that `sforce.one.subscribe()` / `sforce.one.unsubscribe()` is the only supported Visualforce-side API for LMS; standard `publish` from `lightning/messageService` cannot be imported in VF pages.

**Why not the alternative:** Postmessage hacks across iframe boundaries bypass Salesforce's security model and are unsupported.

### Pattern 3: Cross-Namespace Channel Consumption

**When to use:** A managed package defines a channel marked `isExposed: true` and a subscriber org component must subscribe to it.

**How it works:** Import the channel using the namespace prefix:
```javascript
import PACKAGE_CHANNEL from '@salesforce/messageChannel/myNamespace__SomeChannel__c';
```
The double underscore is intentional — namespace separator plus the custom `__c` suffix both appear. Subscribers in the managed package or subscriber orgs can publish and subscribe freely as long as `isExposed` is `true` on the channel definition. AppExchange security review requires `isExposed: false` unless cross-namespace use is intentional and documented.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Parent passes data to child | `@api` property | Direct, declarative, no infrastructure needed |
| Child notifies parent of intent | Custom event | Propagates up the ownership tree cleanly |
| Unrelated components on same page | Lightning Message Service | Designed for cross-hierarchy pub/sub on a single page |
| Components in separate workspace tabs | LMS + APPLICATION_SCOPE | Default scope only fires for the active tab |
| Visualforce embedded in Lightning page | LMS via `sforce.one` on VF side | Only supported cross-iframe LMS API |
| Cross-namespace package channel | LMS with namespace prefix import | Channel must have `isExposed: true` |
| Components in separate browser tabs | Not possible with LMS | LMS is single-page; use server polling or Streaming API |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Message channel XML is deployed to the org before dependent components are deployed.
- [ ] Publisher wires `MessageContext` via `@wire(MessageContext)` before calling `publish()`.
- [ ] Subscriber calls `subscribe()` in `connectedCallback`, not in the constructor.
- [ ] Subscriber stores the handle returned by `subscribe()` and calls `unsubscribe(handle)` in `disconnectedCallback`.
- [ ] Scope is explicitly chosen: `APPLICATION_SCOPE` for cross-tab delivery, default for active-tab-only.
- [ ] Payload is a plain serializable JSON object — no functions, no class instances, no symbols.
- [ ] Cross-namespace channel references use the full `namespace__ChannelName__c` import path.
- [ ] `lightning:messageChannel` in Aura is an immediate child of `aura:component`, not nested inside another component or HTML element.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Messages are constrained by iframe boundaries** — LMS messages published inside a Visualforce page embedded via iframe do not reach LWC subscribers on the same Lightning page unless the Visualforce page uses `sforce.one.publish()` and subscribers use `APPLICATION_SCOPE`. Using the standard `publish()` import from `lightning/messageService` inside a VF page is not supported.
2. **Cached-but-not-destroyed components keep receiving messages** — When navigating away from a Lightning page, Salesforce may cache the component tree without destroying it. Components in this state still receive LMS messages if their subscription was not cleaned up. Always unsubscribe in `disconnectedCallback`, and test behavior after navigation rather than only on first load.
3. **Channel must be deployed before importing components** — There is no late-binding for message channel imports. If `ProductSelected__c` does not exist in the org, any component with `import ... from '@salesforce/messageChannel/ProductSelected__c'` will fail to load entirely, blocking the whole page region, not just the message feature.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `messageChannels/ChannelName.messageChannel-meta.xml` | Deployable channel metadata with field declarations |
| Publisher LWC | Component with `@wire(MessageContext)` and `publish()` call |
| Subscriber LWC | Component with `connectedCallback` subscription and `disconnectedCallback` cleanup |
| Scope decision | `APPLICATION_SCOPE` recommendation with rationale for the specific use case |
| Review findings | Notes on missing unsubscribe, wrong scope, iframe boundary, or deployment order issues |

---

## Related Skills

- `lwc/component-communication` — use when components share a direct ownership chain; prefer `@api` or custom events before reaching for LMS.
- `lwc/lifecycle-hooks` — use when LMS subscription or cleanup bugs are really timing issues related to `connectedCallback` / `disconnectedCallback` execution order.
