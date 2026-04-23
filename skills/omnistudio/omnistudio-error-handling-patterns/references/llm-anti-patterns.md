# LLM Anti-Patterns — OmniStudio Error Handling

## Anti-Pattern 1: Leaving `Fail On Step Error` At Default

**What the LLM generates:** IP definitions with `Fail On Step Error` unset even on record writes.

**Why it happens:** The flag is easy to miss in the JSON export; defaults feel safe.

**Correct pattern:** Set the flag explicitly per step. Writes terminate on error; best-effort reads continue.

## Anti-Pattern 2: Generic Error Messages

**What the LLM generates:** "An error occurred. Please try again."

**Why it happens:** Without context the LLM produces the safest neutral sentence.

**Correct pattern:** Map each recoverable error to a business-readable message and an action ("Your payment method was declined. Use a different card or contact support."). Unrecoverable errors include a support path.

## Anti-Pattern 3: Retry Without Idempotency

**What the LLM generates:** A retry button that re-fires the IP with the same payload.

**Why it happens:** Retry is "just try again."

**Correct pattern:** Include a correlation ID generated on first attempt; downstream systems dedupe by correlation ID or external ID.

## Anti-Pattern 4: Swallowing DataRaptor Errors

**What the LLM generates:** IP that calls a DataRaptor Load and moves on without inspecting the response.

**Why it happens:** DataRaptors return an envelope even on failure.

**Correct pattern:** Inspect the envelope's `errors` array and route to failure if non-empty.

## Anti-Pattern 5: No Compensating Action On Multi-System Write

**What the LLM generates:** A two-system write with no rollback.

**Why it happens:** The happy path shipped; the failure path was never designed.

**Correct pattern:** Every multi-system write has a compensating DataRaptor or async cleanup plan. Partial success should be the designed norm, not a surprise.
