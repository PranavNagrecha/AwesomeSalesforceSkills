# LLM Anti-Patterns — Order of Execution Deep Dive

Common mistakes AI coding assistants make when generating or advising on Salesforce order of execution. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Placing After-Save Flows at the Same Step as After Triggers

**What the LLM generates:** Statements like "after-save Flows and after triggers both run after the record is saved, so they are equivalent in timing" or code designs that assume a Flow-created record will be available when an after trigger queries for it.

**Why it happens:** LLMs conflate "after save" (the conceptual grouping) with "same step." After triggers are step 8; after-save Flows are step 14. The gap of six steps (assignment rules, auto-response rules, workflow rules, escalation rules, legacy Process Builder / workflow-launched Flows) is significant and not intuitive from the label alone.

**Correct pattern:**

```
After Apex trigger  → step 8  (record Id available, same transaction)
After-save Flow     → step 14 (runs after workflow rules and Process Builder)

A record created by the after trigger IS visible to the after-save Flow.
A record created by the after-save Flow is NOT visible to the after trigger.
```

**Detection hint:** Any response that uses "after save" as a single category without distinguishing step 8 from step 14 should be flagged. Also flag "step 15" for after-save Flows — that number comes from a superseded version of the docs page (step 15 is now entitlement rules).

---

## Anti-Pattern 2: Claiming Workflow Field Updates Cause Infinite Trigger Loops

**What the LLM generates:** Warnings that "workflow field updates will cause an infinite loop in your trigger" or suggestions to add a Boolean guard to prevent infinite recursion caused specifically by workflow field updates.

**Why it happens:** Recursion is a genuine concern for after triggers that perform DML. LLMs over-generalize this to workflow field updates, which are actually bounded: they trigger at most one additional pass of before/after triggers.

**Correct pattern:**

```
Workflow field update re-fire (step 11):
- Before update and after update triggers re-fire exactly once
  ("one more time (and only one more time)" — Apex Developer Guide)
- System validations re-run; custom validation rules, duplicate rules,
  escalation rules, and record-triggered Flows do NOT re-run
- No infinite loop is possible from workflow field updates alone

Infinite loops require: after trigger → DML on same object → trigger re-fires → DML again
Recursion guard (static Set<Id>) is needed for that pattern, not for workflow field updates.
```

**Detection hint:** Look for "infinite loop" combined with "workflow field update" in the same sentence. The pairing is incorrect.

---

## Anti-Pattern 3: Claiming Before-Save Flow vs. Before Trigger Order Is Indeterminate

**What the LLM generates:** Statements like "before-save Flows and before triggers both run at step 3, and Salesforce does not guarantee which runs first, so the result is indeterminate — never rely on their relative order." Also: step sequences that collapse the two into one shared step, or that place before-save Flows after validation rules.

**Why it happens:** For years the Apex Developer Guide's order-of-execution list did place before triggers at step 3 and did not enumerate before-save Flows as their own step, and a large volume of blog and forum content was written against that list. That guidance has been superseded. The current page lists **20 steps**, with before-save record-triggered Flows at **step 3** and before triggers at **step 4** — two separate, consecutively numbered steps.

**This is the highest-severity error in this domain**, because it does not merely misnumber a step: it converts a deterministic, documented ordering into an imagined race condition, and then advises the reader to design around uncertainty that does not exist.

**Correct pattern:**

```
Step 3: Execute record-triggered flows configured to run BEFORE the record is saved
Step 4: Execute all before triggers
Step 5: System validation re-run + custom validation rules

The order is DETERMINATE and documented:
  before-save Flow (3)  ALWAYS runs before  before trigger (4).

Therefore, if both write the same field:
  the BEFORE TRIGGER wins, on every transaction, in every org.

The fix is single field ownership — or making the trigger (the later
writer) conditional so it acts as a fallback. The fix is NOT "add a
guard because the order might flip"; it cannot flip.
```

**What IS still order-sensitive:** the relative order of *multiple record-triggered Flows of the same type on the same object*. That is controlled by the Flow `triggerOrder` field (Metadata API 54.0+, surfaced as Flow Trigger Explorer), not left to chance. Separately, step 13 (Process Builder and workflow-launched Flows) is documented as running "not in a guaranteed order" — that caveat belongs to step 13, not to steps 3 and 4.

**Detection hint:** Flag any output containing "indeterminate," "no guaranteed order," "whichever runs second wins," or "race" **in the same sentence as** before-save Flow and before trigger. Also flag any sequence that puts before triggers at step 3 with before-save Flows folded into it, any total step count of 18 or 19, and any sequence showing before-save Flows after validation rules. A model that has learned the old list will usually reveal it by citing "18 steps" or by putting after-save Flows at step 15.

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

**Why it happens:** It is intuitive that validation should gate execution. In most frameworks, input validation happens first. Salesforce inverts this: before-save Flows (step 3) and before triggers (step 4) both run before custom validation rules (step 5).

**Correct pattern:**

```
Step 3: Before-save record-triggered Flows run — they CAN introduce or fix bad data
Step 4: Before triggers run — same, and they see what step 3 wrote
Step 5: System validation re-runs (required fields, field lengths, foreign keys)
        AND custom validation rules evaluate — AFTER steps 3 and 4

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

**Why it happens:** `@future` is often described as "asynchronous Apex" without emphasizing that it executes in a separate transaction after the current one commits (step 19 commit, step 20 post-commit logic).

**Correct pattern:**

```
@future methods:
- Are queued at the point they are called but do NOT execute until after the
  commit at step 19 — they run as part of the post-commit logic at step 20
- Run in a completely separate transaction with fresh governor limits
- Their results are NOT visible to any code in the originating transaction
- If the originating transaction rolls back, the @future call is cancelled

Use @future for: fire-and-forget side effects, callouts, post-commit notifications
Do NOT use @future for: work whose results must be available in the same transaction
```

**Detection hint:** Any code that calls `@future` and then reads from a field or record expecting to see the future method's writes within the same transaction.
