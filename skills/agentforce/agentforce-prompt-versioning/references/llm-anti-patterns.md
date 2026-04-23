# LLM Anti-Patterns — Prompt Versioning

## Anti-Pattern 1: UI-Only Edits

**What the LLM generates:** "Open Prompt Builder and edit the template."

**Why it happens:** suggests the direct UI flow.

**Correct pattern:** retrieve metadata to repo; edit in repo; deploy.

## Anti-Pattern 2: In-Place Rename

**What the LLM generates:** renames prompt without bumping the suffix.

**Why it happens:** treats rename as cosmetic.

**Correct pattern:** rename means v-bump; update all callers.

## Anti-Pattern 3: No Model Pin

**What the LLM generates:** `<modelVersion>auto</modelVersion>`.

**Why it happens:** defaults.

**Correct pattern:** pin critical topics; schedule re-evals.

## Anti-Pattern 4: Delete-Then-Deploy

**What the LLM generates:** remove old prompt and deploy.

**Why it happens:** cleanup instinct.

**Correct pattern:** 0% traffic for 7 days, then delete.

## Anti-Pattern 5: Policy Text Inside Prompt

**What the LLM generates:** prompt includes "as of 2026-04, refund
window is 30 days."

**Why it happens:** reads natural in the prompt.

**Correct pattern:** inject `refund_window_days` variable; keep policy
in data.
