# Well-Architected Notes — Event-Driven Architecture Patterns

## Relevant Pillars

- **Reliability** — The primary pillar for this skill. The choice between Platform Events (72h retention, at-least-once), CDC (72h retention, gap events on overflow), Streaming API (24h retention, no gap events), and Outbound Messages (SOAP retry, no replay) has direct, measurable impact on whether integration events survive subscriber outages, bulk operations, and retry scenarios. Selecting the wrong mechanism for a given retention or throughput requirement produces silent data loss that only surfaces during incidents.
- **Operational Excellence** — Event mechanism selection determines the operational surface area of the integration. CDC with automatic field-delta tracking requires less maintenance than Platform Events with manually managed event schemas. PushTopic subscriptions require monitoring for the 24-hour retention cliff. The decision matrix should be evaluated for long-term maintainability, not just initial implementation ease.
- **Scalability** — Throughput limits differ significantly across mechanisms. Standard Platform Events support 250,000 events/day on Enterprise+; PushTopic supports approximately 50,000 events/day org-wide. Choosing PushTopic for a high-volume sync without validating throughput requirements against the allocation is a scalability anti-pattern that will not manifest in sandbox but will shed events in production.

## Architectural Tradeoffs

**Platform Events vs CDC for record-change streams:** Platform Events require a publisher (Apex trigger, Flow action, or REST call) that explicitly fires the event. CDC fires automatically on DML. The tradeoff is control vs. automation: Platform Events give the publisher full control over event timing, payload shape, and filtering, but introduce a publisher layer that can fail, be mis-configured, or be missed when new fields are added. CDC requires no publisher but is constrained to the automatic change-event schema — custom business context cannot be added to the payload.

**Streaming API (PushTopic) vs CDC for external sync:** Both deliver record-change events to external CometD or Pub/Sub subscribers. PushTopic limits the payload to the SOQL SELECT list and retains for 24 hours. CDC includes automatic field-delta tracking and retains for 72 hours. PushTopic has a 50k/day throughput ceiling; CDC operates at the Event Bus allocation level. For any new external record-sync integration, CDC is the superior choice. The only justification for PushTopic is maintaining a legacy integration that already uses it.

**Platform Events vs Outbound Messages for workflow notifications:** Outbound Messages are SOAP-only and Workflow-triggered. They provide at-least-once delivery with acknowledgment-based retry, but have no replay capability and depend on the legacy Workflow Rule framework. Platform Events are protocol-agnostic, support JSON payload via CometD or Pub/Sub, have 72-hour replay, and work with current automation (Flow, Apex). The migration path from Outbound Messages is: replace Workflow Rule with Flow → publish Platform Event in Flow → external subscriber handles delivery. This migration is the recommended long-term direction for any org that currently uses Outbound Messages.

## Anti-Patterns

1. **Using PushTopic for production integrations with >24-hour outage risk** — Streaming API's 24-hour retention makes it inappropriate for any external integration where the subscriber can be offline for more than 24 hours (weekend maintenance, deployment windows, incident recovery). Teams that deploy PushTopic-based integrations without a compensating reconciliation mechanism will experience silent data loss on the first extended outage. The correct pattern is CDC or Platform Events with 72-hour retention and an explicit gap-recovery procedure.

2. **Building a custom CDC simulation on top of Platform Events** — Some teams build Apex triggers on every object that publish Platform Events containing field-delta information, attempting to replicate CDC behavior. This introduces a custom publisher layer with its own failure modes, maintenance burden (every new field requires a trigger update), and edge cases (transaction rollback, bulk operation governor limits). When the requirement is record-change streaming to an external system, CDC should be evaluated first before building this custom layer.

3. **Assuming Outbound Messages can be replaced with Platform Events directly** — Outbound Messages and Platform Events do not deliver via the same protocol. Replacing an Outbound Message with a Platform Event eliminates the SOAP delivery guarantee and the acknowledgment-based retry unless a SOAP callout is explicitly added in a subscriber. Teams that migrate Outbound Messages to Platform Events without evaluating the receiver's protocol requirements risk breaking the external integration silently if the receiver expects SOAP.

## Official Sources Used

- Platform Events Developer Guide — event bus, allocations, replay, High-Volume Platform Events, transaction behavior
  URL: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm

- Change Data Capture Developer Guide — CDC entity selection, allocations, gap events, supported objects, ChangeEventHeader structure
  URL: https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm

- Pub/Sub API Developer Guide — gRPC subscription model for Platform Events and CDC, replay ID management
  URL: https://developer.salesforce.com/docs/platform/pub-sub-api/guide/overview.html

- Integration Patterns (Salesforce Architects) — asynchronous vs synchronous integration pattern selection, fire-and-forget, at-least-once delivery patterns
  URL: https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html

- Salesforce Well-Architected Overview — Reliability and Operational Excellence pillars applied to integration design
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
