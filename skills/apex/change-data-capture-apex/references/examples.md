# Examples — Change Data Capture Apex

## Example 1: Selective UPDATE Handler — React Only When SLA Fields Change

**Context:** A support team tracks SLA compliance on Case records. An Apex trigger must fire downstream logic only when `SLAExpirationDate__c` or `Priority` changes on an existing Case — not on every save.

**Problem:** Without field-level filtering, the trigger fires and executes expensive SOQL and callout-dispatching logic on every Case update, including UI saves that touch unrelated fields like `Description`. This burns governor limits and floods the downstream system with unnecessary signals.

**Solution:**

```apex
trigger CaseChangeEventTrigger on CaseChangeEvent (after insert) {
    Set<Id> slaAffectedCases = new Set<Id>();

    for (CaseChangeEvent event : Trigger.new) {
        EventBus.ChangeEventHeader header = event.ChangeEventHeader;

        // Only react to UPDATE events
        if (header.changeType != 'UPDATE') {
            continue;
        }

        // React only when SLA-relevant fields changed
        List<String> changed = header.changedFields;
        if (changed.contains('SLAExpirationDate__c') || changed.contains('Priority')) {
            slaAffectedCases.addAll((List<Id>) header.getRecordIds());
        }
    }

    if (slaAffectedCases.isEmpty()) {
        return;
    }

    // Query current state — do NOT read field values from event body for UPDATE
    List<Case> cases = [
        SELECT Id, Priority, SLAExpirationDate__c, OwnerId, Status
        FROM Case
        WHERE Id IN :slaAffectedCases
    ];

    SLAComplianceHandler.evaluate(cases);
}
```

**Why it works:** `header.changedFields` is a list of API field names that changed in the update. Checking membership before collecting record IDs means the trigger dispatches no-ops for irrelevant saves. All SOQL happens outside the event loop using the collected Set — this keeps the trigger within the 100-SOQL governor limit even with a full 2,000-event batch.

---

## Example 2: Full Change-Type Router with GAP Event Recovery

**Context:** An integration layer must keep a downstream inventory system synchronized with Salesforce `Product2` records. All operations — create, update, delete, undelete, and gap events — must be handled distinctly.

**Problem:** A naive trigger that only handles `UPDATE` misses creates, deletes, and undeletes, causing the inventory system to drift. Gap events (caused by bulk data loads that bypass the application server) are silently ignored, leaving records stale in the downstream system.

**Solution:**

```apex
trigger Product2ChangeEventTrigger on Product2ChangeEvent (after insert) {
    Set<Id> createdIds   = new Set<Id>();
    Set<Id> updatedIds   = new Set<Id>();
    Set<Id> deletedIds   = new Set<Id>();
    Set<Id> undeletedIds = new Set<Id>();
    Set<Id> gapIds       = new Set<Id>();

    for (Product2ChangeEvent event : Trigger.new) {
        EventBus.ChangeEventHeader header = event.ChangeEventHeader;
        // getRecordIds() returns List<String>; multiple IDs can appear when events are merged
        List<Id> ids = (List<Id>) header.getRecordIds();

        String changeType = header.changeType;

        if (changeType == 'CREATE') {
            createdIds.addAll(ids);
        } else if (changeType == 'UPDATE') {
            updatedIds.addAll(ids);
        } else if (changeType == 'DELETE') {
            // Record is deleted — do not SOQL without ALL ROWS
            deletedIds.addAll(ids);
        } else if (changeType == 'UNDELETE') {
            undeletedIds.addAll(ids);
        } else if (changeType.startsWith('GAP_')) {
            // Gap event: no field data — mark all IDs for re-fetch
            gapIds.addAll(ids);
        }
    }

    // CREATE / UNDELETE: fetch full record and push to integration
    Set<Id> fetchIds = new Set<Id>(createdIds);
    fetchIds.addAll(updatedIds);
    fetchIds.addAll(undeletedIds);
    fetchIds.addAll(gapIds); // re-fetch gap IDs for full state

    if (!fetchIds.isEmpty()) {
        List<Product2> products = [
            SELECT Id, Name, ProductCode, IsActive, Description, Family
            FROM Product2
            WHERE Id IN :fetchIds
        ];
        InventorySyncQueueable.enqueue('UPSERT', products);
    }

    if (!deletedIds.isEmpty()) {
        InventorySyncQueueable.enqueue('DELETE', deletedIds);
    }
}
```

```apex
// Queueable for callout dispatch (CDC trigger body cannot do synchronous callouts)
public class InventorySyncQueueable implements Queueable, Database.AllowsCallouts {
    private String operation;
    private List<Id> ids;
    private List<Product2> records;

    public static void enqueue(String op, List<Product2> recs) {
        System.enqueueJob(new InventorySyncQueueable(op, recs));
    }

    public static void enqueue(String op, Set<Id> idsToDelete) {
        System.enqueueJob(new InventorySyncQueueable(op, new List<Id>(idsToDelete)));
    }

    // ... constructor and execute() with HTTP callout
    public void execute(QueueableContext ctx) {
        // perform callout to external inventory API
    }
}
```

**Why it works:** Each change type routes to the correct downstream action. Gap events fall through to a re-fetch rather than being dropped — this is the correct recovery strategy since gap events carry no field data. Callouts are dispatched to a `Queueable` with `Database.AllowsCallouts`, sidestepping the restriction on synchronous callouts from CDC trigger context.

---

## Anti-Pattern: Reading Event Field Values Directly for UPDATE Events

**What practitioners do:** After an Account update, they read `event.BillingCity` directly from the event body, assuming it holds the current field value.

```apex
// WRONG — do not do this for UPDATE events
trigger AccountChangeEventTrigger on AccountChangeEvent (after insert) {
    for (AccountChangeEvent event : Trigger.new) {
        if (event.ChangeEventHeader.changeType == 'UPDATE') {
            // BillingCity will be null if it was NOT the field that changed
            String city = event.BillingCity; // UNSAFE — may be null
            if (city != null) {
                // process city — but this silently skips updates that didn't touch BillingCity
            }
        }
    }
}
```

**What goes wrong:** For UPDATE events, unchanged fields are null in the Apex change event message. If `BillingCity` was not part of the update, `event.BillingCity` is null — not the current stored value. The code above silently skips every update that does not modify `BillingCity`, and would also misinterpret a legitimate null-set as "unchanged."

**Correct approach:** Use `header.changedFields` to identify what changed, then issue a SOQL query for full current field state:

```apex
trigger AccountChangeEventTrigger on AccountChangeEvent (after insert) {
    Set<Id> updatedIds = new Set<Id>();
    for (AccountChangeEvent event : Trigger.new) {
        EventBus.ChangeEventHeader header = event.ChangeEventHeader;
        if (header.changeType == 'UPDATE' && header.changedFields.contains('BillingCity')) {
            updatedIds.addAll((List<Id>) header.getRecordIds());
        }
    }
    if (!updatedIds.isEmpty()) {
        List<Account> accounts = [SELECT Id, BillingCity FROM Account WHERE Id IN :updatedIds];
        // process accounts with reliable current values
    }
}
```

---

## Example 3: Reading a Real Event Payload and Deriving the Dedupe Key From It

**Context:** A team is about to build an idempotent subscriber and needs to see what the header
actually carries before choosing a key. This is the Object Reference's own change event message for a
new Account (`object_reference` L5178–5203), unmodified except for the redacted ids it ships with.

```json
{
  "schema": "IeRuaY6cbI_HsV8Rv1Mc5g",
  "payload": {
    "ChangeEventHeader": {
      "entityName": "Account",
      "recordIds": ["<record_ID>"],
      "changeType": "CREATE",
      "changeOrigin": "com/salesforce/api/soap/51.0;client=SfdcInternalAPI/",
      "transactionKey": "0002343d-9d90-e395-ed20-cf416ba652ad",
      "sequenceNumber": 1,
      "commitTimestamp": 1612912679000,
      "commitNumber": 10716283339728,
      "commitUser": "<User_ID>"
    },
    "Name": "Acme",
    "Description": "Everyone is talking about the cloud. But what does it mean?",
    "OwnerId": "<Owner_ID>",
    "CreatedDate": "2021-02-09T23:17:59Z",
    "CreatedById": "<User_ID>",
    "LastModifiedDate": "2021-02-09T23:17:59Z",
    "LastModifiedById": "<User_ID>"
  },
  "event": { "replayId": 6 }
}
```

**Problem:** Three of those fields look like idempotency keys and only one combination is one.

| Candidate | Value here | Verdict |
|---|---|---|
| `transactionKey` alone | `0002343d-9d90-e395-ed20-cf416ba652ad` | **No.** Identifies the transaction, not the change. A lead conversion emits four events under one key (`apexrefguide` L157429–157436) |
| `commitNumber` | `10716283339728` | **No.** "Not guaranteed to be unique in Salesforce — it is unique only in a single database instance"; may stop being sequential after an instance migration (`apexrefguide` L157306–157310). Diagnostics only |
| `commitTimestamp` | `1612912679000` | **No.** Milliseconds, and merged events share one. Useful for ordering and for a `Datetime.newInstance(...)` audit column, not for identity |
| `replayId` | `6` | **No.** It lives in `event`, outside `ChangeEventHeader`, and is the streaming-transport cursor — an Apex trigger never sees it |
| `transactionKey` + `sequenceNumber` | `0002343d-…-cf416ba652ad:1` | **Yes.** Transaction plus the change's position within it (`apexrefguide` L157420–157441) |

**Solution:** derive the key in one expression and store it behind a unique External Id.

```apex
String dedupeKey = header.transactionKey + ':' + String.valueOf(header.sequenceNumber);
```

**Why it works:** the pair is stable across redelivery of the same event and distinct across the four
events of one lead conversion. The unique index on `Change_Event_Receipt__c.Dedupe_Key__c`
(`references/code-examples.md` Artifact 5) turns a concurrent replay into a rejected row rather than a
duplicated downstream effect.

**What the payload also shows:** `changeOrigin` here is `com/salesforce/api/soap/51.0;client=SfdcInternalAPI/`
— the `soap` half is the API category, the `client=` half is the only part that identifies an
application, and it is present only because that caller set the Call Options header
(`apexrefguide` L157245–157275). And note what is *absent* from the payload: no `IsDeleted`, no
`SystemModStamp`, no formula fields (`object_reference` L5157–5163).
