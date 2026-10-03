# Gotchas: Roll Up Summary Alternatives

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each one names the official source it rests on.

## Gotcha 1: Merges reparent children without firing child triggers

**What happens:** Two Accounts are merged. The losing Account's children move to the winner, but the child trigger that maintains the winner's lookup total never runs. The winner's count is now low.

**When it occurs:** On any merge of a parent that has trigger-maintained totals.

**How to avoid:** Recompute the winning parent in an Account after-delete handler (the losing rows carry `MasterRecordId`), and run a scheduled recompute.

**Source:** Apex Developer Guide (262), "Triggers and Merge Statements": "Any child records that are reparented as a result of the merge operation do not fire triggers"; "Operations That Don't Invoke Triggers."

---

## Gotcha 2: Cascaded deletes skip the child trigger

**What happens:** Deleting a master record cascades to its detail rows. Those detail rows also look up to a second parent with a custom total, and that total stays high.

**When it occurs:** When a child is master-detail to one parent and lookup to another parent that carries a trigger-maintained rollup.

**How to avoid:** Handle the cascade in the master's delete trigger, or rely on a scheduled recompute.

**Source:** Apex Developer Guide (262), "Operations That Don't Invoke Triggers": "Cascading delete operations. Only records that initiate a delete cause trigger evaluation."

---

## Gotcha 3: Undeleting a parent restores children silently

**What happens:** An Account is undeleted from the Recycle Bin and its child records come back. Only the Account after undelete trigger runs, so child-driven totals on other parents do not move.

**When it occurs:** On undelete of top-level records whose children feed lookup rollups.

**How to avoid:** Recompute affected parents from the top-level undelete trigger, or rely on the repair job.

**Source:** Apex Developer Guide (262), "Triggers and Recovered Records": "The after undelete trigger events only run on top-level objects."

---

## Gotcha 4: Record-triggered flows have no after-delete or undelete trigger

**What happens:** A Flow rollup designed with "after delete" and "after undelete" steps cannot be built. The only delete option runs before the record is deleted, so a recount by Get Records still includes the row being deleted.

**When it occurs:** When a Flow replaces a trigger-based or DLRS rollup.

**How to avoid:** In the before-delete flow, filter the recount with `Id` not equal to `$Record.Id`, or subtract the triggering record's value. Cover undeletes with a scheduled recompute.

**Source:** Metadata API Developer Guide (262), "Flow": `triggerType` values include `RecordAfterSave`, `RecordBeforeSave`, and `RecordBeforeDelete` ("before the record is deleted from the database"); `recordTriggerType` values are Create, Update, CreateAndUpdate, Delete, and None.

---

## Gotcha 5: SUM over a large parent burns query rows

**What happens:** A recompute of a parent with tens of thousands of children fails on the query-row limit even though it runs one query.

**When it occurs:** SUM, MIN, MAX, and AVG count every aggregated row as a query row.

**How to avoid:** Prefer COUNT where it answers the question (one row, or one per group). Recompute very large parents in Batch Apex with smaller scopes.

**Source:** Apex Developer Guide (262), "Working with SOQL Aggregate Functions," note on query rows.

---

## Gotcha 6: Parent locks during loads

**What happens:** A bulk load of children fails with lock errors on parents, and the rollup update makes the window longer.

**When it occurs:** When child rows for the same parent are spread across batches, or one parent has thousands of children (data skew).

**How to avoid:** Group child rows by parent ID in the same batch. Write only parents whose total changed. Keep skew low.

**Source:** Best Practices for Deployments with Large Data Volumes (262), "Minimizing parent record-locking conflicts" and the data skew case study.

---

## Gotcha 7: Native roll-ups re-save the parent and grandparent

**What happens:** Adding a child fires the parent's save procedure, and a grandparent with a roll-up is saved too. Parent triggers and flows run on edits that users made only to children.

**When it occurs:** When parent automation assumes it runs only on direct parent edits.

**How to avoid:** Make parent automation idempotent and check which fields changed.

**Source:** Apex Developer Guide (262), "Triggers and Order of Execution," steps 16 and 17.

---

## Gotcha 8: Deleting a native roll-up through Metadata API purges it

**What happens:** A destructive deploy removes a roll-up summary field while migrating to a custom total. The field skips the Recycle Bin and cannot be restored.

**When it occurs:** On `destructiveChanges.xml` deploys that include a roll-up summary field.

**How to avoid:** Back up the field definition, report references, and current values before the destructive deploy.

**Source:** Metadata API Developer Guide (262), deploy notes: "When you delete a roll-up summary field using Metadata API, the field isn't saved in the Recycle Bin. The field is purged even if you don't set the purgeOnDelete deployment option to true."

---

## Gotcha 9: Opportunity product edits skip Opportunity triggers but still roll up

**What happens:** Editing an opportunity product updates the Opportunity's native roll-ups, but Opportunity before and after triggers and validation rules do not run.

**When it occurs:** When custom totals on Opportunity are maintained by Opportunity triggers and expected to react to line edits.

**How to avoid:** Maintain line-driven totals from the OpportunityLineItem trigger, not the Opportunity trigger.

**Source:** Apex Developer Guide (262), trigger considerations: "The before and after triggers and the validation rules don't fire for an opportunity when you modify an opportunity product ... However, roll-up summary fields do get updated."
