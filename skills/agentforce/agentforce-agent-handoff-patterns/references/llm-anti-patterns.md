# LLM Anti-Patterns — Agentforce Agent Handoff

## Anti-Pattern 1: "Handoff On Error" With No Trigger Design

**What the LLM generates:** "When the agent encounters an error, escalate to a human."

**Why it happens:** Error is the obvious trigger.

**Correct pattern:** Design triggers across six categories (user-initiated, confidence, scope, policy, authorization, technical). Error is only one.

## Anti-Pattern 2: Verbatim Transcript As Context

**What the LLM generates:** A handoff action that packs the entire turn history into the case description.

**Why it happens:** More context feels safer.

**Correct pattern:** Structured summary + transcript link. Human agents benefit from the summary; the link preserves raw history for audit.

## Anti-Pattern 3: No Deflection Path

**What the LLM generates:** Handoff logic that assumes a human is always available.

**Why it happens:** Happy path dominates design.

**Correct pattern:** Include deflection with a next-best-action when the queue is empty, off-hours, or the query truly belongs elsewhere.

## Anti-Pattern 4: Silent Transfer

**What the LLM generates:** Handoff fires without a user-facing message.

**Why it happens:** The transfer is a back-office action in the flow.

**Correct pattern:** Every handoff has an explicit user message, with expected wait when known.

## Anti-Pattern 5: Missing Confidence-Based Escalation

**What the LLM generates:** Handoff triggers only on hard errors.

**Why it happens:** Confidence is harder to define.

**Correct pattern:** Retry-then-escalate after N unsuccessful attempts on the same intent. Prevents loops.
