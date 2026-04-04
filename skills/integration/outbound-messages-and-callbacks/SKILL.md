---
name: outbound-messages-and-callbacks
description: "Use when implementing or troubleshooting Salesforce Outbound Messages — the workflow-triggered SOAP notification mechanism that pushes record field values to an external HTTPS endpoint. Trigger keywords: outbound message not delivering, configure outbound message endpoint, SOAP callback from Salesforce, workflow rule sends notification to external system, outbound message retry loop, acknowledgment SOAP response, session ID in outbound message. NOT for Platform Events, Change Data Capture, REST callouts from Apex, or selecting between event-driven mechanisms (use event-driven-architecture-patterns for selection)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "how do I configure an outbound message to notify an external system when a record changes"
  - "my outbound message keeps retrying and the external endpoint is getting duplicate calls"
  - "workflow rule outbound message not delivering to the endpoint URL"
  - "how to acknowledge a Salesforce outbound message SOAP request to stop retries"
  - "outbound message session ID callback pattern for Salesforce REST API access"
  - "outbound message delivery queue showing pending messages in Setup"
  - "SOAP endpoint requirements for receiving Salesforce outbound messages"
tags:
  - outbound-messages
  - workflow-rules
  - soap
  - integration
  - legacy-automation
  - callbacks
  - at-least-once-delivery
inputs:
  - "The Salesforce object and field values that should be included in the outbound message payload"
  - "The external HTTPS endpoint URL that will receive the SOAP notification"
  - "Whether the external system can return a valid SOAP acknowledgment response"
  - "Whether the triggering automation is a Workflow Rule (required — Outbound Messages cannot be triggered by Flow or Apex directly)"
  - "The org type: new orgs created after Spring '25 cannot create new Workflow Rules"
  - "Any TLS/SSL certificate requirements for the external endpoint"
outputs:
  - "A configured Outbound Message definition referencing the correct object, fields, and endpoint URL"
  - "External endpoint implementation guidance including the required SOAP acknowledgment response structure"
  - "Idempotency design for the receiving endpoint to handle at-least-once delivery duplicates"
  - "Monitoring and failure-recovery guidance using the Outbound Message delivery queue in Setup"
dependencies:
  - event-driven-architecture-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Outbound Messages and Callbacks

Use this skill when implementing, configuring, or troubleshooting Salesforce Outbound Messages — the platform's built-in mechanism for pushing record field values to an external HTTPS SOAP endpoint when a Workflow Rule fires. This skill covers the full implementation lifecycle: configuring the Outbound Message in Setup, designing the receiving endpoint, handling acknowledgment, building callback patterns using the session ID, monitoring delivery, and recovering from failure.

---

## Before Starting

Gather this context before working on Outbound Messages:

- **Is a Workflow Rule already in place, or does one need to be created?** As of Spring '25, new Workflow Rules cannot be created in new Salesforce orgs. If the triggering automation needs to be net-new in a new org, Outbound Messages are not available — evaluate Platform Events published from Flow instead.
- **Can the external endpoint accept SOAP 1.1 over HTTPS?** Outbound Messages are SOAP-only. If the external system is REST-native and cannot be fronted by a SOAP adapter, Outbound Messages are not viable.
- **Does the external system operator understand at-least-once delivery?** Salesforce retries delivery for up to 24 hours. The receiver will receive duplicates during normal retry windows. Idempotency is mandatory, not optional.
- **What TLS version does the endpoint support?** Salesforce enforces TLS 1.2 or higher on all outbound HTTPS connections. Endpoints using TLS 1.0 or 1.1 will fail every delivery attempt with no useful error in Setup.
- **Is the endpoint publicly reachable from Salesforce servers?** Outbound Messages originate from Salesforce infrastructure. Firewall rules that restrict inbound traffic by IP must allowlist Salesforce's published IP ranges.

---

## Core Concepts

### Concept 1 — What Outbound Messages Are (and Are Not)

An Outbound Message is a Salesforce-native notification mechanism that fires when a Workflow Rule evaluation matches a record. Salesforce constructs a SOAP 1.1 envelope containing the specified field values from the triggering record and POSTs it to a configured HTTPS endpoint.

Key platform facts:
- Triggered exclusively by **Workflow Rules** — not by Flow, Process Builder, or Apex triggers directly.
- Sends **SOAP 1.1 only** — no JSON, no REST, no custom payload format.
- Payload contains only the **fields selected at configuration time** plus the record ID, organization ID, and a session ID.
- The session ID in the payload can be used by the external endpoint to make **callback REST or SOAP API calls** back into Salesforce on behalf of the triggering user.
- As of Spring '25, Workflow Rules are a **legacy mechanism**: they still function in existing orgs but cannot be created in newly provisioned orgs.

### Concept 2 — At-Least-Once Delivery and the Acknowledgment Contract

Outbound Messages use an at-least-once delivery model driven by acknowledgment. When Salesforce sends the SOAP envelope, it waits for the external endpoint to return a specific SOAP acknowledgment response. If the acknowledgment is not received — due to an HTTP error, a timeout, a malformed response body, or a network failure — Salesforce treats the delivery as failed and schedules a retry.

Retry behavior:
- Salesforce retries for up to **24 hours** from the initial delivery attempt.
- Retry intervals use **exponential backoff** — early retries are seconds apart, later retries can be hours apart.
- After 24 hours without a successful acknowledgment, the message is **permanently dropped** and marked as failed in the delivery queue. There is no automatic replay.
- A successful HTTP 200 response is **not sufficient** — the response body must contain the correct SOAP acknowledgment structure. An HTTP 200 with an empty body or a REST-style JSON body is treated as a delivery failure and triggers retries.

Required acknowledgment structure the external endpoint must return:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notificationsResponse xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notificationsResponse>
  </soapenv:Body>
</soapenv:Envelope>
```

Returning `<Ack>false</Ack>` is a valid intentional signal to Salesforce to retry delivery — useful when the endpoint cannot process the message at that moment and wants Salesforce to try again later without the endpoint returning an HTTP error.

### Concept 3 — The Session ID Callback Pattern

Every Outbound Message payload includes a `SessionId` element containing a valid Salesforce session token scoped to the user whose record change triggered the Workflow Rule. The external endpoint can use this session ID to make authenticated API calls back into Salesforce (REST API, SOAP API, Apex REST) within the session's validity window.

This enables a two-phase integration pattern:
1. Salesforce pushes the selected record field values outbound via SOAP.
2. The external endpoint uses the session ID as a Bearer token to query additional data or write records back into Salesforce via REST.

Constraints on the session ID:
- The session expires with the triggering user's session. For long-running external processes, the session may be invalid by the time the callback is needed.
- The session is tied to the triggering user's profile and permission sets — the callback has exactly the access that user has. If the user cannot see certain records, neither can the callback.
- Treat the session ID as a credential. Never log it in plaintext, never persist it beyond the immediate callback window, and never expose it in application logs.

### Concept 4 — Monitoring and the Delivery Queue

Salesforce provides a delivery queue for Outbound Messages under **Setup > Process Automation > Outbound Messages**. The queue shows messages currently pending delivery, messages that failed permanently after the 24-hour window expired, and the number of retry attempts for each message.

Failed messages can be manually **requeued** from Setup, which resets the 24-hour retry window. This is the primary recovery mechanism when an endpoint was down for an extended period and messages expired. For high volumes of expired messages, trigger a compensating Apex batch job or data update to re-fire the Workflow Rule against the affected records.

---

## Common Patterns

### Pattern 1 — Standard Workflow-to-SOAP Integration

**When to use:** A Workflow Rule exists in an existing org and the external system exposes a SOAP 1.1 endpoint. This is the baseline Outbound Message configuration.

**How it works:**
1. Configure the Workflow Rule criteria on the target object.
2. Add an Outbound Message action: select the object, enter the endpoint URL, choose the fields to include in the payload.
3. Implement the SOAP endpoint on the external side: parse the incoming SOAP envelope using the namespace `http://soap.sforce.com/2005/09/outbound`, extract field values, process business logic, return the SOAP acknowledgment.
4. Test with a record change in sandbox and verify the delivery queue shows success.
5. Implement idempotency on the receiver — deduplicate by record ID and a timestamp or hash of field values to safely discard duplicate deliveries.

**Why not a synchronous Apex callout:** Apex callouts are synchronous and count against the per-transaction limit (100 callouts per transaction). For high-volume record changes, Apex callouts introduce governor limit risk. Outbound Messages are fully asynchronous and queued outside the transaction — they do not consume any Apex governor limits.

### Pattern 2 — Session ID Callback for Enriched Data Retrieval

**When to use:** The external system needs more data than the fixed Outbound Message field list allows, or needs to write records back into Salesforce after processing the notification.

**How it works:**
1. Configure the Outbound Message with the minimum required identifier fields. The `SessionId` is always included automatically.
2. External endpoint receives the SOAP envelope and extracts the `SessionId` and the record ID.
3. Endpoint makes a REST API call using the session ID as the Authorization Bearer token:
   ```
   GET /services/data/v63.0/sobjects/Account/{id}
   Authorization: Bearer {SessionId}
   ```
4. Endpoint processes the enriched data and optionally writes results back via a REST API PATCH or POST.
5. Endpoint returns the SOAP acknowledgment to close the delivery loop.

**Why not embed all fields in the Outbound Message:** Outbound Messages carry only fields from the triggering object selected at configuration time — no related object data, no formula fields that span relationships, no fields from parent or child records. The callback pattern gives the external system full API access to whatever data it actually needs.

### Pattern 3 — Manual Requeue Recovery After Endpoint Downtime

**When to use:** The external endpoint was unavailable for more than 24 hours (maintenance window, deployment outage) and messages expired from the delivery queue before the endpoint recovered.

**How it works:**
1. Navigate to Setup > Process Automation > Outbound Messages and filter for failed messages.
2. Confirm the endpoint is stable and returning correct SOAP acknowledgments before proceeding.
3. Manually requeue each failed message from Setup — this resets the 24-hour retry window.
4. For high volumes of failed messages (hundreds or thousands), build a compensating Apex batch job that touches the relevant records to re-fire the Workflow Rule, which regenerates fresh Outbound Message delivery attempts automatically.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| External system requires SOAP, Workflow Rule exists in existing org | Outbound Message (this skill) | Only built-in mechanism delivering SOAP from Salesforce on a record change |
| External system is REST-native and accepts JSON | Platform Events + external CometD/Pub-Sub subscriber | Outbound Messages cannot deliver REST or JSON payloads |
| Triggering automation is a Flow (not a Workflow Rule) | Platform Event published from Flow + external subscriber | Flow cannot directly trigger Outbound Messages |
| Org was provisioned after Spring '25 (new org) | Platform Events + Flow publish action | New Workflow Rules cannot be created in new orgs |
| External system needs data beyond the fixed field list | Session ID callback pattern (Pattern 2) | Endpoint uses session ID to fetch additional data via REST |
| Endpoint was down and messages have expired | Manual requeue or compensating batch job | 24-hour retry window is not self-healing |
| Need replay of past events | Platform Events with replay ID or CDC | Outbound Messages have no replay capability once messages expire |

---

## Recommended Workflow

Step-by-step instructions for implementing or troubleshooting an Outbound Message integration:

1. **Verify prerequisites** — Confirm the org can create Workflow Rules (existing orgs only as of Spring '25), the external endpoint URL uses HTTPS, and the endpoint supports TLS 1.2 or higher. Confirm the endpoint is reachable from Salesforce's published IP ranges by testing connectivity before configuring the Outbound Message.

2. **Configure the Outbound Message in Setup** — Navigate to Setup > Process Automation > Workflow Rules, open the target Workflow Rule, and add an Outbound Message action. Select the target object, enter the endpoint URL, and select the fields to include in the payload. Save and activate the Workflow Rule.

3. **Implement the SOAP endpoint on the external side** — The endpoint must parse SOAP 1.1 envelopes using the Salesforce namespace `http://soap.sforce.com/2005/09/outbound`. After processing the business logic, return the SOAP acknowledgment response with `<Ack>true</Ack>`. Build idempotency logic using the record ID to detect and safely discard duplicate deliveries caused by normal retry behavior.

4. **Test end-to-end delivery in sandbox** — Modify a record in sandbox that matches the Workflow Rule criteria. Navigate to Setup > Outbound Messages and confirm the message shows as delivered with no retry count. Inspect the external endpoint's logs to verify the payload contains the expected fields and values.

5. **Validate the session ID callback if used** — If the callback pattern is needed, extract the `SessionId` from the payload and make a test REST API call using it as the Authorization Bearer token. Verify the response returns data consistent with the triggering user's permissions and that the session is valid for the expected callback latency.

6. **Configure monitoring and alerting** — Set up monitoring on the Outbound Message delivery queue. Alert operations if messages remain in pending or failed state beyond a defined threshold (for example, 4 hours). Document the manual requeue procedure in the operations runbook for the team responsible for this integration.

7. **Review before production activation** — Confirm idempotency handles duplicate payloads safely, TLS certificate validity extends for the expected integration lifetime, the endpoint returns the exact SOAP ack structure (not just HTTP 200), and the operations runbook covers both the 24-hour expiry recovery procedure and the firewall allowlist requirements.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] External endpoint URL uses HTTPS and the certificate supports TLS 1.2 or higher
- [ ] Outbound Message is configured on the correct object with the correct fields selected
- [ ] Workflow Rule criteria tested in sandbox confirm firing behavior matches the requirement
- [ ] External endpoint returns the exact SOAP acknowledgment structure — not just HTTP 200
- [ ] Endpoint implements idempotency by deduplicating on record ID or payload content
- [ ] Session ID is not logged in plaintext if the callback pattern is used
- [ ] Delivery queue shows successful delivery in sandbox with no retries before production activation
- [ ] Operations runbook documents the manual requeue procedure for expired messages
- [ ] Salesforce IP ranges are allowlisted on the receiving endpoint's firewall
- [ ] Alert is configured for messages remaining in the delivery queue beyond the acceptable threshold

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **HTTP 200 is not enough — the SOAP ack body is required** — Returning HTTP 200 with an empty body, a plain-text body, or a JSON body causes Salesforce to treat every delivery as a failure and triggers the full retry cycle. This creates an apparent retry storm where the external system receives hundreds of duplicate calls even though it is returning 200. The root cause is always the missing or malformed SOAP acknowledgment body.

2. **Workflow Rules cannot be created in newly provisioned orgs as of Spring '25** — Orgs provisioned after Spring '25 cannot create new Workflow Rules. Outbound Messages therefore cannot be configured in new orgs. Existing Workflow Rules in existing orgs continue to function and can still be modified, but this blocker is permanent for new integrations in new orgs.

3. **Session ID has the triggering user's permissions and a limited lifetime** — The session ID expires when the triggering user's session expires. External systems that process the callback asynchronously hours after receipt may find the session invalid. The session is also scoped to the triggering user's access — service account-triggered Workflow Rules produce more predictable permissions than end-user-triggered ones.

4. **Expired messages require manual intervention — there is no automatic replay** — After the 24-hour retry window expires, messages are permanently dropped. Salesforce does not automatically redeliver them, does not log the message body for later inspection, and does not alert by default. Operations teams must monitor the queue actively and have a runbook for the requeue or compensating-process recovery path.

5. **Bulk operations trigger individual SOAP deliveries at scale** — A bulk data load or a mass field update that triggers the Workflow Rule for 50,000 records generates 50,000 individual SOAP POSTs to the external endpoint. The endpoint must handle this burst without returning HTTP errors (which cause retries that compound the volume). Rate limiting or throttling on the receiver side must be designed to degrade gracefully, returning `<Ack>false</Ack>` rather than HTTP 429 or 503, to prevent a retry amplification cascade.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Outbound Message Setup configuration | The configured Outbound Message definition referencing the object, endpoint URL, and selected fields |
| External SOAP endpoint handler | Receiving endpoint implementation with payload parsing and SOAP acknowledgment response |
| Idempotency logic | Deduplication implementation on the receiver using record ID or payload hash |
| Operations runbook | Recovery procedure for expired messages, endpoint downtime, and firewall incidents |

---

## Related Skills

- `event-driven-architecture-patterns` — Use when deciding between Outbound Messages, Platform Events, CDC, or Streaming API before committing to an implementation
- `platform-events-integration` — Use when the triggering automation is Flow-based or the external system is REST-native
- `soap-api-patterns` — Use when the broader SOAP API integration context (WSDL, authentication, error handling) needs to be addressed alongside Outbound Messages
