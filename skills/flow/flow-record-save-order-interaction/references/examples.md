# Examples — Save Order Interactions

Worked traces. The deployable XML lives in `references/metadata-examples.md`;
these are the diagnoses that decide which XML to write.

## Example 1: Before-Save Flow Beats Before Trigger

**Situation:** want to populate `Territory__c` from Zip code.

**Good:** before-save Flow with a Decision and Assignment. Runs at
step 3, no DML, no SOQL.

**Bad:** after-save Flow that does a second DML to set the field, plus
a `@future` trigger.

Save-order trace for the two designs:

```text
GOOD — before-save Flow
  step  3  Set_Territory (before-save Flow)   Territory__c = 'WEST'
  step  5  validation rules see 'WEST'
  step  6  duplicate rules match on 'WEST'
  step  7  save
  step 19  commit
  → one save, no DML element, no re-entry

BAD — after-save Flow + @future
  step  7  save                                Territory__c = null
  step  8  AccountTrigger (after)              enqueues @future
  step 14  Set_Territory (after-save Flow)     Update Records → NEW SAVE CYCLE
             ↳ steps 1..8 run again for the same record
             ↳ steps 9..17 are SKIPPED on that pass (recursive save)
  step 19  commit
  step 20  @future runs in a separate transaction, may re-save again
  → two+ save cycles, extra DML, recursion risk
```

Note the trigger interaction the good design still has to account for:
if an Apex before trigger on Account also writes `Territory__c`, it runs
at **step 4** — one step after the Flow — and its value is the one that
saves.

## Example 2: Validation Runs After Before-Save Flow

A before-save Flow sets `Stage = 'Closed Won'` but an active validation
rule blocks `Closed Won` without `Close Date`. Custom validation rules
run at step 5, **after** the before-save Flow at step 3 (and after the
before trigger at step 4), so the rule fires using the flow-populated
value. Either set Close Date in the same flow or relax the rule.

## Example 3: Recursion Through After-Save → After Trigger

After-save Flow updates `Last_Touch__c`, firing an after trigger that
updates another field, triggering the record-triggered Flow again.

**Fix:** guard on `Trigger.oldMap` vs `Trigger.newMap`; detect no-op
and skip DML. Or move `Last_Touch__c` to before-save so no DML fires.

The Flow-side half of that fix is a `<start>` block that tests a
transition rather than a state — the smallest diff that stops the loop:

```xml
<start xmlns="http://soap.sforce.com/2006/04/metadata">
    <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
    <filterLogic>and</filterLogic>
    <filters>
        <field>Stage</field>
        <operator>EqualTo</operator>
        <value>
            <stringValue>Closed Won</stringValue>
        </value>
    </filters>
    <filters>
        <field>Touch_Logged__c</field>
        <operator>EqualTo</operator>
        <value>
            <booleanValue>false</booleanValue>
        </value>
    </filters>
    <object>Opportunity</object>
    <recordTriggerType>Update</recordTriggerType>
    <triggerType>RecordAfterSave</triggerType>
</start>
```

The two filters do different jobs. `doesRequireRecordChangedToMeetCriteria`
stops the flow re-firing on a later edit while the record is still Closed Won;
`Touch_Logged__c = false` — a marker the flow sets itself — stops it re-firing
if the record leaves and re-enters that stage. Removing either one leaves a
real path back into the loop.

## Example 4: Roll-Up Not Visible In Before-Save

Before-save Flow reads `Amount_Total__c` (a roll-up) — always stale in
the same transaction. The Flow runs at step 3; the parent's roll-up is
not recalculated until step 16, thirteen steps later in the child's save.
(Step 16 is still before the commit at step 19 — the value is stale
because the recalculation is *later in the save*, not because it happens
after commit.)

**Fix:** read the recalculated value in a **parent** before or after
trigger (steps 4 / 8 of the parent's own save). The parent's after-save
Flow is not an option here: the step-16 parent save is a recursive save,
and Salesforce skips steps 9–17 of it, so step 14 never runs. See
gotchas.md Gotcha 8.

## Example 5: The Duplicate Block That Ate The Transaction

**Reported symptom:** "Some web Cases never get their follow-up Task, but
nothing shows up in the flow error email or in `Application_Log__c`."

**Trace:**

```text
step  3  Case_BeforeSave_StampRoutingKey   Routing_Key__c = 'WEB-QUESTION'
step  5  validation rules pass
step  6  duplicate rule matches on Routing_Key__c → BLOCK
         ↳ record is not saved; steps 7-20 do not run
         ↳ so: no after trigger (8), no after-save flow (14),
           no fault path, no Application_Log__c row
step  -  caller receives a DML error
```

The before-save flow at step 3 *created* the value the duplicate rule at step
6 matched on. The fault design assumed a failure would land in a flow fault
path, but the transaction ended two steps before any flow that has one.

**Fix:** the error is only visible to the caller, so it has to be handled
there — Data Loader error file, Apex `Database.insert(records, false)` results,
or the integration's own retry queue. Then either narrow the matching rule or
stop the flow writing the field it keys on.

**Query that finds the population at risk** — records whose flow-written key
collides with an existing one:

```soql
SELECT Routing_Key__c, COUNT(Id) matches
FROM Case
WHERE Routing_Key__c != NULL AND CreatedDate = LAST_N_DAYS:30
GROUP BY Routing_Key__c
HAVING COUNT(Id) > 1
ORDER BY COUNT(Id) DESC
LIMIT 50
```

## Example 6: The Owner Who Was Right In The Flow And Wrong In The Trigger

**Reported symptom:** "The follow-up Task goes to the right queue, but the
notification email from our Apex trigger goes to whoever created the Case."

**Trace:**

```text
step  7  save                        OwnerId = submitter (or object default)
step  8  CaseTrigger (after insert)  reads OwnerId → submitter   ← email sent here
step  9  assignment rules            OwnerId = Tier2_Queue
step 14  Case_AfterSave_CreateFollowUpTask  reads OwnerId → Tier2_Queue  ← task correct
```

Both automations read the same field on the same record in the same
transaction and got different answers, because step 9 sits between them.

**Fix:** move the notification to the after-save flow at step 14, or — if it
must stay in Apex — to a Queueable enqueued from the after trigger, which runs
at step 20 against the committed row. Do not "fix" it by re-querying inside
the after trigger; step 9 has not run yet, so the query returns the same
value.
