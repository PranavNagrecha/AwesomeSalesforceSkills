# LLM Anti-Patterns — Outbound Messages and Callbacks

Common mistakes AI coding assistants make when generating or advising on Outbound Messages and Callbacks.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating a REST-Style Acknowledgment Response Instead of SOAP

**What the LLM generates:** When asked to implement an endpoint that receives Salesforce Outbound Messages, LLMs frequently generate a handler that returns `{"status": "ok"}` with HTTP 200, or returns an empty 200 response, treating the Salesforce SOAP request like a generic webhook:

```python
@app.route("/salesforce-callback", methods=["POST"])
def handle():
    data = request.json  # wrong — Outbound Messages are SOAP, not JSON
    process(data)
    return jsonify({"status": "received"}), 200  # wrong ack format
```

**Why it happens:** LLMs are trained on large volumes of REST webhook implementations (Stripe, GitHub, Slack, etc.) and default to the REST/JSON pattern. The Salesforce SOAP acknowledgment requirement is a domain-specific constraint that overrides the generic "return 200" webhook pattern. Training data for SOAP endpoints is sparse compared to REST, so the LLM falls back to REST idioms.

**Correct pattern:**

```python
from flask import Flask, request, Response

@app.route("/salesforce-callback", methods=["POST"])
def handle():
    # Parse SOAP XML body — it is NOT JSON
    tree = ET.fromstring(request.data)
    # ... process the SOAP payload ...
    ack = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notificationsResponse xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notificationsResponse>
  </soapenv:Body>
</soapenv:Envelope>"""
    return Response(ack, content_type="text/xml; charset=utf-8", status=200)
```

**Detection hint:** Check the response for `application/json` content type or `jsonify(` in Python / `response.json(` in JavaScript. Any non-XML response body is wrong for an Outbound Message endpoint. Also check that `content_type="text/xml"` is set explicitly.

---

## Anti-Pattern 2: Recommending Platform Events as a Direct Drop-In Replacement for Outbound Messages

**What the LLM generates:** When asked how to "replace" or "modernize" an Outbound Message integration, LLMs often suggest publishing a Platform Event from a Flow and having the external system subscribe via CometD, framing this as a direct equivalent:

```
"Instead of the Outbound Message, publish a Platform Event from a Flow.
The external system can subscribe using the CometD protocol — it's the
same as what Outbound Messages do, just using a modern pattern."
```

**Why it happens:** LLMs correctly identify that Platform Events are the modern alternative but underspecify the protocol gap. Outbound Messages push data to the endpoint via SOAP POST. Platform Events require the external system to pull via a subscriber connection (CometD, Pub/Sub API). This is a fundamentally different integration topology — push vs. pull. The LLM conflates "modern event-driven pattern" with "functionally equivalent replacement" without acknowledging the subscriber architecture change.

**Correct pattern:**

```
Platform Events are NOT a direct drop-in for Outbound Messages. The protocol topology
is inverted: Outbound Messages push via SOAP POST to the endpoint. Platform Events
require the external system to maintain an active subscriber connection (CometD or
Pub/Sub API gRPC) and pull events. If the external system cannot maintain a long-lived
subscriber connection, Platform Events require middleware (MuleSoft, middleware iPaaS)
to bridge the gap. Evaluate the external system's architecture before recommending
Platform Events as a replacement.
```

**Detection hint:** Look for the phrase "just use Platform Events instead" without qualification. Flag any recommendation that does not address the subscriber architecture requirement (CometD endpoint or Pub/Sub API gRPC client) on the external system side.

---

## Anti-Pattern 3: Instructing Developers to Trigger Outbound Messages from Apex or Flow

**What the LLM generates:** When a developer needs a notification to fire when an Apex trigger runs, LLMs may suggest code like:

```apex
// Wrong — OutboundMessage is not callable from Apex
OutboundMessage.send('MyEndpoint', record);

// Or suggesting a Flow approach:
// "Create a Record-Triggered Flow and add a Send Outbound Message action"
// (this action type does not exist in Flow)
```

**Why it happens:** LLMs generalize from other automation patterns where callout-style actions are available from Apex (e.g., `Http` class, `EventBus.publish`). They also extrapolate from Flow action types (Send Email, Create Records, Invoke Apex) and assume Outbound Message is a similarly invocable action. Neither assumption is correct — Outbound Messages are exclusively Workflow Rule actions and have no programmatic invocation surface.

**Correct pattern:**

```
Outbound Messages can only be triggered by Workflow Rules — they are a Workflow
Rule action type, not a callable API. There is no Apex method, Flow action, or
Process Builder action that invokes an Outbound Message directly.

If the trigger is Apex: use Http.send() for a direct callout, or use Queueable
Apex for an async callout. Both are fully supported.

If the trigger is Flow: publish a Platform Event from the Flow and configure
the external system to subscribe. Or use a Flow-to-Apex invocable action that
performs the HTTP callout.
```

**Detection hint:** Flag any code that references `OutboundMessage` as an invocable class or method in Apex. Flag any Flow design that includes "Call Outbound Message" as an action type — this action does not exist.

---

## Anti-Pattern 4: Storing the Session ID for Later Use or Logging It in Plaintext

**What the LLM generates:** When implementing the session ID callback pattern, LLMs often generate code that persists the session ID in a database for later use, or logs it as part of standard request logging:

```python
# Wrong — persisting the session ID
db.save({
    "case_id": case_id,
    "session_id": session_id,  # never persist a live credential
    "received_at": datetime.now()
})

# Wrong — logging the full payload including session ID
logger.info(f"Received Outbound Message: {request.data}")
```

**Why it happens:** LLMs follow generic "save everything for debugging" logging patterns. Session IDs look like opaque strings and LLMs don't always recognize them as live credentials equivalent to OAuth access tokens. The security implication — that stored session IDs can be used to make authenticated API calls to Salesforce — is often missed.

**Correct pattern:**

```python
# Correct — use session ID immediately, never persist it
session_id = extract_session_id(soap_body)
try:
    enriched_data = fetch_from_salesforce(session_id, record_id)
    process(enriched_data)
finally:
    # session_id goes out of scope — never stored, never logged
    pass

# Correct — log without credentials
logger.info(f"Received Outbound Message for record {record_id}")
# Do NOT log request.data in full — it contains the session ID
```

**Detection hint:** Check for `session_id` appearing in database write operations, log statements, or any persistent store. Also check for `logger.info(request.data)` or equivalent full-payload logging, which will capture the session ID in log files.

---

## Anti-Pattern 5: Recommending Outbound Messages for New Integrations Without Checking Org Age

**What the LLM generates:** When asked to design a Salesforce-to-external notification integration, LLMs frequently recommend Outbound Messages as a low-configuration option without checking whether the org can actually create Workflow Rules:

```
"The easiest way to push record data to your external system is to configure
an Outbound Message. Go to Setup > Workflow Rules, create a new rule on the
Account object, and add an Outbound Message action."
```

**Why it happens:** LLMs trained on pre-Spring '25 documentation treat Outbound Messages as a universally available feature. The Spring '25 restriction on creating new Workflow Rules in new orgs is a recent platform change that may not be represented proportionally in training data. The LLM recommends the historically available option without knowing the org's provisioning date.

**Correct pattern:**

```
Before recommending Outbound Messages, confirm the org was provisioned before
Spring '25. New orgs (provisioned Spring '25 or later) cannot create new Workflow
Rules and therefore cannot configure new Outbound Messages.

For new orgs or new integrations where Platform Events are viable:
- Use a Record-Triggered Flow with a Publish Platform Event action.
- Configure the external system to subscribe via Pub/Sub API or CometD.
- This is the supported modern path for Salesforce-to-external push notifications.

Outbound Messages remain appropriate only when: (1) the org is pre-Spring '25
and has an existing Workflow Rule infrastructure, and (2) the external system
requires SOAP and cannot be updated to use a Platform Event subscriber.
```

**Detection hint:** Flag any recommendation to "create a new Workflow Rule" for an Outbound Message integration without a qualifier about org provisioning date. Also flag recommendations that describe Workflow Rules as equivalent in availability to Flow — they are not, in orgs provisioned after Spring '25.

---

## Anti-Pattern 6: Assuming No Idempotency Is Needed Because "Salesforce Only Sends Once on Success"

**What the LLM generates:** When asked about duplicate handling for Outbound Messages, LLMs sometimes claim that Salesforce stops retrying immediately on the first success and therefore duplicates are not possible in the happy path:

```
"Once the endpoint returns HTTP 200 and Salesforce marks the message as
delivered, it won't send the same message again. You only need idempotency
handling for failed messages that are manually requeued."
```

**Why it happens:** LLMs conflate "Salesforce stops retrying after a successful ack" (true) with "the endpoint will only ever receive each message exactly once" (false). Multiple legitimate scenarios produce duplicates outside of retry: manual requeue from Setup, compensating batch jobs that re-fire the Workflow Rule, and the fact that at-least-once delivery semantics allow Salesforce to deliver before confirming its own internal state is committed.

**Correct pattern:**

```
Idempotency is required unconditionally for all Outbound Message receivers,
not just for requeued messages. Sources of duplicates include:

1. Normal retry cycles when ack delivery is delayed (network jitter)
2. Manual requeue from Setup during incident recovery
3. Compensating batch jobs that re-fire the Workflow Rule
4. Infrastructure events on Salesforce's side that cause redelivery

The idempotency key should be the record ID combined with the relevant
business state (e.g., record ID + Status field value + a hash of key fields).
Store processed keys in a deduplication log with a TTL appropriate for the
expected maximum requeue window.
```

**Detection hint:** Flag any external endpoint implementation that performs side-effect operations (database inserts, charge processing, record creation) without first checking a deduplication log. Also flag designs where idempotency is described as "optional" or "only for failure recovery."
