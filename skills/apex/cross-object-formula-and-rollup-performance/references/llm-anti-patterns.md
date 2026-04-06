# LLM Anti-Patterns — Cross-Object Formula and Rollup Performance

Common mistakes AI coding assistants make when generating or advising on cross-object formulas and rollup summary fields.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Stating the spanning limit as 10 instead of 15

**What the LLM generates:** "Salesforce limits cross-object formulas to 10 spanning relationships per object."

**Why it happens:** Older documentation and some community blog posts cited 10 as the limit. The actual limit is 15 unique spanning relationships per object (raisable to 20 via Support case). LLMs trained on mixed-era data conflate the old and current values.

**Correct pattern:**

```
The per-object limit is 15 unique spanning relationships across all formula fields,
validation rules, and workflow rules. Salesforce Support can raise it to a maximum of 20.
```

**Detection hint:** Look for the number 10 near "spanning" or "cross-object formula limit."

---

## Anti-Pattern 2: Claiming rollup values are available in after triggers

**What the LLM generates:** "In the after-update trigger on the child, query the parent's rollup field to get the updated total."

**Why it happens:** LLMs assume that "after trigger" means "after everything has finished." In reality, rollup recalculation happens at step 13 of the order of execution, which is after all child triggers but before the parent's own save cycle commits the new rollup value. The trigger runs too early.

**Correct pattern:**

```apex
// Do NOT query rollup value in after trigger — it is stale.
// Instead, enqueue a Queueable:
System.enqueueJob(new RollupDependentAction(parentIds));
```

**Detection hint:** SOQL query for a rollup field inside an after-insert or after-update trigger handler.

---

## Anti-Pattern 3: Suggesting native rollup on lookup relationships

**What the LLM generates:** "Add a roll-up summary field on Account to count related Contacts via the lookup relationship."

**Why it happens:** LLMs do not consistently distinguish master-detail from lookup relationships. Native rollup summary fields are only available on the master side of a master-detail relationship. Lookup relationships do not support native rollups.

**Correct pattern:**

```
Native roll-up summary fields require a master-detail relationship. For lookup
relationships, use a trigger-based rollup, DLRS (Declarative Lookup Rollup Summaries),
or a Flow-based approach.
```

**Detection hint:** "roll-up summary" combined with "lookup" in the same recommendation.

---

## Anti-Pattern 4: Ignoring record locking when suggesting Apex-managed rollups

**What the LLM generates:** An Apex trigger that queries the parent and updates the rollup field without FOR UPDATE, or without any mention of concurrent DML risk.

**Why it happens:** LLMs generate functionally correct code that works in isolation but fails under concurrent load. Without FOR UPDATE, two simultaneous child inserts can both read the parent's old value, compute their delta, and overwrite each other's update — producing an incorrect total.

**Correct pattern:**

```apex
List<Account> parents = [
    SELECT Id, Custom_Total__c
    FROM Account
    WHERE Id IN :parentIds
    FOR UPDATE  // Prevents concurrent overwrites
];
```

**Detection hint:** Absence of `FOR UPDATE` in any parent SOQL query inside a rollup trigger.

---

## Anti-Pattern 5: Recommending cross-object formula fields as filterable in SOQL

**What the LLM generates:** "Create a cross-object formula field and use it in your SOQL WHERE clause to filter records efficiently."

**Why it happens:** LLMs treat formula fields as equivalent to stored fields. Cross-object formula fields cannot be indexed and always cause a full table scan when used in SOQL WHERE clauses, regardless of record volume.

**Correct pattern:**

```
Cross-object formula fields are never indexable. If you need to filter on a
cross-object value in SOQL, denormalize the value into a stored field via trigger
or flow, then filter on the stored field. Request a custom index if needed.
```

**Detection hint:** SOQL WHERE clause referencing a formula field, especially one with `__c` that is known to be a formula.

---

## Anti-Pattern 6: Not accounting for undelete in Apex-managed rollups

**What the LLM generates:** A trigger handler that covers after-insert, after-update, and after-delete but omits after-undelete. The rollup value becomes permanently wrong after a record is restored from the Recycle Bin.

**Why it happens:** LLMs default to the three common trigger events and forget that Salesforce supports record recovery. Native rollups handle undelete automatically; Apex-managed rollups must explicitly handle it.

**Correct pattern:**

```apex
trigger ChildTrigger on Child__c (
    after insert, after update, after delete, after undelete
) {
    // Handler must cover all four events for rollup accuracy
}
```

**Detection hint:** Trigger definition missing `after undelete` when the handler manages a rollup calculation.
