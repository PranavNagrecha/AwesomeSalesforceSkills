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
