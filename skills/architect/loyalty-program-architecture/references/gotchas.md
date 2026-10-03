# Gotchas — Loyalty Program Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Tier Thresholds Set Without A Distribution Analysis

**What happens:** Marketing proposes thresholds based on "what feels right" or "what competitors charge." Implementation builds it. Year 1 review: 99% of members are in Bronze, the program is invisible to most customers, attribution to LTV uplift fails to land.

**When it bites you:** First annual board review of the program. The architecture team is asked "why is no one in Gold?" and the answer is the threshold was a guess.

**How to handle:** Pull customer transaction-volume data over the most recent 12 months. Compute the percentile distribution. Place tier thresholds at percentiles that match the target tier distribution (Gold at the percentile that maps to your target Gold population). Stress-test under "behavior doubles" and "behavior halves" scenarios. Document the math; let the architecture document carry the numerical reasoning.

---

## Gotcha 2: Identical Currency Ratio Causes Marketing Mental Collapse

**What happens:** Architecture sets 1 qualifying point per $1 and 1 non-qualifying point per $1 — a clean 1:1 ratio. Marketing then writes a redemption rule that says "redeem 100 points for a free coffee" without specifying which currency. Six months later a member who hit Gold (1,000 qualifying points) tries to redeem against the same balance and is told their tier resets to zero — the redemption rule was actually drawing against qualifying.

**When it bites you:** Mid-program, when the marketing team has shipped redemption mechanics that quietly read the wrong currency. Member service tickets surge.

**How to handle:** Force a visibly different ratio: 1:5, 1:10, 1:100. The asymmetry forces the marketing team to mentally separate the two currencies. Document the redemption-currency rule in the architecture document explicitly: "all redemptions draw from non-qualifying balance; qualifying balance is read-only outside the tier engine." Include this in the Loyalty admin training.

---

## Gotcha 3: Batch Tier Assessment Is Not Real-Time

**What happens:** A member crosses the Gold threshold mid-day. Marketing sends an "upgrade" email. The member opens the loyalty portal — still showing Silver. The tier process runs in batch and doesn't run until 2 AM. Customer service ticket: "Salesforce loyalty is broken."

**When it bites you:** Whenever the architecture treats tier as real-time without choosing real-time assessment. Tier changes come from the Change Tier process that Loyalty Management generates when the program manager enters minimum eligible balances in Manage Tier Eligibility and clicks Generate Rules; it is not a DPE job. That process runs in real time as a child of a Transaction Journal process, or in batches through Batch Management. Only the batch option lags.

**How to handle:** Architecture must state the choice. If batch, specify "tier upgrades are recognized within the batch cadence (for example 24 hours) of the qualifying balance crossing the threshold" and align marketing communications to that SLA — no congratulations email until the tier change is confirmed. If real-time is required, use the real-time child-process option; no custom upgrade trigger is needed. Regenerate the process after any change to a tier's eligible balance or name.

**Source:** Loyalty Management guide (Spring '26), Tier Assessment; Configure a Tier Assessment Process. Recorded in `skills/integration/loyalty-management-setup/references/gotchas.md` Gotcha 2.

---

## Gotcha 4: DPE Templates Do Nothing Until Cloned, Activated, and Run From a Flow

**What happens:** Architecture documents partner accrual and redemption factors. Implementation configures `LoyaltyProgramPartner` records. Members earn at partners but balances never update — the central ledger shows zero partner-earned points. Partners ask for a status update; the implementation team can't explain.

**When it bites you:** Day-of-go-live for partner loyalty. Partner ledgers and balances come from **one** DPE definition, the `Create Partner Ledgers and Update Partner Balances` template. Loyalty Management ships DPE definitions as templates; they must be cloned, the clone activated, and the activated definition run from a flow (it appears in Flow Builder as an action). A team that searches for a second "Update Partner Balance" definition will not find one.

**How to handle:** Architecture must list every DPE definition to clone and the flow cadence that runs it, and must set `BillingType` and the cost-per-unit fields on each `LoyaltyProgramPartner`. The setup skill (`integration/loyalty-management-setup`) consumes this list and confirms the clone, activation and flow in the implementation runbook. Validate via SOQL after the first flow run: `SELECT COUNT() FROM LoyaltyPartnerLedger` should match the partner-transaction-event count.

**Source:** Loyalty Management guide (Spring '26), Create Partner Ledgers and Update Partner Balances Definition; Data Processing Engine Definitions (Clone the Template Data Processing Engine Definitions). Recorded in `skills/integration/loyalty-management-setup/references/gotchas.md` Gotchas 1 and 4.

---

## Gotcha 5: Tier-Credit Reversals Are Not Automatic

**What happens:** A member books a $5,000 trip, earns 5,000 qualifying points, hits Gold tier. The next day they cancel the trip. The refund event fires; the original transaction is reversed. The qualifying ledger does **not** automatically reverse the points unless the architecture wired up the reversal pipeline.

**When it bites you:** Members game the system intentionally. Or they don't, but tier counts inflate by 5–15% on phantom transactions; finance reconciliation is wrong.

**How to handle:** Architecture must specify the tier-credit reversal pipeline: refund/cancel events post a negative qualifying transaction, the DPE re-aggregates, the tier-evaluation runs, the member is correctly descaled if they fall below the threshold. Implementation typically lives in a Loyalty Promotion (or custom Apex transaction-poster). Confirm the reversal logic is in scope before launch.

---

## Gotcha 6: Lifetime Status Has Material Data Volume Implications

**What happens:** Architecture promises "earned-for-life Gold at 1M lifetime miles." Implementation builds it. Three years in, the lifetime ledger has hundreds of millions of records — the calculation that determines lifetime status takes minutes per member during DPE.

**When it bites you:** Year 3+, when the program scales. The lifetime ledger never expires (that's the point of "lifetime") but DPE re-aggregation against the full ledger is the slowest operation in the program.

**How to handle:** Architect the lifetime ledger as a **rolled-up summary**, not a per-transaction read. Maintain a `Lifetime_Qualifying_Total__c` on the loyalty member, updated incrementally on each transaction post. The DPE reads the summary, not the underlying transactions. Plan this from Day 1; retro-fitting a summary against an established ledger is a multi-quarter migration.

---

## Gotcha 7: Multi-Region Programs And GDPR Data Residency

**What happens:** A US-based brand launches a global single-program loyalty offering. EU members' data lands in the US data center. A GDPR audit later flags this as a data-residency violation; the brand has to fragment the program retroactively.

**When it bites you:** A year or two post-launch, when the EU compliance team notices. Or sooner if a member exercises an Article 17 right-to-erasure.

**How to handle:** Decide the multi-region pattern (single program vs federated) **before** launch. If any non-trivial EU member presence is expected, architect federated programs from Day 1. The cost of federation up front is dwarfed by the cost of fragmentation under audit pressure.
