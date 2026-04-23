---
name: outbound-webhook-from-salesforce
description: "Use when Salesforce must POST a webhook to a third-party endpoint after a record change — with signed payloads, retries, dead-lettering, rate limits, and idempotency. Covers design choice between Outbound Message, Flow HTTP Callout, Apex Queueable callout, and Event Relay. Does NOT cover inbound webhooks into Salesforce (see inbound-webhook or apex-rest-webhook)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "salesforce send webhook"
  - "outbound http from salesforce"
  - "webhook retry salesforce"
  - "signed webhook hmac salesforce"
  - "flow http callout alternative"
tags:
  - integration
  - webhook
  - callout
  - outbound
  - reliability
inputs:
  - Triggering event (record change, platform event, scheduled)
  - Target endpoint + auth requirement
  - Volume and latency SLA
  - Failure tolerance + compliance requirements
outputs:
  - Webhook design (producer pattern, payload shape, signing, retry)
  - Failure handling + dead-letter
  - Observability plan
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Outbound Webhook From Salesforce

## Purpose

Salesforce has four viable ways to POST to an external endpoint on a
record change: legacy Outbound Messages, Flow HTTP Callout (the
`http_callouts` action), Apex Queueable with callout, and Event Relay via
AWS EventBridge plus a downstream dispatcher. Teams routinely pick the
wrong one — Outbound Messages for systems that care about auth modernity,
Flow HTTP Callout for volume it cannot handle, Apex when a lower-code
option exists. This skill gives a deterministic choice and a reference
pattern per option, including signing, retries, and dead-lettering.

## When To Use

- A record change must notify an external system.
- Rebuilding a brittle Outbound Message integration.
- Standardizing webhook behavior across a portfolio of integrations.

## Recommended Workflow

1. **Identify trigger.** Record change, Platform Event, schedule, or
   manual admin action.
2. **Classify volume and SLA.** Events/minute; acceptable max latency;
   max data loss tolerance.
3. **Pick the mechanism.** Decision table below.
4. **Design the payload.** Versioned schema (`v1`), include a
   correlation id, include minimal data (reference ids, not full records
   unless necessary).
5. **Add signing.** HMAC-SHA256 signature header is the industry
   baseline. Key rotation policy defined.
6. **Add retry + dead-letter.** Exponential backoff; cap attempts;
   persist failures to a custom object for replay.
7. **Monitor.** Dashboard on success rate, latency, and DLQ depth.

## Mechanism Selection

| Mechanism | Good At | Avoid When |
|---|---|---|
| Outbound Message | Legacy bespoke receivers | You need OAuth, HMAC, or structured retry logic |
| Flow HTTP Callout | Low-volume, admin-owned integrations | High volume or complex payload shaping |
| Apex Queueable callout | Full control: retry, sign, shape | You want zero-code ownership |
| Event Relay (→ EventBridge → dispatcher) | AWS-backed fleets, fan-out | Single endpoint, low volume |

## Payload Shape

```
POST /webhook
Headers:
  Content-Type: application/json
  X-Signature: sha256=<hex hmac>
  X-Timestamp: <unix>
  X-Event-Id: <uuid>   // idempotency key
  X-Event-Type: OrderClosed.v1
Body:
  {
    "schemaVersion": "v1",
    "occurredAt": "2026-04-23T12:00:00Z",
    "resource": { "type": "Order", "id": "8015..." },
    "change": { "from": "...", "to": "..." }
  }
```

## Signing

- HMAC-SHA256 over `timestamp + "." + body` with a shared secret.
- Consumer must verify signature AND timestamp freshness (5-min window
  prevents replay).
- Store secret in Named Credential External Credential (encrypted); never
  in custom setting or code.

## Retry

- Retry on 5xx, 408, 429 (respect Retry-After).
- Do not retry 4xx (other than 408/429). Treat as permanent.
- Backoff: 30s, 2m, 10m, 1h, 6h, then dead-letter.
- Track attempt count on a custom object.

## Dead-Letter + Replay

- Custom object `WebhookDelivery__c`: status (Pending/Sent/Failed),
  attempt count, last error, payload blob.
- Scheduled Apex sweeps Pending past backoff, re-enqueues.
- Admin UI to replay a specific failed delivery.

## Observability

- Log every attempt with duration and status.
- Platform Event or log on DLQ arrival; page oncall on rising DLQ.
- Correlation id threaded from triggering record → delivery → receiver.

## Anti-Patterns (see references/llm-anti-patterns.md)

- Outbound Message + bespoke SOAP receiver in 2026.
- Flow HTTP Callout without a retry / DLQ plan.
- Apex callout directly inside an after-save trigger (violates
  mixed-DML/callout ordering).
- Full-record payloads (PII exposure).

## Official Sources Used

- Flow HTTP Callout Action — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_action_http_callout.htm
- Apex Callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_http.htm
- Named Credentials + External Credential — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Outbound Messages (legacy) — https://help.salesforce.com/s/articleView?id=sf.workflow_managing_outbound_messages.htm
- integration-pattern-selection — `standards/decision-trees/integration-pattern-selection.md`
