# Process Automation Selection — Examples

## Example 1: Same-Record Update Chooses Before-Save Flow

**Context:** A Lead should set default routing and normalize a field whenever it is created.

**Problem:** The team proposes a trigger because that is what previous projects used.

**Solution:**

```text
Use a before-save record-triggered Flow:
- entry criteria on Lead create
- assignment or formula for the fields on the Lead itself
- no Apex unless a later requirement genuinely needs it
```

**Why it works:** The requirement is same-record, declarative, and does not need service-layer control.

---

## Example 2: High-Control Related-Record Logic Chooses Apex

**Context:** An Opportunity close event must update several related objects, coordinate external side effects, and preserve strict transaction behavior at import volume.

**Problem:** A large after-save Flow becomes hard to reason about and starts sharing limits with other automation.

**Solution:**

```text
Use an Apex trigger handler and service layer.
If admin-owned orchestration is still valuable, expose a narrow invocable action back to Flow at the right boundary.
```

**Why it works:** The requirement needs more control than a purely declarative path provides safely.

**Show the work, not the verdict.** The reviewable output of this example is the two lines of
the decision record that justify the escalation, and the inventory row that shows what was
already on the object:

```yaml
tree_steps_cited:
  - "automation-selection.md Q3 — complex exception handling with rollback (savepoints)"
  - "async-selection.md Q1 — 200 records, < 60s, so nothing leaves the sync transaction"
rejected:
  - alternative: after_save_record_triggered_flow
    reason: "A fault path routes the interview to an error handler; it does not undo DML already performed in the same interview."
```

| Object | Surface | API name | Timing | Owns |
|---|---|---|---|---|
| Opportunity | Flow | `Opp_Before_Save_Defaults` | `RecordBeforeSave` / `TriggerOrder` 10 | Stage-derived fields on the Opportunity |
| Opportunity | Apex trigger | `OpportunityTrigger` | before update, after update | Onboarding child creation + rollback |

Two surfaces, two owners, no shared field — which is what makes the split defensible rather
than accidental. The full record shape and the queries that produce that table are in
`references/decision-record-examples.md`.

---

## Anti-Pattern: Legacy Tool Stays Because It Is Familiar

**What practitioners do:** Keep an old Process Builder because it still mirrors the business rule.

**What goes wrong:** New automation decisions are distorted by legacy behavior, and migration risk keeps growing.

**Correct approach:** Treat Workflow Rule and Process Builder logic as retirement work. Re-evaluate the requirement against current Flow and Apex options instead of preserving the old surface by default.
