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
- **Idempotency store:** `Change_Event_Receipt__c` (see `references/code-examples.md` Artifact 5) / other: ___
- **Enrichment or filtering needed?** `enrichedFields` / `filterExpression` on a custom channel member: ___
- **Running identity:** Automated Process (default) / `PlatformEventSubscriberConfig` user: ___

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

    // --- Creates and undeletes share one hydration query ---
    Set<Id> hydrate = new Set<Id>(createdIds);
    hydrate.addAll(updatedIds);
    hydrate.addAll(undeletedIds);
    if (!hydrate.isEmpty()) {
        List<___> records = [SELECT Id, ___ FROM ___ WHERE Id IN :hydrate];
        ___Handler.upsertDownstream(records);
    }

    // --- Deletes: do NOT query, the record is gone. The ids are the payload. ---
    if (!deletedIds.isEmpty()) {
        ___Handler.notifyDeleted(deletedIds);
    }

    // --- Gap and overflow: no field values. Flag a resync, do not guess. ---
    if (!gapIds.isEmpty()) {
        ___Handler.flagForResync(gapIds);
        ApplicationLogger.warn('___ChangeEventTrigger',
            'Gap event resync flagged for ' + gapIds.size() + ' record(s)');
    }

    ApplicationLogger.flush();
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
- [ ] Unit tests call `Test.enableChangeDataCapture()` before any DML, then `Test.getEventBus().deliver()` per delivery phase
- [ ] Dedupe key is `transactionKey` + `sequenceNumber` (never `transactionKey` alone, never `commitNumber`)
- [ ] Entries in `recordIds` are checked for the `001*` wildcard form before being cast to `Id`
- [ ] The `changeType` chain has an `else` branch that logs the unrecognised value (`SNAPSHOT` is reserved)
- [ ] The watched field is a stored field, not a formula (formula fields never appear in `changedFields`)
- [ ] CDC enablement ships as `ChangeEvents_<Object>ChangeEvent.platformEventChannelMember-meta.xml`

---

## Notes

(Record any deviations from the standard pattern and the reason.)
