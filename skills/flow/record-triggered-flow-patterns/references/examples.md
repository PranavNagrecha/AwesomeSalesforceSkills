# Examples — Record Triggered Flow Patterns

## Example 1: Before-Save Case Normalization

**Context:** A Case must default `Priority`, normalize `Origin`, and stamp a routing key before the record commits.

**Problem:** The first design used after-save and an extra `Update Records`, which retriggered other automation and consumed more transaction budget.

**Solution:**

```text
Start: Case before-save, run only when record is created or Origin changes
Decision: Is Origin blank or inconsistent?
Assignment: Set Origin = 'Web', Priority = 'Medium', Routing_Key__c = 'WEB_DEFAULT'
End
```

**Why it works:** The requirement only changes the current record, so before-save is the correct and cheapest pattern.

---

## Example 2: After-Save Opportunity Follow-Up

**Context:** When an Opportunity moves to `Closed Won`, the org must create onboarding Tasks and notify a downstream team.

**Problem:** Admins tried to do this in before-save, then moved it to after-save but forgot to limit execution to real stage transitions.

**Solution:**

```text
Start: Opportunity after-save, run only when StageName changes to Closed Won
Decision: Was StageName changed from a different value?
Create Records: onboarding task collection
Action: send notification subflow
End
```

**Why it works:** Related side effects belong in after-save, and the field-change gate prevents the flow from firing again on unrelated edits.

---

## Anti-Pattern: After-Save Update Of The Same Record

**What practitioners do:** They build an after-save flow, check a condition, and then use `Update Records` to modify fields on the same record.

**What goes wrong:** The record save can retrigger the same flow or downstream automation, creating loops, extra DML, and confusing debug runs.

**Correct approach:** Move same-record field changes into before-save, or add a deliberate guard if after-save is truly required for a committed side effect.

---

## Example 3: The Duplicate-Task Incident

**Context:** Sales reports two onboarding Tasks on roughly a fifth of closed deals. The flow "hasn't changed in months," which is true and is also why nobody looked at it.

**Problem:** The after-save flow's entry criteria said `StageName = 'Closed Won'` — a state, not a transition. Any later edit to an already-won opportunity satisfied it again. The trigger was a quarterly owner-reassignment load that touched historical records.

**Finding it.** The flow is not the first place to look; the side-effect records are. Count them per parent:

```sql
SELECT WhatId, COUNT(Id) taskCount, MIN(CreatedDate) first, MAX(CreatedDate) latest
FROM Task
WHERE Subject = 'Kick off onboarding'
  AND CreatedDate = LAST_N_DAYS:90
GROUP BY WhatId
HAVING COUNT(Id) > 1
ORDER BY COUNT(Id) DESC
```

Two rows minutes apart means recursion. Two rows *months* apart — which is what this query returned — means the entry criteria re-matched on an unrelated later save. That distinction is the whole diagnosis, and it is visible in `MIN`/`MAX` before anyone opens Flow Builder.

**The fix** is one element in the `<start>` block. Only the Start changes; the rest of the flow is untouched:

```xml
<start>
    <locationX>176</locationX>
    <locationY>50</locationY>
    <connector>
        <targetReference>Create_Onboarding_Task</targetReference>
    </connector>
    <!-- ADDED: fire on the transition into Closed Won, not on the state -->
    <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
    <filterLogic>and</filterLogic>
    <filters>
        <field>StageName</field>
        <operator>EqualTo</operator>
        <value>
            <stringValue>Closed Won</stringValue>
        </value>
    </filters>
    <object>Opportunity</object>
    <!-- CHANGED from CreateAndUpdate: doesRequire... is defined against a triggering update -->
    <recordTriggerType>Update</recordTriggerType>
    <triggerType>RecordAfterSave</triggerType>
</start>
```

**Why it works:** `doesRequireRecordChangedToMeetCriteria` makes the conditions evaluate true only when the record did not meet them before the update and does after it (`api_meta.txt` L72322–72325). The historical records already met the condition, so the reassignment load no longer starts an interview. The complete flow this Start belongs to is in `references/metadata-examples.md` § 2; the deployable test that would have caught it pre-activation is § 4.

**What did not fix it:** three earlier attempts added Decision elements *inside* the flow to bail out early. Every one of them still started an interview per record and still burned the transaction budget — the filter has to be on the Start element to prevent the interview, not on a Decision after it.
