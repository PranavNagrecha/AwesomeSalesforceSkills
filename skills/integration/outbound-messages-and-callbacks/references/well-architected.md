# Well-Architected Notes — Outbound Messages and Callbacks

## Relevant Pillars

- **Reliability** — Outbound Messages implement at-least-once delivery with a 24-hour retry window, which provides a meaningful reliability guarantee compared to fire-and-forget HTTP callouts. However, reliability is conditional: the external endpoint must return the correct SOAP acknowledgment, and operations teams must monitor the delivery queue and have a recovery procedure for messages that expire after 24 hours. The at-least-once contract means duplicates are guaranteed to occur; reliability requires idempotency on the receiving end, not just correct delivery from Salesforce.

- **Security** — The session ID in every Outbound Message payload is a live API credential. Endpoints that log, store, or expose this token create an authentication vulnerability. TLS configuration on the endpoint is a security prerequisite — Salesforce enforces TLS 1.2+ and certificate trust, but endpoint operators must maintain certificates and CA chains independently. The session ID's user-scoped permissions mean callback access control is implicitly tied to which user triggered the Workflow Rule — this is a subtle security surface that must be explicitly designed.

- **Operational Excellence** — Outbound Messages have no built-in alerting, no detailed error logging visible in Setup, and no automatic replay. Operational excellence requires external monitoring of the delivery queue (via the Tooling API or Setup UI), defined SLAs for message delivery, and documented runbooks for the manual requeue and compensating-batch recovery paths. Without this operational instrumentation, delivery failures are invisible until the external system reports missing data.

- **Scalability** — Outbound Messages do not batch or throttle deliveries. Every individual record change generates a separate SOAP POST. Integrations that appear performant in testing (one record at a time) can overwhelm external endpoints during bulk operations. Scalability design requires the external endpoint to handle burst delivery rates, use asynchronous queuing behind the SOAP endpoint, and return `<Ack>false</Ack>` under load rather than HTTP errors that amplify retry volume.

- **Adaptability** — Outbound Messages are a legacy mechanism. As of Spring '25, new Workflow Rules cannot be created in new Salesforce orgs. Integrations built on Outbound Messages have a finite operational horizon — they will eventually need migration to Platform Events + Flow or a similar modern pattern. Well-Architected designs using Outbound Messages should document the migration path and avoid building additional business logic dependencies on the SOAP payload format that would make migration more expensive.

---

## Architectural Tradeoffs

**At-least-once delivery vs. exactly-once processing:** Outbound Messages guarantee delivery attempts but cannot guarantee exactly-once delivery — duplicates will occur during normal retry cycles. This is a correct and intentional design tradeoff for an asynchronous push mechanism. The cost is that every receiver must implement idempotency. Skipping idempotency is technically simpler but creates data integrity risk in production.

**SOAP constraint vs. existing infrastructure:** Outbound Messages are SOAP-only. For organizations whose external systems are entirely REST-native, this constraint requires either a SOAP adapter layer in front of the REST endpoint or a full migration to Platform Events. Adding a SOAP adapter is additional infrastructure to maintain; migrating to Platform Events requires Flow redesign. The right tradeoff depends on the org's migration timeline and the external system's capability — but accepting the SOAP constraint permanently means accepting the legacy automation dependency.

**Simplicity of configuration vs. flexibility:** Outbound Messages require no Apex code, no Connected App, and no OAuth setup — they are configured entirely in Setup UI. This is a meaningful simplicity advantage compared to Apex callout or Platform Event patterns. The tradeoff is zero flexibility: fixed SOAP payload, fixed field list, fixed trigger source (Workflow Rule only), no payload transformation, no conditional routing. When integration requirements evolve beyond what the fixed configuration allows, the entire mechanism must be replaced rather than extended.

**Session ID access vs. service account design:** Using the triggering user's session ID for callbacks gives the external system immediate API access without additional credential management. The tradeoff is non-deterministic permission scope: different users triggering the same Workflow Rule produce callbacks with different data visibility. Architectures that require consistent, auditable, permission-controlled callback access should instead use a dedicated integration user that triggers all relevant record changes, making the callback permission scope deterministic and auditable.

---

## Anti-Patterns

1. **No idempotency on the receiving endpoint** — Treating the first successful delivery as the only delivery. Salesforce's at-least-once model guarantees duplicates during retry cycles, certificate renewals, and infrastructure events. An endpoint without idempotency creates duplicate records, duplicate charges, or duplicate processing for every retry. Every Outbound Message receiver must deduplicate by record ID plus a relevant field value or timestamp before performing side-effect business logic.

2. **Relying on Outbound Messages for new integrations in new orgs** — Planning an Outbound Message integration for a Salesforce org provisioned after Spring '25, or designing a managed package around Outbound Messages without verifying subscriber org compatibility. This results in an integration that cannot be configured on the target org and requires an emergency architecture pivot. The mitigation is to verify the org provisioning date before committing to Outbound Messages and to use Platform Events for any integration that may run on new orgs.

3. **No delivery queue monitoring — treating Outbound Messages as self-healing** — Assuming that the 24-hour retry window will always succeed and that operations does not need to monitor the delivery queue. Outbound Messages are permanently dropped after 24 hours with no alert and no automatic replay. An unmonitored integration can silently lose messages during endpoint outages, certificate expirations, or firewall changes. Well-Architected Outbound Message integrations include active queue monitoring (via Setup UI or Tooling API queries against `WorkflowOutboundMessage`) and defined escalation procedures for message expiry.

---

## Official Sources Used

- Salesforce Help — Workflow Outbound Messages — https://help.salesforce.com/s/articleView?id=sf.workflow_outbound_messages.htm
- Metadata API Developer Guide — OutboundMessage metadata type — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_outboundmessage.htm
- Integration Patterns (Salesforce Architects) — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
