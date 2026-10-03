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

**What the LLM generates:** "When a member crosses the Gold threshold, send them a real-time congratulations email with their new tier benefits." Or the opposite error: "tier evaluation is a scheduled DPE job, so real-time tier needs custom code."

**Why it happens:** The model either assumes real-time is free, or assumes tier assessment is a DPE job. Tier changes come from the Change Tier process generated from Manage Tier Eligibility (Generate Rules). It runs in real time as a child of a Transaction Journal process, or in batches through Batch Management. The DPE definitions (balance calculation, Reset Qualifying Points, expiration, partner ledgers) are templates that run only when a flow calls the activated clone.

**Correct pattern:**

```
Choose and document the tier-assessment mode:
  - Real time: Change Tier runs as a child of the Transaction Journal
    process; upgrades land with the transaction. Costs work per transaction.
  - Batch: Change Tier runs through Batch Management; upgrades are
    recognized within the batch cadence (for example 24 hours).
Marketing communications align to whichever SLA is chosen.
No custom upgrade trigger is needed for either mode.
```

**Detection hint:** If the answer treats tier promotion as instant without naming the real-time Change Tier option, or builds a custom trigger to get real-time tier, it is missing the generated Change Tier process. Ask which mode the customer needs before promising an SLA.

---

## Anti-Pattern 4: Forgetting To Architect Tier-Credit Reversals

**What the LLM generates:** Documents the earn flow ("members earn qualifying points on transaction") but does not document the reversal flow for refunds, cancellations, or chargebacks.

**Why it happens:** "Earn flow" is the optimistic case the model has seen most often. Reversals are the operational reality but easy to omit.

**Correct pattern:**

```
Architecture must specify the reversal pipeline:
  refund/cancel/chargeback event
    → posts a negative qualifying transaction
    → qualifying balance is recalculated (DPE definition run from a flow)
    → the Change Tier process re-assesses the member
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
