# LLM Anti-Patterns — Rebate Management Setup

Common mistakes AI coding assistants make when configuring Rebate Management.

## Anti-Pattern 1: Using CPQ discount schedules for rebates

**What the LLM generates:** Suggests CPQ discount schedules tied to quantity tiers for channel rebate programs.

**Why it happens:** CPQ discounts are well-known; Rebate Management is a separate license and less represented in training.

**Correct pattern:**

```
CPQ discount = quote-time, applied before signing. Rebate = after-the-
fact, calculated against delivered transactions with accruals and payout
cycles. They are not interchangeable.
```

**Detection hint:** A "channel rebate program" implemented as CPQ Discount Schedule metadata.

---

## Anti-Pattern 2: Hand-rolling accrual calculations in Apex

**What the LLM generates:** A nightly scheduled Apex job that queries Transactions, calculates tier-based benefit, and inserts `Rebate_Accrual__c` records.

**Why it happens:** The model reaches for generic scheduled Apex when the shipped Rebate Calculation engine is unfamiliar.

**Correct pattern:**

```
Use the shipped Rebate Calculation process. It handles tiering, retroactive
adjustment, accrual posting, and audit trail. Custom Apex bypasses audit
and breaks period-close reconciliation.
```

**Detection hint:** Scheduled Apex named like `NightlyRebateAccrual` or `CalculatePartnerRebate` in a Rebate-Management-licensed org.

---

## Anti-Pattern 3: Single monolithic `Rebate_Program__c` for all programs

**What the LLM generates:** One program record with hundreds of Benefits for every partner and tier combination.

**Why it happens:** The model minimizes record count without thinking about auditability.

**Correct pattern:**

```
One Rebate_Program__c per contractually distinct program. Separate programs
per region, product line, or contract version. Auditors trace payouts back
to the program record that authorized them.
```

**Detection hint:** A single program with 100+ Benefits and participants from different contractual agreements.

---

## Anti-Pattern 4: Loading transactions without the participant mapping

**What the LLM generates:** Transactions with account names as strings instead of Account lookups.

**Why it happens:** The model treats Transaction as a flat fact table; Rebate needs relational integrity to roll up to Benefit.

**Correct pattern:**

```
Every Transaction.Participant (or AccountId) must resolve to the Account
that is the rebate participant on the Program. Unmapped transactions do
not accrue; they silently drop out of the calculation.
```

**Detection hint:** Transaction imports with non-null `ParticipantName__c` text but null Account lookup.

---

## Anti-Pattern 5: Showing partners raw accrual data without a snapshot

**What the LLM generates:** An Experience Cloud page that real-time-queries `Rebate_Accrual__c` sums.

**Why it happens:** The model defaults to real-time queries; Rebate shipped pattern is snapshot-based.

**Correct pattern:**

```
Use the Benefit Accrual snapshot job. Partners see the last snapshot's
numbers. Avoids long queries, mid-recalculation fluctuations, and lets
finance control what partners see vs internal adjustments.
```

**Detection hint:** A partner-facing LWC that aggregates `Rebate_Accrual__c` directly via SOQL.
