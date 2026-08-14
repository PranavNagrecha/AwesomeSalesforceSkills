# Examples — Cross-Cloud Data Deployment

## Example 1: A change-event subscriber sized for the real batch

**Context:** Service Cloud is the system of record for `Case`. A downstream cloud needs to react when the case owner or
priority changes, and the flow is carried by Change Data Capture.

**Problem:** The subscriber gets written like a record trigger — a query per event, a callout per event — because the
author's mental model of "batch" is 200. For change events it is not: "The Apex trigger batch size for platform events
and Change Data Capture events is 2,000." One SOQL per event exhausts the 100-query synchronous limit at event 101,
five percent into the batch. The trigger passes every test written against a handful of events and fails on the first
bulk update in the publishing cloud.

**Solution:** Filter on the header's `changedFields`, collect ids, query once, and hand the expensive work to a
separate transaction.

```apex
trigger CaseChangeEventTrigger on CaseChangeEvent (after insert) {
    Set<Id> recordIds = new Set<Id>();

    for (CaseChangeEvent event : Trigger.new) {
        EventBus.ChangeEventHeader header = event.ChangeEventHeader;

        // Only react to the fields this integration contracted for. A change event
        // carries the fields that changed — it does not carry a before-image, so
        // value comparison cannot tell you whether the field you care about moved.
        // changedFields is empty for operations other than update, including creation.
        Set<String> changed = new Set<String>(header.changedFields);
        if (!changed.contains('OwnerId') && !changed.contains('Priority')) {
            continue;
        }

        // One event can carry several record ids.
        for (String recordId : header.recordIds) {
            recordIds.add((Id) recordId);
        }
    }

    if (recordIds.isEmpty()) {
        return;
    }

    // One query for the whole batch of up to 2,000 events.
    List<Case> cases = [SELECT Id, CaseNumber, OwnerId, Priority FROM Case WHERE Id IN :recordIds WITH USER_MODE];

    // Callouts and heavy work move to a fresh transaction with its own limits.
    System.enqueueJob(new CrossCloudCaseSyncQueueable(cases));
}
```

**Why it works:** The per-event work is now bounded arithmetic — set membership and id collection — and the two
expensive operations happen once per batch rather than once per event. `changedFields` is available "in Apex saved
using API version 47.0 or later", so the trigger's `.trigger-meta.xml` version is part of the contract, not an
incidental detail. Handing the callout to a Queueable also removes the subscriber from the org's long-running
inbound request pool, which is capped at 25 concurrent requests of 20 seconds or longer.

---

## Example 2: A system-of-record matrix that survives contact with the pipeline

**Context:** Four clouds touch the same customer. Every team believes it owns the email address.

**Problem:** "Who owns this field" gets settled verbally in a workshop and then re-litigated every time a sync
overwrites something. Without a written matrix, the integration is designed around whichever direction was built first,
and the deployment order for shared keys is discovered when an upsert fails.

**Solution:** Write ownership down per field, with the propagation mechanism and the deployment order attached — the
document is the input to the pipeline, not a summary of it.

```yaml
# docs/architecture/cross-cloud-sor.yaml
entity: Customer
shared_key:
  field: Global_Customer_Id__c
  type: Text(64)
  external_id: true
  unique: true
  note: >-
    Present on every cross-cloud object so every write can be an upsert.
    Deploy this field to ALL clouds before any integration is enabled —
    an upsert against a key that does not yet exist in the target is an insert.

fields:
  - name: Email
    system_of_record: service-cloud
    propagates_to: [marketing, data-360]
    mechanism: cdc                       # CaseChangeEvent / ContactChangeEvent
    subscriber_batch_size: 2000          # NOT 200 — size the subscriber for this
    filter: changedFields contains Email

  - name: Lifetime_Value__c
    system_of_record: data-360
    propagates_to: [sales-cloud]
    mechanism: activation
    note: Derived, never written by a human. Read-only in every other cloud.

  - name: Marketing_Consent__c
    system_of_record: marketing
    propagates_to: [service-cloud, sales-cloud]
    mechanism: platform-event            # a domain event, not a field sync
    note: >-
      Consent is a business decision with an audit requirement, so it moves as a
      named event carrying who/when, not as a field-level CRUD replication.

deployment_order:
  - shared-key fields to every cloud
  - CustomerDataPlatformSettings         # org-level Data 360 switch
  - DataConnector / DataConnectorIngestApi
  - data kit (DataPackageKitDefinition + kit objects)
  - ActivationPlatform targets
  - enable CDC channels and subscribers
smoke_test:
  - create one record in service-cloud
  - assert arrival in data-360 within the agreed window
  - assert activation reaches marketing
```

**Why it works:** Each row forces the two decisions that actually matter — who writes, and by what mechanism — and the
`mechanism` column makes the CDC-versus-event choice explicit per field rather than per project. The
`deployment_order` block encodes a real dependency: in the Metadata API, Data 360 org settings, connectors
(`DataConnector`, `DataConnectorS3`, `DataConnectorIngestApi`) and the data kit are separate deployables, so a kit that
lands before its connector produces objects that never ingest.

---

## Anti-Pattern: Replicating every field change and calling it integration

**What practitioners do:** Enable CDC on the object, subscribe, and write every changed field through to every other
cloud, on the theory that keeping everything identical everywhere is the safe default.

**What goes wrong:** Three costs, all deferred. Volume: a bulk update publishes batches of up to 2,000 events into a
subscriber sized for far less. Semantics: a field-level CRUD replica cannot express *why* something changed, so the
receiving cloud cannot distinguish a correction from a business decision — which is fatal for anything with an audit
requirement, like consent. Ownership: with everything flowing everywhere, there is no system of record, so the last
writer wins and the winner varies by timing.

**Correct approach:** Replicate the minimum, and promote anything with business meaning to a named event.

```apex
// Field-level replication — for fields whose only meaning is "the current value"
if (changed.contains('MailingCity')) { syncAddress(recordIds); }

// Domain event — for anything a human decided and an auditor may ask about
EventBus.publish(new Marketing_Consent_Changed__e(
    Global_Customer_Id__c = customer.Global_Customer_Id__c,
    Consent_Granted__c    = true,
    Source_System__c      = 'marketing',
    Decided_At__c         = System.now()
));
```

The test is simple: if the receiving cloud needs to know *why* the value changed, it is an event. If it only needs the
current value, it is replication — and it should carry a `changedFields` filter so it fires only for the fields that
integration actually contracted for.
