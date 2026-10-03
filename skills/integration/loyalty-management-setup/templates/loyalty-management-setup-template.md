# Loyalty Management Setup — Work Template

## Scope

**Skill:** `loyalty-management-setup`

**Request summary:** (fill in: program creation, tier design, DPE activation, partner loyalty, or portal setup)

## Currency Architecture

| Currency Name | Type | Purpose | Tier Group Association |
|---|---|---|---|
| (e.g., Reward Points) | Non-Qualifying | Redemption | N/A |
| (e.g., Elite Qualifying) | Qualifying | Tier measurement | (Tier Group name) |

- **Each qualifying currency on exactly one tier group (a tier group may hold several):** [ ] Confirmed
- **Tier assessment currency set on each tier group:** [ ] Confirmed
- **Non-qualifying points NOT used for tier thresholds:** [ ] Confirmed

## Tier Group Design

| Tier Group | Qualifying Currency | Tiers (name: min threshold) |
|---|---|---|
| (Tier Group name) | (Currency name) | Silver: 0, Gold: 25000, Platinum: 75000 |

## DPE Job Activation

| DPE Template | Cloned? | Clone Activated? | Flow That Runs It | Cadence |
|---|---|---|---|---|
| Credit Qualifying / Non-Qualifying Points to Members | [ ] | [ ] | | Daily |
| Reset Qualifying Points | [ ] | [ ] | | Reset date |
| Expire Fixed Non-Qualifying Points (or the Aggregated Expiration Ledgers variant) | [ ] | [ ] | | Daily |
| Create Partner Ledgers and Update Partner Balances (if partner loyalty) | [ ] | [ ] | | |

## Tier Assessment

- **Change Tier process generated (Manage Tier Eligibility > Generate Rules):** [ ] Yes
- **Runs:** [ ] Real time (child of Transaction Journal process)  [ ] Batch Management job
- **Select Members for Tier Assessment Automatically turned on:** [ ] Yes

## Partner Loyalty (if applicable)

- **LoyaltyProgramPartner records created:** [ ] Yes
- **BillingType, PartnerType, AccrualCostperUnit, RedemptionCostperUnit set:**
- **Create Partner Ledgers and Update Partner Balances clone active and scheduled:** [ ] Yes

## Member Portal

- **Experience Cloud site template:** Loyalty Member Portal
- **One program per site:** [ ] Confirmed
- **Program associated with site:**

## Checklist

- [ ] Two-currency architecture: qualifying (tier) + non-qualifying (redemption)
- [ ] Each qualifying currency on exactly one tier group
- [ ] Tiers created with minimum eligible balances; Change Tier process generated
- [ ] DPE clones for balances, reset, and expiration activated and called by scheduled flows
- [ ] Partner ledger definition clone active (if partner loyalty)
- [ ] Member portal associated with exactly one program

## Notes

(Record currency naming decisions, DPE flow schedules, partner cost per unit values)
