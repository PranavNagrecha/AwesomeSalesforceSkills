# Field-Update Automation — Decision And Migration Record

One record per field being written. Fill it before building anything; keep it
next to the deployment so the next person can see why this tool and not another.

**Skill:** `admin/workflow-field-update-patterns`
**Object / field:** `<Object>.<Field__c>`
**Author / date:**
**Status:** Proposed | Approved | Deployed | Superseded

---

## 1. The requirement, in one sentence

> Set `<Object>.<Field__c>` to `<value>` when `<condition>`.

| Question (from SKILL.md) | Answer |
|---|---|
| Which record does the value land on — the one being saved, its parent, its children, an unrelated one? | |
| Can the value be derived from other same-record fields at read time? | |
| Must the stored value be frozen at a point in time, or track its inputs forever? | |
| Is the write in the "not updateable in before triggers" set (`IsClosed`, `Amount` with line items, `ForecastCategory`, `ActivatedDate`, …)? | |
| Does anything downstream read the field in the same transaction? | |
| Is there an existing Workflow Rule field update on this field? | |
| What is the save volume — single edits, hundreds, a bulk load? | |

## 2. Tool chosen

| | |
|---|---|
| **Tool** | Formula field / Before-save Flow / After-save Flow / Apex trigger |
| **Decision-tree branch** | `automation-selection.md` Q_ → …; `flow-pattern-selector.md` Q_ → … |
| **Order-of-execution slot** | step 3 / step 4 / step 8 / step 11 / step 14 |
| **Rejected alternative** | …and why |

## 3. If this replaces a Workflow Rule field update

| Legacy element | Value in the org today | Flow equivalent chosen |
|---|---|---|
| `rules/fullName` | | — |
| `rules/active` | | — |
| `rules/triggerType` | `onCreateOnly` / `onCreateOrTriggeringUpdate` / `onAllChanges` | `recordTriggerType` = ___ , `doesRequireRecordChangedToMeetCriteria` = ___ |
| `rules/criteriaItems` or `rules/formula` | | `start/filters` or `start/filterFormula` |
| `fieldUpdates/operation` | `Formula` / `Literal` / `LookupValue` / `NextValue` / `Null` / `PreviousValue` | |
| `fieldUpdates/formula` or `literalValue` | | |
| `fieldUpdates/reevaluateOnChange` | true / false | if true: which rules ran on the cascade, and where they land now |
| `fieldUpdates/targetObject` | | if set: after-save Flow, not before-save |
| `rules/workflowTimeTriggers` | | if present: second Flow with scheduled paths |
| `rules/failedMigrationToolVersion` | | if populated: manual rebuild, not another tool run |

Run first, and paste the inventory block here:

```bash
python3 skills/admin/workflow-field-update-patterns/scripts/check_workflow_field_update_patterns.py \
  --manifest-dir force-app/main/default
```

## 4. Existing automation on this object

List every Apex trigger, Flow and rule that already fires on this object. The
cutover deploy changes how many times each trigger runs (`references/gotchas.md`
§ 10), so this list is the blast radius, not background reading.

| Component | Slot | Reads or writes this field? | Affected by the cutover? |
|---|---|---|---|
| | | | |

**Trigger-entry count for one save, measured in a sandbox:** before ___ / after ___
Any difference in counters, enqueued jobs or callouts is a blocker.

## 5. Recursion guard

| | |
|---|---|
| Needed? | yes / no — and why |
| Mechanism | before-save (no guard needed) / `doesRequireRecordChangedToMeetCriteria` / decision branch on current value / `TriggerHandler.skipOnce()` |
| Verified how | |

## 6. Parity test

Copy the seven-row table from `references/metadata-examples.md` and fill in the
actual values observed. Run it twice: with the legacy rule live, then with it
deactivated. Identical results are the go signal.

| # | Setup | Action | Expected | Observed (rule on) | Observed (rule off) |
|---|---|---|---|---|---|
| 1 | | | | | |

## 7. Cutover and verification

- [ ] Replacement Flow deployed as `Draft` to the mirror sandbox
- [ ] Parity table passes with the legacy rule live
- [ ] Legacy rule deactivated in the sandbox; parity table passes again
- [ ] Trigger-entry count difference from § 4 reviewed and accepted
- [ ] Production deploy contains **both** the `Active` Flow and `<active>false</active>` on the rule
- [ ] Post-deploy field-history query returns a new row for the field
- [ ] Orphaned `fieldUpdates` blocks scheduled for removal in a **later** deploy

Verification query actually run:

```sql
SELECT Field, OldValue, NewValue, CreatedDate
FROM   <Object>FieldHistory
WHERE  <Object>Id = '<record id>'
AND    Field = '<Field__c>'
ORDER  BY CreatedDate DESC
LIMIT  20
```

## 8. Deviations

Anything done differently from the pattern in `SKILL.md`, and the reason. An
empty section here means the standard pattern applied unchanged — say so
explicitly rather than leaving it blank.
