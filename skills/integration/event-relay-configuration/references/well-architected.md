# Well-Architected Notes — Event Relay

## Relevant Pillars

- **Security** — IAM trust and external id design is the main Security
  decision.
- **Reliability** — at-least-once + 72h retention shape the replay story.
- **Operational Excellence** — managed service reduces ops burden vs DIY
  Apex callouts.

## Architectural Tradeoffs

- **Event Relay vs Apex callout:** relay is reliable and no-code; callouts
  give arbitrary payload shaping but carry operational debt.
- **High-Volume vs standard PE:** high-volume costs more but is the
  correct storage for relay.
- **Filter upstream vs downstream:** upstream reduces cost; downstream
  enables richer logic.
- **CDC vs domain PE:** CDC is automatic but payloads are deltas; domain
  PEs are explicit but require publishing code.

## Official Sources Used

- Event Relay — https://help.salesforce.com/s/articleView?id=sf.event_relay.htm
- Pub/Sub API — https://developer.salesforce.com/docs/platform/pub-sub-api/overview
- AWS EventBridge — https://docs.aws.amazon.com/eventbridge/
- integration-pattern-selection — `standards/decision-trees/integration-pattern-selection.md`
