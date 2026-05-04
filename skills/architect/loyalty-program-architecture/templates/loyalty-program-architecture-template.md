# Loyalty Program Architecture — Work Template

Use this template when designing a loyalty-program architecture. Fill it in collaboratively with marketing/finance/legal owners; archive the completed copy as the program's master architecture document. Hand off to the implementation team driving `integration/loyalty-management-setup`.

---

## Scope

**Skill:** `loyalty-program-architecture`

**Customer / Brand:**
**Architecture owner:**
**Marketing owner:**
**Finance owner:**
**Target program launch date:**

---

## 1. Business Targets

| Target | Year-1 Goal | Measurement |
|---|---|---|
| Lifetime value uplift |  |  |
| Retention rate |  |  |
| Tier distribution (Bronze/Silver/Gold) |  |  |
| Active member percentage |  |  |
| Average ticket lift |  |  |

These targets drive every downstream decision. **Without them, the architecture is unanchored.**

---

## 2. Customer Distribution Analysis

- [ ] 12-month transaction-volume distribution pulled per member
- [ ] Percentile cuts computed:
  - 50th percentile annual qualifying-equivalent: ___
  - 75th percentile: ___
  - 90th percentile: ___
  - 95th percentile: ___
  - 99th percentile: ___
- [ ] Stress test scenarios documented:
  - Behavior doubles → tier distribution becomes: ___ / ___ / ___
  - Behavior halves → tier distribution becomes: ___ / ___ / ___

---

## 3. Tier Ladder

| Tier | Threshold (Qualifying Points / Year) | Target Population | Justification |
|---|---|---|---|
| Bronze (entry) | 0 | __% |  |
| Silver |  | __% |  |
| Gold |  | __% |  |
| (Platinum, if 4-tier) |  | __% |  |
| (Diamond, if 5-tier) |  | __% |  |

**Number of tiers:** ___ — justification: ___________

---

## 4. Currency Design

| Currency | Type | Earn Rate | Reset Cadence | Notes |
|---|---|---|---|---|
| Qualifying ("Status Points") | Tier driver | 1 per $1 (or: ___) | Annual / Anniversary / Other |  |
| Non-Qualifying ("[Brand] Points") | Redemption | 10 per $1 (or: ___) | Expires after ___ months |  |

**Ratio (qualifying:non-qualifying):** ___ — confirm visibly distinct (1:5 to 1:100)

**Redemption rules:** all redemptions draw from non-qualifying balance. Documented in admin training: ___

---

## 5. Fraud Prevention Controls

| Control | Threshold | Action | DPE Job |
|---|---|---|---|
| Per-account daily accrual cap | $___ | Flag for manual review |  |
| Per-account weekly accrual cap | $___ | Auto-hold |  |
| Single-redemption cap | ___ points | Manual review queue |  |
| Refund/cancel reversal | Auto on event | Negative qualifying transaction posted |  |
| Tier-credit reversal pipeline | Auto | DPE re-aggregates → tier evaluation |  |

---

## 6. Partner Loyalty (if applicable)

**Topology:** [ ] Hub-and-spoke   [ ] Peer-to-peer (custom federation)

| Partner | Type | Accrual Factor | Redemption Factor | Ledger Visibility |
|---|---|---|---|---|
|  |  |  |  | own only / member balance / none |
|  |  |  |  |  |

**Partner DPE jobs to activate:**
- [ ] Create Partner Ledgers (cadence: ___)
- [ ] Update Partner Balance (cadence: ___)
- [ ] Aggregate Partner Transactions for Reporting (cadence: ___)

---

## 7. Multi-Region Federation (if applicable)

**Pattern:** [ ] Single program, multi-region   [ ] Federated programs (one per region)   [ ] Tiered hybrid

| Region | Program Record | Local Tier Names | Cross-Earn Mechanism |
|---|---|---|---|
| US | LoyaltyProgram_US | Bronze/Silver/Gold | Platform Event |
| EU | LoyaltyProgram_EU | Member/Bronze/Silver/Gold | Platform Event |
| APAC |  |  |  |

**Tier mapping (cross-region equivalence):** ___________

**Lifetime status reconciliation:** quarterly DPE that rolls per-region lifetime totals to a global member field

---

## 8. Tier Descalation Policy

- [ ] Reset cadence: annual / anniversary / biennial
- [ ] Grace period on missed threshold: ___ months at current tier with lower-tier earn rate
- [ ] Lookback window: calendar year / rolling 12 months
- [ ] Lifetime status path: yes / no — criteria: ___________
- [ ] Pre-descalation comms cadence: 30/60/90 days out

---

## 9. DPE Schedule

| DPE Job | Cadence | Dependencies | Failure Handling |
|---|---|---|---|
| Reset Qualifying Points | Annual / Anniversary | none |  |
| Aggregate/Expire Fixed Non-Qualifying Points | Monthly | none |  |
| Tier Evaluation | Daily / Hourly | Aggregate must complete |  |
| Create Partner Ledgers (if partner) | Daily |  |  |
| Update Partner Balance (if partner) | Daily | Create Partner Ledgers must complete |  |

---

## 10. Hand-Off To Implementation

- [ ] Architecture document signed off by marketing, finance, legal
- [ ] Hand-off package includes: tier-ladder spec, currency design, fraud-control matrix, DPE schedule, partner topology (if applicable), multi-region pattern (if applicable), descalation policy
- [ ] Implementation team has access to `integration/loyalty-management-setup` skill
- [ ] Open questions log: ___________

---

## Notes

Record deviations from canonical patterns and the reasoning:
