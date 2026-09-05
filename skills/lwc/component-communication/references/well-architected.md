# Well-Architected Notes - Component Communication

## Relevant Pillars

### Reliability

Clear communication contracts reduce accidental coupling and make rerender, propagation, and state ownership easier to reason about.

### Scalability

As component trees and workspaces grow, communication patterns that were acceptable in a two-component demo become expensive to maintain. LMS and public APIs need disciplined scope.

### User Experience

Poor communication design shows up as stale state, missed events, and UI actions that appear random to users. Good contracts produce predictable interactions.

## Architectural Tradeoffs

- **Declarative state vs imperative commands:** `@api` properties are easier to scale, but some workflows genuinely need narrow public methods.
- **Local events vs LMS:** Custom events are simpler and cheaper when ownership is local; LMS is justified only when the scope is truly cross-hierarchy.
- **Small payloads vs rich shared objects:** Rich objects are tempting, but they blur ownership and create mutation bugs.

## Anti-Patterns

1. **Global or legacy pubsub for simple local communication** - a wide mechanism hides what should be a simple parent-child contract.
2. **Parent reaching into child internals** - DOM coupling bypasses the public API and breaks encapsulation.
3. **Overusing LMS as a default bus** - messaging becomes harder to trace than the page hierarchy itself.

## Official Sources Used

- Configure Event Propagation — https://developer.salesforce.com/docs/platform/lwc/guide/events-propagation.html (`bubbles` and `composed` both default to `false`; the `true/true` configuration makes the event type part of every ancestor's public API and can collide at the document root)
- Events Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/events-best-practices.html (send primitives in `detail`, or a copy; never a non-primitive that arrived from `@api` or `@wire`)
- Create and Dispatch Events — https://developer.salesforce.com/docs/platform/lwc/guide/events-create-dispatch.html (event naming: no uppercase, no spaces, underscores to separate words, never an `on` prefix)
- Data Flow — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-data-flow.html (one-way data flow; only the owner sets an `@api` value after initialisation; prefer primitives over object-shaped public properties)
- Set Properties on Children — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-data-binding.html (non-primitives passed to a child are read-only proxies and mutating one raises `Invalid mutation … is read-only`)
- Call Methods on Children — https://developer.salesforce.com/docs/platform/lwc/guide/create-javascript-methods.html (`@api` methods as the imperative surface; `this.template.querySelector` and why `id` selectors do not work)
- Boolean Properties — https://developer.salesforce.com/docs/platform/lwc/guide/js-props-boolean.html (a public boolean must default to `false`; `show="false"` in markup evaluates to true)
- Getters and Setters — https://developer.salesforce.com/docs/platform/lwc/guide/js-props-getters-setters.html (annotate the getter or the setter with `@api`, not both)
- Reactivity for Fields, Objects, and Arrays — https://developer.salesforce.com/docs/platform/lwc/guide/reactivity-fields.html (primitives are already reactive; `@track` adds deep observation only for plain objects and arrays)
- Define the Scope of the Message Service — https://developer.salesforce.com/docs/platform/lwc/guide/use-message-channel-scope.html (active area is the default; utility items are always active; scoping requires `@wire(MessageContext)`)
- Subscribe and Unsubscribe from a Message Channel — https://developer.salesforce.com/docs/platform/lwc/guide/use-message-channel-subscribe.html (the `subscribe`/`unsubscribe` lifecycle pattern this skill's code examples follow, and `createMessageContext`/`releaseMessageContext` for API modules)
- Publish on a Message Channel — https://developer.salesforce.com/docs/platform/lwc/guide/use-message-channel-publish.html (delivery continues until the destroy phase, and cached pages are not destroyed; `@wire(MessageContext)` is unusable in `constructor()`)
- Message Service Limitations — https://developer.salesforce.com/docs/platform/lwc/guide/use-message-channel-considerations.html (supported containers; the iframe boundary; no support in Salesforce Tabs + Visualforce sites)
- Communicate Across the DOM — https://developer.salesforce.com/docs/platform/lwc/guide/events-pubsub.html (LMS is the supported cross-DOM mechanism; the `pubsub` module is no longer officially supported or actively maintained)
- Metadata API Developer Guide, `LightningMessageChannel` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`masterLabel`, `isExposed`, `lightningMessageFields`/`fieldName`; `isExposed: true` cannot be reversed; AppExchange Security Review requires `false`)
- Metadata API Developer Guide, `LightningComponentBundle` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`apiVersion`, `isExposed`, `targets`, `targetConfigs`/`objects` in the `js-meta.xml`)
- XML Configuration File Elements — https://developer.salesforce.com/docs/platform/lwc/guide/reference-configuration-tags.html (every component must specify an API version from Spring '25; `isExposed: true` needs at least one `<target>` to appear in the builders)
- Jest Test Patterns — https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest-patterns.html (the `moduleNameMapper` entry for `lightning/messageService`; rerender assertions belong inside `Promise.resolve().then(…)`)
