# Well-Architected Notes — Cross-Cloud Data Deployment

## Relevant Pillars

- **Resilient (primary)** — cross-cloud data movement is where an implementation's failure modes become other teams'
  failure modes. Two platform facts set the design envelope: change-event subscribers batch at 2,000 rather than 200,
  and inbound requests of 20 seconds or longer contend for 25 concurrent slots org-wide. Both mean a badly-sized flow
  degrades every other integration in the org, not just its own.
- **Adaptable** — the durable artifact is the system-of-record matrix, not the pipeline. Ownership recorded per field
  survives a tool change; ownership encoded only in whichever direction was built first does not.
- **Secure** — a field-level replica cannot express *why* a value changed. For anything with a consent, privacy, or
  audit obligation, that is not a modelling preference; the receiving cloud has no way to evidence the decision.
- **Efficient** — sub-20-second inbound requests are not counted against the concurrency pool at all. Query shape is
  therefore an architectural lever, not a tuning detail: the difference between a 19-second and a 21-second read is the
  difference between an uncounted call and a contended slot.

## Architectural Tradeoffs

**CDC replication vs domain events.** CDC is nearly free to enable and gives every field change to every subscriber,
which is why it gets chosen by default. What it cannot carry is intent: the receiving cloud sees that `Consent__c`
became `true` and cannot tell a correction from a decision. Platform Events cost design effort per event type and carry
who, when, and why. The rule that holds up: if the receiver needs to know *why*, it is an event; if it only needs the
current value, it is replication.

**Hub-and-spoke vs point-to-point.** A hub gives one identity-resolution point and one place to reason about the
unified profile, at the cost of a latency floor that no amount of tuning removes — which makes it wrong for operational
flows with tight SLAs even when it is right for analytics and activation. Point-to-point is faster per hop and grows
combinatorially; four clouds is six pairs, and each pair is a contract someone must own. Use the hub for identity and
derived attributes, point-to-point for the two or three flows with real latency requirements, and write down which is
which.

**Synchronous read vs replicated copy.** Reading across a boundary at request time keeps one copy and puts the other
cloud's availability on your critical path — and, past 20 seconds, in the org's concurrency pool. Replicating trades
freshness for isolation. The honest question is how stale the receiving process can tolerate the data being; answer it
per field, because the answer differs between a mailing address and a credit limit.

**Bulkified subscriber vs deferred subscriber.** Doing the work inline in the change-event trigger is simpler and
bounded by one transaction's limits against a batch of up to 2,000. Enqueuing gives a fresh limit budget and removes
the work from the inbound request path, at the cost of an extra hop to monitor and a retry story to design. Prefer
enqueuing for anything involving a callout.

## Anti-Patterns

1. **Sizing a change-event subscriber like a record trigger.** A query or callout per event, written by muscle memory
   against a 200-record batch. It passes every test and fails on the first bulk load, at event 101 of 2,000, against a
   governor limit rather than a business error.
2. **Replicating everything in both directions.** With every field flowing everywhere there is no system of record, so
   the last writer wins and the winner depends on timing. The symptom is a recurring "the address keeps reverting"
   ticket that no single team can reproduce.
3. **Deploying the data kit before the connector.** Data 360 org settings, connectors, the data kit, and activation
   targets are four separate deployables in the Metadata API. Promoting the kit alone produces objects that exist,
   ingest nothing, and look correct in every screenshot.
4. **Treating `changedFields` as always populated.** It is empty for operations other than update, including record
   creation — so a subscriber that filters on it alone silently drops every new record.

## Official Sources Used

- Salesforce Developer Limits and Allocations Quick Reference — *Apex Governor Limits*: "The Apex trigger batch size
  for platform events and Change Data Capture events is 2,000", and the 100 synchronous SOQL query limit.
  https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_apexgov.htm (verified 2026-08-14)
- Salesforce Developer Limits and Allocations Quick Reference — *Concurrent API Request Limits*: the 25
  (production/sandbox) and 5 (Developer Edition and Trial) concurrency limits for inbound requests of 20 seconds or
  longer, `REQUEST_LIMIT_EXCEEDED`, and the absence of any limit below 20 seconds.
  https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm (verified 2026-08-14)
- Change Data Capture Developer Guide — *ChangeEventHeader Fields*: `changedFields` semantics (empty for non-update
  operations), `transactionKey`, `recordIds`, `changeType`, `commitNumber`.
  https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_event_fields_header.htm (verified 2026-08-14)
- Apex Reference Guide — *ChangeEventHeader Class*: the header properties and the API version 47.0 gate on the
  `changedFields` property.
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_eventbus_ChangeEventHeader.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Data 360 Metadata Types*: the settings / connector / data kit /
  activation split that sets the promotion order.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_data_cloud_types.htm (verified 2026-08-14)
