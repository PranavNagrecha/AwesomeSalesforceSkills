# LLM Anti-Patterns — Flow Migration From Trigger

## Anti-Pattern 1: Migrating without benchmarking

**What the LLM generates:** "Just migrate — Flow can do it."

**Why it happens:** LLMs don't think about per-element overhead.

**Correct pattern:** Benchmark bulk scenarios before migrating. Flow adds overhead; if the Apex handler runs hot, Flow may not meet SLA.

---

## Anti-Pattern 2: Deleting the Apex trigger immediately

**What the LLM generates:** Migration PR deactivates and deletes the Apex trigger in one commit.

**Why it happens:** LLMs treat "migration" as "replace".

**Correct pattern:** Deactivate trigger; leave source code for 2 release cycles; delete only after stability confirmed.

---

## Anti-Pattern 3: No test-parity check

**What the LLM generates:** Migration without running existing tests against the new Flow.

**Why it happens:** LLMs assume "same logic = same tests pass".

**Correct pattern:** Run the full test suite in sandbox with Flow active; every pre-migration test must still pass.

---

## Anti-Pattern 4: Full-scope cutover for complex triggers

**What the LLM generates:** Attempts to migrate a 1000-line handler with SavePoints and recursion to Flow in one commit.

**Why it happens:** LLMs don't recognize migration-infeasibility patterns.

**Correct pattern:** Check the migration decision matrix first. If any "❌ No" row applies, KEEP Apex or split the migration.

---

## Anti-Pattern 5: Skipping shadow-mode

**What the LLM generates:** Direct cutover in production.

**Why it happens:** LLMs treat feature-flagging as optional.

**Correct pattern:** Custom Permission gate. Ramp from 1 user to 10% to 100%. Rollback = revoke permission.

---

## Anti-Pattern 6: Assuming Before-Save semantics are identical to Before-trigger

**What the LLM generates:** Migrates a Before-trigger to Before-Save Flow as if they fire at the same order-of-execution point.

**Why it happens:** LLMs conflate "fires before save" concepts.

**Correct pattern:** Re-read the trigger order of execution doc. Before-Save Flow fires AFTER Before-triggers; the field values your Flow reads may differ from what the Apex handler saw.
