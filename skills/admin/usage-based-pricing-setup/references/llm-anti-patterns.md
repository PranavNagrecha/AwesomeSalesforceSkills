# LLM Anti-Patterns — Usage-Based Pricing Setup

Common mistakes AI coding assistants make when configuring consumption-based pricing.

## Anti-Pattern 1: Implementing usage pricing as CPQ discount schedules

**What the LLM generates:** A CPQ discount schedule with volume tiers, stamped on the quote line, used as "usage pricing."

**Why it happens:** CPQ is well-documented; Consumption Schedule is less so.

**Correct pattern:**

```
CPQ discount schedule = one-time volume-based price for the deal.
Consumption Schedule = ongoing rating of post-sale telemetry. They are
not interchangeable.
```

**Detection hint:** A product sold "per API call" with a CPQ discount schedule and no Consumption Schedule attached.

---

## Anti-Pattern 2: Non-idempotent rating

**What the LLM generates:** A scheduled Apex rating job that queries "usage records" and inserts priced usage, without a `Rated` flag or unique constraint.

**Why it happens:** The model treats rating as a one-shot batch, not a retry-safe pipeline.

**Correct pattern:**

```
Rate only usage records with Rated = false. Set Rated = true and link to
the rated record in the same transaction. Every retry must be safe. Use
a unique key on (UsageRecordId, ConsumptionScheduleId) to prevent
duplicates.
```

**Detection hint:** A rating job that does not filter on an explicit `Rated`/`IsRated` flag.

---

## Anti-Pattern 3: Real-time customer dashboard querying raw usage

**What the LLM generates:** An LWC that queries `SELECT SUM(Quantity) FROM UsageRecord WHERE ...` on every page load.

**Why it happens:** The model defaults to live queries; raw usage volume is too high.

**Correct pattern:**

```
Rolled-up UsageSummary (daily or near-real-time snapshot). LWC reads
from the rollup. Raw records are the audit trail, not the presentation
layer.
```

**Detection hint:** A customer portal LWC with a SOQL query aggregating `UsageRecord` directly.

---

## Anti-Pattern 4: Mid-period price change by editing existing Consumption Schedule

**What the LLM generates:** Increases the Price on a Consumption Rate in the current schedule.

**Why it happens:** The model treats the rate as a config row; it is actually a versioned financial contract term.

**Correct pattern:**

```
Create a NEW Consumption Schedule version with a new effective date.
The prior version remains for already-rated usage. Auditors and reratings
depend on the historical schedule being intact.
```

**Detection hint:** Metadata diffs showing direct edits to `ConsumptionRate.Price` on an active schedule.

---

## Anti-Pattern 5: Unbounded UsageRecord growth in Salesforce

**What the LLM generates:** "Load every API call event into UsageRecord; it is our audit trail."

**Why it happens:** The model treats Salesforce as the durable record. It is expensive and poor at high-volume log retention.

**Correct pattern:**

```
Keep rated / billed summaries in Salesforce. Archive raw usage records
after a defined retention window (30-90 days) to a big object or external
warehouse. Billing references archived events via external id lookups
when disputes arise.
```

**Detection hint:** An org with hundreds of millions of `UsageRecord` rows and no archival policy.
