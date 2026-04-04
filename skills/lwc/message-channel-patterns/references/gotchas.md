# Gotchas — Message Channel Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Missing Unsubscribe Causes Stale Message Handlers on Cached Components

**What happens:** A component that has been navigated away from continues to receive and process LMS messages. Handlers fire on a component that is no longer visible, mutating `@track` state or triggering `@wire` refreshes on data that the user cannot see. In console apps this can trigger multiple simultaneous data loads or cause the visible component to flicker when the user navigates back.

**When it occurs:** Lightning Experience may cache component trees on navigation rather than destroying them, especially in console navigation with multiple workspace tabs. The platform documentation explicitly states that "sometimes when you navigate away from a Lightning page, components are cached and not destroyed. These components still receive messages." Any subscription created in `connectedCallback` that is not cleaned up in `disconnectedCallback` will survive this navigation cycle.

**How to avoid:** Always store the subscription handle returned by `subscribe()` and call `unsubscribe(this.subscription)` in `disconnectedCallback`. Set the property to `null` after unsubscribing to prevent double-unsubscribe bugs on re-mount:

```javascript
disconnectedCallback() {
    unsubscribe(this.subscription);
    this.subscription = null;
}
```

---

## Gotcha 2: APPLICATION_SCOPE Is Required for Cross-iframe and Inactive-Tab Subscribers

**What happens:** A subscriber component silently receives zero messages. There are no console errors and no warnings. The developer confirms the channel is deployed, the imports are correct, and the publisher is firing — but the subscriber handler never runs.

**When it occurs:** This occurs in two common situations: (1) The publisher is inside a Visualforce page embedded via iframe, and the subscriber uses the default scope. (2) The subscriber is in a workspace tab that the user has not currently selected, and default scope only delivers to active navigation areas. Both cases look identical from the subscriber's perspective: the subscription object exists, no errors are thrown, but no messages arrive.

**How to avoid:** Import `APPLICATION_SCOPE` from `lightning/messageService` and pass it as the scope option:

```javascript
import { subscribe, APPLICATION_SCOPE } from 'lightning/messageService';

this.subscription = subscribe(
    this.messageContext,
    MY_CHANNEL,
    this.handleMessage.bind(this),
    { scope: APPLICATION_SCOPE }
);
```

Use `APPLICATION_SCOPE` whenever: the subscriber might be in an inactive tab, the publisher is in a Visualforce iframe, or either component lives in the utility bar alongside navigation tabs. Do not apply `APPLICATION_SCOPE` universally — it delivers to all live subscribers regardless of active state, which can cause unexpected double-handling if multiple page instances are open.

---

## Gotcha 3: Message Channel Must Be Deployed Before Dependent Components

**What happens:** An LWC component that imports a message channel fails to load entirely at runtime — it does not partially render or fail gracefully. The entire component region on the page goes blank, and the browser console shows a module resolution error for the `@salesforce/messageChannel/ChannelName__c` import.

**When it occurs:** During deployment in a new sandbox, scratch org setup, or CI pipeline where metadata deployment order is not enforced. Message channels are Metadata API types deployed like custom objects. A component that references `@salesforce/messageChannel/OrderUpdated__c` will fail if `OrderUpdated__c` has not yet been deployed to that org. This also affects package upgrades where a new channel is introduced — subscriber components must be deployed after the channel is installed or deployed.

**How to avoid:** Ensure `messageChannels/` metadata is deployed before `lwc/` metadata that references those channels. In Salesforce DX projects, use `force-app/main/default/messageChannels/` as a dedicated directory and deploy it as a first pass. In package upgrades, deploy or install the channel package version before deploying component updates. Validate deployment order in CI by running the channel deploy step as a separate pipeline stage before the component deploy step.

---

## Gotcha 4: lightning:messageChannel Must Be a Direct Child of aura:component

**What happens:** An Aura component that wraps `lightning:messageChannel` inside a `lightning:card`, `lightning:layout`, or any other child component or HTML element throws a runtime error when the Aura component renders. The error is not caught at compile time — it only surfaces at runtime, often in production after passing basic testing.

**When it occurs:** Developers nesting the channel declaration for visual organization inside a container component. The Aura renderer enforces that `lightning:messageChannel` must be an immediate child of `aura:component`. Nesting it inside any other element or component breaks this constraint.

**How to avoid:** Always declare `lightning:messageChannel` as an immediate child of the root `aura:component` tag. Keep it at the top of the component markup alongside other `aura:attribute` and `aura:handler` declarations:

```html
<!-- Correct -->
<aura:component>
    <lightning:messageChannel type="MyChannel__c" aura:id="myChannel"/>
    <lightning:card>...</lightning:card>
</aura:component>

<!-- Wrong — throws runtime error -->
<aura:component>
    <lightning:card>
        <lightning:messageChannel type="MyChannel__c" aura:id="myChannel"/>
    </lightning:card>
</aura:component>
```
