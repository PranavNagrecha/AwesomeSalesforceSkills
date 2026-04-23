# LLM Anti-Patterns — Performance Budgets

## Anti-Pattern 1: Single Global LCP Number

**What the LLM generates:** "budget LCP < 2.5 s globally."

**Why it happens:** one-size-fits-all.

**Correct pattern:** per-page-template budget. A login screen has a
very different baseline from a record page with a 40-field sidebar.

## Anti-Pattern 2: Bundle Size Only, No Wire Count

**What the LLM generates:** caps on `.js` size only.

**Why it happens:** tooling gives KB easily.

**Correct pattern:** include wire adapter count, imperative Apex
round-trips, and image weight.

## Anti-Pattern 3: Gate Without Waiver Path

**What the LLM generates:** hard CI fail, no exception.

**Why it happens:** discipline-first instinct.

**Correct pattern:** waiver system with expiring exceptions, otherwise
teams disable the gate under release pressure.

## Anti-Pattern 4: Lab Measurement Only

**What the LLM generates:** Lighthouse CI as the sole truth.

**Why it happens:** easy to automate.

**Correct pattern:** combine Lighthouse CI (gate) with CrUX field
monitoring (alerting). Lab misses real-user variability.

## Anti-Pattern 5: Budget Never Tightens

**What the LLM generates:** "set budgets once, forget."

**Why it happens:** scheduling fatigue.

**Correct pattern:** quarterly review, tighten toward observed 90th
percentile.

## Anti-Pattern 6: Counting Only Direct Imports

**What the LLM generates:** measures only the leaf `.js` file.

**Why it happens:** simple to implement.

**Correct pattern:** include transitive imports (shared utilities, i18n
catalogues). Use webpack/rollup analyse output.
