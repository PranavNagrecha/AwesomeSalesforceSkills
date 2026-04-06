# LLM Anti-Patterns — Message Channel Patterns

Common mistakes AI coding assistants make when generating or advising on Lightning Message Service and message channels.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not unsubscribing in disconnectedCallback

**What the LLM generates:**

```javascript
import { subscribe, MessageContext } from 'lightning/messageService';
import MY_CHANNEL from '@salesforce/messageChannel/MyChannel__c';

@wire(MessageContext) messageContext;

connectedCallback() {
    this.subscription = subscribe(this.messageContext, MY_CHANNEL, (message) => {
        this.handleMessage(message);
    });
}
// No disconnectedCallback — subscription leaks when component is destroyed
```

**Why it happens:** Training examples often show only the subscribe side. The unsubscribe cleanup is in a separate section or omitted from abbreviated snippets.

**Correct pattern:**

```javascript
import { subscribe, unsubscribe, MessageContext } from 'lightning/messageService';

connectedCallback() {
    if (!this.subscription) {
        this.subscription = subscribe(this.messageContext, MY_CHANNEL, (message) => {
            this.handleMessage(message);
        });
    }
}

disconnectedCallback() {
    unsubscribe(this.subscription);
    this.subscription = null;
}
```

**Detection hint:** File that imports `subscribe` from `lightning/messageService` but does not import or call `unsubscribe`.

---

## Anti-Pattern 2: Using APPLICATION_SCOPE by default

**What the LLM generates:**

```javascript
import { APPLICATION_SCOPE } from 'lightning/messageService';

this.subscription = subscribe(
    this.messageContext, MY_CHANNEL, this.handler,
    { scope: APPLICATION_SCOPE }
);
```

**Why it happens:** LLMs add `APPLICATION_SCOPE` as a "just works" approach because it makes messages arrive regardless of workspace tab context. Default scope (same page area) is correct for the vast majority of use cases.

**Correct pattern:**

```javascript
// Default scope — receives messages only from the active page area
this.subscription = subscribe(this.messageContext, MY_CHANNEL, this.handler);
```

Only add `APPLICATION_SCOPE` when the publisher and subscriber genuinely live in different workspace tabs, utility bars, or console app panels.

**Detection hint:** `APPLICATION_SCOPE` without a code comment explaining the cross-tab or utility-bar need.

---

## Anti-Pattern 3: Publishing with too many fields or treating LMS as a data bus

**What the LLM generates:**

```javascript
publish(this.messageContext, MY_CHANNEL, {
    recordId: this.recordId,
    recordName: this.name,
    recordPhone: this.phone,
    recordEmail: this.email,
    recordAddress: this.address,
    accountOwner: this.owner,
    relatedContacts: JSON.stringify(this.contacts)
});
```

**Why it happens:** LLMs try to be helpful by sending all available data in the message. LMS is designed for lightweight coordination signals, not bulk data transfer.

**Correct pattern:**

```javascript
// Send only the identifier — let subscribers fetch their own data
publish(this.messageContext, MY_CHANNEL, {
    recordId: this.recordId
});
```

Subscribers should use wire adapters or imperative calls to load the data they need.

**Detection hint:** `publish(` call with more than 3 fields in the payload, or fields containing serialized JSON objects.

---

## Anti-Pattern 4: Generating the message channel metadata XML with wrong structure

**What the LLM generates:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>My Channel</masterLabel>
    <fields>
        <fieldName>recordId</fieldName>
        <type>String</type>
    </fields>
</LightningMessageChannel>
```

**Why it happens:** LLMs hallucinate a `type` attribute on field definitions. The actual metadata format does not include a `type` element — fields are untyped in the XML and typed by convention in the publisher.

**Correct pattern:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>My Channel</masterLabel>
    <isExposed>true</isExposed>
    <description>Communicates record selection between page components.</description>
    <lightningMessageFields>
        <fieldName>recordId</fieldName>
        <description>The Id of the selected record</description>
    </lightningMessageFields>
</LightningMessageChannel>
```

**Detection hint:** `<type>` element inside a `<lightningMessageFields>` block, or using `<fields>` instead of `<lightningMessageFields>`.

---

## Anti-Pattern 5: Using LMS for parent-child communication

**What the LLM generates:**

```javascript
// Parent component publishes to LMS
publish(this.messageContext, CHANNEL, { filter: this.filter });

// Child component subscribes to the same channel
subscribe(this.messageContext, CHANNEL, (msg) => {
    this.filter = msg.filter;
});
```

**Why it happens:** LLMs treat LMS as the universal communication mechanism. For parent-child relationships, `@api` properties (parent to child) and custom events (child to parent) are simpler and more performant.

**Correct pattern:**

```html
<!-- Parent: pass data down via @api -->
<c-child-filter filter-value={filter}></c-child-filter>
```

LMS should only be used for components that are unrelated in the DOM hierarchy.

**Detection hint:** LMS publish and subscribe in components where the subscriber is a direct child in the publisher's template.

---

## Anti-Pattern 6: Missing isExposed flag for cross-namespace or Visualforce interop

**What the LLM generates:**

```xml
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>My Channel</masterLabel>
    <!-- isExposed not set — defaults to false -->
</LightningMessageChannel>
```

**Why it happens:** LLMs omit `isExposed` because it defaults to `false` and the channel works fine within the same namespace. But if Visualforce pages or managed packages need to access the channel, `isExposed` must be `true`.

**Correct pattern:**

```xml
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>My Channel</masterLabel>
    <isExposed>true</isExposed>
    <description>Cross-technology coordination channel</description>
</LightningMessageChannel>
```

**Detection hint:** Message channel intended for Visualforce or cross-namespace use but missing `<isExposed>true</isExposed>`.
