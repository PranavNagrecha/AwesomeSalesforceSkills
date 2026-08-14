# Examples — Scheduled Path Patterns

## Example 1: A 24-hour follow-up that re-reads before it acts

**Context:** When a high-priority Case is created and left unworked for a day, the owner's manager should be notified. Business wants exactly one notification, and none for Cases that were closed in the meantime.

**Problem:** The naive build branches on `$Record.Status` inside the scheduled path. `$Record` is the snapshot captured when the interview was queued, so the branch evaluates yesterday's status and notifies on Cases that are already closed.

**Solution:** The scheduled path is authored on the record-triggered Flow's Start element, and the branch's first element is a Get Records that re-reads the Case by Id.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <label>Case Follow Up Reminder</label>
    <processType>AutoLaunchedFlow</processType>
    <status>Active</status>

    <start>
        <object>Case</object>
        <recordTriggerType>Create</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Priority</field>
            <operator>EqualTo</operator>
            <value><stringValue>High</stringValue></value>
        </filters>
        <scheduledPaths>
            <name>Day_After_Creation</name>
            <label>1 Day After Creation</label>
            <offsetNumber>1</offsetNumber>
            <offsetUnit>Days</offsetUnit>
            <timeSource>RecordTriggerEvent</timeSource>
            <connector>
                <targetReference>Reread_Case</targetReference>
            </connector>
        </scheduledPaths>
    </start>

    <!-- FIRST element in the branch: re-read current state. Never trust $Record here. -->
    <recordLookups>
        <name>Reread_Case</name>
        <label>Re-read Case</label>
        <object>Case</object>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value><elementReference>$Record.Id</elementReference></value>
        </filters>
        <getFirstRecordOnly>true</getFirstRecordOnly>
        <queriedFields>Id</queriedFields>
        <queriedFields>IsClosed</queriedFields>
        <queriedFields>OwnerId</queriedFields>
        <connector><targetReference>Still_Open</targetReference></connector>
    </recordLookups>

    <decisions>
        <name>Still_Open</name>
        <label>Still Open?</label>
        <defaultConnectorLabel>Closed - do nothing</defaultConnectorLabel>
        <rules>
            <name>Open</name>
            <label>Open</label>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>Reread_Case.IsClosed</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue><booleanValue>false</booleanValue></rightValue>
            </conditions>
            <connector><targetReference>Notify_Manager</targetReference></connector>
        </rules>
    </decisions>
</Flow>
```

**Why it works:** `timeSource` anchors the offset to the trigger event rather than a field, so nothing can move the schedule after the fact. `offsetUnit` uses `Days`, one of the four values the `FlowScheduledPathOffsetUnit` enumeration documents — "Months, Days, Hours, Minutes". And the Get Records → Decision pair makes the *current* `IsClosed` the deciding value, which is the only correct source in a branch that runs a day after it was queued.

Entry criteria on the Start element (`Priority = High`) matter beyond correctness: they are what stops a bulk Case load from queueing an interview for every row.

---

## Example 2: A field-anchored reminder, plus the sweep that keeps it honest

**Context:** Send a renewal reminder 30 days before `Renewal_Date__c` on Contract.

**Problem:** Field-anchored offsets are computed once, when the interview is queued. Sales revises renewal dates constantly, and the queued reminder does not move with them.

**Solution:** Author the field-anchored path *and* accept that it needs a supersede mechanism.

In Flow Builder, on the Start element: **Time Source** = the `Renewal_Date__c` field on Contract (rather than "When Contract is created or updated"), **Offset Number** = `-30`, **Offset Unit** = `Days`.

> The Flow metadata for a *field*-anchored path is not reproduced here. Example 1's event-anchored `<timeSource>RecordTriggerEvent</timeSource>` is the shape this package verifies; the element that carries a **field API name** for a field-anchored path is a separate one, and this package does not assert its name. Retrieve the flow from an org and read the real XML before hand-authoring one.

The scheduled branch re-reads the Contract and, before sending, verifies the reminder is still due:

| Check in the branch | Why |
|---|---|
| `Reread_Contract.Renewal_Date__c` still within 30–31 days of today | The date moved after queueing; this reminder is stale — exit silently. |
| `Reread_Contract.Reminder_Sent__c` is false | An earlier interview already sent it. Prevents duplicates when the date moved twice. |
| `Reread_Contract.Status` is Active | Contract was cancelled during the wait. |

Then set `Reminder_Sent__c = true` in the same branch.

**Why it works:** The negative `offsetNumber` is what makes the offset "before" rather than "after" the field value. The three-check guard turns a stale interview into a no-op instead of a wrong email, and the `Reminder_Sent__c` flag makes the whole path idempotent — which matters because a date edited twice queues two interviews and neither one cancels the other.

If the business needs the reminder to genuinely track the current date rather than the date at queue time, the scheduled path is the wrong tool: use a scheduled (batch) Flow that runs nightly and evaluates `Renewal_Date__c = TODAY + 30` against live data.

---

## Anti-Pattern: A scheduled path with no entry criteria on a high-volume object

**What practitioners do:** Add a scheduled path to a record-triggered Flow on Lead or Task with entry criteria left at "every record", planning to filter inside the branch with a Decision element.

**What goes wrong:** Every record that fires the trigger queues a paused interview, including the 500,000 rows from tonight's data load. The Decision element cannot help — it runs *after* the interview has already been created and resumed. The queue becomes the bottleneck, the resumed batches contend for the asynchronous limit budget (200 SOQL queries, 150 DML statements, 12 MB heap, 60,000 ms CPU per transaction — shared across each resumed batch, not per interview), and Setup → Paused And Waiting Interviews becomes unusable for diagnosing anything else.

**Correct approach:** Filter at the Start element, where the platform evaluates the criteria before creating an interview:

```xml
<start>
    <object>Lead</object>
    <recordTriggerType>Create</recordTriggerType>
    <triggerType>RecordAfterSave</triggerType>
    <filterLogic>1 AND 2</filterLogic>
    <filters>
        <field>LeadSource</field>
        <operator>EqualTo</operator>
        <value><stringValue>Web</stringValue></value>
    </filters>
    <filters>
        <field>Rating</field>
        <operator>EqualTo</operator>
        <value><stringValue>Hot</stringValue></value>
    </filters>
    <scheduledPaths>...</scheduledPaths>
</start>
```

Then bulk-test it: load a realistic batch into a sandbox, count the resulting rows in Paused And Waiting Interviews, and confirm the number matches what the filters should have admitted. If it does not, the filter is in the wrong place.
