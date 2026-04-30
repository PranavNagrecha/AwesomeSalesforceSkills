# LLM Anti-Patterns — Flow Recursion and Re-Entry Prevention

Common mistakes AI coding assistants make when generating record-triggered Flow logic.

## Anti-Pattern 1: Suggesting a `static Boolean` flag in Flow

**What the LLM generates:**

> "Add a static Boolean flag at the top of the Flow to mark whether it has already run, similar to the trigger handler pattern in Apex."

**Why it happens:** Pattern transfer from Apex. The LLM knows the canonical recursion break and doesn't notice that Flow has no static-variable mechanism.

**Correct pattern:** Model the recursion guard as a record field (state, hash, or lock), or use a tightened entry condition that excludes the post-update state. Flow has no per-transaction static state; the recursion guard must live in record data.

**Detection hint:** Any Flow advice that mentions "static," "transient," or "in-memory flag." None of those concepts exist for Flow recursion control.

---

## Anti-Pattern 2: Recommending `ISCHANGED()` alone as a recursion guard

**What the LLM generates:**

> "Use `ISCHANGED({!$Record.Status__c})` as the entry condition to ensure the Flow only fires when the status field actually changes."

**Why it happens:** `ISCHANGED` looks like a guard. Until you realize the Flow's own DML triggers it just as user DML does.

**Correct pattern:** Pair `ISCHANGED` with a state guard. The minimum is `AND(ISCHANGED(field), field <> Last_Tracked_Field__c)` plus a corresponding update of `Last_Tracked_Field__c` at the end of the Flow.

**Detection hint:** Any Flow entry condition that uses `ISCHANGED` on a field the same Flow updates, with no comparison-based companion clause.

---

## Anti-Pattern 3: Recommending a time-based throttle ("don't run if updated in the last N seconds")

**What the LLM generates:**

```text
Decision: Was the record updated less than 30 seconds ago?
  Yes → exit
  No  → continue
```

**Why it happens:** Throttles are common in API rate-limit contexts and feel like a natural fit. They're a poor fit for save-cycle recursion.

**Correct pattern:** Use deterministic state. Two near-simultaneous user edits both deserve to fire the Flow; throttles silently skip the second. State guards distinguish "Flow's own write" from "user's write" without dropping legitimate work.

**Detection hint:** Any reference to "seconds ago," "rate-limit," or "debounce" inside Flow recursion advice.

---

## Anti-Pattern 4: Confusing before-save Flow exemption with cross-object exemption

**What the LLM generates:**

> "Use a before-save Flow to update the field — before-save Flows don't recurse, so the loop is impossible."

**Why it happens:** Before-save Flows do skip the second save on the same record. The LLM extends that property too far.

**Correct pattern:** Before-save Flows still participate in cross-object cascades. If your before-save Flow updates a related record, the related record's after-save Flow can still loop back. Only same-record self-recursion is exempted.

**Detection hint:** Any "use before-save to avoid recursion" advice paired with a Flow that updates related records.

---

## Anti-Pattern 5: Suggesting "deactivate the Flow during the save" (Apex `Skip` patterns)

**What the LLM generates:**

> "Have the Apex trigger set a custom setting 'Skip Flow' to TRUE before performing the cascading update."

**Why it happens:** The custom-setting bypass is a real (and sometimes appropriate) Apex-side technique. The LLM extends it into Flow when the actual problem is that the Flow's entry criteria are wrong.

**Correct pattern:** Fix the entry criteria. A Flow that needs an Apex flag to "skip" it on every cascading update has under-specified its trigger condition. The cleaner fix is a state guard or hash check that the Flow itself enforces. Reach for the bypass-flag pattern only when the alternative is a much more invasive refactor.

**Detection hint:** Any recommendation that adds a custom setting / custom metadata flag whose only purpose is "tell the Flow to skip itself." Usually a sign the entry condition needs work, not an outboard flag.
