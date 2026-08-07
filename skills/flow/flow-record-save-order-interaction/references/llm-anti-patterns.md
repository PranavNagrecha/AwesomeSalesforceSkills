# LLM Anti-Patterns — Save Order

## Anti-Pattern 1: Use After-Save For Same-Record Field Updates

**What the LLM generates:** record-triggered Flow "After Save" that
updates a field on the triggering record.

**Why it happens:** defaults to after-save.

**Correct pattern:** before-save Flow. Same-record, no DML, runs at
step 3.

## Anti-Pattern 2: Expect Roll-Up In Before-Save

**What the LLM generates:** before-save Flow that reads a roll-up
summary field.

**Why it happens:** "the record has a field, read it."

**Correct pattern:** the roll-up on the parent is not recalculated until
step 16 of the child's save, long after the before-save Flow ran at
step 3. Put logic that needs the roll-up on the parent's after-save
flow. (Step 16 precedes the commit at step 19 — "roll-ups recalc after
commit" is a common but incorrect gloss.)

## Anti-Pattern 3: Workflow + Record-Triggered Flow On Same Field

**What the LLM generates:** migrates half the workflows, leaves the
other half running the same field update.

**Why it happens:** incremental migration without ordering check.

**Correct pattern:** retire workflow or flow — never both writing the
same field.

## Anti-Pattern 4: Ignore Recursion, Add `Trigger.isExecuting` Guards

**What the LLM generates:** Apex guards without addressing the flow
that fires the loop.

**Why it happens:** trigger-only mental model.

**Correct pattern:** trace the chain across flow + trigger. Kill the
DML-causing step, not the symptom.

## Anti-Pattern 5: Treat Platform Event Flows As Part Of The Save Order

**What the LLM generates:** "the platform-event flow will see the record
after the save at step 7."

**Why it happens:** conflation.

**Correct pattern:** platform-event-triggered flows are separate
transactions. Reason about them independently.

## Anti-Pattern 6: Call Before-Save Flow vs Before Trigger Order "Indeterminate"

**What the LLM generates:** "Before-save Flows and Apex before triggers
both run at step 3, and Salesforce doesn't guarantee which goes first —
so if they write the same field the result is unpredictable. Don't rely
on the order." Sometimes framed as advice to "detect and correct" any
code that assumes a fixed order.

**Why it happens:** an older revision of the Apex Developer Guide's
order-of-execution list did not enumerate before-save Flows as their own
numbered step, and a large volume of writing filled that gap by
declaring the ordering unspecified. Models trained on it reproduce the
claim confidently, and because it sounds appropriately cautious it
survives review.

This is the most damaging error in this domain: it converts a documented,
deterministic ordering into an imagined race, and then tells the reader
to distrust correct code.

**Correct pattern:**

```text
Step 3: record-triggered flows configured to run BEFORE the record is saved
Step 4: all before triggers

Separate, consecutive, documented. The Flow ALWAYS runs first.
Both write the same field → the TRIGGER's value saves. Every time.

Fix = single field ownership. If both must write, condition the TRIGGER
(the later writer). Conditioning the Flow changes nothing.
```

**Detection hint:** flag "indeterminate", "not guaranteed", "unpredictable",
"whichever runs second", or "race" appearing alongside before-save Flow and
before trigger. Flag any claim that the two share step 3. Flag any total
step count other than 20, or after-save Flows placed anywhere but step 14
(step 15 is the most common stale value; step 15 is now entitlement rules).
