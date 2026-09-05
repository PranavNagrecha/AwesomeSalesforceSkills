# Examples - Flow Governance

## Example 1: Replace Generic Names With A Durable Convention

**Context:** The org has flows named `New Flow`, `Case Flow Copy`, and `Case Flow Final`.

**Problem:** Support cannot tell which automation owns case routing or which one is safe to modify.

**Solution:**

Adopt a convention that encodes purpose and trigger style.

```text
Before:
- New Flow
- Case Flow Copy
- Case Flow Final

After:
- Case_AfterSave_AssignOwner
- Case_Screen_CloseCaseWizard
- Case_Scheduled_SendEscalationReminders
```

**Why it works:** The portfolio becomes readable without opening each flow individually.

---

## Example 2: Activation Gate With Named Owner And Rollback Note

**Context:** A team frequently activates new flow versions during release windows with minimal metadata.

**Problem:** When issues appear, support does not know who owns the change or how to roll it back safely.

**Solution:**

Require a simple release record for every activation.

```text
Flow: Opportunity_AfterSave_SetRenewalRisk
Owner: Revenue Operations
Change summary: Added partner-channel branch
Validated by: Sandbox regression + fault-path review
Rollback plan: Reactivate version 12 if version 13 causes incorrect task creation
```

**Why it works:** Activation becomes an auditable operational event rather than an opaque config change.

---

## Anti-Pattern: Governance By Tribal Memory

**What practitioners do:** They assume the right admin or developer will remember what each flow does and which versions matter.

**What goes wrong:** Incident response slows down, duplicate automations accumulate, and retirement becomes risky because nobody trusts the portfolio map.

**Correct approach:** Put naming, ownership, and lifecycle expectations directly into the flow governance standard and enforce them at release time.

---

## Example 3: The Tie Nobody Saw — Two Active Flows, One Save Context

**Context:** Two teams shipped record-triggered flows on `Case` eleven months apart. Both are Active, both are after-save, both set `Case.Owner`. Support reports that ownership "sometimes" comes out wrong after a bulk update.

**Problem:** Setup shows both flows as healthy. Flow Trigger Explorer shows them in *an* order, but neither declares one, and nothing in either flow's logic explains the inconsistency. The Apex order of execution treats after-save flows as a single step (step 14, `apexdev.txt` L15466) and does not rank flows within it.

**Solution:**

Find the tie before arguing about the logic. This is the whole diagnosis in one query — no source access required:

```sql
SELECT TriggerObjectOrEventLabel, TriggerType, ApiName, Label,
       TriggerOrder, ApiVersion, IsOutOfDate, LastModifiedBy
FROM FlowDefinitionView
WHERE IsActive = true
  AND TriggerObjectOrEventLabel = 'Case'
  AND TriggerType = 'RecordAfterSave'
  AND InstalledPackageName = null
ORDER BY TriggerOrder NULLS FIRST
```

Two rows with `TriggerOrder = null` is the finding. The `InstalledPackageName = null` filter matters: managed-package flows land in this view but never in your manifest (`api_meta.txt` L68035), so leaving them in makes the count look worse than the part you can fix, and taking them out entirely makes the runtime look calmer than it is. Run it both ways.

Then assign order in the policy file, deploy, and re-run the query expecting `10` and `20`:

```yaml
# excerpt from flow-governance-policy.yaml — the rule that would have caught this
record_triggered:
  require_trigger_order_when_co_resident: true
  trigger_order_min: 1
  trigger_order_max: 2000
```

```
$ python3 scripts/check_flow_governance.py --manifest-dir force-app/main/default
ERROR Case/RecordAfterSave: 2 Active record-triggered flows share this save context and 2
      declare no <triggerOrder> (Case_AfterSave_AssignOwner, Case_AfterSave_SetPriority).
```

**Why it works:** The finding is a property of the portfolio, not of either flow, so no per-flow review would ever have surfaced it. `triggerOrder` is nullable and defaults to nothing (`api_meta.txt` L68438), which is why "both flows passed review" and "the org has a defect" are both true.

---

## Example 4: A Retirement That Cannot Ship

**Context:** The quarterly retirement review lists version 7 of `Case_Screen_EscalationWizard` for deletion. The destructive change fails.

**Problem:** "You can delete a flow version if it isn't active and doesn't have any paused interviews" (`api_meta.txt` L68041–68042). The org enabled `enableFlowPauseEnabled`, and version 7 has paused interviews that nobody inventories.

**Solution:**

```sql
SELECT i.Id, i.InterviewLabel, i.InterviewStatus, i.PauseLabel,
       i.Owner.Name, i.CreatedDate, i.FlowVersionViewId
FROM FlowInterview i
WHERE i.InterviewStatus IN ('Paused', 'VersionPaused')
  AND i.FlowVersionViewId = '301xx000000ABCDAA2'
ORDER BY i.CreatedDate
```

Non-empty means the deletion is blocked. Before deciding to delete the interviews instead, find out what they are holding:

```sql
SELECT ParentId, Parent.InterviewLabel, Parent.Owner.Name, RelatedRecordId
FROM FlowRecordRelation
WHERE Parent.InterviewStatus IN ('Paused', 'VersionPaused')
```

**Why it works:** The retirement blocker and its blast radius are both queryable, and neither is visible on the Flow's detail page. `PauseLabel` carries the user's own "Why Paused" text (`object_reference.txt` L140018–140026), which is usually enough to decide whether an eleven-month-old interview is abandoned or is someone's open case.
