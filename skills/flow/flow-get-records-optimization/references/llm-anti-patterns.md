# LLM Anti-Patterns — Get Records

## Anti-Pattern 1: Get Records Inside Loop

**What the LLM generates:** a neat loop with a per-iteration lookup.

**Why it happens:** imperative mental model.

**Correct pattern:** collect IDs, one Get Records outside the loop,
match in-memory.

## Anti-Pattern 2: "Automatically Store All Fields"

**What the LLM generates:** accepts the Flow builder default.

**Why it happens:** path of least resistance.

**Correct pattern:** explicit fields only.

## Anti-Pattern 3: No Explicit Limit

**What the LLM generates:** relies on 50k default.

**Why it happens:** "the filter is narrow enough."

**Correct pattern:** cap matches the flow's design: 1 for single, a
meaningful upper bound for collections.

## Anti-Pattern 4: Leading-Wildcard LIKE

**What the LLM generates:** `Name LIKE '%term%'`.

**Why it happens:** mirrors user input search.

**Correct pattern:** trailing wildcard only, or SOSL.

## Anti-Pattern 5: Sort Before Limit On Unindexed Field

**What the LLM generates:** sort clause on a free-text field, limit 10.

**Why it happens:** "the limit protects me."

**Correct pattern:** sort on an indexed field, or filter first to
reduce volume before sort.

## Anti-Pattern 6: Re-Query On Every Screen

**What the LLM generates:** each screen in a Screen Flow re-runs the
same Get Records.

**Why it happens:** copy-paste screen design.

**Correct pattern:** query once, pass the variable forward.
