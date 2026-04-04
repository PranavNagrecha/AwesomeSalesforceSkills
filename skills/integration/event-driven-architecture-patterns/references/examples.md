# Examples — Event-Driven Architecture Patterns

## Example 1: ERP Order Sync — Choosing CDC Over Platform Events

**Context:** A manufacturing company's Salesforce org tracks Orders (a custom object). An external ERP must be notified whenever an Order record's status, amount, or shipping address changes so the ERP can update its corresponding order record in near-real time.

**Problem:** The team initially proposes creating an Apex after-update trigger that publishes a custom Platform Event (`OrderChanged__e`) whenever an Order is updated, populating the event payload with the fields that changed. After prototyping, they realize:
- They must manually maintain the list of fields on the Platform Event object to match the Order object's fields.
- They must track which fields actually changed in the Apex trigger to avoid publishing noise.
- Each new Order field added in future releases requires updating the Apex trigger AND the Platform Event definition.

**Solution:**

Enable Change Data Capture for the custom Order object. The ERP subscriber connects via the Pub/Sub API and subscribes to `/data/Order__ChangeEvent`. The `ChangeEventHeader` automatically includes `changedFields` — the list of fields that changed in the DML transaction — and the body contains the new values of those fields. No Apex publisher code is required.

```
// Setup: enable CDC in Setup > Integrations > Change Data Capture
// Select "Order__c" (custom object) from the entity list

// Pub/Sub API subscriber receives:
{
  "ChangeEventHeader": {
    "changeType": "UPDATE",
    "changedFields": ["Status__c", "ShippingCity__c"],
    "recordIds": ["a01000000000001AAA"]
  },
  "Status__c": "Shipped",
  "ShippingCity__c": "Chicago"
}
```

**Why it works:** CDC is the correct mechanism for record-change stream to external systems. It eliminates the custom publisher layer entirely, provides automatic field-delta tracking, and requires no code changes when new fields are added to the object. The 72-hour replay window provides recovery for ERP downtime up to 3 days.

---

## Example 2: Cross-System Business Event — Platform Events for a Non-DML Trigger

**Context:** A financial services org runs a nightly batch process in Apex that evaluates loan applications and approves or rejects them. When a batch completes, an external notification service must be alerted so it can send SMS confirmations to applicants. The decision (approve/reject) is made in Apex — there is no corresponding single DML operation that consistently marks a "batch complete" milestone.

**Problem:** The team considers CDC on the Loan Application object, but the "batch complete" milestone is not expressed as a single record update on a single object. The batch updates many records across multiple transactions. CDC would fire per-record change events but has no concept of a "batch boundary" or aggregate completion signal. Subscribing to CDC would require the notification service to reconstruct batch completion from individual record events — complex and fragile.

**Solution:**

Define a Platform Event (`LoanBatchComplete__e`) with fields for `BatchId__c`, `ProcessedCount__c`, `ApprovedCount__c`, and `RejectedCount__c`. At the end of the Apex batch's `finish()` method, publish one event summarizing the batch outcome.

```apex
// In the Batch Apex finish() method
LoanBatchComplete__e evt = new LoanBatchComplete__e(
    BatchId__c = jobId,
    ProcessedCount__c = scope.size(),
    ApprovedCount__c = approvedCount,
    RejectedCount__c = rejectedCount
);
Database.SaveResult sr = EventBus.publish(evt);
if (!sr.isSuccess()) {
    // Log failure — subscribers will not receive this batch signal
    System.debug('Event publish failed: ' + sr.getErrors());
}
```

The external notification service subscribes via the Pub/Sub API to `/event/LoanBatchComplete__e` and triggers its SMS dispatch workflow on receipt.

**Why it works:** Platform Events are the correct mechanism when the event represents an application-level milestone that is not a direct consequence of a single DML operation. The publisher is in full control of the event schema and timing. CDC cannot express this pattern because there is no single sObject whose state change represents "batch complete."

---

## Example 3: Legacy SOAP Integration Assessment — When Outbound Messages Are the Only Option

**Context:** A utility company has a legacy billing system that exposes a SOAP endpoint. When a Salesforce Account's billing status changes, the billing system must be notified via SOAP. The billing system vendor has no plans to expose a REST or event subscription endpoint. A Workflow Rule with an Outbound Message was implemented five years ago and is in production.

**Problem:** The team is evaluating whether to migrate the Outbound Message to Platform Events. The billing system cannot be changed. Any replacement must still deliver SOAP to the existing endpoint.

**Solution:**

Assess whether migration is justified using the decision matrix:
- The receiver requires SOAP — Platform Events alone cannot satisfy this without a middleware translation layer.
- The trigger is a Workflow Rule that is already working and cannot be replaced with a new Workflow Rule in orgs created after Spring '25.
- No enhanced payload or replay is required.

**Decision: maintain the existing Outbound Message.** If the org was created before the Workflow Rules restriction, the existing rule continues to work. If migration is eventually required (e.g., due to org migration), the correct target architecture is: Flow (replaces the Workflow Rule trigger) → publishes a Platform Event → Apex subscriber → makes a SOAP callout to the billing system using a Named Credential.

**Why it works:** Outbound Messages remain the correct choice when the receiver is a SOAP-only system and no middleware translation layer exists. The decision matrix correctly routes this scenario to Outbound Messages rather than forcing a more complex architecture where none of the event-native mechanisms can fulfill the delivery requirement.

---

## Anti-Pattern: Using PushTopic for External System Sync

**What practitioners do:** An external integration team builds a PushTopic subscription on Account to stream Account changes to an external data warehouse. They use CometD long-polling from a middleware process and store the `replayId` for recovery.

**What goes wrong:**
- The 24-hour retention window is insufficient for weekend outages or maintenance windows. Events lost during a 30-hour maintenance window cannot be replayed.
- The PushTopic SOQL SELECT limits which fields appear in the payload — when new Account fields are added, the PushTopic must be updated manually.
- The 50,000 events/day limit is hit during bulk data migration projects, silently dropping events with no backpressure signal to the publisher.

**Correct approach:** Use Change Data Capture for Account synchronization to external systems. CDC provides 72-hour retention, automatic field-delta tracking with `changedFields`, and a higher throughput ceiling. The Pub/Sub API subscriber is the same gRPC-based consumer used for Platform Events, so the migration cost is primarily the subscriber-side channel change (from `/topic/` to `/data/AccountChangeEvent`).
