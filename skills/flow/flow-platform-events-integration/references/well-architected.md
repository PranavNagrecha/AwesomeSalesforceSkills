# Flow Platform Events Integration — Salesforce Well-Architected Mapping

Platform Events are a natural fit for the Well-Architected principles of **Resilient** (Reliability), **Performant**, and **Secure** architectures when used correctly. Misuse undermines all three. This skill's recommendations map as follows.

## Reliability

Well-Architected Resilient emphasizes loose coupling, independent failure, and recoverability under partial outages.

- **Publish-after-commit prevents phantom events.** The most common reliability bug with record-change events is notifying downstream systems for saves that rolled back. Publish-after-commit is the first-line defense and should be the default for all record-triggered publishers.
- **Subscribers are independent.** A Flow subscriber's failure does not affect an Apex subscriber's success, nor does it affect the publisher. This independence IS the reliability feature — but it requires subscriber-local error handling. Never rely on another subscriber's side effect.
- **At-least-once delivery requires idempotency.** The platform guarantees delivery at least once. It does not guarantee exactly once. Every subscriber must be idempotent against its logical payload key.
- **High-Volume events are durable for 72 hours.** External consumers via Pub/Sub API can replay from a checkpointed replayId after an outage of up to 72 hours. Beyond that window, events are lost.
- **Fault paths to durable logs are mandatory.** Subscriber failures are silently swallowed by the platform. A durable error log (custom object, ApplicationLogger, Big Object) is the only way to know when delivery was accepted but processing failed.
- **Ordering is weak.** Cross-subscriber ordering is undefined; same-subscriber ordering under High-Volume is usually preserved within a partition, but not absolute. Do not design around strict ordering; include sequence fields or accept commutative semantics.

## Performance

Well-Architected Performant asks that work run at the lowest cost and at the correct latency for the user.

- **Decoupling improves interactive save latency.** Publishing an event shifts heavy downstream work out of the user's save transaction. The user sees a faster page return.
- **High-Volume PEs scale horizontally.** Multiple external Pub/Sub API consumers can subscribe independently; adding consumers does not add load to Salesforce write-paths.
- **Publish cost is DML + per-hour.** Each publish is 1 DML statement in the originating transaction. 200 events = 1 DML if published as a collection; 200 DML if published in a loop. Bulk-safe publishing is a direct performance multiplier.
- **Subscriber batching reduces overhead.** High-Volume subscribers receive up to 2,000 events per flow invocation. A bulk-safe subscriber (collection SOQL + collection DML) processes an entire batch for 1 SOQL + 1 DML.
- **Publish limits are a performance ceiling.** Standard-Volume's 6,000/hour org-wide cap is easy to hit during an import. Monitor the Platform Event Usage page. Route high-rate use cases to High-Volume early; retrofitting later requires consumer changes.
- **Pause is NOT a PE substitute.** A Pause-and-wait design holds a flow interview in storage. PE publish-and-subscribe is stateless per subscriber invocation. For long-running waits on external events, PEs with a PE-triggered resumption flow are usually cheaper than Pause.

## Security

Well-Architected Trusted / Secure emphasizes correct running-user context and least-privilege access.

- **Subscriber default is Automated Process user.** The subscriber flow runs as Automated Process by default, which has broad internal access but different sharing visibility from the publishing user. Audit queries and writes in subscribers for sharing correctness.
- **Run-As is configurable.** Platform-Event-Triggered flows can be set to run as a specific user. For sensitive subscribers, create a dedicated integration user with a scoped permission set — least privilege.
- **Event payloads may carry sensitive data.** If the event includes PII (customer name, SSN fragments), the bus becomes a potential data-exposure surface. Consider:
  - Publishing IDs only and letting the subscriber fetch details with proper FLS.
  - Restricting event field visibility via the event definition's FLS.
  - Encrypting sensitive fields and using Pub/Sub API authorization policies on external consumers.
- **External consumer authorization matters.** Pub/Sub API consumers authenticate via Connected App + OAuth with specific scopes. Do not share tokens across external teams; each external consumer gets its own Connected App.
- **Audit trail for PEs is limited.** Event publishing and subscription are logged in Event Monitoring (add-on). Without Event Monitoring, forensics after an incident is hard. Consider adding audit logging explicitly in publishers and subscribers for high-value events.

## Observability (cross-cutting)

- **Platform Event Usage page** — lists publish counts per event per hour; single source of truth for publish-limit monitoring.
- **Event Monitoring (add-on)** — captures publish and subscribe events with latency.
- **Pub/Sub API checkpointing** — external consumers track replayId; internal logging should record consumed replayIds for forensics.
- **Error-log objects** — every subscriber writes failures to a known object; reports and dashboards monitor that object.

## Related Frameworks

- `templates/apex/ApplicationLogger.cls` — durable error logging for subscribers.
- `skills/flow/flow-transactional-boundaries/SKILL.md` — publish-after-commit is a transaction-boundary choice.
- `skills/flow/fault-handling/SKILL.md` — fault connectors in publisher and subscriber.
- `standards/decision-trees/integration-pattern-selection.md` — when PE is the right integration mechanism vs CDC, REST, Bulk API.

## Official Sources Used

- Salesforce Developer Documentation — "Platform Events Developer Guide": https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Salesforce Help — "Platform Event–Triggered Flow": https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_platform_event.htm
- Salesforce Developer Documentation — "High-Volume Platform Events Allocations": https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
- Salesforce Developer Documentation — "Pub/Sub API": https://developer.salesforce.com/docs/platform/pub-sub-api/overview
- Salesforce Architects — "Well-Architected: Resilient": https://architect.salesforce.com/well-architected/trusted/resilient
- Salesforce Architects — "Well-Architected: Performant": https://architect.salesforce.com/well-architected/trusted/performant
- Salesforce Architects — "Well-Architected: Secure": https://architect.salesforce.com/well-architected/trusted/secure
