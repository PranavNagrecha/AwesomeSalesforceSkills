# LLM Anti-Patterns — Outbound Message Setup

Common mistakes AI coding assistants make when advising on Outbound Message configuration.

## Anti-Pattern 1: Claiming HTTP 200 Is Sufficient for Outbound Message Acknowledgment

**What the LLM generates:** "Configure your external endpoint to return HTTP 200 when it receives the Outbound Message. Salesforce will mark the message as Delivered after receiving the 200 response."

**Why it happens:** HTTP 200 is the universal "success" signal for web services. LLMs apply this general knowledge without knowing Salesforce's specific SOAP acknowledgment requirement.

**Correct pattern:**

```xml
<!-- External endpoint MUST return this exact structure -->
HTTP/1.1 200 OK
Content-Type: text/xml; charset=UTF-8

<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notifications xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notifications>
  </soapenv:Body>
</soapenv:Envelope>

Without <Ack>true</Ack> in the correct namespace:
Salesforce retries every few minutes for 24 hours → 200+ duplicate deliveries.
```

**Detection hint:** Any response stating that HTTP 200 alone confirms Outbound Message delivery.

---

## Anti-Pattern 2: Suggesting Outbound Messages Can Be Triggered by Flow

**What the LLM generates:** "Add an Outbound Message action to your Flow to notify the external system when the Flow completes."

**Why it happens:** Outbound Messages look like a general-purpose notification mechanism. LLMs may assume they work as Flow actions because Flow supports many action types.

**Correct pattern:**

```
Outbound Messages are ONLY available as Workflow Rule actions.
They are NOT available as Flow Actions.

For Flow-triggered external notifications:
→ Use Platform Events (Salesforce streaming, near-real-time)
→ Use Apex callout (synchronous, full control)
→ Use External Services (REST API invocation from Flow)

Note: New Workflow Rules cannot be created as of Spring '23.
For new implementations, Platform Events are the strategic replacement.
```

**Detection hint:** Any suggestion to add an Outbound Message in the context of Flow.

---

## Anti-Pattern 3: Not Mentioning the 24-Hour Drop Window

**What the LLM generates:** "If the external endpoint is unavailable, Salesforce will retry the Outbound Message delivery until it succeeds."

**Why it happens:** LLMs may describe retry behavior without knowing the 24-hour hard limit after which messages are permanently dropped.

**Correct pattern:**

```
Outbound Message retry window: 24 hours from first failed delivery.
After 24 hours: Message permanently dropped. No automatic replay.

Actions before the 24-hour window expires:
- Manually requeue from Setup > Process Automation > Outbound Messages > Pending
- Fix the endpoint issue
- Monitor the queue for affected messages

After the 24-hour window:
- Message is gone — no recovery
- Must re-trigger: re-save the Salesforce record to fire the Workflow again
- Consider implementing reconciliation queries for critical integrations
```

**Detection hint:** Any description of Outbound Message retries that says "until it succeeds" without mentioning the 24-hour limit.

---

## Anti-Pattern 4: Recommending Outbound Messages for High-Volume or Bulk Scenarios

**What the LLM generates:** "Use Outbound Messages to notify your ERP system whenever any of your Salesforce records change. This will keep your systems in sync."

**Why it happens:** Outbound Messages are described as a sync mechanism. LLMs apply them broadly without knowing their per-record, SOAP-sequential delivery model.

**Correct pattern:**

```
Outbound Messages: Single-record, SOAP-only, Workflow Rule-triggered.
NOT suitable for:
- High-volume change notification (100s+ records/hour)
- Bulk data sync
- JSON-required external systems
- Flow/Apex triggered events

For high-volume scenarios:
→ Change Data Capture (CometD event bus, bulk-capable, JSON)
→ Platform Events (high-throughput, JSON, subscriber fan-out)
→ Bulk API + scheduled reconciliation (for batch sync)
```

**Detection hint:** Any recommendation of Outbound Messages for high-volume or "keep systems in sync" scenarios.

---

## Anti-Pattern 5: Suggesting Outbound Messages Support JSON Payloads

**What the LLM generates:** "Configure the Outbound Message to send the record data as a JSON payload to your REST endpoint."

**Why it happens:** Modern integrations use JSON. LLMs may generate REST/JSON patterns without knowing that Outbound Messages are SOAP-only.

**Correct pattern:**

```
Outbound Messages deliver SOAP 1.1 XML ONLY.
JSON payload delivery is NOT supported.

External system requirements:
- Must accept SOAP 1.1 XML
- Must parse the sforce namespace XML envelope
- Must return SOAP acknowledgment (not JSON)

For JSON delivery:
→ Apex HttpRequest with JSON body (callout)
→ External Services (REST API definition from Flow)
→ Platform Events with a middleware subscriber that calls a REST API
```

**Detection hint:** Any description of Outbound Messages with JSON payload or REST endpoint recommendations.
