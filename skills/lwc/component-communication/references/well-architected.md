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

- Set Properties on Child Components - https://developer.salesforce.com/docs/platform/lwc/guide/create-components-data-binding.html
- Create and Dispatch Events - https://developer.salesforce.com/docs/platform/lwc/guide/events-create-dispatch.html
- Lightning Message Service - https://developer.salesforce.com/docs/platform/lwc/guide/lwc-message-channel.html
