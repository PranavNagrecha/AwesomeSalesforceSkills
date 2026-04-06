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
- **Active workflow rules with field updates:** (list rule names — these cause trigger re-fire at step 12)
- **Active validation rules:** (list names relevant to the symptom)
- **Roll-up summary fields on parent object:** (yes/no; if yes, list parent object and field)
- **Process Builder processes (legacy):** (list names; these run at step 13)

---

## Step Map for This Object

Annotate each step that has active automation for this object and DML type:

| Step | Platform Action | Active Automation (this org) | Notes |
|------|----------------|------------------------------|-------|
| 1 | Load from database | — | |
| 2 | Overwrite with new values | — | |
| 3 | Before triggers + before-save Flows | | |
| 4 | System validation | — | Required fields, field lengths, FK |
| 5 | Custom validation rules | | |
| 6 | Duplicate rules | | |
| 7 | Save to DB (no commit) | — | |
| 8 | After triggers | | |
| 9 | Assignment rules | | |
| 10 | Auto-response rules | | |
| 11 | Workflow rules | | |
| 12 | Workflow field update re-fire (if step 11 had field updates) | | Before+after triggers re-run once |
| 13 | Process Builder (legacy) | | |
| 14 | Escalation rules | | |
| 15 | After-save record-triggered Flows | | |
| 16 | Entitlement rules | | |
| 17 | Roll-up summary update → parent triggers | | Starts parent object OOE |
| 18 | Commit + post-commit (@future, emails) | | |

---

## Symptom Location

**Observed symptom:** (wrong field value, duplicate record, missing side effect, wrong trigger fire count)

**Likely step(s) where it occurs:** (identify from the step map above)

**Which automation is the last writer for the affected field, based on step order:** (fill in)

---

## Recursion Risk Assessment

- [ ] Does any after trigger (step 8) perform DML on the same object? If yes, a static `Set<Id>` guard is required.
- [ ] Does any after trigger (step 8) perform DML on a parent with a roll-up summary? If yes, parent triggers will fire — verify they handle this.
- [ ] Are there workflow rules with field updates (step 11)? If yes, before and after triggers re-fire once — verify trigger logic is idempotent.
- [ ] Does any after-save Flow (step 15) write back to the triggering record? If yes, this starts a new DML cycle — verify it does not loop.

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
- [ ] After-save Flow (step 15) vs. after trigger (step 8) timing dependency reviewed
- [ ] Roll-up summary parent trigger re-fire considered
- [ ] Tests run with full automation stack enabled (not trigger in isolation)

---

## Notes

(Record any deviations from the standard pattern and why.)
