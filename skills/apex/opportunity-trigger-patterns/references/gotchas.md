# Gotchas — Opportunity Trigger Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: DML on OpportunitySplit Is Blocked in Before Contexts

**What happens:** Any attempt to insert, update, or delete `OpportunitySplit` records inside a before-insert, before-update, or before-delete trigger context fails immediately with `System.DmlException: DML not allowed on OpportunitySplit in a trigger context`. This applies even when the trigger is on a different object (e.g. a before-insert trigger on `OpportunityTeamMember`).

**When it occurs:** Any before-context trigger that contains DML on `OpportunitySplit`, whether directly or through a helper class that is called from the before context.

**How to avoid:** Move all `OpportunitySplit` DML to an after-insert or after-update handler. If the logic is triggered by `OpportunityTeamMember` inserts, register the trigger for `after insert` on that object and perform all split work there.

---

## Gotcha 2: Team Member Deletion Cascade-Deletes Splits Before After-Delete Fires

**What happens:** When an `OpportunityTeamMember` record is deleted, the platform automatically deletes all `OpportunitySplit` records for that user on that Opportunity as a cascade operation. By the time the `after delete` trigger fires on `OpportunityTeamMember`, the split records are already gone.

**When it occurs:** Any `OpportunityTeamMember` deletion — via UI, API, or Apex DML. The cascade is platform-enforced and cannot be overridden.

**How to avoid:** Do not attempt to delete split records manually in an `OpportunityTeamMember` after-delete handler — they no longer exist. If the goal is to rebalance remaining splits after a team member removal, query the remaining team members in after-delete and redistribute from that reduced set. Never assume split records are present after a team member delete.

---

## Gotcha 3: Revenue Split Percentages Must Sum to Exactly 100

**What happens:** The platform enforces a constraint that all `OpportunitySplit` records for a single Opportunity under a Revenue split type must have `SplitPercentage` values that sum to exactly 100. If any DML operation leaves the total at 99 or 101 (e.g. due to integer rounding), the entire DML statement fails with `FIELD_INTEGRITY_EXCEPTION: The sum of all revenue splits must equal 100%`.

**When it occurs:** Inserting or updating split records when integer division distributes shares unevenly — e.g. 3 members each receiving `Integer(100/3) = 33` produces a total of 99. This is a test failure as well as a production failure.

**How to avoid:** Use explicit remainder arithmetic. Compute `baseShare = 100 / count` and `remainder = 100 - (baseShare * count)`. Assign `baseShare + remainder` to the first record. Always assert the sum before issuing DML in tests. This constraint applies only to Revenue split types — Overlay types are unconstrained.

---

## Gotcha 4: Trigger.oldMap Is Null on Insert — NullPointerException Risk

**What happens:** `Trigger.oldMap` is only populated for update and delete operations. On insert, it is `null`. A handler method that calls `oldMap.get(opp.Id)` without first checking for insert context will throw a `NullPointerException` that is surfaced to the user as an unhandled exception.

**When it occurs:** Any handler method shared between insert and update contexts that accesses `Trigger.oldMap` directly — a common mistake when copy-pasting update handlers for insert reuse.

**How to avoid:** Either gate the method call with `if (Trigger.isUpdate)` before invoking any logic that reads `oldMap`, or pass `null` safely and add a null check at the call site (`if (oldMap != null && oldMap.containsKey(opp.Id))`). Never access `oldMap` inside an insert-context execution path.

---

## Gotcha 5: Reparenting Leaves Stale Rollups on the Former Parent Account

**What happens:** When an Opportunity's `AccountId` is changed in an update, a rollup trigger that only reads `Trigger.new` will update the new parent Account but leave an inflated `Open_Pipeline__c` total on the old parent Account. The stale data persists until another Opportunity on that Account is saved.

**When it occurs:** Any Opportunity update where `AccountId` changes — including merges, data migrations, and user corrections. This is easy to miss because stage-change tests rarely change AccountId.

**How to avoid:** In the rollup handler, collect AccountIds from both `Trigger.new` and `Trigger.oldMap.values()`. A simple pattern: iterate `Trigger.oldMap.values()` and add `old.AccountId` to the same `Set<Id>` used for `Trigger.new` AccountIds. The aggregate query then recalculates both the old and new parent, zeroing out the former if no open Opportunities remain.
