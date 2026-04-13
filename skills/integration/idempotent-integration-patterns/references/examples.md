# Examples — Idempotent Integration Patterns

## Example 1: Fixing Duplicate Records from a Retrying ETL Integration

**Context:** An ETL tool syncs Order records from an ERP into Salesforce. On network timeouts, the ETL retries the POST call to create the Order. Each retry creates a duplicate Order record in Salesforce because POST creates new records unconditionally.

**Problem:** The ETL generates a UUID for each sync request, but generates a new UUID on each retry. Each retry looks like a unique operation to both the ETL and Salesforce. After 3 retries, 4 identical Order records exist in Salesforce.

**Solution:**

1. Create a custom field on Order: `ERP_Order_Number__c` (type: Text, External ID: true, Unique: true).
2. Update the ETL to populate this field with the ERP's stable order number (e.g., `ORD-2025-0012345`) — the same value on every attempt for the same order.
3. Change the ETL's API call from POST to PATCH with the External ID path:
```
PATCH /services/data/v63.0/sobjects/Order/ERP_Order_Number__c/ORD-2025-0012345
Content-Type: application/json
{
  "Status": "Pending",
  "ERP_Order_Number__c": "ORD-2025-0012345",
  "Amount": 5200.00
}
```
4. First attempt: record does not exist → Salesforce inserts the Order.
5. Retry attempt: record exists with same external ID → Salesforce updates (no-op for unchanged fields).
6. No duplicate records. All retries produce the same result.

**Why it works:** External ID upsert is inherently idempotent — 0 matches inserts, 1 match updates. The External ID field's UNIQUE constraint ensures 2+ match conditions cannot exist if the field is properly maintained.

---

## Example 2: Platform Event Publish Immediately Delivering Orphan Events

**Context:** An Apex trigger on Opportunity publishes a `DealClosed__e` Platform Event when an Opportunity reaches "Closed Won." Downstream subscribers process the event to trigger customer onboarding workflows. Occasionally, customers report being contacted for onboarding on deals that the sales team says were not actually closed — they were closed by mistake and then rolled back.

**Problem:** The Apex trigger uses `EventBus.publish()` with the default Publish Immediately setting. The event is published as soon as the trigger runs. If a subsequent trigger or validation on the same transaction fails and the transaction rolls back, the event has already been delivered to subscribers. The Opportunity was never actually saved as Closed Won, but the subscriber processed the onboarding workflow.

**Solution:**

Change all `DealClosed__e` publishes to use Publish After Commit:

```apex
// Before (Publish Immediately — risky)
trigger OpportunityTrigger on Opportunity (after update) {
    for (Opportunity opp : Trigger.new) {
        if (opp.StageName == 'Closed Won') {
            EventBus.publish(new DealClosed__e(
                OpportunityId__c = opp.Id,
                AccountId__c = opp.AccountId
            ));
        }
    }
}

// After (Publish After Commit — safe)
trigger OpportunityTrigger on Opportunity (after update) {
    List<DealClosed__e> events = new List<DealClosed__e>();
    for (Opportunity opp : Trigger.new) {
        if (opp.StageName == 'Closed Won') {
            events.add(new DealClosed__e(
                OpportunityId__c = opp.Id,
                AccountId__c = opp.AccountId,
                PublishBehavior = 'PublishAfterCommit'
            ));
        }
    }
    EventBus.publish(events);
}
```

**Why it works:** Publish After Commit holds the event until the DML transaction fully commits. If the transaction rolls back for any reason, the event is discarded — no subscriber receives it.

---

## Anti-Pattern: Generating a New Idempotency Key on Each Retry

**What practitioners do:** A middleware integration generates a UUID for each API call attempt:

```python
# Wrong — new UUID per retry
for attempt in range(1, max_retries + 1):
    idempotency_key = str(uuid.uuid4())  # New UUID every time
    headers = {"X-Idempotency-Key": idempotency_key}
    response = requests.post(salesforce_url, headers=headers, json=payload)
    if response.ok:
        break
```

**What goes wrong:** Each retry sends a different `X-Idempotency-Key`. Salesforce's idempotency log treats each key as a unique operation. Every retry that succeeds creates another record. After 3 retries, 3 records exist.

**Correct approach:** Generate the idempotency key once before the first attempt and reuse it for all retries:

```python
# Correct — key generated once before all retries
idempotency_key = str(uuid.uuid4())  # Generated once

for attempt in range(1, max_retries + 1):
    headers = {"X-Idempotency-Key": idempotency_key}  # Same key every retry
    response = requests.post(salesforce_url, headers=headers, json=payload)
    if response.ok:
        break
    time.sleep(2 ** attempt)  # Exponential backoff
```

The server-side idempotency log finds the same key on every retry and returns the prior result without creating additional records.
