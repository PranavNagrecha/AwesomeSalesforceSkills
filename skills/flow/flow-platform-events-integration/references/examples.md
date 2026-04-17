# Flow Platform Events Integration — Worked Examples

## Example 1: Record-Change Event With Publish-After-Commit

**Context:** When an Opportunity is Won, notify three downstream systems: a fulfillment flow, a billing Apex trigger, and an analytics pipeline via Pub/Sub API. The event must not fire if the save rolls back (e.g., a validation rule on a related record fails).

**Event definition:** `Opportunity_Won__e` (High-Volume).

Custom fields on the event:
- `opportunityId__c` (Text 18)
- `accountId__c` (Text 18)
- `amount__c` (Currency)
- `closedAt__c` (DateTime)

**Publisher Flow:**

Name: `Publish_Opportunity_Won`
Type: Record-Triggered, After-Save, on Opportunity
Entry condition: `ISCHANGED(StageName) AND StageName = 'Closed Won'`

Step-by-step elements:

1. **Start element** — Object: Opportunity. Trigger: A record is created or updated. Run: After the record is saved. Entry criteria: condition logic as above.
2. **Decision `Is_Amount_Positive`** — branches on `$Record.Amount > 0`. True branch continues; False branch routes to a `Create Records` that writes a data-quality warning to `Data_Quality_Log__c`.
3. **Create Records element `Publish_Event`** — Object: `Opportunity_Won__e`. Field mapping:
   - `opportunityId__c` ← `$Record.Id`
   - `accountId__c` ← `$Record.AccountId`
   - `amount__c` ← `$Record.Amount`
   - `closedAt__c` ← `$Record.CloseDate`
4. **Fault Path on `Publish_Event`** — routes to `Create Records` on `Platform_Event_Publish_Error__c` with error text from `$Flow.FaultMessage`.

**Why publish-after-commit:** Because this publisher is After-Save on a record-triggered flow, the event is buffered until the Opportunity DML commits. If a downstream Apex trigger throws and rolls back the save, the `Opportunity_Won__e` message is discarded. No downstream system acts on a "Won" that did not actually commit.

**Verification:**
- Update an Opportunity to `Closed Won`. Confirm an event delivery shows in the Event Monitoring or in subscriber logs.
- Set a validation rule to block `Closed Won` and try to save. Confirm NO event is delivered (the save failed).

**Bulk behavior:** bulk-update 200 Opportunities to `Closed Won`. Confirm 200 events are published as ONE batched DML (Flow aggregates the Create Records). The publisher counts 1 DML statement against the 150 transaction limit regardless of the 200-event payload.

---

## Example 2: Platform-Event-Triggered Subscriber With Idempotency

**Context:** A subscriber flow creates a `Fulfillment_Request__c` record for every `Opportunity_Won__e` event. Because delivery is at-least-once, a duplicate event must not create two fulfillment requests.

**Subscriber Flow:**

Name: `Fulfill_Opportunity_Won`
Type: Platform-Event-Triggered on `Opportunity_Won__e`
Run-as: Automated Process User (default; acceptable here because Fulfillment_Request__c has OWD Public Read/Write)

Step-by-step elements:

1. **Start element** — Object: `Opportunity_Won__e`. Entry conditions: none (process all deliveries).
2. **Get Records `Find_Existing_Request`** — Object: `Fulfillment_Request__c`. Filter: `Source_Opportunity_Id__c = {!$Record.opportunityId__c} AND Source_Closed_At__c = {!$Record.closedAt__c}`. Sort: CreatedDate DESC. Return: only first record.
3. **Decision `Exists?`** — branches on whether `Find_Existing_Request` returned a record.
4. **True branch (duplicate)** — `Create Records` on `Platform_Event_Duplicate_Log__c` for observability; end.
5. **False branch (new)** — `Create Records` on `Fulfillment_Request__c`:
   - `Source_Opportunity_Id__c` ← `$Record.opportunityId__c`
   - `Source_Closed_At__c` ← `$Record.closedAt__c`
   - `Amount__c` ← `$Record.amount__c`
   - `Status__c` ← `'Pending'`
6. **Fault Path** on Create Records — writes `PE_Subscriber_Error_Log__c` row with `$Flow.FaultMessage` and the event payload.

**Idempotency contract:**
- Uniqueness derived from `(opportunityId, closedAt)`. Even if the subscriber runs twice, the second run finds the existing request and exits.
- To make this robust against concurrent duplicate events, add a unique external-id index on `Source_Opportunity_Id__c` (unique across the org). Then a concurrent duplicate Create Records fails with a DUPLICATE_VALUE error that the fault path catches.

**Bulk behavior:** the platform may batch up to 2,000 events into one flow invocation. The flow receives `$Record` as a COLLECTION of events. The Get Records filter should be reworked to `Source_Opportunity_Id__c IN :{!allOpportunityIdsFromBatch}` for bulk-safety:

```text
[Start: PE-Triggered on Opportunity_Won__e]
  └── [Assignment: collect allOpportunityIds, allClosedAts from $Record batch]
  └── [Get Records: Fulfillment_Request__c WHERE Source_Opportunity_Id__c IN :allOpportunityIds]
  └── [Loop over $Record batch]
        └── [Find matching Fulfillment_Request__c in in-memory collection]
        └── [Decision: matched?]
              ├── Yes → skip
              └── No  → [Assignment: add new request to createList]
  └── [Create Records: createList]  // one DML for the whole batch
```

This keeps SOQL at 1 and DML at 1 per batch regardless of batch size.

---

## Example 3: Cross-Org Integration via High-Volume PE and Pub/Sub API

**Context:** An org publishes `Order_Placed__e` (High-Volume). A MuleSoft integration consumes via Pub/Sub API and forwards to a Kafka topic. Expected rate: 50,000 events/hour.

**Publisher Flow:**

Name: `Publish_Order_Placed`
Type: Record-Triggered, After-Save on Order__c
Entry condition: `Status = 'Submitted' AND ISCHANGED(Status)`

Elements:

1. **Start element** — Object: Order__c, After-Save, conditions above.
2. **Create Records `Publish`** — Object: `Order_Placed__e`. Fields from `$Record`.
3. **Fault Path** — writes to `Integration_Error_Log__c` with details.

**External Consumer (MuleSoft):**

Subscribes via Pub/Sub API:
- Topic: `/event/Order_Placed__e`
- Starting point: `LATEST` for normal operation, `replayId` on reconnect
- Durability: 72 hours; if MuleSoft is down > 72 hours, events are lost

**Why High-Volume:**
- 50,000 events/hour exceeds Standard-Volume allocation.
- External consumers need replayId durability to recover from network outages.
- No publish-after-commit ordering between Standard and High volumes; for this use case, internal Salesforce subscribers (if any) should tolerate that.

**Internal flow subscriber (optional, for analytics):**

Name: `Analytics_Snapshot_Order_Placed`
Type: Platform-Event-Triggered on `Order_Placed__e`
Run-as: dedicated integration user with FLS on the analytics object.
Elements:
1. Loop over `$Record` batch (up to 2,000 events).
2. Build a collection of `Analytics_Snapshot__c` records in memory.
3. One Create Records DML at the end.
4. Fault path to error log.

**Monitoring:**
- Platform Event Usage report in Setup.
- Event Monitoring on the publish/subscribe events.
- MuleSoft-side: replayId checkpointing to track progress.

---

## Example 4: Using Platform Events to Break a Transaction Boundary

**Context:** A Screen Flow needs to send an external email as part of a save, but external HTTP callouts cannot be called synchronously with DML. The team wants the user to see "Submitted — email sent" feedback.

**Pattern:** Publish a Platform Event at the end of the screen flow; a PE-triggered flow (or Apex subscriber) makes the callout. Use publish-after-commit for correctness.

**Screen Flow `Submit_Request`:**

1. Screen — collect input.
2. Create Records — `Request__c` new row.
3. Create Records — `Request_Submitted__e` with `requestId__c`, `userEmail__c`.
4. Screen — "Submitted! Email will arrive within 2 minutes."

**Subscriber Flow `Send_Request_Email`:**

Type: Platform-Event-Triggered on `Request_Submitted__e`.
1. Invocable Apex `SendEmailViaExternalService` with the event payload.
2. Fault path → `Integration_Error_Log__c`.

**Why this works:**
- The Create Records publish counts 1 DML in the user's transaction; after-commit semantics mean the event is buffered and delivered only if the save commits.
- The subscriber flow runs in its own async transaction, with no DML constraint conflict with the callout.
- If the callout fails, the publisher is unaffected; the error log captures the failure for retry.

**Gotcha:** the user UX shows "email will arrive" but the email may never arrive if the callout fails. Pair the pattern with:
- A scheduled sweep flow that re-publishes events from the error log after a delay.
- An admin notification for persistent failures.

Never claim "done" in the UI for work that is actually pending in async.
