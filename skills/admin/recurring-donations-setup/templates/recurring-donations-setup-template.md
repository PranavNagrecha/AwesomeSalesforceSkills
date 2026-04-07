# Recurring Donations Setup — Work Template

Use this template when configuring, troubleshooting, or documenting NPSP Enhanced Recurring Donations in an org.

## Scope

**Skill:** `recurring-donations-setup`

**Request summary:** (fill in what the user asked for — e.g., "Enable ERD and configure monthly installments" or "Diagnose why Upcoming Installments UI does not reflect Opportunity edit")

---

## Context Gathered

Answer these before taking any action:

- **ERD or Legacy?** (Verified in NPSP Settings > Recurring Donations):
- **NPSP version installed:**
- **Default installment period configured (Monthly / Quarterly / Annually / Weekly / Custom):**
- **Day of Month default:**
- **Lapsed threshold (days since last payment):**
- **Closed threshold (days since last payment):**
- **Batch job scheduled?** (Yes / No / Unknown):
- **Known constraints or customizations in this org:**

---

## Approach

Which pattern from SKILL.md applies to this request?

- [ ] Configuring a new Recurring Donation from scratch
- [ ] Applying a future-dated amount or schedule change (Effective Date pattern)
- [ ] Diagnosing Upcoming Installments UI vs. actual Opportunity records
- [ ] Diagnosing Lapsed / Closed status issues
- [ ] Diagnosing nightly batch failures or stale rollup fields
- [ ] Migrating from legacy model to ERD
- [ ] Other: _______________

**Why this pattern applies:**

---

## Schedule Object State

Document the active `npe03__RecurringDonationSchedule__c` record for the Recurring Donation in scope:

| Field | Value |
|---|---|
| Record ID | |
| npe03__Amount__c | |
| npe03__InstallmentPeriod__c | |
| npe03__InstallmentFrequency__c | |
| npe03__DayOfMonth__c | |
| npe03__StartDate__c (Effective Date) | |
| Status__c | Active |

If there are additional Inactive schedule records (history), note them here:

| Record ID | Amount | Period | Status | StartDate |
|---|---|---|---|---|
| | | | Inactive | |

---

## Current Open Pledged Opportunity

In ERD, there should be exactly ONE open pledged Opportunity per active Recurring Donation:

| Field | Value |
|---|---|
| Opportunity ID | |
| CloseDate | |
| Amount | |
| StageName | Pledged |
| npe03__Recurring_Donation__c | (parent RD ID) |

If more than one open pledged Opportunity exists, document the count and investigate whether the org is running legacy mode or has a batch/trigger issue.

---

## Checklist

Copy and complete before marking the task done:

- [ ] ERD mode confirmed active in NPSP Settings (not legacy mode)
- [ ] Installment Period, Frequency, and Day of Month defaults are configured
- [ ] Lapsed and Closed status thresholds are set in NPSP Settings > Recurring Donations
- [ ] Test Recurring Donation created with exactly ONE future pledged installment Opportunity
- [ ] npe03__RecurringDonationSchedule__c record present on test Recurring Donation with correct values
- [ ] Upcoming Installments UI confirmed to show schedule projections (not Opportunity record edits)
- [ ] Future-dated amount change tested: new schedule record created, current Opportunity unchanged
- [ ] Nightly batch confirmed scheduled and recalculating rollup fields correctly
- [ ] Total Paid Amount and Number of Paid Installments update after closing a test installment Opportunity

---

## Change Log

Document any changes made during this task:

| Change | Before | After | Reason |
|---|---|---|---|
| | | | |

---

## Notes and Deviations

Record any deviations from the standard ERD pattern and the reason why:

(e.g., "Org has a custom Flow that pre-creates future Opportunities for reporting purposes — this is intentional and the team is aware it bypasses ERD's single-installment constraint.")
