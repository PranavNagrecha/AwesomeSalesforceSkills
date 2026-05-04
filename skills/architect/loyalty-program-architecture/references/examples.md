# Examples — Loyalty Program Architecture

## Example 1: Three-Tier Program For A 4M-Member Quick-Service Restaurant Chain

**Context:** A national quick-service restaurant brand with 4 million app-active customers wants to launch a loyalty program to lift visit frequency by 8% and average ticket by 3%. Marketing and finance have committed to those targets and to a 70/22/8 tier distribution (Bronze / Silver / Gold).

**Problem:** The brand's first proposal: 5 tiers, 1 point per dollar, gold threshold at 500 points. Architectural review shows: at the brand's average ticket of $12 and 18 visits per year per loyal customer (based on transaction data), 18 × 12 = 216 points/year — well below the 500 threshold. Even the top 5% of customers earn 750 points. The proposal would put 99% of members in Bronze, defeating the purpose.

**Solution:**

Architecture document delivered:

**Tier ladder:**
- Bronze (entry, automatic on enrollment) — 70% target population
- Silver (90th percentile spend = $260 annual = 260 qualifying points) — 22% target
- Gold (98th percentile spend = $520 annual = 520 qualifying points) — 8% target

**Currency design:**
- 1 qualifying point per $1 spent
- 10 non-qualifying ("Crave Points") per $1 spent — visible-ratio prevents collapse
- Redemption: $1 off menu = 100 Crave Points (1% effective discount, sustainable)

**Fraud controls:**
- DPE flags > $300 single-day per-account accrual for manual review (typical max-loyalty-customer pattern is < $50/day)
- Refund event triggers a tier-credit reversal in the qualifying ledger
- Redemptions over 5,000 points (~$50 reward) go to a queue, not auto-issue

**Annual reset:** member-anniversary-date based to spread DPE load across the year.

**Tier descalation:** soft-landing — a member who misses Silver threshold drops to Bronze at next anniversary but earns at Bronze rate; the marketing team gets a warning email pipeline 30/60/90 days out.

**Why it works:** The thresholds are derived from real customer behavior, not a marketing wish. Three tiers match the population shape (no long-tail VIP segment to justify a 4th/5th tier). The 1:10 currency ratio gives "you have 5,000 Crave Points!" marketing weight without inflating the tier engine. Fraud controls are right-sized to actual customer behavior (5x the typical max).

---

## Example 2: Hub-And-Spoke Partner Loyalty For A Hotel Chain

**Context:** A hotel chain with 8M loyalty members wants to extend earning to a network of 12 partner brands (3 airlines, 2 car rental, 4 dining, 3 retail). Members complain the existing program "only rewards staying at hotels" — they want to earn on the full travel journey.

**Problem:** The implementation team's first instinct is to build a custom integration per partner — bespoke ETL, partner-specific Apex, partner-specific objects. By partner #3 the org has 14 custom objects, 8 batch jobs, and a fragmented ledger.

**Solution:**

Architecture document delivered:

**Topology:** Hub-and-spoke. Hotel program is the hub; 12 partners are spokes.

**Per-partner config (`LoyaltyProgramPartner`):**

| Partner | Type | Accrual Factor | Redemption Factor |
|---|---|---|---|
| Airline A (alliance member) | Travel | 1.5 | 1.0 |
| Airline B | Travel | 1.0 | 1.0 |
| Car rental A | Travel | 1.0 | 1.0 |
| Dining (4 brands) | Lifestyle | 0.5 | 0.5 |
| Retail (3 brands) | Lifestyle | 0.3 | 0.5 |

**Ledger:** all earning posts to the hotel central ledger via `LoyaltyMemberCurrency` records. Partner-side rewards consume central balance with the configured redemption factor.

**Partner DPE jobs activated:**
- `Create Partner Ledgers` — schedules nightly
- `Update Partner Balance` — schedules nightly
- `Aggregate Partner Transactions for Reporting` — weekly

**Partner ledger visibility:** partners see their own posted transactions but not member balances (privacy boundary). A partner-portal Experience Cloud site is built per the integration/loyalty-management-setup skill's member portal pattern.

**Fraud isolation:** per-partner daily-rate-limit, alerted to the hotel program team. A compromised partner feed is contained without member-balance risk.

**Why it works:** Salesforce Loyalty Management's `LoyaltyProgramPartner` model is the supported hub-and-spoke implementation. Custom integrations per partner work but produce the 14-objects sprawl. The accrual-factor mechanism handles partner economics without per-partner Apex.

---

## Anti-Pattern: Tier Inflation Without A Descalation Plan

**What practitioners do:** Launch a program with generous initial thresholds to drive sign-ups. "Make Gold easy in year 1 to seed the top tier with influencers."

**What goes wrong:**
- Year 1: 8% of members are Gold, marketing celebrates.
- Year 2: 18% are Gold, no one fell out (no descalation rule).
- Year 3: 35% are Gold, the tier is no longer aspirational, brand-team panic, "raise the threshold!"
- Year 4: legacy Gold members revolt when they're descaled retroactively.

The program is now a brand crisis instead of a loyalty driver.

**Correct approach:** Architect descalation in v1, not v3. Specify:
- Annual qualifying reset (calendar or anniversary-date)
- Soft-landing grace (one-tier-down at next anniversary, not two)
- 30/60/90-day pre-descalation marketing campaigns
- Lifetime status as the only "Gold forever" path, with clearly published criteria

Generous launch thresholds are fine **if** the descalation pipeline is in place from Day 1. Without it, generosity becomes a one-way door.
