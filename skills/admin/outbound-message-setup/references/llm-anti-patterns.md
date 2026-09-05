# LLM Anti-Patterns — Outbound Message Setup

Common mistakes AI coding assistants make when advising on Outbound Message configuration.

## Anti-Pattern 1: Claiming HTTP 200 Is Sufficient for Outbound Message Acknowledgment

**What the LLM generates:** "Configure your external endpoint to return HTTP 200 when it receives the Outbound Message. Salesforce will mark the message as Delivered after receiving the 200 response."

**Why it happens:** HTTP 200 is the universal "success" signal for web services. LLMs apply this general knowledge without knowing Salesforce's specific SOAP acknowledgment requirement — that `notificationsResponse` is a body-level boolean, not a status code.

**Correct pattern:**

The listener must return a `notificationsResponse`, whose schema is a single boolean `Ack`
(SOAP API Developer Guide, *Understanding Outbound Messaging*). Response line and headers:

```http
HTTP/1.1 200 OK
Content-Type: text/xml; charset=UTF-8
```

Body:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notificationsResponse xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notificationsResponse>
  </soapenv:Body>
</soapenv:Envelope>
```

The guide's own C# listener is one line of logic — `notificationsResponse r = new
notificationsResponse(); r.Ack = true; return r;` — which is exactly why teams assume the
transport layer's HTTP 200 covers it. It does not: `Ack` is a value in the response body,
not a status code. Without it Salesforce redelivers.

**Detection hint:** Any response stating that HTTP 200 alone confirms Outbound Message delivery — and, one level subtler, any generated listener that loops the notifications and returns `Ack=true` unconditionally at the end. `Notification` is `maxOccurs="100"` and there is one `Ack` per message, so that loop discards every record after the first failure.

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

For new implementations, Platform Events are the strategic replacement.

Grounded: OutboundMessage is a WorkflowActionType enum value (api_meta.txt L139961)
and an ApprovalProcess action type (L23615-23641). FlowAction is a SEPARATE enum
value whose "pilot program for flow trigger workflow actions is closed" (L139962-139966).
```

UNVERIFIED (2026-09-05): the commonly repeated claim that new Workflow Rules cannot be created as of Spring '23 is not stated in the extracted Metadata API guide — greps for "retire", "no longer create" and "can't create workflow" return nothing, and `WorkflowRule` remains fully documented, including a `failedMigrationToolVersion` field added in API 54.0 for retrying migrations (L140399–140404). Do not assert the Spring '23 cutoff to a customer without checking that release's Release Notes. The grounded statement — that outbound messages are not reachable from Flow — is enough to make the routing decision.

**Detection hint:** Any suggestion to add an Outbound Message in the context of Flow.

---

## Anti-Pattern 3: Not Mentioning the 24-Hour Drop Window

**What the LLM generates:** "If the external endpoint is unavailable, Salesforce will retry the Outbound Message delivery until it succeeds."

**Why it happens:** LLMs may describe retry behavior without knowing the 24-hour hard limit after which messages are permanently dropped.

**Correct pattern:** UNVERIFIED (2026-09-05): the 24-hour figure and the retry cadence are help-only — no delivery, retry or queue limit for outbound messages appears in the Salesforce App Limits Cheat Sheet. The bounded-window *shape* is what matters for the correction; re-confirm the number before quoting it.

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

---

## Anti-Pattern 6: Scaffolding a `.workflow` File Instead of Retrieving It

**What the LLM generates:** "Create `force-app/main/default/workflows/Account.workflow-meta.xml` with the following content:" followed by a `<Workflow>` document containing only the new outbound message and its rule.

**Why it happens:** Most Salesforce metadata types are one file per component, so generating a fresh file is the right move. `Workflow` is not: "There's one file per standard or custom object that has workflow" (api_meta.txt L139896–139898), and it holds every `alert`, `fieldUpdate`, `task`, `rule` and `outboundMessage` for that object (L139908–139948). A deploy of a file containing only the new members removes the rest.

**Correct pattern:**

```bash
# ALWAYS retrieve first -- the file is the object's entire workflow surface
sf project retrieve start --metadata Workflow:Account --target-org my-sandbox

# Then ADD the <outboundMessages> and <rules> elements to what came back
# Then diff, so you can see you removed nothing
git diff -- force-app/main/default/workflows/Account.workflow-meta.xml
```

Two further traps in the same move:

```
Do NOT scaffold from the guide's Declarative Metadata Sample Definition.
  api_meta.txt L140666-140669 contains <fullName>Field_Update</name> -- a mismatched
  tag, so the sample document does not parse. It also puts fullName on a
  WorkflowActionReference, which has only name and type (L139952-139958).

Do NOT wildcard-deploy Workflow.
  <members>*</members> is supported (L140742-140744) and is right for RETRIEVE.
  On deploy it sends every object's whole workflow surface.
```

**Detection hint:** Any generated `.workflow` file that is short, or any deploy step that is not preceded by a retrieve of the same object's workflow file.
