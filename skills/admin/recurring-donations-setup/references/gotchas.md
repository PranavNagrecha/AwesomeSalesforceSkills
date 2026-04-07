# Gotchas — Recurring Donations Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: ERD Generates One Future Opportunity — Not Twelve

**What happens:** In Enhanced Recurring Donations, NPSP creates exactly one open pledged installment Opportunity per active Recurring Donation at any point in time. When that Opportunity is closed (won or lost), the nightly batch creates the next one. Reports, automations, and integrations that expect twelve forward-looking Opportunities (as the legacy model created) will silently return wrong results or fail validation in ERD orgs.

**When it occurs:** Any time an integration, Flow, Apex trigger, or report is built assuming multiple open future Opportunities exist per Recurring Donation. Also occurs when practitioners migrate from legacy to ERD and do not audit their existing automations.

**How to avoid:** Always verify ERD mode is active before writing installment-processing logic. Design automations to work with one open pledged Opportunity per Recurring Donation. For future installment projections beyond the next period, calculate from the active `npe03__RecurringDonationSchedule__c` record rather than querying Opportunities.

---

## Gotcha 2: Upcoming Installments UI Is a Schedule Projection, Not a Record List

**What happens:** The Upcoming Installments related list on a Recurring Donation displays projected future installment dates calculated from the active `npe03__RecurringDonationSchedule__c` record. It is NOT a list of existing Opportunity records. Any manual edit to a future pledged Opportunity's Close Date or Amount is completely invisible in this UI. The nightly batch may also overwrite those manual edits when it recalculates installments.

**When it occurs:** Whenever a practitioner manually edits a pledged installment Opportunity and then checks the Upcoming Installments UI expecting to see the change reflected. Also occurs when a developer queries Opportunities to "confirm what the UI shows" — the UI and the Opportunity records are not the same data source.

**How to avoid:** Treat the Upcoming Installments UI as a schedule-driven projection only. To change projected dates, modify the schedule record (e.g., change Day of Month or apply a future-dated schedule change). Communicate clearly to data entry staff that direct Opportunity edits do not affect the schedule projection.

---

## Gotcha 3: Nightly Batch Can Overwrite Manual Opportunity Edits

**What happens:** If a user manually edits a pledged installment Opportunity's Amount, Close Date, or Stage, NPSP's nightly recurring donations batch may recalculate those fields back to their schedule-driven values on the next run. The manual edit persists only until the batch fires, then disappears silently. This is especially disruptive in orgs where staff regularly adjust individual installment dates to accommodate donor requests.

**When it occurs:** Any time a manual edit is made directly to a pledged Opportunity that is still in an open state and linked to an active Recurring Donation with an active `npe03__RecurringDonationSchedule__c`. The batch treats the schedule as authoritative.

**How to avoid:** Use the Effective Date mechanism on the Recurring Donation for any intended persistent changes to amount or timing. For one-off date adjustments, document the override and warn staff the batch will recalculate. If per-installment overrides are a business requirement, disable the relevant batch recalculation or use a custom Process Builder/Flow that fires post-batch to restore the override — but treat this as a customization that must be maintained across NPSP upgrades.

---

## Gotcha 4: Schedule History Is Preserved as Multiple Records — Always Filter by Active Status

**What happens:** Every time a Recurring Donation's amount or frequency is changed, NPSP creates a new `npe03__RecurringDonationSchedule__c` record and deactivates the old one. A Recurring Donation with three schedule changes will have four schedule records (one Active, three Inactive). Queries or automations that do not filter by `Status__c = 'Active'` will retrieve all schedule records and produce incorrect installment calculations, duplicate amounts, or wrong frequency values.

**When it occurs:** Any SOQL query against `npe03__RecurringDonationSchedule__c` that lacks a `WHERE Status__c = 'Active'` filter. Common in custom reports, Apex triggers that read schedule details, and developer tools that "SELECT *" the schedule object.

**How to avoid:** Always filter `npe03__RecurringDonationSchedule__c` queries by `Status__c = 'Active'`. Be aware that an Active record with a future Effective Date may exist alongside the currently-applying Active record during a transition window; if Effective Date precision matters, also filter on `npe03__StartDate__c <= TODAY`.

---

## Gotcha 5: Status Transitions Are Batch-Driven, Not Real-Time

**What happens:** Recurring Donation status transitions to Lapsed or Closed are not instant. They happen only when the nightly NPSP recurring donations batch runs and evaluates each Recurring Donation against the configured days-since-last-payment thresholds. If a payment is missed, the Recurring Donation remains Active until the batch fires and the threshold is exceeded. Conversely, if a payment is recorded but the batch has not yet run, a genuinely paid-up Recurring Donation may continue to show Lapsed status.

**When it occurs:** Immediately after a missed payment or a recovered payment, before the nightly batch runs. Also occurs in orgs where the batch is paused, misconfigured, or hitting Apex governor limits that cause it to abort silently.

**How to avoid:** Monitor the NPSP recurring donations batch job health as part of standard org operations. After recording a recovered payment, manually trigger a recalculation via NPSP Settings > Recurring Donations > Recalculate if immediate status correction is needed. Alert the ops team if the batch fails so they can re-run it promptly.
