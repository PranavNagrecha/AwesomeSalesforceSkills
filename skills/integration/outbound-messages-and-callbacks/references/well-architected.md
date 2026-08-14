# Well-Architected Notes — Outbound Messages and Callbacks

## Relevant Pillars

- **Reliability** — Outbound Messages implement at-least-once delivery with a 24-hour retry window, which provides a meaningful reliability guarantee compared to fire-and-forget HTTP callouts. However, reliability is conditional: the external endpoint must return the correct SOAP acknowledgment, and operations teams must monitor the delivery queue and have a recovery procedure for messages that expire after 24 hours. The at-least-once contract means duplicates are guaranteed to occur; reliability requires idempotency on the receiving end, not just correct delivery from Salesforce.

- **Security** — Salesforce removed session IDs from Outbound Message payloads the week of February 23, 2026, and the reasoning is instructive: shipping a live API credential inside an integration payload meant the credential landed in every listener log, proxy trace and message queue that touched the notification. Callbacks now require the listener to hold its own OAuth 2.0 credential, which moves the secret into a managed store and gives it an explicit, auditable scope. Treat the access token with the care the session ID deserved and rarely got. TLS configuration remains a prerequisite — Salesforce enforces TLS 1.2+ and certificate trust, but endpoint operators must maintain certificates and CA chains independently.

- **Operational Excellence** — Outbound Messages have no built-in alerting, no detailed error logging visible in Setup, and no automatic replay. Operational excellence requires external monitoring of the delivery queue (via the Tooling API or Setup UI), defined SLAs for message delivery, and documented runbooks for the manual requeue and compensating-batch recovery paths. Without this operational instrumentation, delivery failures are invisible until the external system reports missing data.

- **Scalability** — Outbound Messages do not batch or throttle deliveries. Every individual record change generates a separate SOAP POST. Integrations that appear performant in testing (one record at a time) can overwhelm external endpoints during bulk operations. Scalability design requires the external endpoint to handle burst delivery rates, use asynchronous queuing behind the SOAP endpoint, and return `<Ack>false</Ack>` under load rather than HTTP errors that amplify retry volume.

- **Adaptability** — Outbound Messages are a legacy mechanism. As of Spring '25, new Workflow Rules cannot be created in new Salesforce orgs. Integrations built on Outbound Messages have a finite operational horizon — they will eventually need migration to Platform Events + Flow or a similar modern pattern. Well-Architected designs using Outbound Messages should document the migration path and avoid building additional business logic dependencies on the SOAP payload format that would make migration more expensive.

---

## Architectural Tradeoffs

**At-least-once delivery vs. exactly-once processing:** Outbound Messages guarantee delivery attempts but cannot guarantee exactly-once delivery — duplicates will occur during normal retry cycles. This is a correct and intentional design tradeoff for an asynchronous push mechanism. The cost is that every receiver must implement idempotency. Skipping idempotency is technically simpler but creates data integrity risk in production.

**SOAP constraint vs. existing infrastructure:** Outbound Messages are SOAP-only. For organizations whose external systems are entirely REST-native, this constraint requires either a SOAP adapter layer in front of the REST endpoint or a full migration to Platform Events. Adding a SOAP adapter is additional infrastructure to maintain; migrating to Platform Events requires Flow redesign. The right tradeoff depends on the org's migration timeline and the external system's capability — but accepting the SOAP constraint permanently means accepting the legacy automation dependency.

**Simplicity of configuration vs. flexibility:** Outbound Messages require no Apex code, no Connected App, and no OAuth setup — they are configured entirely in Setup UI. This is a meaningful simplicity advantage compared to Apex callout or Platform Event patterns. The tradeoff is zero flexibility: fixed SOAP payload, fixed field list, fixed trigger source (Workflow Rule only), no payload transformation, no conditional routing. When integration requirements evolve beyond what the fixed configuration allows, the entire mechanism must be replaced rather than extended.

**Borrowed credential vs. owned credential (resolved by Salesforce in February 2026):** The session ID callback traded credential management for coupling — no Connected App to configure, but the listener's ability to authenticate depended on what Salesforce chose to put in the payload. That coupling is exactly what broke when session IDs were removed. The OAuth 2.0 replacement costs a Connected App, a client secret and a token cache; in exchange the listener controls its own token lifetime (making deferred and queued processing safe) and its permission scope is fixed and auditable rather than inherited. There is no longer a decision to make here — the borrowed-credential option no longer exists — but the general lesson transfers: an integration that authenticates using something another system hands it has a dependency it does not control.

Worth correcting a widespread misconception while migrating: the session ID represented the outbound message's configured `integrationUser`, **not** the user whose change triggered the Workflow Rule. Teams that believed otherwise often sized the replacement Connected App's permissions against the wrong user.

---

## Anti-Patterns

1. **No idempotency on the receiving endpoint** — Treating the first successful delivery as the only delivery. Salesforce's at-least-once model guarantees duplicates during retry cycles, certificate renewals, and infrastructure events. An endpoint without idempotency creates duplicate records, duplicate charges, or duplicate processing for every retry. Every Outbound Message receiver must deduplicate by record ID plus a relevant field value or timestamp before performing side-effect business logic.

2. **Relying on Outbound Messages for new integrations in new orgs** — Planning an Outbound Message integration for a Salesforce org provisioned after Spring '25, or designing a managed package around Outbound Messages without verifying subscriber org compatibility. This results in an integration that cannot be configured on the target org and requires an emergency architecture pivot. The mitigation is to verify the org provisioning date before committing to Outbound Messages and to use Platform Events for any integration that may run on new orgs.

3. **No delivery queue monitoring — treating Outbound Messages as self-healing** — Assuming that the 24-hour retry window will always succeed and that operations does not need to monitor the delivery queue. Outbound Messages are permanently dropped after 24 hours with no alert and no automatic replay. An unmonitored integration can silently lose messages during endpoint outages, certificate expirations, or firewall changes. Well-Architected Outbound Message integrations include active queue monitoring (via Setup UI or Tooling API queries against `WorkflowOutboundMessage`) and defined escalation procedures for message expiry.

---

## Official Sources Used

- Salesforce Help — Security Updates to Outbound Messages: Session ID Will No Longer Be Sent — https://help.salesforce.com/s/articleView?id=005232763&language=en_US&type=1 — confirms the **Send Session ID** checkbox is removed, that the `IncludeSessionId` flag "will be ignored and always set to FALSE", that the value no longer appears within the `<sessionID></sessionID>` element, the enforcement date of the week of February 23, 2026 (rescheduled from February 16, 2026), and the OAuth 2.0 remediation. The article states an enforcement date rather than naming a release. (verified 2026-08-13)
- SOAP API Developer Guide — Understanding the Outbound Messaging WSDL — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_wsdl.htm — confirms `SessionId` is declared `nillable="true"` (so it is not removed from the schema, only emptied), and the `OrganizationId`, `ActionId`, `notificationsResponse` and `Ack` element names. (verified 2026-08-13)
- Metadata API Developer Guide — Workflow / WorkflowOutboundMessage — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_workflow.htm — confirms the metadata field name `includeSessionId` and that `integrationUser` is "the named reference to the user under which this message is sent". Note this page still documents the pre-2026 session ID behaviour. (verified 2026-08-13)
- SOAP API Developer Guide — Setting Up Outbound Messaging — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_setting_up.htm — confirms the sessionId "represents the user defined in the previous step and not the user who triggered the workflow". Cited as evidence the developer guide is **stale**: it still instructs readers to select **Send Session ID**. (verified 2026-08-13)
- Salesforce Help — Workflow Outbound Messages — https://help.salesforce.com/s/articleView?id=sf.workflow_outbound_messages.htm
- Metadata API Developer Guide — OutboundMessage metadata type — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_outboundmessage.htm
- Integration Patterns (Salesforce Architects) — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
