# Soft Credits and Matching Gifts — Work Template

Use this template when working on a soft credit or matching gift task in NPSP.

## Scope

**Skill:** `soft-credits-and-matching`

**Request summary:** (fill in what the user or ticket asked for)

**Credit type:** (check one)
- [ ] Relationship-based soft credit (board member, solicitor, influencer)
- [ ] Household auto-soft-credit investigation or adjustment
- [ ] Matching gift — new configuration
- [ ] Matching gift — duplicate record remediation
- [ ] Rollup recalculation / stale totals
- [ ] Partial soft credit split between multiple recipients

---

## Context Gathered

Answer these before proceeding:

- **NPSP version installed:** ___________
- **Rollup mode (Real-Time or Batch):** ___________
- **Soft credit roles configured in NPSP Settings > Contact Roles:** ___________
- **Does the employer Account have an open Matching Gift Opportunity?** (for matching gift tasks) Yes / No / N/A
- **Known constraints or limits:** ___________
- **Failure modes already observed:** ___________

---

## Pre-Flight Checks

- [ ] NPSP managed package confirmed installed
- [ ] Soft credit role values confirmed in NPSP Settings > Contact Roles > Soft Credit Roles list
- [ ] For matching gifts: Matching Gift Opportunity exists on employer Account before Find Matched Gifts
- [ ] For matching gifts: no existing Matched Donor OCR already on the Matching Gift Opportunity for this contact (to avoid duplicate-record bug)

---

## OCR Configuration

| Opportunity | Contact | Role | Is Primary | Notes |
|---|---|---|---|---|
| (opp name or ID) | (contact name) | Soft Credit / Matched Donor / Household Member | false | |

---

## Partial Soft Credit Records (if applicable)

Complete this section only when the credited amount differs from the full opportunity amount.

| Opportunity | Contact | Amount | OCR Id | Notes |
|---|---|---|---|---|
| (opp name or ID) | (contact name) | $_____ | (OCR record Id) | |

**Reminder:** `npsp__Contact_Role_ID__c` must be populated. A missing OCR Id means NPSP silently uses the full opportunity amount instead of the partial amount.

---

## Matching Gift Linkage (if applicable)

| Employee Donation Opportunity | Matching Gift Opportunity (on employer) | Match Amount | npsp__Matching_Gift__c populated? |
|---|---|---|---|
| | | $ | Yes / No |

---

## Duplicate Record Check

After any Find Matched Gifts operation, run this query:

```sql
SELECT ContactId, Count(Id) cnt
FROM OpportunityContactRole
WHERE OpportunityId = '[matching_gift_opp_id]'
  AND Role = 'Matched Donor'
GROUP BY ContactId
HAVING Count(Id) > 1
```

- [ ] Query returned 0 rows (no duplicates)
- [ ] Duplicates found and removed before rollup recalculation

---

## Rollup Recalculation

- [ ] Manual recalculation triggered via NPSP Settings > Batch Processing > Recalculate Rollups, OR
- [ ] Contact-level Recalculate Rollups button used for affected contacts
- [ ] Soft credit rollup fields verified after recalculation:

| Contact | npsp__Soft_Credit_This_Year__c | Expected | Match? |
|---|---|---|---|
| | | $ | Yes / No |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Relationship-based soft credit (full amount OCR)
- [ ] Partial soft credit split (OCR + Partial_Soft_Credit__c per recipient)
- [ ] Matching gift via Find Matched Gifts
- [ ] Rollup stale totals — trigger recalculation only

Reason this pattern was chosen: ___________

---

## Deviations and Notes

Record any deviations from the standard pattern and why:

(none)

---

## Completion Checklist

- [ ] Required OCR records created with correct roles
- [ ] `npsp__Partial_Soft_Credit__c` records created where partial amounts apply, with `npsp__Contact_Role_ID__c` populated
- [ ] For matching gifts: Matching Gift Opportunity linked via `npsp__Matching_Gift__c` on employee donation
- [ ] No duplicate OCR or Partial_Soft_Credit__c records remaining
- [ ] Rollup recalculation triggered and soft credit totals verified
- [ ] Affected Contact records spot-checked — totals match expected values
