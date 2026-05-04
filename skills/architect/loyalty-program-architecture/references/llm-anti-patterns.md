# LLM Anti-Patterns — Loyalty Program Architecture

Common mistakes AI coding assistants make when generating or advising on Loyalty Program Architecture.

## Anti-Pattern 1: Suggesting Tier Thresholds Without Customer-Distribution Data

**What the LLM generates:** "A typical loyalty program uses 500 points for Silver, 2,000 for Gold, and 5,000 for Platinum. Use those thresholds."

**Why it happens:** The model has seen many marketing-blog "typical loyalty program" articles. It defaults to median industry benchmarks, with no idea what the customer's actual transaction distribution looks like.

**Correct pattern:**

```
1. Pull the per-customer 12-month qualifying-equivalent distribution.
2. Compute the percentile that maps to the target tier population
   (e.g., Gold at 8% target → 92nd percentile threshold).
3. Stress-test under behavior-doubling and behavior-halving scenarios.
4. THEN propose thresholds derived from the math, not benchmarks.
```

**Detection hint:** If the answer proposes specific tier-threshold numbers without first asking for or analyzing the brand's transaction-volume distribution, the LLM is benchmark-guessing.

---

## Anti-Pattern 2: Conflating Qualifying And Non-Qualifying Currencies

**What the LLM generates:** "Members earn 10 points per dollar. Use those points for tier qualification and redemption."

**Why it happens:** Single-currency loyalty is the most common pattern in training data (most retail programs collapse the two). The model doesn't know about Salesforce Loyalty Management's two-currency model.

**Correct pattern:**

```
Architecture must specify TWO currencies:
  - Qualifying (tier currency): 1 per $1 — drives tier advancement only,
    reset annually
  - Non-qualifying (redemption currency): 10 per $1 — used for redemption,
    expires per policy

Different ratios prevent marketing teams from collapsing them mentally.
Redemption rules MUST read non-qualifying balance, never qualifying.
```

**Detection hint:** If the answer proposes a single point currency for both tier and redemption, the model is using a non-Salesforce loyalty model. Reject the proposal.

---

## Anti-Pattern 3: Promising Real-Time Tier Upgrades

**What the LLM generates:** "When a member crosses the Gold threshold, send them a real-time congratulations email with their new tier benefits."

**Why it happens:** Real-time customer experiences are a popular pattern in modern app architecture. The model doesn't know that Loyalty Management's tier evaluation runs as a scheduled DPE job, not a real-time trigger.

**Correct pattern:**

```
Tier upgrades are recognized within 24 hours of qualifying-balance
crossing the threshold (when the next DPE cycle runs).

If the use case truly needs real-time:
  - Build a custom upgrade trigger on LoyaltyMemberCurrency updates.
  - Reconcile against DPE on each cycle to handle edge cases.
  - This is significant custom work, not a config switch.
```

**Detection hint:** If the answer treats tier promotion as instant or transaction-synchronous, the model is missing the DPE schedule constraint. Ask whether the customer accepts a 24-hour SLA before promising real-time.

---

## Anti-Pattern 4: Forgetting To Architect Tier-Credit Reversals

**What the LLM generates:** Documents the earn flow ("members earn qualifying points on transaction") but does not document the reversal flow for refunds, cancellations, or chargebacks.

**Why it happens:** "Earn flow" is the optimistic case the model has seen most often. Reversals are the operational reality but easy to omit.

**Correct pattern:**

```
Architecture must specify the reversal pipeline:
  refund/cancel/chargeback event
    → posts a negative qualifying transaction
    → DPE re-aggregates qualifying balance
    → tier evaluation runs
    → member tier is descaled if they fall below threshold
    → notification email pipeline informs member of the change

Without this, members earn tier on phantom transactions and finance
reconciliation breaks.
```

**Detection hint:** If the architecture document covers earning but not reversal, ask "what happens when a transaction is refunded?" If the answer is hand-wavy, the model missed the reversal pipeline.

---

## Anti-Pattern 5: Ignoring Multi-Region GDPR Implications

**What the LLM generates:** "Launch a single global loyalty program. Members in the US, EU, and APAC all share one ledger."

**Why it happens:** Single-program architecture is operationally simpler and the model defaults to the simpler answer. GDPR data residency requirements are not always salient.

**Correct pattern:**

```
For brands with EU members:
  - GDPR Article 17 (right to erasure) and data residency rules apply.
  - Architect federated programs (one LoyaltyProgram per region) with
    cross-earn via Platform Events.
  - Tier mapping table maintains brand parity across regions.
  - Lifetime status rolls up via a quarterly DPE reconciliation.

Single global program is acceptable only when EU member data is hosted
in an EU data center AND the program operator has documented compliance.
```

**Detection hint:** If the answer recommends a single global program for a multi-region brand without mentioning GDPR or data residency, the model is missing the regulatory dimension. Push back.
