# LLM Anti-Patterns — Agentforce Testing

## Anti-Pattern 1: Exact-Match Response Assertions

**What the LLM generates:** `assertEquals("Your refund is pending.",
response)`.

**Why it happens:** unit-test instinct.

**Correct pattern:** structure checks — topic, action, contains / not
contains, JSON shape.

## Anti-Pattern 2: No Adversarial Tests

**What the LLM generates:** coverage only for happy paths.

**Why it happens:** "LLM behaves if prompt is friendly."

**Correct pattern:** 6 categories of adversarial cases; zero-tolerance
metrics.

## Anti-Pattern 3: PII In Test Prompts

**What the LLM generates:** real-looking SSNs, real customer emails.

**Why it happens:** copy-paste from prod logs.

**Correct pattern:** synthetic PII, strip before adding to corpus.

## Anti-Pattern 4: Revert On First Divergence

**What the LLM generates:** treat any golden failure as a bug to
revert.

**Why it happens:** unaware models improve.

**Correct pattern:** triage: regression vs improvement. Update golden
after human review if improvement.

## Anti-Pattern 5: One-Shot Suite, Never Revisited

**What the LLM generates:** 200 goldens at launch, never updated.

**Why it happens:** suite is done once and forgotten.

**Correct pattern:** quarterly prune + add; weekly prod replay.
