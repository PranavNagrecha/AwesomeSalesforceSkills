# LLM Anti-Patterns — Flow Rollback Patterns

## Anti-Pattern 1: Writing the only copy of the failure evidence as a record the rollback cancels

**What the LLM generates:** Fault path that logs to a custom object with Create Records, then rolls back (or rolls back, then logs, and claims the log is erased).

**Why it happens:** LLMs treat "log first, rollback second" as the safe order. Rollback Records "cancels its pending record changes" (api_meta 264 L73986), and a log record created earlier is one of them.

**Correct pattern:** Write the evidence to a Publish Immediately platform event, which "can't be rolled back" (platform_events 264 L276-277), before or after the rollback. UNVERIFIED (2026-10-20): whether a Create Records log placed after the rollback persists is not in the corpus. The earlier version of this entry said "Log first, rollback second" and that a log after rollback would itself be rolled back; both sit badly with the documented behavior.

---

## Anti-Pattern 2: Assuming Rollback undoes callouts

**What the LLM generates:** Flow that does an HTTP callout and a DML, with Rollback as the fault handler — claims this makes the operation atomic.

**Why it happens:** LLMs generalize "transaction rollback" across systems.

**Correct pattern:** Rollback only affects Salesforce DML. External state needs compensation (second callout to undo, or acknowledging non-atomic boundary).

---

## Anti-Pattern 3: Using Delete Records instead of Rollback

**What the LLM generates:** Fault path that explicitly Deletes the records it earlier Created.

**Why it happens:** LLMs default to explicit deletes from traditional coding.

**Correct pattern:** Rollback Records is cheaper (one element, one action) and atomic. Delete Records can itself fault. UNVERIFIED (2026-10-20): "cheaper" is not in the corpus; Rollback Records is available only in screen flows (api_meta 264 L73987).

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

**Correct pattern:** Rollback failure is almost always a platform issue; retry won't help. Log the rollback failure and escalate. The Rollback Records element has no fault connector (api_meta 264 L73990-73992), so there is nothing to retry from; UNVERIFIED (2026-10-20): "almost always a platform issue".
