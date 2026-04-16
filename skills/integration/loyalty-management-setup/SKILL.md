---
name: loyalty-management-setup
description: "Use this skill when setting up or extending Salesforce Loyalty Management — including program and currency creation, tier group design, qualifying vs. non-qualifying point currency separation, DPE batch job activation, partner loyalty configuration, and member portal setup on Experience Cloud. Triggers on: Loyalty Management setup, loyalty tier setup Salesforce, qualifying points vs redemption points, DPE batch job for loyalty, partner loyalty program Salesforce, loyalty member portal. NOT for Marketing Cloud engagement program design (separate product), not for B2B loyalty via Sales Cloud (standard opportunity, not loyalty program), not for general Experience Cloud site setup (use experience-cloud-setup skill)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - loyalty-management
  - loyalty-program
  - tier-management
  - qualifying-points
  - non-qualifying-points
  - partner-loyalty
  - dpe
  - data-processing-engine
  - member-portal
  - experience-cloud
inputs:
  - "Loyalty Management license enabled on the org"
  - "Loyalty program structure: tier groups, tiers, currencies defined"
  - "DPE (Data Processing Engine) permission sets assigned"
  - "Partner organizations and conversion factors (for partner loyalty)"
outputs:
  - "Configured Loyalty Program with tier groups and currency types"
  - "Activated DPE batch jobs for tier processing and point expiration"
  - "Partner Loyalty configuration with ledger and balance tracking"
  - "Loyalty Member Portal on Experience Cloud"
triggers:
  - "Salesforce Loyalty Management program setup"
  - "qualifying vs non-qualifying points currency loyalty"
  - "DPE batch job for loyalty tier reset"
  - "partner loyalty DPE configuration"
  - "loyalty member portal Experience Cloud setup"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Loyalty Management Setup

This skill activates when a practitioner is setting up or troubleshooting Salesforce Loyalty Management — the Industry Cloud product for customer loyalty programs. It covers the two-currency model (qualifying vs. non-qualifying), tier design constraints, DPE batch job requirements, partner loyalty configuration, and member portal setup. It does NOT cover Marketing Cloud engagement programs or general Experience Cloud setup.

---

## Before Starting

Gather this context before working on anything in this domain:

- Loyalty Management separates currencies into two distinct types with different purposes: **qualifying** (tier points, measuring engagement for tier advancement — one currency per tier group) and **non-qualifying** (redeemable for products/services — can have multiple per program). These are not interchangeable.
- A qualifying currency can be associated with **only one tier group** at a time — this is a hard structural constraint.
- Tier assessment is driven by **DPE batch jobs** (Reset Qualifying Points, Aggregate/Expire Fixed Non-Qualifying Points) that must be explicitly activated and scheduled. They are NOT automatic by default.

---

## Core Concepts

### Two-Currency Architecture: Qualifying vs. Non-Qualifying

This is the foundational design concept in Loyalty Management:

**Qualifying Points (Tier Currency):**
- Used ONLY for tier advancement — measuring whether a member qualifies for a tier
- Do NOT expire unless explicitly configured
- Are typically reset at the start of a new qualifying period
- One qualifying currency per tier group (hard constraint)
- Examples: miles flown for airline status, spend amount for VIP tier

**Non-Qualifying Points (Redemption Currency):**
- Redeemable for rewards, products, discounts
- Can expire based on configured expiration rules
- Multiple non-qualifying currencies per program are allowed
- Examples: reward points redeemable for products

Mixing these concepts — using non-qualifying points for tier assessment — breaks the tier calculation engine. Tier groups look specifically for their associated qualifying currency record.

### Tier Groups and Tiers

A **Tier Group** defines a set of tiers (e.g., Silver, Gold, Platinum) and is associated with exactly one qualifying currency. Tiers within a tier group have threshold values for the qualifying currency.

A qualifying currency can be associated with only one tier group. If a program needs multiple tier tracks (e.g., one for spending, one for engagement), separate qualifying currencies and tier groups must be created.

### DPE Batch Jobs Are Not Automatic

Loyalty Management tier processing relies on Data Processing Engine (DPE) batch jobs. These are NOT automatically scheduled:

- **Reset Qualifying Points** — resets qualifying currency balances at the start of each qualifying period. Must be activated and scheduled.
- **Aggregate/Expire Fixed Non-Qualifying Points** — handles point expiration rules. Must be activated and scheduled.

Without these jobs running, tier advancement stops working, points accumulate without expiring, and members cannot be promoted or demoted between tiers.

### Partner Loyalty

Partner organizations can earn and redeem points in a Loyalty Program. Configuration requires:

1. **Partner Loyalty Program** record linking the external partner organization
2. **LoyaltyProgramPartner** record with accrual factor and redemption factor
3. **Create Partner Ledgers DPE definition** — must be activated or no partner balance tracking occurs
4. **Update Partner Balance DPE definition** — must also be activated

Without the Partner DPE definitions activated, partner transactions are recorded but balances are never calculated.

### Member Portal on Experience Cloud

The Loyalty Member Portal uses the **Loyalty Member Portal Experience Cloud template**. Only **one loyalty program can be associated with a given Experience Cloud site**. Members log in to view their points, tier status, and transaction history.

---

## Common Patterns

### Pattern 1: Program Setup with Qualifying and Non-Qualifying Currencies

**When to use:** First-time Loyalty Program configuration.

**How it works:**

1. In Loyalty Management Setup, create a **Loyalty Program**.
2. Create a **Non-Qualifying Currency** (e.g., "Reward Points") — redeemable.
3. Create a **Tier Group** (e.g., "Status Tier").
4. Create a **Qualifying Currency** (e.g., "Elite Qualifying Miles") — associate it with the Tier Group.
5. Create **Tiers** within the Tier Group with qualifying currency thresholds (e.g., Silver: 0, Gold: 25000, Platinum: 75000).
6. Configure **Promotion Rules** to define how members earn qualifying and non-qualifying points per transaction.
7. Activate and schedule the **Reset Qualifying Points** DPE job.

**Why separate currencies:** Using a single currency for both redemption and tier tracking makes it impossible to reset tier progress without wiping redemption balances, and vice versa.

### Pattern 2: Activate DPE Jobs for Tier Processing

**When to use:** After program setup, before going live.

**How it works:**

1. In Setup > Data Processing Engine, locate the **Reset Qualifying Points** definition linked to the Loyalty Program.
2. Activate the definition.
3. Schedule the job: typically run at the start of each qualifying period (annually or quarterly per program rules).
4. Locate the **Aggregate/Expire Fixed Non-Qualifying Points** definition.
5. Activate and schedule according to the program's point expiration policy.
6. Test by running the DPE jobs manually in a sandbox and verifying tier recalculation results.

**Why not rely on defaults:** DPE jobs are opt-in. Without activation, the Loyalty program will not advance members through tiers regardless of qualifying point accumulation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single tier track (spend-based) | One qualifying currency + one tier group | Hard constraint: one qualifying currency per tier group |
| Multiple tier tracks (spend + engagement) | Two qualifying currencies + two tier groups | Each track needs its own qualifying currency |
| Points that expire | Use non-qualifying currency with expiration rules | Qualifying points typically reset, not expire |
| Partner points earning and redemption | Partner Loyalty + LoyaltyProgramPartner + Partner DPE | Partner balances require separate DPE definitions |
| Member self-service portal | Loyalty Member Portal Experience Cloud template | Only one program per Experience Cloud site |

---

## Recommended Workflow

1. Design the point economy on paper first: identify tier currencies (qualifying) and redemption currencies (non-qualifying) before touching Setup.
2. Create the Loyalty Program, then currencies (non-qualifying first, then qualifying with tier group association).
3. Create the Tier Group and associate the qualifying currency. Create Tiers with thresholds.
4. Configure Promotion Rules for earning points.
5. Activate and schedule DPE batch jobs: Reset Qualifying Points and Aggregate/Expire Fixed Non-Qualifying Points.
6. For partner loyalty: create LoyaltyProgramPartner records and activate Create Partner Ledgers and Update Partner Balance DPE definitions.
7. Set up the Loyalty Member Portal Experience Cloud site using the Loyalty Member Portal template and associate it with the program.
8. Test end-to-end: earn points, verify tier advancement after DPE run, test partner balance tracking.

---

## Review Checklist

- [ ] Qualifying and non-qualifying currencies correctly separated — no conflation
- [ ] Each tier group associated with exactly one qualifying currency
- [ ] DPE Reset Qualifying Points job activated and scheduled
- [ ] DPE Aggregate/Expire Fixed Non-Qualifying Points job activated and scheduled
- [ ] Partner Loyalty: Create Partner Ledgers DPE activated
- [ ] Partner Loyalty: Update Partner Balance DPE activated
- [ ] Member portal: only one loyalty program associated with the Experience Cloud site
- [ ] Promotion rules configured for qualifying and non-qualifying earning

---

## Salesforce-Specific Gotchas

1. **Qualifying and Non-Qualifying Currencies Are Not Interchangeable** — Using non-qualifying points for tier assessment silently breaks the tier calculation engine. Tier groups are configured to look for their associated qualifying currency. Build the two-currency architecture from the start.

2. **DPE Jobs Are Not Auto-Scheduled** — New Loyalty Programs have no active DPE jobs. Tier advancement will not occur without explicitly activating and scheduling the Reset Qualifying Points DPE definition. This is the most common go-live gap.

3. **One Qualifying Currency Per Tier Group** — A qualifying currency can be associated with only one tier group. If this constraint is missed in design, re-architecting the currency model after member data is accumulated is extremely difficult.

4. **Partner Loyalty Requires Two Separate DPE Definitions** — Both Create Partner Ledgers AND Update Partner Balance must be activated. Activating only one results in partner transactions being recorded but balances not being calculated.

5. **One Loyalty Program Per Experience Cloud Site** — The Loyalty Member Portal template only supports one loyalty program association per site. Organizations with multiple loyalty programs must create separate Experience Cloud sites for each.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Loyalty Program blueprint | Program design with qualifying/non-qualifying currencies, tier groups, and tiers |
| DPE activation checklist | List of DPE definitions to activate with recommended schedule cadence |
| Partner Loyalty configuration | LoyaltyProgramPartner records with conversion factors and DPE activations |
| Member portal setup guide | Experience Cloud site creation using Loyalty Member Portal template |

---

## Related Skills

- loyalty-program-architecture — for architect-level tier economy and partner integration design decisions
- experience-cloud-setup — for Experience Cloud site setup prerequisites before configuring the Loyalty Member Portal
