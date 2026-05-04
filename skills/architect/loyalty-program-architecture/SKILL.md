---
name: loyalty-program-architecture
description: "Use when designing or reviewing the architecture of a Salesforce Loyalty Management program before configuration begins — tier-ladder economics, qualifying-vs-non-qualifying currency split, point inflation/deflation modeling, fraud-prevention controls, partner-network topology, multi-region program federation, and tier-descalation policy. Triggers: 'designing a loyalty program', 'how many tiers should we have', 'point economy design', 'preventing loyalty fraud', 'partner loyalty architecture', 'multi-region loyalty rollout', 'tier descalation policy', 'how do we set the qualifying threshold'. NOT for hands-on Loyalty Management setup (use integration/loyalty-management-setup) — this skill produces the architecture document, not the configuration steps. NOT for Marketing Cloud engagement programs (different product). NOT for B2B partner programs that aren't loyalty (regular Sales Cloud opportunity tracking applies)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Security
tags:
  - loyalty-management
  - loyalty-architecture
  - tier-design
  - point-economy
  - fraud-prevention
  - partner-loyalty
  - multi-region-loyalty
  - program-design
  - architecture-decision
triggers:
  - "we are launching a new loyalty program — how should we structure tiers and points"
  - "should our loyalty program have 3 tiers or 5"
  - "how do we prevent point-redemption fraud and accrual abuse"
  - "designing a partner loyalty network alongside our consumer program"
  - "rolling out a single loyalty program across the US, EU, and APAC"
  - "tier-descalation rules — how do we drop members down without losing them"
  - "what's the right exchange rate between qualifying and non-qualifying points"
inputs:
  - "Business goals: lifetime value uplift target, retention rate target, tier-distribution target"
  - "Existing customer transaction data (ARPU, transaction frequency, recency profile)"
  - "Partner ecosystem (if applicable): which partners will earn / award / redeem points"
  - "Geographic footprint and regulatory constraints (privacy, prize/sweepstakes law, currency)"
  - "Marketing organization's tier-naming conventions and brand guardrails"
outputs:
  - "Architecture document covering tier ladder, point economy, currency split, fraud controls"
  - "Tier threshold proposal grounded in transaction-volume distribution analysis"
  - "Qualifying vs non-qualifying currency design with explicit redemption-to-qualifying ratio"
  - "Fraud-prevention control matrix (DPE pre-aggregation, anomaly thresholds, manual review queues)"
  - "Partner network topology (if applicable): hub-and-spoke vs peer-to-peer, accrual factor design"
  - "Multi-region federation design (if applicable): single program vs federated programs"
  - "Tier-descalation policy with grace-period and lookback-window rules"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# Loyalty Program Architecture

This skill activates when an architect is designing or reviewing a Salesforce Loyalty Management program **before** the implementation team starts configuring it. It produces the architectural decisions that shape every downstream choice in `integration/loyalty-management-setup`: how many tiers, what their thresholds are, how qualifying and non-qualifying currencies split, fraud-prevention controls, partner network topology, and tier-descalation rules. The setup skill answers "how do I configure this." This skill answers "what should we configure, and why?"

---

## Before Starting

Gather this context before working on anything in this domain:

- A loyalty program is a **point-economy decision** before it is a Salesforce configuration. Tier thresholds, accrual rates, and redemption ratios are hypotheses about customer behavior. Get the marketing/finance owner to commit to specific business targets (lifetime value uplift, retention rate, tier distribution) before discussing object models.
- Salesforce Loyalty Management's **two-currency model** (qualifying vs non-qualifying) is non-negotiable: qualifying points drive tier advancement, non-qualifying points drive redemption. Conflating them in design produces an unimplementable program. Confirm the customer understands the split before tier design begins.
- **Tier inflation is the leading cause of loyalty-program failure**: thresholds are set generously at launch to drive adoption, then half the customer base lands in the top tier within 18 months and the program loses differentiation. Build tier-descalation into the architecture, not as an afterthought.
- Partner loyalty is a separate architectural problem from B2C loyalty. The `LoyaltyProgramPartner` model accommodates partner-earned and partner-redeemed transactions but architectural decisions (accrual factor, redemption factor, ledger transparency, fraud isolation) must be made before configuration.
- The DPE (Data Processing Engine) is the heartbeat of the program. **Architecture must be DPE-aware**: the cadence of "Reset Qualifying Points," "Aggregate Non-Qualifying Points," and "Update Partner Balance" jobs determines what's in scope for tier-realtime vs tier-batch decisions.

---

## Core Concepts

### Tier Ladder Design: Threshold Mathematics

Tier thresholds are not arbitrary. They are derived from the customer transaction-volume distribution and a target tier-distribution policy. A typical good architecture targets a **10/30/60** or **5/20/75** Gold/Silver/Bronze distribution — most members in the lowest tier, a meaningful but not majority middle tier, an aspirational top tier.

To derive thresholds:

1. Pull the per-customer annual qualifying-equivalent (e.g., dollars spent or trips taken) over the last 12 months.
2. Compute the percentile distribution. The Gold threshold sits at the customer-count percentile that maps to your target Gold population (e.g., the 90th percentile if Gold should be 10%).
3. Stress-test: if every customer doubles their behavior in year 2, what does the tier distribution become? If you'd land at 30% Gold, the threshold is too low.

Three-tier programs are the canonical baseline (Bronze / Silver / Gold). Five-tier programs (adding Platinum and Diamond, or Member / Bronze / Silver / Gold / VIP) are justified when the customer base has long-tail "VIP" behavior (top 1% spend 10× the median) and you need a separate aspirational tier.

### Qualifying vs Non-Qualifying: The Exchange-Rate Question

Members earn both qualifying points (tier currency) and non-qualifying points (redemption currency) on the same transaction. The architecture decision is the **ratio**.

A common model: 1 qualifying point per $1 spent (tier driver), and 10 non-qualifying points per $1 spent (redemption driver). The 1:10 ratio gives reward statements visual heft ("you earned 1,000 points!") without inflating tier qualification.

Architectural pitfall: setting the qualifying-to-non-qualifying ratio identical (1:1) makes the marketing team mentally collapse them, then start writing redemption rules against qualifying balance — which breaks the tier engine because qualifying balance is reset annually. Force the ratio to be visibly different (1:5, 1:10, 1:100) to keep the two currencies psychologically distinct.

### Fraud Prevention: Pre-Aggregation Vs Post-Detection

Loyalty programs attract fraud at three layers:

1. **Accrual abuse** — gaming the earn rules (returned items still earned points; points awarded twice for the same transaction).
2. **Redemption abuse** — using points fraudulently obtained or pooled across accounts.
3. **Tier-laddering abuse** — engineered transactions to hit a tier threshold then unwound (e.g., book a trip for tier credit, then cancel without losing the tier).

Architecture controls that must be in the design:

- **DPE-driven pre-aggregation with anomaly thresholds**: the accrual DPE flags transactions above a per-account daily/weekly cap for manual review.
- **Redemption holds**: large redemptions (above an architecture-defined threshold) go to a queue, not auto-process.
- **Tier-credit reversals**: tier-credit posting DPE accepts return/cancellation events and reverses the qualifying-points award. Without this in the architecture, members earn tier on phantom transactions.

### Partner Loyalty: Hub-And-Spoke Vs Peer-To-Peer

Partner loyalty extends the program to ecosystem partners (hotel + airline + car rental; bank + retailer; pharmacy + insurance). The architectural choice:

- **Hub-and-spoke** — your program is the hub; partners are spokes. Each partner has its own `LoyaltyProgramPartner` record with accrual and redemption factors. Members earn at any partner; redemption happens against your central currency. The hub owns the ledger.
- **Peer-to-peer** — multiple programs federate. Each program owns its members; reciprocal earning happens via cross-program APIs. Complex, used by airline alliances. Salesforce Loyalty Management primarily supports hub-and-spoke; peer-to-peer is custom.

Architectural decisions for hub-and-spoke: accrual factor per partner (1.0 = parity, 1.5 = bonus partner), redemption factor (how many central points equal a partner-side reward), partner ledger visibility (does the partner see member balances or only their own transaction posts).

### Multi-Region Federation

A single program across US/EU/APAC has architectural choices:

| Pattern | When to use | Tradeoff |
|---|---|---|
| Single program, multi-region | Brand parity is paramount; transactions are cross-region | Currency conversion, tax / GDPR complexity, single DPE schedule |
| Federated programs (one per region) | Local regulatory requirements (GDPR data residency, EU prize regulations) | Members can't earn cross-region without a federation API |
| Tiered hybrid | Premium tier is global, base tier is regional | Most complex; needs explicit tier-mapping rules |

The decision driver is usually regulatory (GDPR data residency forces federation in EU) or transactional (if 30% of members earn in multiple regions, federation is operational pain).

### Tier Descalation Policy

Most programs spend 2 years promoting members up the ladder, then realize they have no rule for keeping them at the top tier (or dropping them gracefully). Architecture must answer four questions:

| Question | Common answers | Notes |
|---|---|---|
| Reset cadence | Annual, biennial, never | Annual is most common; aligns with most marketing cycles |
| Grace period | Same-day drop, or 3–12 month soft landing at current tier with lower earn rate | Soft landing is the better member experience but adds DPE complexity |
| Lookback window | Calendar year, or rolling 12 months | Rolling smooths the member experience but DPE re-evaluates monthly |
| Lifetime status | Yes (e.g., 1M miles → Platinum forever) or no | Lifetime ledger never expires; plan a rolled-up summary on the member object |

Without an architectural answer, each of these gets implemented ad-hoc and produces a mess.

---

## Common Patterns

### Pattern 1: Three-Tier Consumer Program With Annual Reset

**When to use:** First-time loyalty program for a B2C brand, transactional volume of 100k–10M members.

**How it works:**

1. Tier ladder: Bronze (entry, automatic on enrollment) / Silver (90th percentile spend) / Gold (99th percentile spend). Target distribution 75/20/5.
2. Currency design: 1 qualifying point per $1, 10 non-qualifying points per $1. Visible ratio prevents mental collapse.
3. Annual qualifying reset on member's anniversary date (avoids January DPE-overload).
4. Soft-landing tier descalation: a member who misses the threshold drops one tier at the next anniversary and earns at the lower rate; they don't drop two tiers in a single reset.
5. Fraud controls: DPE flags >$5,000/day per-account accrual, redemptions over 50k points go to manual review.

**Why not the alternative:** Five-tier programs at 100k members produce tier populations < 1% in the top tier — too small to drive aspirational behavior. Stick with three until you have the long-tail data to justify more.

### Pattern 2: Hub-And-Spoke Partner Loyalty (Travel Alliance)

**When to use:** Brand owns the central program (e.g., a hotel chain) and partners with airlines, car rental, dining for cross-earning.

**How it works:**

1. Central program owns the master `LoyaltyProgram` and member ledger.
2. Each partner is a `LoyaltyProgramPartner` with explicit accrual factor (e.g., 0.5 for non-strategic partners, 1.0 for parity, 1.5 for promo partners).
3. Partner-earned transactions post to the central ledger via Partner DPE jobs (`Create Partner Ledgers`, `Update Partner Balance` — both must be activated).
4. Redemption happens centrally; partner-side rewards come out of the central non-qualifying balance with a configured redemption factor.
5. Fraud controls per partner: rate limits per partner-day to catch a compromised partner-feed.

**Why not the alternative:** Peer-to-peer partner loyalty (each partner runs their own program; programs federate) is feasible but custom. Salesforce Loyalty Management is built for hub-and-spoke; fight that pattern only when you must.

### Pattern 3: Multi-Region Federated Programs With Cross-Earn API

**When to use:** US + EU + APAC coverage with GDPR data residency forcing region-local programs.

**How it works:**

1. Three `LoyaltyProgram` records, one per region. Each owns its members and ledger.
2. Cross-region earn handled via a custom federation API: when a US member transacts in EU, the EU program emits a Platform Event; the US program subscribes and posts qualifying + non-qualifying points to the US member.
3. Tier mapping table: US Gold = EU Premier = APAC Platinum (configured at enrollment by region).
4. Lifetime tier achievements roll up to a per-member "global tier" custom field, calculated by a quarterly DPE reconciliation.
5. Marketing communications respect regional preferences (don't email US-tier upgrades to an EU member).

**Why not the alternative:** A single global program runs into GDPR data-residency issues (member data must reside in EU for EU members). Federation is the cost of compliance.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| First-time consumer loyalty program, B2C, 100k–10M members | 3-tier program with annual reset, 1:10 currency ratio | Canonical baseline; complexity scales later if data justifies |
| High-end brand with long-tail VIP behavior (top 1% spend 10× median) | 5-tier program with separate aspirational top tier | Differentiation requires a Platinum/Diamond layer |
| Partner ecosystem (airlines + hotels + dining) | Hub-and-spoke with central program | Salesforce Loyalty Management is built for this pattern |
| US + EU + APAC | Federated programs (one per region) | GDPR data residency forces regional separation |
| B2B distribution channel rewards | Loyalty Management with Partner Loyalty | Channel programs work but consider Channel Revenue Management for incentives proper |
| Loyalty + Marketing Cloud existing | Loyalty Management is the system of record; MC is the engagement channel | Don't try to use MC engagement programs to replace loyalty tier engine |
| Subscription-based product (e.g., SaaS) | Treat tier as account-state, not point-state | Loyalty Management is built for transaction-driven programs; subscription state belongs in custom logic |
| Concerns about point-redemption fraud | Build pre-aggregation DPE controls + redemption holds + tier-credit reversal pipeline | Fraud is a design issue, not a runtime issue |

---

## Recommended Workflow

Step-by-step instructions for an architect or AI agent working on this task:

1. Confirm business targets. Get marketing/finance to commit to lifetime-value uplift, retention rate, and target tier distribution. Without these, tier thresholds are guesses.
2. Pull customer transaction-volume data for the last 12 months. Compute percentile distribution of qualifying-equivalent transactions per member.
3. Propose tier thresholds derived from the distribution and target distribution. Stress-test under "all members double behavior" and "all members halve behavior" scenarios.
4. Design the currency split. Pick a visibly distinct ratio between qualifying and non-qualifying (1:5 to 1:100). Document the redemption-to-qualifying logic so the marketing team can build redemption rules without bleeding into tier logic.
5. Define fraud controls. Per-account daily/weekly accrual caps, redemption holds, tier-credit reversal pipeline. Document the DPE jobs that enforce each.
6. Decide partner topology (if applicable). Hub-and-spoke is the default. Document accrual factor per partner and the partner-DPE schedule.
7. Decide multi-region pattern (if applicable). Federation is the GDPR-safe default.
8. Design tier descalation. Reset cadence, grace period, lookback window, lifetime-status policy. Document the member-experience text that explains the rule.
9. Hand off to `integration/loyalty-management-setup` for configuration. Provide the architecture document as the input; the setup skill consumes it.

---

## Review Checklist

Run through these before marking architectural work in this area complete:

- [ ] Business targets are explicit (lifetime value uplift, retention rate, tier distribution)
- [ ] Tier thresholds are derived from the customer-distribution percentile, not from competitor benchmarking alone
- [ ] Currency ratio (qualifying:non-qualifying) is visibly distinct (1:5 to 1:100)
- [ ] Fraud-prevention controls are designed (accrual caps, redemption holds, tier-credit reversal)
- [ ] Partner topology decision is documented (if applicable): hub-and-spoke vs peer-to-peer, accrual factors per partner
- [ ] Multi-region federation decision is documented (if applicable) with regulatory rationale
- [ ] Tier-descalation policy is explicit: reset cadence, grace period, lookback, lifetime-status rules
- [ ] DPE schedule is documented: which jobs run at what cadence, what their dependencies are
- [ ] Stress-test scenarios documented: how does the tier distribution evolve under behavior shifts
- [ ] Architecture document handed off to the setup team with a clean spec

---

## Salesforce-Specific Gotchas

(Detailed entries live in `references/gotchas.md`.)

1. **Point inflation is the most common program failure** — without a descalation rule, members concentrate in the top tier within 18 months.
2. **Identical qualifying:non-qualifying ratio invites mental collapse** — marketing teams will write redemption rules against qualifying balance and break tier logic.
3. **DPE schedule constraints on architecture** — qualifying-reset DPE runs on a schedule, not real-time; "instant tier upgrade on hitting the threshold" is not a supported pattern.
4. **Partner DPE jobs are not on by default** — architecture must specify which jobs are activated and on what cadence.
5. **Tier-credit reversals aren't automatic** — return/cancel events must be wired into the architecture or members earn tier on phantom transactions.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Architecture Document | Tier ladder, currency design, fraud controls, partner topology, multi-region pattern, tier-descalation policy |
| Tier Threshold Derivation | Percentile distribution analysis, threshold proposals, stress-test scenarios |
| DPE Schedule Spec | Which DPE jobs run at what cadence, dependency graph, failure-handling expectations |
| Fraud Control Matrix | Per-control-type: accrual caps, redemption holds, tier-credit reversal, anomaly thresholds, manual review queues |
| Partner Topology Diagram (if applicable) | Hub-and-spoke layout, accrual/redemption factors per partner, partner-ledger visibility |
| Multi-Region Federation Diagram (if applicable) | Per-region program, cross-earn API design, tier mapping table |
| Setup Hand-Off Spec | Document the setup team uses to drive `integration/loyalty-management-setup` configuration |

---

## Related Skills

- `integration/loyalty-management-setup` — the implementation skill that consumes this architecture
- `integration/channel-revenue-management-setup` — for B2B channel partner incentive programs (often confused with B2B partner loyalty)
- `architect/data-residency-and-compliance` — for the multi-region federation decision-making
- `integration/data-cloud-integration` — if loyalty data feeds Data Cloud for customer 360 / segmentation
- `architect/event-driven-architecture` — for the cross-region federation Platform Event pattern in multi-region designs
