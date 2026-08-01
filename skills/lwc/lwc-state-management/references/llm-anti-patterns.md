# LLM Anti-Patterns — LWC State Management

Scope: sharing state **between** components that are not in a parent-child relationship.
In-component reactivity (`@track`, reassignment semantics, getters) belongs to
`lwc/lwc-reactive-state-patterns`. The mechanics of Lightning Message Service — channel
definition, scope, context — belong to `lwc/message-channel-patterns`. Parent-child
plumbing belongs to `lwc/component-communication`. This file is about picking the right
one and the failures that follow from picking wrong.

## Anti-Pattern 1: Reaching for a global store when the components are related

The React habit. Asked "these two components need the same value", assistants produce a
module-level singleton and subscribe both components to it — even when one is the other's
parent. That replaces a declarative, framework-managed binding with hand-rolled
subscription plumbing that has to be torn down manually and cannot be seen in the markup.

❌ A shared store for a parent and its own child.
✅ Walk the distance first, and only then choose:

| Relationship | Mechanism |
| --- | --- |
| Parent to child | A public `@api` property |
| Child to parent | A `CustomEvent` the parent listens for |
| Ancestor to distant descendant | `@api` down, or a message channel if the chain is long enough to be absurd |
| Siblings, or across an Aura boundary | Lightning Message Service |
| Server-owned data any component needs | A wire adapter, which already caches and shares |

The mechanism follows from the relationship. Reversing that — choosing a mechanism and
then arranging components to suit — is what produces components that cannot be reused.

## Anti-Pattern 2: Generating the legacy pubsub module

There is a widely copied `pubsub.js` from an older sample application, and assistants
reproduce it from memory because it appears in so much training material. It predates
Lightning Message Service, it is confined to a single page and cannot cross into Aura, and
it is not a platform module — you own every bug in it.

❌ `import { fireEvent, registerListener } from 'c/pubsub';`
✅ `lightning/messageService`, which is a platform module with defined scope semantics and
works across Aura and Visualforce boundaries. Treat any generated code importing `c/pubsub`
as a sign the model is reciting a pre-LMS sample rather than answering the question.

## Anti-Pattern 3: Subscribing without unsubscribing

Assistants write the `connectedCallback` subscription and stop, because that is the half
that makes the feature work. Without the matching teardown the subscription survives the
component, so navigating between records accumulates handlers that fire against destroyed
components — which surfaces as duplicated work and console errors that point at the wrong
component entirely.

**Wrong** — subscribes on every connect, never releases:

```javascript
import { LightningElement, wire } from 'lwc';
import { subscribe, MessageContext } from 'lightning/messageService';
import RECORD_SELECTED from '@salesforce/messageChannel/RecordSelected__c';

export default class ContactList extends LightningElement {
    @wire(MessageContext) messageContext;

    connectedCallback() {
        subscribe(this.messageContext, RECORD_SELECTED, (msg) => this.handle(msg));
    }
}
```

**Right** — retain the token and release it symmetrically:

```javascript
import { LightningElement, wire } from 'lwc';
import { subscribe, unsubscribe, MessageContext, APPLICATION_SCOPE }
    from 'lightning/messageService';
import RECORD_SELECTED from '@salesforce/messageChannel/RecordSelected__c';

export default class ContactList extends LightningElement {
    @wire(MessageContext) messageContext;
    subscription = null;

    connectedCallback() {
        if (this.subscription) return;          // connectedCallback can fire more than once
        this.subscription = subscribe(
            this.messageContext,
            RECORD_SELECTED,
            (msg) => this.handle(msg),
            { scope: APPLICATION_SCOPE }
        );
    }

    disconnectedCallback() {
        unsubscribe(this.subscription);
        this.subscription = null;
    }
}
```

The `if (this.subscription) return;` guard matters: `connectedCallback` is not guaranteed
to run only once for a component instance, and a second subscription to the same channel
means every message is handled twice.

Source: lightning/messageService module —
https://developer.salesforce.com/docs/platform/lwc/guide/use-message-channel.html

## Anti-Pattern 4: Forgetting that the message channel is deployable metadata

The most confusing failure in this area, because nothing errors. The channel is a
`.messageChannel-meta.xml` file. If it was created locally and never deployed, publish
succeeds, subscribe succeeds, and no message is ever delivered. Assistants generate the
JavaScript and omit the metadata because the import statement looks like a library import.

❌ Import `@salesforce/messageChannel/RecordSelected__c` and assume it exists.
✅ Create and deploy the channel alongside the components:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Record Selected</masterLabel>
    <isExposed>true</isExposed>
    <description>Broadcasts the currently selected record across sibling components.</description>
    <lightningMessageFields>
        <fieldName>recordId</fieldName>
        <description>Id of the selected record</description>
    </lightningMessageFields>
    <lightningMessageFields>
        <fieldName>objectApiName</fieldName>
        <description>API name of the selected record's object</description>
    </lightningMessageFields>
</LightningMessageChannel>
```

`isExposed` must be true for components in other namespaces to use it. When a message
never arrives, check deployment before debugging anything else.

## Anti-Pattern 5: Assuming a message channel works everywhere

Message Service is not available in every container, and assistants recommend it
uniformly. A component that works on a record page and silently does nothing in another
context is the result, and it is diagnosed as a component bug rather than a container
constraint.

❌ Design the whole feature around a channel without checking where it will run.
✅ Check the supported-containers list against the surfaces this component targets before
committing to the design. Where the channel is unavailable, the fallback is ordinary
parent-child plumbing through a wrapper, which works everywhere.

## Anti-Pattern 6: Ignoring the publish-before-subscribe race

Nothing retains the last message. A component that renders after the publish never sees
it, so the defect is timing-dependent — it reproduces on a slow connection and not on the
developer's machine, which is the worst possible signature.

❌ Publish current selection once, on the publisher's `connectedCallback`.
✅ Either keep the current value in something with state that a late subscriber can read
on connect, or have late-joining components ask for the current value explicitly. Design
for "I arrived late" as the normal case, not the exception, because component order is not
something you control.

## Anti-Pattern 7: Building a store for data the server already owns

Asked to "share the account record across components", assistants build a store that
fetches once and distributes. Lightning Data Service already does this — it caches, shares
across components, and updates them when the record changes. A hand-rolled store gives up
all of that and introduces a second source of truth that goes stale silently.

❌ A module-level cache of record data with manual invalidation.
✅ Wire adapters for server-owned data, and reserve any hand-rolled store for genuinely
client-only state — a selected filter, a collapsed panel, an in-progress wizard step. Keep
it small and export a subscribe function with a matching unsubscribe, because the teardown
problem from anti-pattern 3 applies just as much to your own store.
