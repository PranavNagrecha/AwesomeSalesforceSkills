# LLM Anti-Patterns — DataRaptor Transform Optimization

## Anti-Pattern 1: Recommending Apex For Logic A Formula Handles

**What the LLM generates:** `AccountAddressFormatter.format(account)` Apex expression for a simple string concat.

**Why it happens:** Apex looks "more powerful" and the LLM reaches for it by default.

**Correct pattern:** Try formula first; only escalate to Apex when formula cannot express the logic.

## Anti-Pattern 2: Leaving Row-By-Row On Array Inputs

**What the LLM generates:** A Transform over a 200-row array without checking the bulk flag.

**Why it happens:** The designer hides the flag and defaults are inconsistent.

**Correct pattern:** Verify `isBulk` (or equivalent) in the export; set explicitly.

## Anti-Pattern 3: Adding Transforms Instead Of Merging

**What the LLM generates:** "Add a new Transform to handle the rename step."

**Why it happens:** Adding is additive and feels safe.

**Correct pattern:** Check whether an adjacent Transform can absorb the new mapping; merge if scopes match.

## Anti-Pattern 4: Trusting Formula Empty-Values As Real Data

**What the LLM generates:** Downstream logic that branches on `{ComputedField}` being empty.

**Why it happens:** Formula errors produce empties silently; the LLM assumes empty is intentional.

**Correct pattern:** Add a validation step or defensive Apex check; empty often means "formula reference broken."

## Anti-Pattern 5: Per-Row Apex That Could Be One Bulk Invocable

**What the LLM generates:** An Apex expression that fires N times per row for N-row arrays.

**Why it happens:** Apex expressions look row-scoped.

**Correct pattern:** Replace the Transform with an Invocable Apex that receives the full array and returns the transformed output in a single call.
