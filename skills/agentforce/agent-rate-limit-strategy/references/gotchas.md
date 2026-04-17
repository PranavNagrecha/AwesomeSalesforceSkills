# Gotchas — Agent Rate Limit Strategy

## Gotcha 1: Estimating tokens from chars misses long RAG context

**What happens:** Estimate says 500 tokens; reality is 5000 after grounding.

**When it occurs:** Data Cloud grounding enabled.

**How to avoid:** Add grounding-source length to the estimate or use a post-hoc reconciliation step.


---

## Gotcha 2: Platform Event volume limits

**What happens:** High-traffic agent saturates your 24h PE quota.

**When it occurs:** Every consumption publishes an event.

**How to avoid:** Batch consumption events per-minute via a Queueable aggregator.


---

## Gotcha 3: Ledger bucket skew

**What happens:** Timezone boundary resets at midnight UTC, users see it mid-afternoon locally.

**When it occurs:** Default to UTC buckets without telling users.

**How to avoid:** Document the reset time in the fallback UX copy.

