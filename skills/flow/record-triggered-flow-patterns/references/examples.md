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

## Example 3: Sequencing Two After-Save Flows With Trigger Order

**Context:** An acquisition left the Case object with two after-save flows that must both stay: `Case_SLA_Stamp` (writes an SLA target onto a child record) and `Case_Escalation_Notify` (reads that SLA target and notifies). Notify was firing before Stamp about half the time.

**Problem:** Neither flow had a trigger order value, so they ran in created-date order — and the deploy history of the two orgs made that order effectively arbitrary. The team's first fix was to set `Case_Escalation_Notify` to 1,500 "so it runs late." It ran first, because unset flows sequence *between* the 1–1,000 band and the 1,001–2,000 band.

**Solution:**

```text
Case_SLA_Stamp          → trigger order 10
Case_Escalation_Notify  → trigger order 20
(no flow in the phase is left without a value)
Verify the resulting sequence in Flow Trigger Explorer before deploying.
```

**Why it works:** Both flows sit in the 1–1,000 ascending band, so they sequence by value. The gap between 10 and 20 leaves room to insert a third flow later without renumbering. Leaving one flow unset would have reintroduced the band problem. Note the ceiling on this technique: trigger order sequences flow-against-flow inside one phase — it cannot move either flow ahead of the Case object's Apex triggers.

---

## Anti-Pattern: After-Save Update Of The Same Record

**What practitioners do:** They build an after-save flow, check a condition, and then use `Update Records` to modify fields on the same record.

**What goes wrong:** The record save can retrigger the same flow or downstream automation, creating loops, extra DML, and confusing debug runs.

**Correct approach:** Move same-record field changes into before-save, or add a deliberate guard if after-save is truly required for a committed side effect.
