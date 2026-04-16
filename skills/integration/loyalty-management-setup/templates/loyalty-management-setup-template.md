# Loyalty Management Setup — Work Template

## Scope

**Skill:** `loyalty-management-setup`

**Request summary:** (fill in: program creation, tier design, DPE activation, partner loyalty, or portal setup)

## Currency Architecture

| Currency Name | Type | Purpose | Tier Group Association |
|---|---|---|---|
| (e.g., Reward Points) | Non-Qualifying | Redemption | N/A |
| (e.g., Elite Qualifying) | Qualifying | Tier measurement | (Tier Group name) |

- **One qualifying currency per tier group:** [ ] Confirmed
- **Non-qualifying points NOT used for tier thresholds:** [ ] Confirmed

## Tier Group Design

| Tier Group | Qualifying Currency | Tiers (name: min threshold) |
|---|---|---|
| (Tier Group name) | (Currency name) | Silver: 0, Gold: 25000, Platinum: 75000 |

## DPE Job Activation

| DPE Definition | Activated? | Scheduled? | Cadence |
|---|---|---|---|
| Reset Qualifying Points | [ ] Yes  [ ] No | [ ] Yes  [ ] No | Annual |
| Aggregate/Expire Fixed Non-Qualifying Points | [ ] Yes  [ ] No | [ ] Yes  [ ] No | Daily |
| Create Partner Ledgers (if partner loyalty) | [ ] Yes  [ ] No | [ ] Yes  [ ] No | |
| Update Partner Balance (if partner loyalty) | [ ] Yes  [ ] No | [ ] Yes  [ ] No | |

## Partner Loyalty (if applicable)

- **LoyaltyProgramPartner records created:** [ ] Yes
- **Accrual factor and redemption factor set:**
- **Both partner DPE definitions activated:** [ ] Yes — BOTH required

## Member Portal

- **Experience Cloud site template:** Loyalty Member Portal
- **One program per site:** [ ] Confirmed
- **Program associated with site:**

## Checklist

- [ ] Two-currency architecture: qualifying (tier) + non-qualifying (redemption)
- [ ] One qualifying currency per tier group
- [ ] Tiers created with threshold values
- [ ] DPE Reset Qualifying Points activated and scheduled
- [ ] DPE Aggregate/Expire activated and scheduled
- [ ] Partner DPE definitions both activated (if partner loyalty)
- [ ] Member portal associated with exactly one program

## Notes

(Record currency naming decisions, DPE schedule cadence, partner conversion factors)
