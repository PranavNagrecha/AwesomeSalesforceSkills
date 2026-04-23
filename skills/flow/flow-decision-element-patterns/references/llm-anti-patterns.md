# LLM Anti-Patterns — Decision Element

## Anti-Pattern 1: Unnamed Default Outcome

**What the LLM generates:** leaves "Default Outcome" unlabeled.

**Why it happens:** it's the builder default.

**Correct pattern:** rename to the case it actually represents.

## Anti-Pattern 2: Implicit Null Equals Miss

**What the LLM generates:** `Field = 'Target'` as sole outcome,
expecting null to go default silently.

**Why it happens:** SQL mental model where NULL = NULL is null/false
anyway.

**Correct pattern:** decide explicitly: does null route to default or
a dedicated branch? Write that branch.

## Anti-Pattern 3: Sort Outcomes By Likelihood, Not Specificity

**What the LLM generates:** puts the wildest condition first because
it "covers most records."

**Why it happens:** statistical instinct.

**Correct pattern:** most specific first. Top-down evaluation.

## Anti-Pattern 4: Label-Based Pick-list Equality

**What the LLM generates:** `Status = 'In Progress'` (label).

**Why it happens:** reading from UI.

**Correct pattern:** API value, not label.

## Anti-Pattern 5: Deeply Nested Decision Trees

**What the LLM generates:** 4-deep Decision chain mirroring the
business description.

**Why it happens:** mirrors the narrative.

**Correct pattern:** flatten to one decision with explicit combined
outcomes, or extract sub-flow. Depth cap = 2.

## Anti-Pattern 6: Custom Logic Without Parens

**What the LLM generates:** custom condition logic like `1 AND 2 OR 3`.

**Why it happens:** assumes AND binds tighter.

**Correct pattern:** parenthesise explicitly: `(1 AND 2) OR 3`.
