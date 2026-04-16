---
name: data-cloud-activation-development
description: "Use this skill when building developer-driven Data Cloud activation surfaces: webhook Data Action Targets with HMAC-SHA256 signing, Salesforce Platform Event data actions, Data Cloud-Triggered Flows on DMO insert, or Marketing Cloud journey triggers. Triggers on: webhook data action target, Data Cloud triggered Flow not firing, HMAC secret key for data action, platform event from Data Cloud, DMO insert trigger. NOT for configuring standard admin-level Activation Targets (SFTP, ad platform segment publishing, CRM segment activation) — those require admin configuration skills, not this developer extensibility skill."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
tags:
  - data-cloud
  - data-action-target
  - webhook
  - hmac
  - triggered-flow
  - platform-event
  - activation
  - near-real-time
inputs:
  - "Data Cloud org with Data Action Targets feature enabled"
  - "Target DMO name that will trigger the action"
  - "External webhook endpoint URL (for webhook targets)"
  - "HMAC-SHA256 secret key for webhook signing"
  - "Platform Event API name (for Platform Event targets)"
outputs:
  - "Configured Data Action Target (Webhook, Platform Event, or Marketing Cloud)"
  - "Streaming Insight definition linked to Data Action Target"
  - "Data Cloud-Triggered Flow bound to DMO insert"
  - "HMAC receiver verification code"
  - "Event retention and failure-handling strategy"
triggers:
  - "Data Cloud webhook activation not firing"
  - "how to verify HMAC signature Data Cloud webhook"
  - "Data Cloud triggered flow not executing"
  - "Data Action Target vs Activation Target difference"
  - "Data Cloud near-real-time event delivery setup"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Data Cloud Activation Development

This skill activates when a developer needs to build event-driven automations or external integrations triggered by Data Cloud DMO events. It covers Data Action Targets (Webhook, Salesforce Platform Event, Marketing Cloud) and Data Cloud-Triggered Flows, including HMAC security configuration, payload handling, event retention limits, and failure recovery patterns. It does NOT cover segment-level Activation Targets (SFTP, ad platforms) — those are admin activation tasks.

---

## Before Starting

Gather this context before working on anything in this domain:

- Data Cloud has two distinct activation surfaces: **Activation Targets** (segment-level, batch-publishing) and **Data Action Targets** (event-level, near-real-time). Developer work belongs in Data Action Targets.
- For webhook targets, the HMAC-SHA256 secret key is MANDATORY — omitting it silently causes the target to receive no payload. There is no error message.
- Data Cloud-Triggered Flows fire on DMO row **insertion** only. Updates to existing unified profile records do NOT trigger flows.
- Events are retained for only 4 days with no automatic retry on delivery failure.

---

## Core Concepts

### Data Action Targets vs. Activation Targets

**Activation Targets** publish segment membership in batch to external channels (Marketing Cloud, SFTP, ad networks, CRM). Configured by admins. Run on batch schedules.

**Data Action Targets** fire near-real-time when a Streaming Insight condition is met on a DMO. Three types:
- **Webhook** — HTTP POST to external endpoint, optionally HMAC-signed
- **Salesforce Platform Event** — publishes event to Salesforce event bus
- **Marketing Cloud** — fires a journey entry event via Journey Builder API

### HMAC-SHA256 Secret Key for Webhooks

Every webhook Data Action Target should have an HMAC-SHA256 secret key configured. The platform computes the signature as HMAC-SHA256 of the raw request body using the key and includes it in the `X-SFDC-Signature` request header. Receivers must verify this signature. If the key is missing, the platform silently drops outbound payloads — there is no error logged and no delivery occurs.

After changing or regenerating the key, allow up to 15 minutes for propagation before expecting correct signatures.

### Data Cloud-Triggered Flows

Data Cloud-Triggered Flows bind an autolaunched Salesforce Flow to a specific DMO. They fire when a row is inserted into that DMO. The Flow receives the inserted record's fields as input variables. Since the trigger is insert-only, any downstream logic that must respond to profile updates needs an explicit re-insert pattern or must use Calculated Insights with delta detection.

### Event Retention and No Retry

Data Action Target events are retained for 4 days. If the target (webhook endpoint or Platform Event bus) is unavailable during event delivery, the event is not retried. External dead-letter queues or idempotent replay mechanisms must be built outside the Data Cloud platform.

---

## Common Patterns

### Pattern 1: Webhook Data Action Target with HMAC Verification

**When to use:** External system needs near-real-time notification when a DMO condition is met.

**How it works:**

1. In Data Cloud Setup > Data Action Targets, create a new Webhook target.
2. Enter the endpoint URL and set a strong HMAC-SHA256 secret key.
3. Create a Streaming Insight that defines the DMO condition.
4. Link the Streaming Insight to the Data Action Target.

Receiver-side HMAC verification:

```python
import hmac, hashlib

def verify_payload(secret: str, raw_body: bytes, sig_header: str) -> bool:
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, sig_header)

# In your webhook handler:
# sig = request.headers.get("X-SFDC-Signature", "")
# if not verify_payload(SECRET, request.get_data(), sig):
#     return 403
```

**Why not skip HMAC:** No HMAC key means no payload delivery and no security verification.

### Pattern 2: Data Cloud-Triggered Flow for Automated CRM Actions

**When to use:** A new unified profile DMO record should trigger CRM record creation or update.

**How it works:**

1. Build an autolaunched Salesforce Flow in Flow Builder with input variables matching DMO fields.
2. Activate the Flow.
3. In Data Cloud Setup > Data Cloud-Triggered Flows, create a new entry binding the Flow to the target DMO.
4. Activate the triggered flow binding.
5. When a new DMO row is inserted, the Flow executes with that record's data as inputs.

**Why not use record-triggered Flow:** Record-triggered Flows only watch standard Salesforce CRM objects, not Data Cloud DMOs.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Near-real-time external system notification | Webhook Data Action Target with HMAC | Event-level trigger with payload signing |
| Salesforce-internal automation on DMO event | Data Cloud-Triggered Flow | Native Flow, no external dependency |
| Segment membership push to ad platform | Admin Activation Target (not this skill) | Batch segment-level publishing |
| React to unified profile update | Re-insert pattern or CI delta | Triggered Flows fire on insert only |
| Reliable delivery despite endpoint downtime | External dead-letter queue + idempotent receiver | Platform has no auto-retry |

---

## Recommended Workflow

1. Confirm the use case is event-level (Data Action Target) vs. segment-level (Activation Target admin config).
2. Identify the target DMO and the triggering condition for the Streaming Insight.
3. For webhook targets: generate the HMAC-SHA256 secret key BEFORE creating the target. Set it during creation.
4. Create the Streaming Insight defining the DMO condition and link it to the Data Action Target.
5. For Triggered Flows: build and activate the autolaunched Flow, then create the Data Cloud-Triggered Flow binding in Data Cloud Setup and activate it.
6. Test by inserting a qualifying DMO record and verifying payload delivery or Flow execution.
7. Implement idempotent receivers and external retry/dead-letter handling for webhook targets.

---

## Review Checklist

- [ ] Data Action Target type correctly selected (Webhook, Platform Event, or Marketing Cloud)
- [ ] Webhook HMAC-SHA256 secret key configured — not blank
- [ ] Streaming Insight condition correctly defined and linked to target
- [ ] Triggered Flow is both activated (Flow) and enabled (Data Cloud-Triggered Flow binding)
- [ ] Flow handles insert-only DMO trigger; update scenario uses re-insert pattern
- [ ] Receiver implements HMAC verification against `X-SFDC-Signature` header
- [ ] External retry queue or dead-letter mechanism designed for webhook failures
- [ ] 15-minute HMAC propagation delay accounted for after key changes

---

## Salesforce-Specific Gotchas

1. **Missing HMAC Key Causes Silent Payload Drop** — No HMAC key on a webhook target means no payload is ever delivered. No error is surfaced in Data Cloud. Always configure the HMAC key at target creation time.

2. **Triggered Flows Are Insert-Only** — DMO row updates do NOT fire Data Cloud-Triggered Flows. Only new insertions do. This is a hard platform constraint, not a configuration option.

3. **15-Minute Key Propagation After Change** — After regenerating the HMAC secret key, up to 15 minutes elapse before the new key is applied. Plan rotations for low-traffic periods.

4. **No Auto-Retry on Delivery Failure** — Events retained for 4 days but not retried automatically. Endpoint downtime = lost events after retention window. External dead-letter queues are required for reliable delivery.

5. **Naming Confusion: Activation Targets vs. Data Action Targets** — Creating a webhook under the wrong menu (Activation Targets vs. Data Action Targets in Setup) creates a segment-level batch publisher, not an event-level trigger. These are different features with different menus in Data Cloud Setup.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Data Action Target | Webhook, Platform Event, or Marketing Cloud target configuration |
| Streaming Insight | DMO condition filter definition linked to target |
| HMAC verification code | Python/Node receiver-side signature check |
| Triggered Flow binding | Data Cloud-Triggered Flow entry in Setup |

---

## Related Skills

- data-cloud-integration-strategy — for the full ingestion pipeline upstream of activation
- data-cloud-query-api — for querying DMO data to understand activation source data
- platform-events-integration — for consuming Platform Events fired by Data Cloud Data Action Targets
- flow-for-slack — for Flow-based downstream notifications after Data Cloud trigger
