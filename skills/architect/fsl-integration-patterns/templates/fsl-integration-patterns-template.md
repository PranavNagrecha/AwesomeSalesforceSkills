# FSL Integration Patterns — Work Template

Use this template when designing FSL integrations with external systems.

## Scope

**Skill:** `fsl-integration-patterns`

**Request summary:** (fill in)

## Integration Inventory

| External System | Direction | Frequency | Pattern | Gotchas |
|-----------------|-----------|-----------|---------|---------|
| ERP (inventory) | Bidirectional | Nightly inbound, near-RT outbound | Upsert + Platform Event | ProductConsumed feedback required |
| GPS/Fleet | Inbound (push) | Every 10-15 min | REST inbound from fleet | Never poll outbound |
| IoT platform | Inbound (event) | Real-time | Platform Event | Schedule via Queueable only |
| Notification (SMS/email) | Outbound | Status-triggered | Named Credential callout | Offline sync latency |

## ProductConsumed ERP Feedback Loop

- [ ] ERP → Salesforce: Product2 + ProductItem nightly batch upsert
- [ ] Salesforce → ERP: ProductConsumed Platform Event → ERP consumption endpoint
- [ ] External IDs on ProductConsumed and ProductRequired for idempotent upsert
- [ ] ERP idempotency using External ID as dedup key

## IoT Work Order Pattern

- [ ] Platform Event channel defined for IoT alerts
- [ ] Event handler creates WorkOrder + ServiceAppointment (DML only — no scheduling)
- [ ] Queueable (AllowsCallouts) enqueued for FSL scheduling
- [ ] Dead-letter queue / retry pattern for failed event processing

## Authentication

- [ ] All outbound integrations use Named Credentials
- [ ] No API keys in Custom Labels, Custom Settings, or Apex code
- [ ] Named Credentials configured for each external system

## Checklist

- [ ] ProductConsumed → ERP feedback loop designed and implemented
- [ ] IoT scheduling uses Queueable (not synchronous in event handler)
- [ ] GPS integration uses inbound push (not outbound Salesforce polling)
- [ ] Daily API limit impact calculated for GPS update frequency
- [ ] Named Credentials used for all outbound authenticated callouts
- [ ] Offline sync latency impact documented for customer notification timing

## Notes

(Record design decisions, integration limitations, and retry strategies.)
