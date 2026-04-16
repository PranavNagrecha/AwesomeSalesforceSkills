# Gotchas — Large Data Volume Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LIKE and custom index sampling

**What happens:** The query optimizer samples up to one hundred thousand rows to decide whether a leading-`%` LIKE predicate can use a custom index.

**When it occurs:** Text search-style filters on large custom objects in integrations or Apex loops.

**How to avoid:** Prefer selective equality or prefix filters on indexed fields; redesign integrations that depend on non-sargable LIKE patterns at LDV scale.

---

## Gotcha 2: OR defeats indexes unless every branch qualifies

**What happens:** For OR conditions, the optimizer may abandon index paths unless each branch is selective and indexed; thresholds are stricter than for AND.

**When it occurs:** Dynamic SOQL builders that concatenate OR across optional search fields.

**How to avoid:** Restructure into union-style batches, separate queries per branch, or require at least one highly selective indexed predicate.

---

## Gotcha 3: Divisions require license and scale gates

**What happens:** Divisions only apply when the org meets documented scale and license thresholds; they are not a universal knob for small orgs.

**When it occurs:** Teams enable divisions hoping for a quick fix on moderately sized objects.

**How to avoid:** Confirm eligibility in official division documentation before baking divisions into the architecture; otherwise invest in selectivity and skew fixes first.
