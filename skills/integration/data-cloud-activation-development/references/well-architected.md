# Well-Architected Notes — Data Cloud Activation Development

## Relevant Pillars

- **Security** — Webhook Data Action Targets must use HMAC-SHA256 signing. Missing HMAC causes both delivery failure and security exposure (unauthenticated endpoints). Secret key rotation must be planned for low-traffic periods.
- **Reliability** — No auto-retry on delivery failure is the primary reliability risk. External dead-letter queues and idempotent receivers are required for reliable event delivery. Event retention of 4 days must be factored into SLA design.
- **Performance** — Data Action Targets are near-real-time (not true real-time). Streaming Insights evaluate conditions on DMO events, but there is platform processing lag between DMO insertion and event delivery. Not suitable for sub-second latency requirements.
- **Operational Excellence** — DRO steps and Triggered Flows require monitoring. Failed DRO steps stall fulfillment plans. Triggered Flows that fault need monitoring via flow fault email alerts or Flow Error Reporting.

## Architectural Tradeoffs

**Webhook vs. Platform Event:** Webhook targets deliver to external systems directly. Platform Event targets deliver to the Salesforce event bus, where internal Apex subscribers or Flows can consume them. Choose Platform Event when the target consumer is inside the Salesforce platform. Choose Webhook for external system integration.

**Triggered Flow vs. Data Action Target:** Triggered Flows are synchronous Salesforce-internal automations (limited callouts). Data Action Targets push to external systems without Flow governor limits. For CRM record creation, use Triggered Flows. For external system notification, use Data Action Targets.

**Near-Real-Time vs. Batch Activation:** Data Action Targets fire near-real-time per DMO event. Standard Activation Targets (SFTP, ad networks) are batch-scheduled. Choose the right surface for the use case: event-driven integrations → Data Action Targets; bulk segment exports → Activation Targets.

## Anti-Patterns

1. **Webhook Without HMAC Security** — Creating a webhook Data Action Target without configuring the HMAC secret key is both a delivery failure and a security gap. Any caller can submit arbitrary payloads to an unprotected webhook endpoint. Always configure and verify HMAC signing.

2. **Assuming Insert-Only Trigger Covers All Profile Changes** — Designing automation that must respond to profile attribute updates using a DMO insert trigger will miss all update events. Architecture must account for the insert-only constraint through immutable event patterns or Calculated Insight delta detection.

3. **No Dead-Letter Handling for Webhook Targets** — Designing webhook-based integration without external dead-letter queues accepts silent data loss when the target endpoint fails. This is an architectural reliability gap, not a configuration option.

## Official Sources Used

- Activation Targets in Data Cloud — https://help.salesforce.com/s/articleView?id=c360_a_activation_targets.htm
- Data Action Targets in Data Cloud — https://help.salesforce.com/s/articleView?id=c360_a_data_action_target_in_customer_data_platform.htm
- Webhook Data Action Targets in Data 360 — https://developer.salesforce.com/docs/data/data-cloud-int/references/webhook-data-action-targets
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
