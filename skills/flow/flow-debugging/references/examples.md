# Examples — Flow Debugging

## Example 1: Record-Triggered Flow Not Firing on Update

**Context:** A record-triggered flow on the Opportunity object is supposed to send an internal Chatter notification when an Opportunity stage changes to "Closed Won." After deployment, the notification never appears, even when the stage is updated manually.

**Problem:** The flow appears inactive from the user's perspective — no errors, no fault emails, nothing happens. Checking entry conditions is skipped because the flow is confirmed active and the trigger event is "A record is created or updated."

**Solution:**

The bug is in the entry conditions. The flow was configured with **"Only when a record is updated to meet the conditions"** and the condition checks `StageName Equals Closed Won`.

With that setting, the flow fires only when the record transitions from a non-"Closed Won" value to "Closed Won" during the same DML operation. Any Opportunity already in "Closed Won" that gets updated for another field (e.g., CloseDate) will never fire this path — the stage field did not change to match, it was already matching.

Steps to diagnose:
1. Open the flow in Flow Builder.
2. Click the Start element.
3. Read the **Entry Conditions** section.
4. Check the condition evaluation option — "Only when a record is updated to meet the conditions" vs "Every time a record is saved and meets the conditions."
5. Use **Debug mode** in a sandbox: set `StageName` = "Prospecting" on the test record, save, then update `StageName` to "Closed Won" — the flow fires. Then update `StageName` to "Closed Won" again on an already-"Closed Won" record — the flow does not fire.

Fix: Change entry condition evaluation to **"Every time a record is saved and meets the conditions"** if the flow should fire on any save where the stage is "Closed Won," or add a condition that checks `ISCHANGED(StageName)` in a formula resource if the intention is strictly on-change-only.

**Why it works:** The "Only when updated to meet" behavior is a common source of confusion because the flow is not broken — it is working exactly as configured. The debug trace makes this immediately visible: the entry condition check shows "Not Met" when the record was already in the target state.

---

## Example 2: Fault Email Received for After-Save Flow on Case

**Context:** The admin receives a fault email with the subject "Unhandled Fault in Flow: Case_Escalation_Flow." The email identifies the failing element as "Update_Related_Account" and the error message as `FIELD_INTEGRITY_EXCEPTION: Required fields are missing: [Billing Street]`.

**Problem:** The practitioner assumes the flow logic is wrong and begins restructuring the decision branches. Time is lost investigating the wrong layer.

**Solution:**

The fault email contains everything needed to identify the cause directly:

1. **Element name**: `Update_Related_Account` — this is a Flow Update Records element that writes to the Account associated with the Case.
2. **Error category**: `FIELD_INTEGRITY_EXCEPTION` — this is a required-field validation on the Account object, not a flow logic error.
3. **Error detail**: `Required fields are missing: [Billing Street]` — a required field on the Account is not being populated.

Investigation path:
1. Open the flow to the `Update_Related_Account` element.
2. Check which Account fields are being written. The element is updating the Account but not providing a value for `Billing Street`, which has been made required by a recent validation rule.
3. Confirm by checking the Account object's validation rules — a new validation rule was added last week requiring `Billing Street` for all Account updates.

Fix options:
- Add `Billing Street` to the Update element's field assignments using the existing Account record value (Get the Account first, then pass `{!Account.BillingStreet}` back into the update).
- Or add a fault connector from the Update element to an error-logging path so that partial failures do not roll back the entire Case save.

**Why it works:** The fault email element name directly pins the failing operation. Mapping the SFDC error code (`FIELD_INTEGRITY_EXCEPTION`) to its cause (validation rule or required field enforcement) narrows the diagnosis to minutes instead of hours.

---

## Anti-Pattern: Running Debug Without Setting Matching Field Values

**What practitioners do:** Open Flow Builder, click Debug, accept all default variable values, and step through the debug session. The flow completes with no visible issue. The practitioner concludes the flow is working correctly and closes the session.

**What goes wrong:** The default variable values in a debug session are empty or zero. If the flow has entry conditions that require a specific field value (e.g., `Priority = High`), the debug run enters the flow with `Priority = null`, which evaluates to a different decision branch than the real failing scenario. The bug is never surfaced because the debug run did not replicate the actual triggering conditions.

**Correct approach:** Before clicking Run in the Debug modal, explicitly set all relevant input variables and record field values to match the failing scenario. For a record-triggered flow: set the field values that represent the record state at the time of the failure. For an autolaunched flow: set the input variable values that the calling process would pass. Always confirm the debug session is running the same data path as the production failure before interpreting results.

---

## Example 3: The Flow Ran, Nothing Errored, and the Data Is Wrong

**Context:** An after-save flow on a custom `Inspection__c` object routes records to one of
three queues based on `Result__c`. For about one record in twenty, the record lands in the
default queue. No fault email, no failed interview, no error anywhere. The flow reports
success every time.

**Problem:** There is no failure to hunt. Every technique that starts from an error — fault
emails, `FlowInterview.InterviewStatus = 'Error'`, `FLOW_ELEMENT_ERROR` — returns nothing,
because nothing failed. The flow did exactly what it was told; what it was told was wrong on
a subset of inputs. This is the case where practitioners fall back to reading the flow and
guessing, and where the log is worth the most.

**Solution:**

The two events that answer a wrong-branch question are `FLOW_RULE_DETAIL` — "interview ID,
rule name, and result" — and `FLOW_VALUE_ASSIGNMENT` — "interview ID, key, and value"
(`apexdev.txt` L38847, L38896). Both log at **Workflow / FINER and above**. At `FINE` you
see element boundaries and learn only that the decision ran; the *result* of each rule and
the *value* of each variable appear only at `FINER`. So the level choice is not caution, it
is the difference between an answer and a shrug.

Set the capture rig, reproduce on a record known to route wrongly, and pull the log. Then
read only the two event types, in order:

```bash
# Which rules fired, and what each one evaluated to.
grep -n 'FLOW_RULE_DETAIL' inspection-flow.log

# Every variable write, in execution order.
grep -n 'FLOW_VALUE_ASSIGNMENT' inspection-flow.log

# The two together, interleaved in the order the interview executed them --
# this is the reading that localises the branch point.
grep -nE 'FLOW_(RULE_DETAIL|VALUE_ASSIGNMENT|ELEMENT_BEGIN)' inspection-flow.log

# Sanity check on the Get that fed the decision: a record count of 0 with a
# downstream null is the signature of a filter that matched nothing.
grep -n 'FLOW_BULK_ELEMENT_DETAIL' inspection-flow.log
```

Walk the `FLOW_RULE_DETAIL` lines top to bottom and find the first rule whose result is not
what you expected. That decision is the branch point — everything above it behaved. Then
walk *back* through `FLOW_VALUE_ASSIGNMENT` to the last write of each variable that rule
reads. The value is printed in the log; you do not have to infer it from the flow's logic,
which is the step where a wrong assumption normally enters.

In this case the last write before the decision showed the routing variable holding a
trailing-whitespace variant of the picklist value, assigned from a formula that concatenated
a text field. The decision compared with `EqualTo`, the comparison failed, and the default
connector fired — correctly, on a value that was wrong three elements earlier.

Confirm the population and the blast radius before changing anything:

```soql
SELECT Result__c, COUNT(Id) records
FROM Inspection__c
WHERE CreatedDate = LAST_N_DAYS:30
GROUP BY Result__c
ORDER BY COUNT(Id) DESC
```

```soql
SELECT Id, Name, Result__c, OwnerId, Owner.Name, CreatedDate
FROM Inspection__c
WHERE CreatedDate = LAST_N_DAYS:30
  AND Owner.Name = 'Inspections Default Queue'
ORDER BY CreatedDate DESC
```

Then encode the corrected expectation so it cannot regress silently. A `FlowTest` assertion
at `Finish` is the cheapest guard:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <flowApiName>Inspection_AfterSave_RouteToQueue</flowApiName>
    <label>Critical result routes to safety queue</label>
    <testType>WithAssertion</testType>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{&quot;Result__c&quot;:&quot;Fail - Critical Safety Violation &quot;}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <elementApiName>Finish</elementApiName>
        <assertions>
            <conditions>
                <leftValueReference>routingQueueName</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Inspections Safety Queue</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>A trailing-space result value fell through to the default connector. See gotcha 6 and Example 3.</errorMessage>
        </assertions>
    </testPoints>
</FlowTest>
```

Note the deliberate trailing space inside the `sobjectValue` — the test asserts the *fixed*
comparison survives the dirty input that caused the original misroute, which is a stronger
guarantee than asserting the clean value routes correctly.

**Why it works:** A wrong-branch bug has no error to follow, so the only path to it is the
printed value of each variable and the printed result of each rule at the moment the
interview made its choice. `FINER` is the level at which the platform prints both. Everything
else in this case — the SOQL, the test — is confirmation of an answer the log already gave.

---

## Which Surface Answers Which Question

| Question | Surface | Why the others do not answer it |
|---|---|---|
| Did the flow start at all? | `FLOW_START_INTERVIEWS_BEGIN` at Workflow INFO+ | A missing fault email proves nothing; `FlowInterviewLog` holds screen flows only |
| Which element failed? | `FLOW_ELEMENT_FAULT` / `FLOW_ELEMENT_ERROR` line | The fault email names it too, but only if it reached someone |
| Was the failure caught? | Which of the two events appears | Both read as "it failed" everywhere else |
| Why did it take that branch? | `FLOW_RULE_DETAIL` + `FLOW_VALUE_ASSIGNMENT` at FINER | Nothing else prints the evaluated result or the value |
| Is it a volume problem? | `*_LIMIT_USAGE` events at FINER | Per-record reasoning misleads; the limits are per transaction |
| Where is a paused interview stuck? | `FlowInterview.CurrentElement` | Logs for that interview expired long ago |
| Did it fail last week? | `FlowInterview.Error` (API 62.0+) | Both log-retention windows are shorter than the report |
| Will it fail again after the fix? | `FlowTest` with `HasError` | A manual re-save proves it once, for one person |
