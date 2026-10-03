---
name: loyalty-management-setup
description: "Use this skill when setting up or extending Salesforce Loyalty Management — including program and currency creation, tier group design, qualifying vs. non-qualifying point currency separation, DPE batch job. NOT for Marketing Cloud engagement program design or B2B loyalty via Sales Cloud — use architect/loyalty-program-architecture."
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
  - "Partner accounts and their accrual and redemption cost per unit (for partner loyalty)"
outputs:
  - "Configured Loyalty Program with tier groups and currency types"
  - "Cloned and activated DPE definitions run from flows for point balances, qualifying-point reset, and expiration"
  - "Generated Change Tier loyalty program process for tier assessment"
  - "Partner Loyalty configuration with ledger and balance tracking"
  - "Loyalty Member Portal on Experience Cloud"
triggers:
  - "Salesforce Loyalty Management program setup"
  - "qualifying vs non-qualifying points currency loyalty"
  - "DPE batch job for loyalty tier reset"
  - "partner loyalty DPE configuration"
  - "loyalty member portal Experience Cloud setup"
  - "loyalty management cloud program and tier rules"
  - "set up loyalty program rules tier point accrual"
  - "configure loyalty management for retail brand"
  - "send transaction journals to a loyalty program from an external POS"
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Loyalty Management Setup

This skill activates when a practitioner is setting up or troubleshooting Salesforce Loyalty Management, the Industry Cloud product for customer loyalty programs. It covers the two-currency model (qualifying vs. non-qualifying), tier groups and tier assessment, the Data Processing Engine (DPE) templates that calculate balances, reset qualifying points, and expire points, partner loyalty, the member portal, and the Transaction Journals API that feeds the program. It does NOT cover Marketing Cloud engagement programs or general Experience Cloud setup.

---

## Before Starting

Gather this context before working on anything in this domain:

- Loyalty Management separates currencies into **qualifying** (engagement, used for tier evaluation) and **non-qualifying** (earned for redemption). A qualifying currency "can be associated with only one tier group", and "a tier group can have more than one qualifying point" (Loyalty Management guide, Loyalty Program Currencies).
- Confirm the license: several features named here (the generated tier assessment process, Batch Management for loyalty processes, the DPE templates) require Loyalty Management - Growth or Loyalty Management - Advanced, or the B2C/B2B Loyalty licenses the guide lists per feature.
- DPE templates do not run on their own. Admins clone a template, activate the clone, and run it from a flow at the required frequency.
- Decide where transactions come from: an external system posting to the Transaction Journals Execution resource, records created in Salesforce, or both.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "What earns status, and what earns rewards?" | Status uses qualifying currencies tied to a tier group; rewards use non-qualifying currencies that can expire by a fixed period or by inactivity | The currency list with type, tier group, and expiry model | Status can reset without touching reward balances |
| "Is status measured on one currency or several?" | The generated tier assessment process takes a minimum balance for one qualifying currency (the tier group's tier assessment currency); two or more need a custom process | A one-currency design, or an explicit custom tier process | Tier changes that follow the stated rules instead of a process nobody can regenerate |
| "When do qualifying points reset, and how often must balances, expirations, and tiers update?" | Reset dates come from the tier model; DPE clones run only when a flow runs them; tier upgrades run in real time or through Batch Management | A schedule per DPE clone and per tier process | Balances and tiers that are current when members look |
| "Do partners earn or redeem, and are they prepaid or postpaid?" | `LoyaltyProgramPartner` holds `BillingType`, `PartnerType`, and cost per unit; the Create Partner Ledgers and Update Partner Balances definition maintains ledgers | The partner list with billing type and costs | Partner balances that reconcile with invoices |
| "Will members use a portal, and how many programs exist?" | An Experience Cloud site can be associated with only one loyalty program | The site-to-program map | No late discovery that two programs need two sites |
| "Which system sends transactions, and must promotion limits be enforced?" | The Transaction Journals Execution resource does not enforce `PromotionLimit` unless the caller first uses Eligible Promotions List | The integration call sequence | Promotions that respect their usage limits |

What a proper configuration adds over "just creating a program": currencies, tier rules, and DPE schedules match the business rules, tier changes run on a documented trigger, partner ledgers reconcile, and transaction feeds apply promotion limits.

---

## Core Concepts

### Two-Currency Architecture: Qualifying vs. Non-Qualifying

| | Qualifying points (QP) | Non-qualifying points (NQP) |
|---|---|---|
| Purpose | Engagement; tier upgrade and downgrade | Redemption for rewards |
| Tier group link | One tier group per qualifying currency; a tier group can have several qualifying currencies | None |
| Lifecycle | Reset to zero on the reset date by the Reset Qualifying Points job | Expire by the currency's expiry model: Fixed (each point after a period) or Activity (whole balance after inactivity) |
| Data model | `LoyaltyProgramCurrency.CurrencyType = Qualifying`, `LoyaltyTierGroupId` set | `LoyaltyProgramCurrency.CurrencyType = NonQualifying` |

Member balances live in `LoyaltyMemberCurrency` (`PointsBalance`, `TotalPointsAccrued`, `LastResetDate`, and related fields), which links to `LoyaltyProgramCurrency`; the currency type is read through that relationship. Since API 58.0, `LoyaltyTierGroup.TierAssessmentCurrencyId` names the currency used to assign tiers.

### Tier Assessment

Program managers set the minimum eligible balance for each tier (Manage Tier Eligibility), then Generate Rules. Salesforce generates and activates a Change Tier loyalty program process for that tier group. The process can run in real time as a child of a Transaction Journal process, or in batches through a Batch Management job that selects members with Eligible for Tier Assessment checked (Loyalty Management Settings: Select Members for Tier Assessment Automatically). Regenerate the process after changing any tier's eligible balance or name, or after adding a tier.

### Data Processing Engine Templates

| Template | What it does |
|---|---|
| Credit Qualifying / Non-Qualifying Points to Members (Point Balance Calculation) | Aggregates points credited since the last run into member balances |
| Reset Qualifying Points | Resets qualifying balances to zero based on the tier model |
| Expire Fixed Non-Qualifying Points, and Expire Fixed Non-Qualifying Points Using Aggregated Expiration Ledgers | Expire fixed-model non-qualifying points |
| Roll Over Escrow Points to Members | Moves escrow points into balances |
| Create Partner Ledgers and Update Partner Balances | One definition that updates partner points (prepaid) or balance amount (postpaid) and creates partner ledgers |

"After the cloned definition is modified and activated, it's available in the Flow Builder as an action. Use the action to run the definition at your required frequency." The balance templates assume only they update balances in batches; if the org updates balances in real time, make the definitions ignore ledgers already processed.

### Partner Loyalty

A `LoyaltyProgramPartner` record links a partner `Account` (`LoyaltyPartnerId`) to the program, with `PartnerType` (Accrual, Redemption, Both), `BillingType` (Prepaid, Postpaid), `AccrualCostperUnit`, and `RedemptionCostperUnit`. Prepaid partners buy points packs; the Create Partner Ledgers and Update Partner Balances definition maintains their balances.

### Member Portal on Experience Cloud

The Loyalty Member Portal template creates the portal. "You can't associate the same Experience Cloud site to another loyalty program." If no program is associated, the site shows every program the contact belongs to.

### Transaction Journals API

`POST /services/data/vXX.X/connect/realtime/loyalty/programs/{programName}` (API 54.0+) creates and processes transaction journals against the program's processes. It needs one of the B2C - Loyalty, B2C - Loyalty Plus, Loyalty Management - Growth, or Loyalty Management - Advanced licenses and the Loyalty Management permission set. A worked request is in [`references/metadata-examples.md`](references/metadata-examples.md).

---

## Common Patterns

### Pattern 1: Program Setup with Qualifying and Non-Qualifying Currencies

**When to use:** First-time Loyalty Program configuration.

**How it works:**

1. Create the Loyalty Program.
2. Create the Tier Group (e.g., "Status Tier") and its Tiers.
3. Create the Qualifying Currency (e.g., "Elite Qualifying Miles") and associate it with the tier group.
4. Create the Non-Qualifying Currency (e.g., "Reward Points") with its expiry model.
5. Set each tier's minimum eligible balance and Generate Rules to create the Change Tier process.
6. Configure Transaction Journal processes that credit qualifying and non-qualifying points.
7. Clone, activate, and schedule (through flows) the DPE templates the program needs.

**Why separate currencies:** A single currency cannot reset status without wiping redemption balances.

### Pattern 2: Run DPE Templates on a Schedule

**When to use:** After program setup, before going live.

**How it works:**

1. From the DPE templates for Loyalty Management, clone Reset Qualifying Points and the expiration template that fits the expiry model.
2. Adjust the clone if needed and activate it.
3. Build a scheduled flow that calls the clone's action at the required frequency (for example, daily for balances and expiration, on the reset date for qualifying points).
4. Run the flow in a sandbox and check member balances and `LastResetDate` values.

**Why not rely on defaults:** Templates are templates. Nothing runs until a clone is activated and a flow calls it.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single tier track (spend-based) | One qualifying currency on one tier group, tier assessment from the generated process | The generated process supports one currency |
| Status measured on two currencies together | Custom tier process (DPE or Apex to select members, Tier Processing process with Change Member Tier) | The generated process takes one currency |
| Independent tracks (spend tiers and engagement clubs) | Separate tier groups, each with its own qualifying currency | A qualifying currency belongs to one tier group |
| Points that expire | Non-qualifying currency with a Fixed or Activity expiry model | Qualifying points reset; they do not expire |
| Partner earning and redemption | `LoyaltyProgramPartner` plus the Create Partner Ledgers and Update Partner Balances definition | One definition maintains ledgers and balances |
| Member self-service portal | Loyalty Member Portal template, one site per program | A site can be associated with only one program |

---

## Recommended Workflow

1. Design the point economy first: list currencies with type, tier group, expiry model, and reset dates.
2. Create the program, tier groups, tiers, and currencies; set the tier assessment currency and eligible balances, then Generate Rules.
3. Build Transaction Journal processes for accrual and redemption; retrieve them as `LoyaltyProgramSetup` into source control.
4. Clone, activate, and schedule the DPE templates through flows; set up Batch Management for tier assessment if it is not real time.
5. For partners, create `LoyaltyProgramPartner` records and clone the Create Partner Ledgers and Update Partner Balances definition.
6. Set up the member portal and connect the transaction source; call Eligible Promotions List before Transaction Journals Execution when promotion limits apply.
7. Run `python3 skills/integration/loyalty-management-setup/scripts/check_loyalty_management_setup.py --manifest-dir <project>` and test end to end in a sandbox: earn, assess tier, reset, expire.

---

## Review Checklist

- [ ] Qualifying and non-qualifying currencies separated; each qualifying currency on exactly one tier group
- [ ] Tier assessment currency and minimum eligible balances set; Change Tier process generated after the last tier change
- [ ] DPE clones for balances, reset, and expiration activated and called by scheduled flows
- [ ] Batch Management job (or real-time child process) runs tier assessment
- [ ] Partner Loyalty: Create Partner Ledgers and Update Partner Balances clone active and scheduled
- [ ] Member portal: each site associated with one program
- [ ] Member currency records exist for currencies added after members enrolled
- [ ] Transaction feed calls Eligible Promotions List first where promotion limits apply

---

## Salesforce-Specific Gotchas

One-line summaries; the full entries are in [`references/gotchas.md`](references/gotchas.md).

| Gotcha | Short form |
|---|---|
| Templates do not run themselves | Clone, activate, then call from a flow |
| One currency per generated tier process | Two-currency status needs a custom process |
| Partner DPE | One definition, Create Partner Ledgers and Update Partner Balances |
| New currencies | Existing members need `LoyaltyMemberCurrency` records created by a custom process |
| Real-time and batch balance updates | Make the DPE definitions skip ledgers already processed |
| `LoyaltyProgramSetup` label | A label that matches no program creates a new program on deploy |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Loyalty Program blueprint | Currencies, tier groups, tiers, expiry models, reset dates |
| DPE schedule | Cloned definitions, their flows, and cadence |
| Tier assessment design | Generated or custom process, real time or Batch Management |
| Partner Loyalty configuration | `LoyaltyProgramPartner` records and the partner ledger definition |
| Integration contract | Transaction Journals Execution calls with promotion-limit handling |

---

## Related Skills

- loyalty-program-architecture — for architect-level tier economy and partner integration design decisions
- experience-cloud-setup — for Experience Cloud site setup prerequisites before configuring the Loyalty Member Portal
