# Gotchas — LWC Pub/Sub Patterns

Real-world surprises in LWC sibling communication.

---

## Gotcha 1: Forgotten `unsubscribe` in `disconnectedCallback` leaks subscriptions

**What happens.** Subscriber component subscribes in
`connectedCallback`. User navigates away. Component is removed but
subscription persists. On next page visit a new instance subscribes;
two handlers now run for each message.

**When it occurs.** Code reviews that miss the unsubscribe step.

**How to avoid.** Make `disconnectedCallback` with `unsubscribe`
mandatory in code review. Test with a navigation away and back; if
handlers double-fire, the unsubscribe is missing.

---

## Gotcha 2: LMS does not cross browser tabs

**What happens.** Engineer expects a publish in tab A to reach a
subscriber in tab B (same user, same session, same org). It does
not — LMS scope is the Lightning Experience instance in a single
tab.

**When it occurs.** Multi-tab workflows.

**How to avoid.** Use Platform Events for cross-tab. Or share state
via the Salesforce backend (a polled custom object).

---

## Gotcha 3: Default scope (`ACTIVE`) misses utility-bar subscribers

**What happens.** Page-level component publishes with default
scope; utility-bar component does not receive. Or vice versa.

**When it occurs.** Utility-bar / page-level mix without
`APPLICATION_SCOPE`.

**How to avoid.** Use `APPLICATION_SCOPE` whenever the publisher
and subscriber may live in different navigation contexts.

---

## Gotcha 4: `@wire(MessageContext)` returns `undefined` on first render

**What happens.** Code calls `subscribe(this.messageContext, ...)`
synchronously in `connectedCallback`; `messageContext` is still
undefined the first time. Subscribe call fails or no-ops.

**When it occurs.** Race in the wire-resolution timing.

**How to avoid.** Either subscribe in `renderedCallback` (which
fires after wires resolve) with a guard against re-subscribing, or
ensure the subscribe path tolerates an undefined context and
re-runs once context arrives.

---

## Gotcha 5: Message Channel deployment is metadata; channel must exist on both sides

**What happens.** Publisher works in dev sandbox; deploy to QA;
subscriber gets nothing. Cause: the `MessageChannel-meta.xml` was
not part of the deploy package.

**When it occurs.** Custom channels left out of `package.xml`.

**How to avoid.** Include `messageChannels` in the deploy manifest.
Some teams treat channels as a separate metadata directory;
confirm CI pipeline picks them up.

---

## Gotcha 6: Field names in messages are not validated against the channel

**What happens.** Publisher sends `{ recordId: '0010K00001ABC' }`;
subscriber expects `{ id: '0010K00001ABC' }`. The runtime delivers
the message; subscriber reads `msg.id` and gets undefined. No error.

**When it occurs.** Channel field names not standardized between
publisher and subscriber.

**How to avoid.** Treat the Message Channel definition as the
contract. Use the field names from the channel verbatim. Code
review enforces the convention.

---

## Gotcha 7: Aura subscribers require a different API

**What happens.** Aura component cannot import
`@salesforce/messageChannel/...` the same way LWC can; the API
shape is similar but distinct.

**When it occurs.** Mixed Aura + LWC pages on a long-lived org.

**How to avoid.** Use the LMS Aura API (`lightning:messageChannel`
component or programmatic API) on the Aura side. The channel
metadata is shared; the consumer code differs.

---

## Gotcha 8: Subscribing inside a loop in `connectedCallback`

**What happens.** Component subscribes repeatedly because
`connectedCallback` fires on every reconnection. Each
re-attachment adds a new subscription on top of the old one.

**When it occurs.** Components that are detached / re-attached as
the user toggles UI state. `connectedCallback` is not "called once
per lifetime"; it is called every time the component is attached
to the DOM.

**How to avoid.** Guard subscription creation: only subscribe if
`this.subscription` is currently null. In `disconnectedCallback`,
unsubscribe and set to null.

---

## Gotcha 9: Message payloads are JSON-serialized

**What happens.** Engineer publishes a message containing a
function or a class instance. Subscriber receives a stripped-down
version (functions removed, prototypes flattened).

**When it occurs.** Treating LMS as in-memory function-call
mechanism.

**How to avoid.** Treat LMS messages as JSON-serializable
data only. For richer interaction, use direct method calls (when
parent-child) or Apex-mediated state.
