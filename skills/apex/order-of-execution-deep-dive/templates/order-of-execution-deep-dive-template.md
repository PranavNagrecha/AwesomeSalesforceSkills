# Order of Execution Analysis — Work Template

Use this template when debugging automation ordering issues or designing multi-layer automation on a Salesforce object.

---

## Scope

**Object:** (e.g., Account, Case, Opportunity__c)

**DML operation:** insert / update / delete / undelete

**Request summary:** (describe the symptom or design requirement)

---

## Context Gathered

Answer these before proceeding:

- **Active before triggers on this object:** (list trigger names)
- **Active after triggers on this object:** (list trigger names)
- **Before-save record-triggered Flows:** (list Flow API names)
- **After-save record-triggered Flows:** (list Flow API names)
- **Active workflow rules with field updates:** (list rule names — these cause a one-time trigger re-fire within step 11)
- **Active validation rules:** (list names relevant to the symptom)
- **Roll-up summary fields on parent object:** (yes/no; if yes, list parent object and field — steps 16-17)
- **Process Builder processes (legacy):** (list names; these run at step 13)

---

## Step Map for This Object

Annotate each step that has active automation for this object and DML type:

| Step | Platform Action | Active Automation (this org) | Notes |
|------|----------------|------------------------------|-------|
| 1 | Load original record from database | — | |
| 2 | Overwrite with new values + request-type system validation | — | |
| 3 | Before-save record-triggered Flows | | Runs FIRST, before the before trigger |
| 4 | Before triggers | | Runs AFTER step 3 — wins any field-write conflict with it |
| 5 | System validation re-run + custom validation rules | | Required fields, lengths, FK, then VRs |
| 6 | Duplicate rules | | Block action stops the save here |
| 7 | Save to DB (no commit) | — | |
| 8 | After triggers | | |
| 9 | Assignment rules | | Lead / Case only |
| 10 | Auto-response rules | | Lead / Case only |
| 11 | Workflow rules (+ field-update re-fire) | | Field updates re-run before/after update triggers once, and only once |
| 12 | Escalation rules | | Case only |
| 13 | Process Builder + workflow-launched Flows | | Not in a guaranteed order |
| 14 | After-save record-triggered Flows | | |
| 15 | Entitlement rules | | |
| 16 | Roll-up summary on parent → parent save procedure | | Fires parent-object automation |
| 17 | Roll-up summary on grandparent | | Cascades one level further |
| 18 | Criteria-based sharing evaluation | | |
| 19 | Commit all DML | — | |
| 20 | Post-commit logic (@future, Queueable, email, async Flow paths) | | |

---

## Symptom Location

**Observed symptom:** (wrong field value, duplicate record, missing side effect, wrong trigger fire count)

**Likely step(s) where it occurs:** (identify from the step map above)

**Which automation is the last writer for the affected field, based on step order:** (fill in)

---

## Recursion Risk Assessment

- [ ] Does any after trigger (step 8) perform DML on the same object? If yes, a static `Set<Id>` guard is required.
- [ ] Does any after trigger (step 8) perform DML on a parent with a roll-up summary? If yes, parent triggers will fire — verify they handle this.
- [ ] Are there workflow rules with field updates (step 11)? If yes, before update and after update triggers re-fire once — verify trigger logic is idempotent.
- [ ] Does any after-save Flow (step 14) write back to the triggering record? If yes, this starts a new save cycle — verify it does not loop.
- [ ] Do a before-save Flow (step 3) and a before trigger (step 4) write the same field? If yes, the trigger's value is the one that persists — confirm that is intended, and give the field one owner.

---

## Findings

(Fill in after analysis)

**Root cause:** (which step, which automation, and what it did that caused the symptom)

**Supporting evidence:** (debug log excerpt, step map annotation, code review finding)

---

## Recommended Fix

**Change type:** Add recursion guard / Move logic to correct step / Consolidate field ownership / Deactivate duplicate automation

**Specific change:**

```apex
// Paste code change or describe configuration change here
```

**Why this fixes it:** (explain which step ordering principle resolves the symptom)

---

## Review Checklist

- [ ] Step map completed with all active automations assigned to their step
- [ ] Workflow field update re-fire risk assessed and trigger idempotency verified
- [ ] Recursion guard added where required
- [ ] Before-save Flow and before trigger field ownership reconciled (no two writers for the same field)
- [ ] After-save Flow (step 14) vs. after trigger (step 8) timing dependency reviewed
- [ ] Roll-up summary parent trigger re-fire considered
- [ ] Tests run with full automation stack enabled (not trigger in isolation)

---

## Notes

(Record any deviations from the standard pattern and why.)
