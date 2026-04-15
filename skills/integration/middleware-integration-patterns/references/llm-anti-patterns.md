# LLM Anti-Patterns — Middleware Integration Patterns

Common mistakes AI coding assistants make when generating or advising on Middleware Integration Patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Apex Callouts for Multi-System Orchestration

**What the LLM generates:** When asked how to synchronize a Salesforce Opportunity close to three external systems (ERP, data warehouse, notification service), the assistant generates an Apex trigger with three `Http.send()` callouts inline, each wrapped in a try/catch, with a retry loop on 503 responses.

**Why it happens:** Apex callout examples are heavily represented in Salesforce developer training data. LLMs default to code generation over architecture guidance, and Apex is the most familiar Salesforce integration primitive. The multi-system orchestration constraint is not recognized as a governor-limit violation scenario until the code is tested under load.

**Correct pattern:**

```
// Do NOT do this in an Apex trigger for multi-system fanout:
// Http h = new Http();
// HttpRequest req1 = new HttpRequest(); req1.setEndpoint('https://erp.example.com/orders'); ...
// HttpRequest req2 = new HttpRequest(); req2.setEndpoint('https://dw.example.com/events'); ...
// HttpRequest req3 = new HttpRequest(); req3.setEndpoint('https://notify.example.com/alerts'); ...

// CORRECT: publish a Platform Event and let middleware handle fanout
OrderSyncEvent__e event = new OrderSyncEvent__e(
    OpportunityId__c = opp.Id,
    ClosedAmount__c = opp.Amount
);
EventBus.publish(event);
// Apex transaction ends here — no callouts, no governor limit risk
```

Middleware subscribes to `OrderSyncEvent__e` via Pub/Sub API and fans out to ERP, data warehouse, and notification service independently.

**Detection hint:** Look for multiple `Http.send()` or `HttpRequest` calls in the same Apex trigger method, or `for` loops over `Http.send()` — strong signal that orchestration has leaked into Apex.

---

## Anti-Pattern 2: Treating Middleware Vendor Selection as MuleSoft-Specific Configuration Advice

**What the LLM generates:** When asked "which middleware should I use for Salesforce integration," the assistant immediately pivots to MuleSoft Anypoint Salesforce Connector configuration steps: how to set up JWT Bearer auth, configure watermark, select the Bulk API — without evaluating whether MuleSoft is the right choice or whether middleware is needed at all.

**Why it happens:** MuleSoft is a Salesforce subsidiary and is disproportionately represented in Salesforce integration documentation and training data. LLMs conflate "Salesforce middleware integration" with "MuleSoft configuration" because the two are co-located in training corpora. The vendor selection question is treated as resolved before it is asked.

**Correct pattern:**

```
Step 1: Determine whether middleware is required at all.
  - Does the integration require protocol conversion, cross-system orchestration,
    durable queuing, or complex transformation?
  - If not, native Salesforce capabilities (Platform Events, Flow HTTP Callout,
    Apex callouts) may be sufficient.

Step 2: If middleware is required, identify the selection criteria:
  - Protocol support needed?
  - Real-time event latency SLA?
  - Team skills and existing licenses?
  - Governance and API management requirements?

Step 3: Score candidate vendors against criteria.
  MuleSoft: enterprise governance, deepest Salesforce connector, highest cost
  Boomi: mid-market, fast deployment, good protocol breadth
  Workato: business-user automation, SaaS-first, 5-min polling minimum
  Informatica: batch ETL/MDM strength, weaker real-time events
```

**Detection hint:** Response that opens with MuleSoft connector XML or Anypoint configuration steps without first asking about the integration requirements, existing licenses, or whether middleware is necessary.

---

## Anti-Pattern 3: Assuming Workato Triggers Are Real-Time for Salesforce Record Changes

**What the LLM generates:** "Use a Workato Salesforce real-time trigger to detect when an Opportunity is closed and immediately sync it to HubSpot. This will fire instantly when the record changes."

**Why it happens:** Workato's marketing materials and documentation label their Salesforce connector trigger as "real-time." LLMs reproduce this label without noting that the implementation is polling-based with a minimum interval of approximately 5 minutes, not a push subscription.

**Correct pattern:**

```
Workato Salesforce "real-time" trigger = polling every ~5 minutes minimum.

For sub-5-minute latency with Workato:
  Option A: Configure Salesforce Flow to POST to a Workato webhook URL
            (achieves near-real-time push without polling delay)
  Option B: Switch to MuleSoft or Boomi which support native Pub/Sub API
            gRPC subscription (true push, sub-second latency)

Only use Workato standard trigger when 5-minute latency is explicitly acceptable.
```

**Detection hint:** Response recommending Workato for a use case with a latency requirement under 5 minutes without noting the polling constraint or recommending the webhook workaround.

---

## Anti-Pattern 4: Conflating Protocol Conversion with REST Transformation

**What the LLM generates:** When asked about integrating Salesforce with a legacy system that exposes a JMS queue or AS2 protocol, the assistant generates Apex code using `HttpRequest` with a custom endpoint, as if JMS or AS2 were HTTP-accessible by default.

**Why it happens:** LLMs trained on web and cloud integration examples treat all integrations as HTTP-based. Non-HTTP protocols (JMS, MQ, AS2, JDBC, RFC, SFTP) require a middleware adapter that has no equivalent in Apex's HTTP callout model. The LLM does not recognize the protocol mismatch.

**Correct pattern:**

```
// JMS, AS2, JDBC, SAP RFC, SFTP — NONE of these are reachable via Apex HttpRequest.

// These protocols require a middleware adapter:
// - MuleSoft: JMS Connector, AS2 Connector, SAP Connector, SFTP Connector
// - Boomi: JMS connector, AS2 connector, SAP connector
// - Informatica: JDBC, flat-file, SAP adapters

// Only after middleware converts the protocol to HTTP/REST can Salesforce
// interact with the result via Named Credentials + External Services or Apex callout.
```

**Detection hint:** Apex `HttpRequest` code targeting a non-HTTP protocol endpoint (e.g., `jms://`, `sftp://`, `sap://`, `jdbc://`) or any endpoint described as a "queue" or "legacy mainframe."

---

## Anti-Pattern 5: Omitting Dead-Letter Queue and Error Recovery Design

**What the LLM generates:** A complete middleware integration flow that handles the happy path (message received → transformed → written to target system) with a single generic `catch` block that logs the error and discards the message. No dead-letter queue, no retry policy, no alerting, no compensating transaction design.

**Why it happens:** Happy-path completeness is easier to demonstrate and is more common in training examples. Error handling design is treated as an implementation detail rather than an architectural requirement. LLMs optimize for code that compiles and runs, not for code that fails gracefully in production.

**Correct pattern:**

```
Every middleware integration requires:

1. Retry policy with exponential backoff:
   - Attempt 1: immediate
   - Attempt 2: after 1 min
   - Attempt 3: after 5 min
   - Attempt 4: after 30 min
   - After max retries: route to dead-letter queue

2. Dead-letter queue:
   - Persistent, durable (survives middleware restart)
   - Stores original message + error metadata + retry count + timestamp
   - Triggers alert to operations team when message lands here

3. Compensating transaction:
   - If Step N succeeds and Step N+1 fails, trigger a rollback action for Step N
   - Document which steps are compensable and which are not (external emails sent = not compensable)

4. Correlation ID propagation:
   - Salesforce record Id (or a UUID generated at event publish time)
   - Carried in every message header through every hop
   - Used to correlate Salesforce event → middleware log → target system write
```

**Detection hint:** Middleware flow design that has no mention of dead-letter queue, retry policy, or compensating transactions, or that has a `catch` block that only logs and exits without routing to a recovery path.

---

## Anti-Pattern 6: Treating MuleSoft Agent Fabric as a Generic Middleware Recommendation

**What the LLM generates:** When asked about Agentforce integrating with external systems, the assistant recommends "use MuleSoft Agent Fabric" as the standard answer regardless of whether the organization uses MuleSoft.

**Why it happens:** MuleSoft Agent Fabric is a real Salesforce product feature for exposing MuleSoft APIs as Agentforce agent actions. LLMs trained on recent Salesforce announcements over-generalize this to mean that all Agentforce external integrations require MuleSoft, which is false. Agentforce agents can call external APIs via Flow HTTP Callout, Apex, or External Services regardless of middleware vendor.

**Correct pattern:**

```
Agentforce external API integration options:
  - Flow HTTP Callout Action: no middleware needed, calls HTTP endpoints directly
  - Apex-defined invocable action: callouts from Apex, any HTTP endpoint
  - External Services registered action: OpenAPI-spec-registered endpoints
  - MuleSoft Agent Fabric: optional when MuleSoft is already the middleware platform
                           and Experience APIs in Anypoint Exchange are the target

MuleSoft Agent Fabric is a convenience feature for existing MuleSoft customers.
It is not required for Agentforce to call external APIs.
```

**Detection hint:** Response recommending MuleSoft Agent Fabric to an organization that has not mentioned MuleSoft, or treating Agent Fabric as the only path for Agentforce external integration.
