# LLM Anti-Patterns — Order of Execution Deep Dive

Common mistakes AI coding assistants make when generating or advising on Salesforce order of execution. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Placing After-Save Flows at the Same Step as After Triggers

**What the LLM generates:** Statements like "after-save Flows and after triggers both run after the record is saved, so they are equivalent in timing" or code designs that assume a Flow-created record will be available when an after trigger queries for it.

**Why it happens:** LLMs conflate "after save" (the conceptual grouping) with "same step." After triggers are step 8; after-save Flows are step 15. The gap of 7 steps (assignment rules, workflow, process builder, escalation) is significant and not intuitive from the label alone.

**Correct pattern:**

```
After Apex trigger  → step 8  (record Id available, same transaction)
After-save Flow     → step 15 (runs after workflow and process builder)

A record created by the after trigger IS visible to the after-save Flow.
A record created by the after-save Flow is NOT visible to the after trigger.
```

**Detection hint:** Any response that uses "after save" as a single category without distinguishing step 8 from step 15 should be flagged.

---

## Anti-Pattern 2: Claiming Workflow Field Updates Cause Infinite Trigger Loops

**What the LLM generates:** Warnings that "workflow field updates will cause an infinite loop in your trigger" or suggestions to add a Boolean guard to prevent infinite recursion caused specifically by workflow field updates.

**Why it happens:** Recursion is a genuine concern for after triggers that perform DML. LLMs over-generalize this to workflow field updates, which are actually bounded: they trigger at most one additional pass of before/after triggers.

**Correct pattern:**

```
Workflow field update re-fire:
- Triggers re-fire exactly once (one additional pass)
- Workflow rules do NOT re-evaluate during the re-fire
- No infinite loop is possible from workflow field updates alone

Infinite loops require: after trigger → DML on same object → trigger re-fires → DML again
Recursion guard (static Set<Id>) is needed for that pattern, not for workflow field updates.
```

**Detection hint:** Look for "infinite loop" combined with "workflow field update" in the same sentence. The pairing is incorrect.

---

## Anti-Pattern 3: Placing Before-Save Flows After Before Triggers in Step Order

**What the LLM generates:** Step sequences that list "before Apex triggers" at step 3 and "before-save record-triggered Flows" at a separate later step, or diagrams showing before-save Flows running after validation rules.

**Why it happens:** Training data often describes before-save Flows as a Flow variant and groups all Flows together late in the sequence. The Apex Developer Guide is explicit that before-save Flows run at the same step as before triggers (step 3).

**Correct pattern:**

```
Step 3: Execute all before triggers
        ↳ This includes before-save record-triggered Flows
        ↳ Relative order between a specific before trigger and a before-save Flow
          at step 3 is not guaranteed by Salesforce

Step 5: Custom validation rules (runs AFTER step 3)
```

**Detection hint:** Any sequence that shows before-save Flows after validation rules is incorrect.

---

## Anti-Pattern 4: Recommending a Static Boolean Instead of a Static Set<Id> for Recursion Guards

**What the LLM generates:** A recursion guard using `private static Boolean alreadyRan = false;` that is set to `true` on first entry.

**Why it happens:** The Boolean guard is simpler to write and is commonly shown in tutorials. It works correctly for single-record scenarios but is incorrect for bulk operations.

**Correct pattern:**

```apex
// Wrong: Boolean guard blocks ALL records after the first trigger fire
private static Boolean alreadyRan = false;
if (alreadyRan) return;
alreadyRan = true;
// ... This prevents processing records 2-200 in a bulk DML of 200 records
// if the trigger fires in multiple batches within the same transaction.

// Correct: Set<Id> guard tracks per-record processing
private static Set<Id> processedIds = new Set<Id>();
List<SObject> toProcess = new List<SObject>();
for (SObject rec : Trigger.new) {
    if (!processedIds.contains(rec.Id)) {
        processedIds.add(rec.Id);
        toProcess.add(rec);
    }
}
```

**Detection hint:** `static Boolean` in a trigger handler class for recursion prevention. Evaluate whether it blocks legitimate bulk processing.

---

## Anti-Pattern 5: Stating That Validation Rules Run Before Before Triggers

**What the LLM generates:** Advice like "validation rules prevent your before trigger from running with invalid data" or "add a validation rule to guard against bad input before your trigger executes."

**Why it happens:** It is intuitive that validation should gate execution. In most frameworks, input validation happens first. Salesforce inverts this: before triggers (step 3) run before validation rules (step 5).

**Correct pattern:**

```
Step 3: Before triggers run — they CAN introduce bad data or fix bad data
Step 4: System validation (required fields, field lengths, foreign keys)
Step 5: Custom validation rules — they evaluate AFTER before triggers have run

Therefore:
- A before trigger CAN supply a missing required field and pass validation.
- A before trigger CAN write an invalid value that validation then rejects.
- Validation rules CANNOT prevent a before trigger from executing.
- To block trigger logic on invalid input, use addError() inside the trigger itself.
```

**Detection hint:** Any claim that validation rules "prevent" or "block" before trigger execution is incorrect.

---

## Anti-Pattern 6: Treating @future Calls as Running Within the Current Transaction

**What the LLM generates:** Code that calls an `@future` method inside a trigger and then expects the future method's results to be available within the same transaction, or designs that use `@future` to avoid DML governor limits within the current transaction while still relying on their side effects.

**Why it happens:** `@future` is often described as "asynchronous Apex" without emphasizing that it executes in a separate transaction after the current one commits (step 18 and beyond).

**Correct pattern:**

```
@future methods:
- Are queued at the point they are called but do NOT execute until after commit (step 18)
- Run in a completely separate transaction with fresh governor limits
- Their results are NOT visible to any code in the originating transaction
- If the originating transaction rolls back, the @future call is cancelled

Use @future for: fire-and-forget side effects, callouts, post-commit notifications
Do NOT use @future for: work whose results must be available in the same transaction
```

**Detection hint:** Any code that calls `@future` and then reads from a field or record expecting to see the future method's writes within the same transaction.
