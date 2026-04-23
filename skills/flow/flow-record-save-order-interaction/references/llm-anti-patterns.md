# LLM Anti-Patterns — Save Order

## Anti-Pattern 1: Use After-Save For Same-Record Field Updates

**What the LLM generates:** record-triggered Flow "After Save" that
updates a field on the triggering record.

**Why it happens:** defaults to after-save.

**Correct pattern:** before-save Flow. Same-record, no DML, runs in
step 2.

## Anti-Pattern 2: Expect Roll-Up In Before-Save

**What the LLM generates:** before-save Flow that reads a roll-up
summary field.

**Why it happens:** "the record has a field, read it."

**Correct pattern:** roll-ups recalc after commit. Put logic on the
parent's after-save.

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

**What the LLM generates:** "the flow will see the record after step 7."

**Why it happens:** conflation.

**Correct pattern:** platform-event-triggered flows are separate
transactions. Reason about them independently.
