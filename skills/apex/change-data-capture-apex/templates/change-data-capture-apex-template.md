# Change Data Capture Apex — Work Template

Use this template when designing or implementing a CDC Apex trigger subscriber.

---

## Scope

**Skill:** `apex/change-data-capture-apex`

**Request summary:** (fill in what the user asked for — e.g., "handle Account changes to sync billing address to external ERP")

---

## Context Gathered

Answer these before writing any code:

- **Object(s) to track:** ___
- **Object enabled in Setup > Change Data Capture?** Yes / No / Pending
- **Custom object API name (if applicable):** e.g., `MyObject__ChangeEvent`
- **Change types required:** CREATE / UPDATE / DELETE / UNDELETE (circle all that apply)
- **Field-level filtering needed for UPDATE?** Yes / No — if yes, list fields: ___
- **Downstream action:** Internal Salesforce DML / Queueable / @future callout / other: ___
- **Known limits concern:** e.g., high daily event volume, large batch sizes, > 5 tracked entities

---

## Entity Tracking Verification

- [ ] Object confirmed enabled in Setup > Integrations > Change Data Capture
- [ ] Entity count confirmed within the 5-object default limit (or CDC add-on licensed)
- [ ] Debug trace flag set for Automated Process entity before testing

---

## Trigger Design

**Change event type:** `___ChangeEvent` (standard) or `___ChangeEvent` (custom: `ObjectName__ChangeEvent`)

**Trigger name:** `___ChangeEventTrigger`

**Change types to handle:**

| changeType | Business logic |
|---|---|
| CREATE | ___ |
| UPDATE | ___ (fields: ___) |
| DELETE | ___ |
| UNDELETE | ___ |
| GAP_* | Re-fetch record from SOQL / mark dirty / ___  |

---

## Skeleton (copy and fill in)

```apex
trigger ___ChangeEventTrigger on ___ChangeEvent (after insert) {
    Set<Id> createdIds   = new Set<Id>();
    Set<Id> updatedIds   = new Set<Id>();
    Set<Id> deletedIds   = new Set<Id>();
    Set<Id> undeletedIds = new Set<Id>();
    Set<Id> gapIds       = new Set<Id>();

    for (___ChangeEvent event : Trigger.new) {
        EventBus.ChangeEventHeader header = event.ChangeEventHeader;
        List<Id> ids = (List<Id>) header.getRecordIds();

        if (header.changeType == 'CREATE') {
            createdIds.addAll(ids);
        } else if (header.changeType == 'UPDATE') {
            // Field filter (if applicable):
            // if (header.changedFields.contains('___')) { updatedIds.addAll(ids); }
            updatedIds.addAll(ids);
        } else if (header.changeType == 'DELETE') {
            deletedIds.addAll(ids);
        } else if (header.changeType == 'UNDELETE') {
            undeletedIds.addAll(ids);
        } else if (header.changeType.startsWith('GAP_')) {
            gapIds.addAll(ids);
        }
    }

    // --- Process creates ---
    if (!createdIds.isEmpty()) {
        List<___> records = [SELECT Id, ___ FROM ___ WHERE Id IN :createdIds];
        // TODO: handler
    }

    // --- Process updates (query for full current state) ---
    if (!updatedIds.isEmpty()) {
        List<___> records = [SELECT Id, ___ FROM ___ WHERE Id IN :updatedIds];
        // TODO: handler
    }

    // --- Process deletes (do NOT query — record is gone) ---
    if (!deletedIds.isEmpty()) {
        // TODO: downstream delete notification using IDs only
    }

    // --- Process undeletes ---
    if (!undeletedIds.isEmpty()) {
        List<___> records = [SELECT Id, ___ FROM ___ WHERE Id IN :undeletedIds];
        // TODO: handler
    }

    // --- Process gap events (re-fetch all affected records) ---
    if (!gapIds.isEmpty()) {
        List<___> records = [SELECT Id, ___ FROM ___ WHERE Id IN :gapIds];
        // TODO: reconcile with downstream system
    }
}
```

---

## Checklist

- [ ] Trigger declared as `after insert` on the change event type (not the base sObject)
- [ ] Object enabled in Change Data Capture Setup before deploying
- [ ] All five change-type branches present (CREATE, UPDATE, DELETE, UNDELETE, GAP_*)
- [ ] changedFields filter applied for UPDATE where field-level filtering is needed
- [ ] SOQL and DML are outside the event loop — bulk-safe
- [ ] DELETE branch does not attempt to SOQL the deleted record
- [ ] No synchronous callouts in trigger body — dispatched to Queueable or @future
- [ ] Automated Process trace flag configured for debugging
- [ ] Unit tests cover all change-type branches using `Test.getEventBus().deliver()`

---

## Notes

(Record any deviations from the standard pattern and the reason.)
