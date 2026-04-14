---
name: error-handling-in-integrations
description: "Use this skill to design orchestration-layer error handling for Salesforce integrations — covering Platform Event replay recovery, dead-letter queue routing, cross-channel error notification patterns, circuit breaker design, and trigger suspension recovery. Trigger keywords: integration error handling, Platform Event retry, integration dead letter queue, EventBus RetryableException, integration circuit breaker, event bus trigger suspended. NOT for Apex exception handling (use apex-exception-handling skill), HTTP error response contracts (use api-error-handling-design), or retry backoff patterns (use retry-and-backoff-patterns)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "Platform Event trigger has been suspended after too many errors — how to recover and replay missed events"
  - "integration errors are not visible to operations team — need cross-channel error notification design"
  - "need to design a dead-letter queue pattern for failed integration messages in Salesforce"
  - "external system is unstable and integration needs a circuit breaker to stop flooding it"
  - "integration failures are silent and data is drifting between systems without anyone noticing"
tags:
  - integration
  - error-handling
  - platform-events
  - reliability
  - error-handling-in-integrations
inputs:
  - "Integration pattern in use (Platform Events, REST API callouts, CDC, Bulk API)"
  - "Current error visibility: how are failures currently surfaced"
  - "Recovery requirements: must failed messages be replayed or can they be discarded"
  - "External system stability characteristics"
outputs:
  - "Dead-letter queue pattern implementation guidance"
  - "Platform Event trigger suspension recovery procedure"
  - "Circuit breaker design for unstable external systems"
  - "Cross-channel notification pattern (Slack, email, Case creation)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-14
---

# Error Handling in Integrations

This skill activates when a developer or integration architect needs to design orchestration-layer error handling for Salesforce integrations. It covers Platform Event trigger suspension recovery, dead-letter queue patterns, circuit breaker design, and cross-channel failure notifications — distinct from single-transaction Apex exception handling and HTTP error response contracts.

---

## Before Starting

Gather this context before working on anything in this domain:

- Platform Events retain messages for 72 hours (replay window). The stable deduplication key is the event message ID — not the Replay ID, which can be corrupted after Salesforce maintenance events.
- `EventBus.RetryableException` triggers up to 9 automatic retries before the Platform Event trigger is suspended. A suspended trigger stops processing ALL new events on that channel.
- Existing skills cover related but distinct topics: `integration/retry-and-backoff-patterns` covers HTTP retry backoff; `integration/api-error-handling-design` covers HTTP error response contracts. This skill covers orchestration-layer routing and recovery.
- The most critical mistake: throwing RetryableException for permanent errors (bad data, invalid config) causes 9 retries of a record that will never succeed, then suspends the trigger — blocking all event processing.

---

## Core Concepts

### Platform Event Trigger Suspension and Recovery

Failure escalation path:
1. EventBus.RetryableException thrown → up to 9 automatic retries
2. After 9 failures: trigger suspended — all new events stop processing
3. Re-enable: Setup > Platform Events > [Event] > Subscribe Triggers > Resume
4. Set Replay ID on re-enable to replay missed events from the 72-hour window

Recovery requires: knowing the last successfully processed Replay ID (must be stored by the subscriber), fixing the root cause, then resuming with replay from the correct position.

### Dead-Letter Queue Pattern

Salesforce has no built-in DLQ. Implement explicitly:
- Custom object `Integration_DLQ__c` with: Source_System__c, Event_Type__c, Payload__c (JSON text), Error_Message__c, Retry_Count__c, Status__c (Pending / Failed_Max_Retries / Resolved)
- Scheduled Apex retries Pending DLQ entries periodically
- After max retries: mark as Failed_Max_Retries and trigger ops notification

### Circuit Breaker

For unstable external systems:
- Track consecutive failures in a Custom Setting (failure count + timestamp)
- CLOSED (normal): calls go through
- OPEN (threshold exceeded): skip external call, log OPEN state, notify ops
- HALF_OPEN (after cooldown): attempt one test call; success → CLOSE; failure → OPEN again

### Cross-Channel Notification

- Platform Event `Integration_Error__e` → Flow → Email Alert for standard failures
- Platform Event → Named Credential callout to Slack webhook for high-severity
- Case creation for SLA-impacting failures requiring human resolution
- CRM Analytics or Lightning report on DLQ volume for operations dashboards

---

## Common Patterns

### Pattern: RetryableException for Transient, DLQ for Permanent

```apex
trigger OrderEventTrigger on OrderEvent__e (after insert) {
    for (OrderEvent__e event : Trigger.new) {
        try {
            OrderIntegrationService.processEvent(event);
            // Store Replay ID on success
            Integration_State__c.getInstance().Last_Replay_Id__c = event.ReplayId;
            update Integration_State__c.getInstance();
        } catch (OrderIntegrationService.TransientException e) {
            // Transient: throw RetryableException for auto-retry
            throw new EventBus.RetryableException('Transient: ' + e.getMessage());
        } catch (Exception e) {
            // Permanent: write to DLQ, do NOT throw RetryableException
            insert new Integration_DLQ__c(
                Event_Type__c = 'OrderEvent',
                Payload__c = JSON.serialize(event),
                Error_Message__c = e.getMessage(),
                Status__c = 'Pending_Retry'
            );
        }
    }
}
```

---

## Decision Guidance

| Failure Scenario | Recommended Pattern | Reason |
|---|---|---|
| Transient external error (timeout, 503) | RetryableException | Platform auto-retry handles transient failures |
| Permanent data error (invalid payload) | Write to DLQ; no RetryableException | RetryableException on permanent errors suspends trigger |
| External system down > 1 hour | Circuit breaker OPEN + DLQ accumulate | Prevent cascade failures and API limit exhaustion |
| Trigger suspended | Recovery runbook: Replay ID re-enable | 72-hour window enables recovery |
| Silent failures not visible to ops | Cross-channel notification platform event | Ops must know about failures immediately |

---

## Recommended Workflow

1. Identify the integration pattern (Platform Events, REST, CDC, Bulk API) — each has different failure modes.
2. For Platform Event subscribers: implement RetryableException for transient errors only; DLQ for permanent failures.
3. Implement Replay ID tracking: store last successful Replay ID in a Custom Setting on every successful event.
4. Design DLQ object schema and Scheduled Apex retry job with configurable max retry count.
5. Design cross-channel notification: Platform Event for failures → Flow Email + Slack + Case creation based on severity.
6. For unstable external systems: implement circuit breaker using Custom Setting for failure count and circuit state.
7. Document the trigger suspension recovery runbook in team operations documentation.

---

## Review Checklist

- [ ] RetryableException used only for transient errors (not permanent)
- [ ] DLQ pattern implemented for permanent failures
- [ ] Replay ID tracking implemented on every successful Platform Event
- [ ] Trigger suspension recovery runbook documented
- [ ] Cross-channel error notification designed
- [ ] Circuit breaker designed for unstable external systems
- [ ] DLQ retry job with max retry limit and ops alert threshold

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Trigger suspension affects ALL events — not just the failing ones** — Suspending a Platform Event trigger blocks all new events on that channel until manually re-enabled. One bad payload can halt all integration processing.
2. **Replay ID is unstable after Salesforce maintenance** — Replay IDs can become stale after maintenance. Store the event message ID for deduplication; use Replay ID only for starting the replay position.
3. **RetryableException on permanent errors suspends the trigger faster** — Throwing RetryableException on a permanent failure wastes all 9 retries on a record that will never succeed, then suspends the trigger. Only use RetryableException for genuinely transient errors.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DLQ schema and retry job | Integration_DLQ__c design and Scheduled Apex pattern |
| Trigger suspension recovery runbook | Steps to re-enable and replay after trigger suspension |
| Circuit breaker design | Custom Setting schema and state-transition logic |
| Cross-channel notification design | Error event → notification channel mapping |

---

## Related Skills

- `integration/retry-and-backoff-patterns` — HTTP retry backoff for external API calls
- `integration/api-error-handling-design` — HTTP error response contracts
- `integration/event-driven-architecture-patterns` — Platform Event architecture
- `admin/integration-pattern-selection` — upstream pattern selection
