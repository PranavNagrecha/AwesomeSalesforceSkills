---
name: outbound-message-setup
description: "Use when configuring Workflow-based Outbound Messages to push SOAP payloads to external endpoints — including endpoint setup, field selection, retry behavior, and delivery monitoring. NOT for Platform Events or Flow-based integrations."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "How do I set up an Outbound Message to notify an external system when a record changes?"
  - "Outbound Message shows as Delivered but the external system is not receiving data"
  - "External endpoint is getting the same Outbound Message hundreds of times — why?"
  - "Outbound Message retry is not stopping — how do I clear the queue?"
  - "What fields can I include in an Outbound Message payload?"
tags:
  - outbound-message
  - workflow
  - integration-admin
  - outbound-message-setup
  - soap-delivery
  - retry
inputs:
  - "Workflow Rule that should trigger the Outbound Message"
  - "External endpoint URL (HTTPS required for production)"
  - "Salesforce object fields to include in the payload"
  - "External system's SOAP acknowledgment capability"
outputs:
  - "Workflow Rule Outbound Message action configuration"
  - "SOAP acknowledgment response template for the external endpoint"
  - "Delivery monitoring procedure via Setup > Process Automation > Outbound Messages"
  - "Retry management guidance for stuck or failed messages"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Outbound Message Setup

This skill activates when a practitioner needs to configure Salesforce Outbound Messages — the built-in SOAP-based notification mechanism that Workflow Rules use to push record data to external endpoints. It covers the acknowledgment format the external endpoint must return, the retry behavior, and the most critical anti-pattern: assuming an HTTP 200 response is sufficient for the external system to stop receiving retries.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Outbound Messages are triggered exclusively by Workflow Rules**: Not Flow, not Apex, not Process Builder (deprecated). Outbound Messages are an action type in Workflow Rules only. If the triggering automation is a Flow or Apex, this skill does not apply — use Platform Events or direct API calls instead.
- **SOAP only — no JSON**: Outbound Messages deliver SOAP 1.1 XML. The external endpoint must be able to parse XML SOAP envelopes and return a specific SOAP acknowledgment response. Systems that only accept JSON cannot use Outbound Messages without a SOAP-to-JSON translation layer.
- **Critical acknowledgment behavior**: The external endpoint must return a SOAP acknowledgment response with `<Ack>true</Ack>` inside the correct Salesforce namespace. An HTTP 200 response with any other body — including empty, JSON, or plain text — is treated as a delivery failure and triggers the full 24-hour retry cycle.

---

## Core Concepts

### Delivery and Acknowledgment

Outbound Messages use at-least-once delivery semantics with SOAP acknowledgment:

1. Salesforce sends a SOAP 1.1 XML payload to the configured endpoint.
2. The external system must return an HTTP 200 response with a specific SOAP body:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notifications xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notifications>
  </soapenv:Body>
</soapenv:Envelope>
```

If the external system returns HTTP 200 with any body that does not match this structure — including an empty body, a JSON response, or a SOAP body with a different namespace — Salesforce treats it as a failed delivery and begins retrying.

### Retry Behavior

Outbound Message delivery retries follow an exponential backoff pattern up to 24 hours from the first failed delivery:
- Retries occur approximately at: 1 min, 2 min, 4 min, 8 min, 16 min, 32 min, and then hourly.
- After 24 hours, if acknowledgment has not been received, the message is permanently dropped — there is no automatic replay.
- Failed messages are visible in Setup > Process Automation > Outbound Messages (Pending Messages tab).
- Failed messages can be manually requeued from the Outbound Messages setup page, resetting the 24-hour window.

### Field Selection Limitations

Outbound Message payloads include:
- The Salesforce organization ID and session ID (can be used by the external system to call back to Salesforce).
- The record ID of the triggering record.
- Selected fields from the object (chosen when configuring the Outbound Message action).
- Formula fields and related object fields (via cross-object formula fields on the object) can be included.

Limitations:
- Binary fields (file attachments) cannot be included.
- Related records cannot be directly included — only fields on the triggering object and cross-object formula fields.
- The payload is a single record at a time. Outbound Messages are not batch delivery mechanisms.

---

## Common Patterns

### Setting Up an Outbound Message for Record Change Notification

**When to use:** An external ERP system needs to be notified when a Salesforce Opportunity stage changes to "Closed Won."

**How it works:**
1. Create a Workflow Rule on the Opportunity object: "Opportunity Stage changed to Closed Won."
2. Add a Workflow Action: "New Outbound Message."
3. Configure the Outbound Message:
   - Name and unique name.
   - Endpoint URL: `https://erp.example.com/salesforce-webhook/opportunity`.
   - User to send as: integration user (their session ID is included in the payload).
   - Select fields: Id, Name, Amount, StageName, CloseDate, AccountId.
4. Activate the Workflow Rule.
5. Configure the ERP endpoint to parse the SOAP envelope and return the acknowledgment response.
6. Test by closing an Opportunity Won and monitoring delivery in Setup > Process Automation > Outbound Messages.

**Why SOAP acknowledgment matters:** The ERP's HTTP 200 with JSON body is not sufficient. The endpoint must return the SOAP acknowledgment XML. If it returns JSON, Salesforce retries the message every few minutes for 24 hours, delivering the same payload hundreds of times before dropping it.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| External system needs record change notification, can handle SOAP | Outbound Message on Workflow Rule | Built-in, no code required, at-least-once guaranteed |
| External system only accepts JSON | Platform Event or Apex callout | Outbound Messages deliver SOAP only |
| Need to trigger from Flow or Apex | Platform Event or direct Apex HttpRequest | Outbound Messages are Workflow Rule actions only |
| External system returning HTTP 200 but receiving retries | Fix acknowledgment body to return SOAP Ack:true | HTTP 200 alone is not sufficient — SOAP body must match |
| Message delivery stuck/retrying for hours | Manual requeue from Outbound Messages Setup page | Resets the 24-hour window |
| Messages dropped after 24 hours | No automatic replay — manual requeue or re-trigger | After 24h drop, the message is gone; re-trigger by re-saving the record |
| Need batch delivery | Not suitable — Outbound Messages are single-record | Use Bulk API or batch Apex with platform events for bulk |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm Workflow Rule trigger exists** — Outbound Messages require a Workflow Rule as the trigger. Verify a Workflow Rule exists for the triggering event (field change, new record, etc.) or create one. Note: new Workflow Rules cannot be created as of Spring '23 — existing rules can be maintained, and new implementations should use Flow with Platform Events.
2. **Create the Outbound Message action** — From the Workflow Rule, add a Workflow Action > New Outbound Message. Specify the endpoint URL, the "Send As" user (the integration user whose session ID will be in the payload), and select the fields to include.
3. **Configure the external endpoint** — The external system must expose an HTTPS endpoint that accepts SOAP 1.1 XML and returns the specific acknowledgment response. Provide the external team with the SOAP acknowledgment template: HTTP 200 with the `<Ack>true</Ack>` body inside the `http://soap.sforce.com/2005/09/outbound` namespace.
4. **Activate the Workflow Rule** — Activate both the Workflow Rule and ensure it is included in the object's Workflow evaluation.
5. **Test delivery** — Trigger the Workflow by updating a test record. Monitor in Setup > Process Automation > Outbound Messages > Pending and Delivered tabs. Confirm the message moves from Pending to Delivered within a few minutes.
6. **Monitor production** — Schedule a periodic review of the Outbound Messages pending queue. Messages stuck in pending for more than a few hours indicate delivery or acknowledgment failures. Manually requeue to reset the 24-hour window while the underlying issue is investigated.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Workflow Rule is active and triggers on the correct condition
- [ ] Outbound Message action configured with correct endpoint URL and fields
- [ ] External endpoint implements SOAP acknowledgment response (HTTP 200 + SOAP body with Ack:true)
- [ ] Test delivery confirmed — message shows Delivered in Setup > Outbound Messages
- [ ] Monitoring procedure established for pending message queue
- [ ] External team understands the 24-hour retry window and acknowledgment requirement

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **HTTP 200 without SOAP acknowledgment triggers a retry storm** — The most critical behavior to communicate to the external system team. An HTTP 200 response is not sufficient for Outbound Message delivery confirmation. The response body must be a SOAP envelope containing `<Ack>true</Ack>` inside the `http://soap.sforce.com/2005/09/outbound` namespace. Any other body — empty, JSON, plain text, wrong SOAP namespace — is treated as failure. The external system receives the same message repeatedly every few minutes for 24 hours, generating hundreds or thousands of duplicate deliveries before the message is finally dropped.
2. **Messages are permanently dropped after 24 hours with no replay** — After 24 hours of failed delivery retries, the Outbound Message is permanently discarded. There is no dead-letter queue, no automatic replay, and no notification that the message was dropped (beyond the message disappearing from the pending queue). If a message needs to be re-delivered after the 24-hour window, the Workflow must be manually re-triggered by re-saving the record. For critical integrations, implement compensating controls — either periodic reconciliation queries or alerts for messages stuck in pending longer than a threshold.
3. **Outbound Messages can only be triggered by Workflow Rules (not Flow)** — As Salesforce phases out Workflow Rules in favor of Flow, new Outbound Message actions cannot be added to Flows. This is a significant limitation for new integration implementations. If the automation is Flow-based, Platform Events are the equivalent asynchronous notification mechanism and support JSON payload.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Outbound Message configuration | Endpoint URL, field selection, Send As user setup |
| SOAP acknowledgment template | XML response the external system must return to confirm delivery |
| Monitoring procedure | Steps to check Outbound Messages pending and delivered queues |
| Retry management guide | Steps to manually requeue failed messages and reset the 24-hour window |

---

## Related Skills

- integration-admin-connected-apps — If the external system calls back to Salesforce using OAuth, configure a connected app
- remote-site-settings — Not required for Outbound Messages (Salesforce is the sender, not the receiver)
