# LLM Anti-Patterns — Agentforce Cost Optimization

## Anti-Pattern 1: Cutting Cost Before Measuring

**What the LLM generates:** "Reduce retriever k to 3 and switch to a smaller model."

**Why it happens:** These are common levers.

**Correct pattern:** Measure first. The contributor driving cost may be topic instructions or conversation history, not retrieval.

## Anti-Pattern 2: Trimming Examples Uniformly

**What the LLM generates:** "Cut every topic's examples to one."

**Why it happens:** Uniform cuts are easy to describe.

**Correct pattern:** Evaluate per topic. Some topics need 2-3 examples for quality; others tolerate zero.

## Anti-Pattern 3: Optimizing Tool Output First

**What the LLM generates:** "Add field projection to every Apex action."

**Why it happens:** Engineering-touchable.

**Correct pattern:** Tool output is usually a small contributor. Topics and grounding dominate. Attack the big contributors first.

## Anti-Pattern 4: Model Tier Downgrade With No A/B

**What the LLM generates:** "Use a smaller model for reasoning steps."

**Why it happens:** It's a one-click win if quality holds.

**Correct pattern:** A/B against the eval set before migrating. Quality regressions are subtle.

## Anti-Pattern 5: Ignoring Conversation Growth

**What the LLM generates:** Optimization plan with no attention to long sessions.

**Why it happens:** Per-turn metrics hide cumulative token counts.

**Correct pattern:** Include conversation-length distribution in the cost model; add summarization for long sessions.
