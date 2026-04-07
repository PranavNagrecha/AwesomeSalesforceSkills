---
name: recurring-donations-setup
description: "Configure and manage NPSP Enhanced Recurring Donations (ERD): enable ERD mode, define schedule objects, configure installment behavior, set status automation thresholds, and interpret the Upcoming Installments UI. NOT for legacy recurring donations (pre-March 2021 model), one-time Opportunity creation, or custom payment gateway integrations beyond native NPSP."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "set up recurring donations NPSP nonprofit"
  - "recurring donation only creates one future installment not twelve"
  - "upcoming installments UI not showing edits I made to future Opportunity"
  - "how does NPSP enhanced recurring donations schedule work"
  - "recurring donation status lapsed closed threshold configuration"
  - "npe03 recurring donation schedule object"
  - "configure installment frequency period recurring donation"
tags:
  - npsp
  - nonprofit
  - recurring-donations
  - enhanced-recurring-donations
  - installments
  - erd
inputs:
  - NPSP installed (version 3.x+ for ERD support)
  - Confirmation of whether org uses Enhanced Recurring Donations (ERD) or legacy model
  - Desired installment frequency and period (monthly, quarterly, annually, etc.)
  - Status automation thresholds (days for Lapsed and Closed transitions)
  - Whether Effective Date logic is required for mid-stream amount or schedule changes
outputs:
  - Configured Enhanced Recurring Donations feature with correct installment behavior
  - npe03__RecurringDonationSchedule__c objects that drive installment generation
  - Status automation (Active/Lapsed/Closed) wired to days-unpaid thresholds
  - Documented understanding of what Upcoming Installments UI shows vs. actual Opportunity records
  - Effective Date change pattern documented for amount and schedule updates
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Recurring Donations Setup

This skill activates when a practitioner needs to configure, troubleshoot, or explain NPSP Enhanced Recurring Donations — covering ERD mode enablement, schedule object behavior, single-installment Opportunity generation, status automation thresholds, Effective Date change patterns, and the distinction between actual Opportunity records and the Upcoming Installments UI projection. It does NOT cover the legacy recurring donations model, one-time Opportunity entry, or custom payment processing outside native NPSP.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Verify ERD is enabled.** Since March 2021, Enhanced Recurring Donations (ERD) is the default for new NPSP installs. Orgs that were on NPSP before that date may still be running the legacy model. Navigate to NPSP Settings > Recurring Donations to confirm "Enhanced Recurring Donations" is selected. Behavior differs fundamentally between the two models — never assume ERD without verifying.
- **Understand the single-installment constraint.** ERD generates only ONE future pledged installment Opportunity at a time, not twelve like the legacy model. This is the most common source of confusion for practitioners migrating from legacy or comparing to other fundraising platforms.
- **Schedules are objects, not fields.** The ERD installment calendar is driven by `npe03__RecurringDonationSchedule__c` records, not fields on the Recurring Donation itself. Understanding this is required to interpret why the Upcoming Installments UI shows data that does not correspond 1:1 with existing Opportunity records.
- **The Upcoming Installments UI is a projection, not a record list.** It calculates and displays future installment dates from the active schedule — it does NOT list actual Opportunity records. Manual edits made directly to a future Opportunity are not reflected in this view.

---

## Core Concepts

### Enhanced Recurring Donations (ERD) vs. Legacy

NPSP shipped two distinct recurring donation models. The legacy model (pre-March 2021) created up to twelve future pledged installment Opportunity records at once, one for each period in the coming year. ERD, the replacement, generates only one future pledged installment Opportunity at a time. When that installment is closed (won or lost), the nightly batch creates the next one. This single-at-a-time approach reduces clutter, avoids premature revenue projection in reports, and simplifies schedule changes.

ERD became the default for all new NPSP installs in March 2021. Existing orgs must explicitly migrate via NPSP Settings. The migration is one-way; there is no rollback path to legacy after migration.

### npe03__RecurringDonationSchedule__c — The Schedule Object

In ERD, the installment calendar is stored as one or more `npe03__RecurringDonationSchedule__c` child records on the Recurring Donation. Each schedule record defines:

- **Installment Amount** — the amount to use for each installment Opportunity
- **Installment Frequency** — how many periods between installments (e.g., 1 = every period, 3 = every third)
- **Installment Period** — the time unit: Monthly, Quarterly, Yearly, Weekly, or Custom
- **Day of Month** — for monthly installments, which day of the month to use
- **Effective Date** — when this schedule becomes active (used for future-dated changes)
- **Status** — Active or Inactive

When an amount or schedule change is applied to a Recurring Donation, NPSP creates a new `npe03__RecurringDonationSchedule__c` record with the updated values and an Effective Date, rather than modifying the existing schedule. The old schedule record is then set to Inactive. This preserves a full audit trail of all schedule history.

### Upcoming Installments UI vs. Actual Opportunity Records

The Upcoming Installments related list on a Recurring Donation does NOT show a list of existing Opportunity records. It calculates and renders projected future installment dates directly from the active `npe03__RecurringDonationSchedule__c` record. This projection is recalculated on every page load.

Consequences of this distinction:
- A practitioner can manually edit the Close Date or Amount on a future pledged Opportunity, but that edit will NOT be visible in the Upcoming Installments UI — the UI will continue showing the schedule-driven projection.
- Deleting a future pledged Opportunity does not change the schedule; the nightly batch will recreate it.
- The only way to change what the Upcoming Installments UI shows is to modify the schedule record.

### Status Automation: Active, Lapsed, Closed

ERD automates Recurring Donation status transitions based on how many days have passed since the last payment:

- **Active** — the default status for a healthy recurring donation.
- **Lapsed** — automatically set when the number of days since the last successful installment exceeds the configured "Number of Days for Lapsed Status" threshold in NPSP Settings. Typically used to flag donors who missed a payment without formally stopping.
- **Closed** — automatically set when the days-since-last-payment threshold for Closed is exceeded. Closed records do not generate new installment Opportunities.

Both thresholds are configurable in NPSP Settings > Recurring Donations. The nightly batch recalculates status transitions along with Total Paid Amount and Number of Paid Installments rollup fields.

### Effective Date Pattern for Amount and Schedule Changes

When a donor requests a change to their recurring gift amount or frequency starting next month (not immediately), the correct mechanism is the Effective Date field on the schedule change. Practitioners set the new amount/frequency and choose a future Effective Date. NPSP creates a new schedule record effective on that date. The current installment Opportunity is not altered; the change takes effect on the next installment created after the Effective Date passes.

Using the Effective Date avoids retroactively modifying the amount on an already-created open Opportunity, which would misrepresent the donor's pledge.

---

## Common Patterns

### Pattern 1: Configuring a New Monthly Recurring Donation

**When to use:** A donor commits to a monthly recurring gift via web form, phone pledge, or in-person entry.

**How it works:**
1. Create a new Recurring Donation record. Set Donor, Amount, Date Established, and Recurring Period = Monthly.
2. NPSP automatically creates the first `npe03__RecurringDonationSchedule__c` record with the specified amount, frequency 1, period Monthly, and a Day of Month.
3. The nightly batch (or on-save trigger depending on NPSP configuration) creates the first pledged installment Opportunity with a Close Date matching the next scheduled date.
4. When that Opportunity is closed-won (payment processed), the batch creates the next single installment Opportunity.
5. The Upcoming Installments UI shows projected future dates based on the schedule — not a list of existing Opportunities.

**Why not pre-create all 12 Opportunities manually:** Pre-creating all twelve inflates the pipeline, interferes with NPSP's batch recalculation of rollups, and creates Opportunities that the schedule does not own — leading to duplicate Opportunities if the batch also fires.

### Pattern 2: Future-Dated Amount Change

**When to use:** A donor increases their gift starting next month. The current open installment Opportunity should remain at the old amount.

**How it works:**
1. Open the Recurring Donation. Navigate to the schedule change interface.
2. Enter the new Amount and set Effective Date to the first day of next month (or the donor's next scheduled payment date).
3. Save. NPSP deactivates the current `npe03__RecurringDonationSchedule__c` and creates a new one with the updated amount and the specified Effective Date.
4. The current open installment Opportunity is unchanged.
5. The next installment created after the Effective Date will use the new amount.

**Why not edit the Opportunity amount directly:** A direct edit to the open Opportunity amount changes only that one record, leaves the schedule unchanged, and will be overwritten by NPSP's batch recalculation on the next run.

### Pattern 3: Diagnosing Lapsed Status

**When to use:** A recurring donation shows Lapsed status but the donor claims they paid.

**How it works:**
1. Check the configured Lapsed threshold in NPSP Settings > Recurring Donations.
2. Review the installment Opportunities on the Recurring Donation — look for any that are Closed-Won with the correct Close Date.
3. Confirm the nightly batch has run since the payment was recorded (check Scheduled Jobs or the NPSP batch history).
4. If the batch has not run, trigger a manual recalculation via NPSP Settings > Recurring Donations > Recalculate.
5. If a payment Opportunity was incorrectly closed as Closed-Lost, reopen and close it as Closed-Won.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New NPSP install after March 2021 | ERD is already default; verify in NPSP Settings | ERD is the default; no action needed unless legacy was manually set |
| Org migrated from legacy before March 2021 | Run ERD migration wizard in NPSP Settings | One-way migration; verify rollup recalculation after migration |
| Donor wants amount change starting next period | Use Effective Date on schedule change | Preserves current open Opportunity at old amount; schedule change takes effect on next creation |
| Practitioner wants to see all future installment dates | Use Upcoming Installments UI | It shows schedule projections — not a SOQL query of existing Opportunities |
| Need to query future installment Opportunities via SOQL | Query `Opportunity WHERE npe03__Recurring_Donation__c = :rdId AND IsClosed = false` | Only one future pledged Opportunity exists at any time in ERD |
| Recurring Donation shows Lapsed unexpectedly | Check Lapsed threshold in NPSP Settings and batch run history | Batch recalculates status nightly; verify batch has run and threshold is configured appropriately |
| Recurring Donation should never auto-close | Set Closed threshold to a very large number (e.g., 9999) in NPSP Settings | Prevents automatic Closed transitions for donors on payment plans |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify ERD is enabled.** In NPSP Settings > Recurring Donations, confirm "Enhanced Recurring Donations" is active. If the org is still on legacy mode, determine whether a migration is appropriate before proceeding — do not mix ERD guidance with legacy behavior.
2. **Configure installment settings.** Set the default Installment Period (Monthly, Quarterly, etc.), default Day of Month, and any custom frequency rules in NPSP Settings > Recurring Donations. Confirm default allocation (General Donation Fund or a specific General Accounting Unit if NPSP GA is installed).
3. **Set status automation thresholds.** Define the number of days for Lapsed and Closed status transitions in NPSP Settings > Recurring Donations. Calibrate against the org's payment retry logic — set Lapsed threshold higher than the maximum payment retry window to avoid false lapsed status.
4. **Test single-installment creation.** Create a test Recurring Donation. Confirm exactly one pledged installment Opportunity is created, not multiple. Verify the `npe03__RecurringDonationSchedule__c` record is created with the correct amount, period, and frequency.
5. **Test the Upcoming Installments UI vs. Opportunity records.** Manually edit the amount on the open pledged Opportunity. Verify the Upcoming Installments UI still shows the schedule-driven projection (not the manual edit). This confirms the practitioner understands the distinction.
6. **Test a future-dated amount change.** Apply a schedule change with an Effective Date one month out. Confirm a new `npe03__RecurringDonationSchedule__c` is created, the old one is inactive, and the current open Opportunity is unaffected.
7. **Confirm nightly batch configuration.** Verify the NPSP recurring donations batch is scheduled to run nightly. Confirm it recalculates Total Paid Amount, Number of Paid Installments, and status transitions. Run a manual recalculation on a test record and verify rollup field values update correctly.

---

## Review Checklist

Run through these before marking work in this area complete:

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

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **ERD generates one future Opportunity, not twelve** — The legacy model created up to twelve future pledged Opportunities. ERD generates exactly one. Any automation, report, or integration that expects to find twelve future installment Opportunities will silently fail or produce wrong results in an ERD org. Always verify how many open pledged Opportunities exist before writing schedule-processing logic.
2. **Upcoming Installments UI is not backed by Opportunity records** — The list rendered in the Upcoming Installments related list is a live projection from `npe03__RecurringDonationSchedule__c` calculations. It is not a SOQL query of Opportunity records. Edits made directly to a future Opportunity's amount or close date are invisible in this UI. Practitioners often assume the UI confirms what records exist — it does not.
3. **Manual Opportunity edits are overwritten by the nightly batch** — If a practitioner edits the Amount or Close Date directly on a pledged installment Opportunity, NPSP's nightly recalculation batch may overwrite those values with the schedule-derived values on the next run. Use schedule changes with an Effective Date for any intended permanent changes.
4. **Status transitions are batch-driven, not real-time** — Lapsed and Closed status changes do not happen immediately when a payment is missed. They require the nightly batch to run. In orgs where the batch is misconfigured or paused, Recurring Donations will remain Active indefinitely regardless of payment history. Monitor the batch job health as part of recurring donations operations.
5. **Schedule history is preserved, not overwritten** — When a donor changes their recurring gift amount, NPSP creates a new `npe03__RecurringDonationSchedule__c` and deactivates the old one. It does NOT update the existing schedule record. Queries that filter only on Active schedule records will return the current schedule; queries without a status filter may return multiple records per Recurring Donation. Always filter by Status = Active when you need the current schedule.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured ERD settings | NPSP Settings > Recurring Donations configured with correct installment period, frequency, and status thresholds |
| npe03__RecurringDonationSchedule__c records | Schedule objects on each Recurring Donation driving installment generation |
| Single pledged installment Opportunity | One open pledged Opportunity per active Recurring Donation, reflecting current schedule |
| Status automation | Active/Lapsed/Closed transitions driven by days-unpaid thresholds, recalculated nightly |
| Rollup field values | Total Paid Amount and Number of Paid Installments updated by nightly batch |

---

## Related Skills

- `gift-entry-and-processing` — Recurring donations that come through Gift Entry use the staging-and-promotion pipeline; ERD installment Opportunities feed into Gift Entry differently than one-time gifts
- `npsp-data-model` — Understand the full object graph: Recurring Donation, npe03__RecurringDonationSchedule__c, and installment Opportunity relationships
- `batch-job-scheduling-and-monitoring` — The nightly NPSP recurring donations batch is critical infrastructure; use this skill to monitor, schedule, and troubleshoot it
