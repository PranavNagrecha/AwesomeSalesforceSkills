---
name: flow-and-platform-events
description: "Publish and subscribe to Platform Events from Flow for async decoupling, high-volume triggers, and cross-org signaling. NOT for regular DML-triggered flows."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
triggers:
  - "flow publish platform event"
  - "platform event triggered flow"
  - "async flow notification"
  - "flow publish high volume event"
tags:
  - platform-events
  - flow
  - async
inputs:
  - "use case (decouple / fan-out / cross-org)"
  - "event payload"
outputs:
  - "PE definition + publish flow + subscribe flow"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Flow and Platform Events

Platform Events are the canonical async bus for Salesforce. Flow supports both publish (Create Records on the PE SObject) and subscribe (Platform Event-Triggered Flow). This skill covers high-volume PE vs standard-volume, replay, and the failure modes when a PE-triggered flow errors.

## Adoption Signals

Decouple producer from consumer (reduce transaction size), fan-out to N subscribers, or cross-org signaling.

- Publish from Flow when a downstream system needs notification but should not delay the user transaction — `Create Records` on the Platform Event object is the publish primitive.
- Subscribe via record-triggered Flow when an external publisher signals an event the org must react to asynchronously.

## Recommended Workflow

1. Define the PE with stable fields; prefer text fields for interoperability.
2. Publish: Create Records on the PE SObject in any flow (record-triggered, screen, scheduled).
3. Subscribe: Platform Event-Triggered Flow; select the PE; build actions.
4. Error handling: subscribed flows retry on failure with a visible 'Failed' status — instrument.
5. For high-volume PEs (>250k/day), choose High-Volume type; Monitor Setup → Platform Event Usage.

## Key Considerations

- PE-triggered flows run asynchronously — no rollback of the publishing transaction on subscriber failure.
- Retention: 72h for Standard, 72h for High-Volume (both).
- PE subscriber flows share daily limits with other subscribers.
- Replay via replay ID requires CometD/Pub-Sub client, not Flow.

## Worked Examples (see `references/examples.md`)

- *Decouple Opp → Billing* — Opportunity closed
- *Fan-out notification* — Case escalation

## Common Gotchas (see `references/gotchas.md`)

- **Assumed transactional** — Consumer failure rolls back producer — it doesn't.
- **Subscriber error silent** — Retries exhaust; no alert.
- **PE allocation exceeded** — Publish fails with LIMIT_EXCEEDED.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Treating PE as transactional
- One PE for too many different events
- Missing idempotency on subscribers

## Official Sources Used

- Flow Builder Guide — https://help.salesforce.com/s/articleView?id=sf.flow.htm
- Flow Best Practices — https://help.salesforce.com/s/articleView?id=sf.flow_best_practices.htm
- Reactive Screens — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen_reactive.htm
- Flow HTTP Callout Action — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_callout.htm
