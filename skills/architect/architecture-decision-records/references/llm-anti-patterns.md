# LLM Anti-Patterns — ADRs

## Anti-Pattern 1: No Alternatives Considered

**What the LLM generates:** skips straight to Decision + Consequences.

**Why it happens:** the chosen path is obvious to the author.

**Correct pattern:** force at least two rejected alternatives with
reason-rejected. If you truly cannot name any, the decision is
premature.

## Anti-Pattern 2: Consequences: Positives Only

**What the LLM generates:** "faster, simpler, more scalable."

**Why it happens:** wants to sell the decision.

**Correct pattern:** list at least one real negative tradeoff.
Decisions without downsides are usually not real decisions.

## Anti-Pattern 3: Edit Old ADR To Reflect New Decision

**What the LLM generates:** rewrites ADR-0007 in place to match
current thinking.

**Why it happens:** "keep it accurate."

**Correct pattern:** supersede with a new ADR. Old ADR's value is
historical.

## Anti-Pattern 4: Per-Team Numbering

**What the LLM generates:** `adr/frontend/0001-...` and
`adr/backend/0001-...`.

**Why it happens:** mirrors team structure.

**Correct pattern:** single global sequence. Teams can rearrange; the
ADRs do not.

## Anti-Pattern 5: ADR For Every PR

**What the LLM generates:** a 40-ADR backlog of routine decisions.

**Why it happens:** "write it down."

**Correct pattern:** reserve ADRs for multi-quarter impact. Routine
choices belong in PR descriptions.

## Anti-Pattern 6: ADR As Spec Document

**What the LLM generates:** 10-page ADR with API definitions and
sequence diagrams.

**Why it happens:** conflates decision + design.

**Correct pattern:** one-page ADR. Link out to the design doc.
