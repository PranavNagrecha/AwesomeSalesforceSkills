# Examples — Platform Event Schema Evolution

## Example 1: Adding an optional field to a live event

**Context:** `Order_Created__e` is published by checkout (Apex) and consumed by 4 Apex triggers + 2 external Pub/Sub clients (warehouse, BI). Product wants to attach `Discount_Code__c` so BI can attribute campaigns.

**Problem:** Six subscribers must keep working through the change.

**Solution:**

```text
1. Deploy a new optional field Discount_Code__c on Order_Created__e.
   - Compatibility: SAFE (additive, optional).
   - Apex subscribers ignore unknown fields automatically.
   - Pub/Sub clients receive a new schema ID. As long as they call
     GetSchema for unknown IDs, they decode the new field; otherwise
     they ignore it and read the fields they expected.

2. Publishers update to populate the field where present.
3. BI subscriber switches to read the field.
4. No v2 event needed.
```

**Why it works:** Salesforce Platform Events apply additive changes without forcing a version bump. The schema-cache discipline at the Pub/Sub client is the only consumer-side requirement.

---

## Example 2: Dual-publish for a breaking rename

**Context:** Field `Customer_Id__c` on `Order_Created__e` is being renamed to `Account_Number__c` (with a string-format change too). Subscribers include three external services on different deploy cadences.

**Problem:** No single maintenance window can update all subscribers atomically.

**Solution:**

```text
1. Create Order_Created_v2__e with Account_Number__c (correct shape).
2. Update Apex publishers to publish to BOTH v1 and v2 in the same
   transaction:

   EventBus.publish(new List<SObject>{
       new Order_Created__e(Customer_Id__c = oldId),
       new Order_Created_v2__e(Account_Number__c = newId)
   });

3. Migrate subscribers from v1 to v2 on their own cadence. Each owner
   is responsible for their migration. Operations team tracks via
   subscriber-count signal.

4. After all subscribers report v2-only, drop v1 publishing.
5. Retire Order_Created__e (delete the event) after a final 72h drain
   of replay traffic.
```

**Why it works:** Dual-publish decouples publisher and subscriber timing. Each external team migrates when ready; no global maintenance window required.

---

## Anti-Pattern: in-place rename "because nobody important reads it"

**What practitioners do:** Rename `Customer_Id__c` to `Account_Number__c` on the live event, deploy, and assume nothing important breaks.

**What goes wrong:** The "nothing important" subscriber turns out to be the warehouse export, which had been silently dropping the field for two days before someone notices the inventory data is stale. By then, two days of Order_Created events are unreplayable correctly.

**Correct approach:** No rename of a published field. Always v2-and-dual-publish, or stop-reading → drain → stop-publishing → delete (if you control all subscribers and have at least 72h of patience between steps).
