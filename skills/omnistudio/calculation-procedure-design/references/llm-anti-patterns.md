# LLM Anti-Patterns — Calculation Procedures

## Anti-Pattern 1: Apex For Tabular Rules

**What the LLM generates:** an Apex class with a 200-line if-else ladder
replicating a rate card.

**Why it happens:** default to "code."

**Correct pattern:** a Calculation Matrix. Rules live with business, not
with devs.

## Anti-Pattern 2: Overlapping Ranges Because "Ranges Are Inclusive"

**What the LLM generates:** `16-24` and `24-64`, with 24 in both.

**Why it happens:** inclusive/exclusive confusion.

**Correct pattern:** unambiguous bands — `16-24`, `25-64`.

## Anti-Pattern 3: Editing Active Matrix

**What the LLM generates:** update the existing matrix to fix a rate.

**Why it happens:** direct editing is fastest.

**Correct pattern:** publish a new version, activate with effective date.

## Anti-Pattern 4: No Fallback Row

**What the LLM generates:** matrix without wildcard row.

**Why it happens:** assumes all inputs are known.

**Correct pattern:** explicit wildcard fallback row, or explicit raise in
a following step.

## Anti-Pattern 5: Cache-Less Hot Procedure

**What the LLM generates:** FlexCard calls Calculation Procedure on every
input change.

**Why it happens:** unaware of caching layer.

**Correct pattern:** wrap in a cacheable Integration Procedure with a
versioned cache key (see `omnistudio/integration-procedure-cacheable-patterns`).
