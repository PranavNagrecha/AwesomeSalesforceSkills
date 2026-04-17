# LLM Anti-Patterns — Flow Rollback Patterns

## Anti-Pattern 1: Rollback before logging

**What the LLM generates:** Fault path that rolls back immediately, then tries to log.

**Why it happens:** LLMs treat rollback as "the first thing on failure".

**Correct pattern:** Log first, rollback second. Logging after rollback means the log is itself rolled back.

---

## Anti-Pattern 2: Assuming Rollback undoes callouts

**What the LLM generates:** Flow that does an HTTP callout and a DML, with Rollback as the fault handler — claims this makes the operation atomic.

**Why it happens:** LLMs generalize "transaction rollback" across systems.

**Correct pattern:** Rollback only affects Salesforce DML. External state needs compensation (second callout to undo, or acknowledging non-atomic boundary).

---

## Anti-Pattern 3: Using Delete Records instead of Rollback

**What the LLM generates:** Fault path that explicitly Deletes the records it earlier Created.

**Why it happens:** LLMs default to explicit deletes from traditional coding.

**Correct pattern:** Rollback Records is cheaper (one element, one action) and atomic. Delete Records can itself fault.

---

## Anti-Pattern 4: Rollback on every fault

**What the LLM generates:** Every fault connector routes to Rollback.

**Why it happens:** LLMs generalize error handling.

**Correct pattern:** Rollback only when the partial state would violate a business invariant. Non-critical failures (logging, notifications) should take Silent End instead.

---

## Anti-Pattern 5: Publishing "Publish Immediately" + Rollback

**What the LLM generates:** Flow publishes an event with Publish Immediately, then does DML, then rolls back on fault — assumes event is undone.

**Why it happens:** LLMs don't distinguish the two publish modes.

**Correct pattern:** Use Publish After Commit if you want the event tied to transaction success. If Publish Immediately is needed, add a compensating event to the rollback path.

---

## Anti-Pattern 6: Rollback in subflow without parent coordination

**What the LLM generates:** Subflow fault → Rollback. Parent flow's earlier DML is silently undone.

**Why it happens:** LLMs treat subflows as isolated.

**Correct pattern:** Subflow returns an error flag; parent decides whether to rollback. Centralize rollback at the outermost flow.

---

## Anti-Pattern 7: Unbounded retry loop around Rollback

**What the LLM generates:** "If rollback fails, retry rollback" loop.

**Why it happens:** LLMs add retry logic reflexively.

**Correct pattern:** Rollback failure is almost always a platform issue; retry won't help. Log the rollback failure and escalate.
