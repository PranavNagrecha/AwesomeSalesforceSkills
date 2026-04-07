# Gotchas — Billing Schedule Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Data Pipelines Disabled Causes Silent Billing Schedule Failure

**What happens:** When an Order is activated, Salesforce Billing is supposed to create `blng__BillingSchedule__c` records for each OrderProduct. If Data Pipelines is not enabled in the org, this creation silently fails — no error is thrown, no process log is written, and the Order activation itself succeeds. The admin sees a cleanly activated Order with no billing schedules and no indication of why.

**When it occurs:** Any time Salesforce Billing (blng__ namespace) is installed but Data Pipelines has not been explicitly enabled in Setup. This is common in sandbox refreshes where Data Pipelines must be re-enabled manually — it does not carry over from production automatically. Also common in new Billing installations where the admin follows the CPQ setup guide but does not realize Billing has an additional platform dependency.

**How to avoid:** Before debugging any "missing billing schedule" issue, navigate to Setup > Data Pipelines and confirm it is enabled. Make Data Pipelines enablement a required step in every Billing go-live checklist and every sandbox refresh runbook. Do not proceed to Billing Rule configuration until Data Pipelines is confirmed.

---

## Gotcha 2: Invoice Run Target Date Excludes Same-Day Items When Set to Yesterday

**What happens:** An admin runs a monthly Invoice Run and sets `blng__TargetDate__c` to yesterday's date, expecting to capture all items "up to and including the current period." Items scheduled for today are excluded from the run. The Invoice Run completes with fewer invoices than expected, and the admin re-runs it thinking there is a system error.

**When it occurs:** The `blng__TargetDate__c` field is a hard cutoff: only `blng__BillingSchedule__c` items with a next billing date on or before the target date are processed. Setting target date to yesterday (e.g., April 6) excludes any item scheduled for today (April 7). This trips up admins who interpret "target date" as a "through date" inclusive of the current day.

**How to avoid:** Set `blng__TargetDate__c` to today's date (or the desired cutoff date inclusive of the items you want). Scheduled Invoice Runs should use a formula or Process Builder/Flow to dynamically set target date to `TODAY()`. For manual runs, always confirm the target date is not set to the prior day.

---

## Gotcha 3: Manually Created blng__BillingSchedule__c Records Are Skipped by Invoice Runs

**What happens:** A team uses Data Loader or a Flow to create `blng__BillingSchedule__c` records directly, either to backfill historical data or to create schedules for Orders that were activated before Billing was configured. Invoice Runs execute without errors but never generate invoices for these manually created records. The records appear valid in the UI.

**When it occurs:** The Invoice Run engine internally validates that billing schedule records were created through the Order activation trigger chain — it checks internal metadata set by the managed package during that process. Records created outside this trigger (via SOQL insert, Data Loader, Flow, or Apex DML on the object directly) do not carry the internal flag and are silently excluded from Invoice Run processing.

**How to avoid:** Do not create `blng__BillingSchedule__c` records directly. If backfilling is needed, the supported path is to reactivate the Order (set it back to Draft and re-activate) to regenerate schedules through the proper trigger chain. For historical data loading, engage Salesforce Professional Services or use Billing's native data migration tools if available for the org's version.

---

## Gotcha 4: Billing Policy on Account Is Not Inherited from Parent Account

**What happens:** In a hierarchical account structure, an admin sets `blng__BillingPolicy__c` on the parent Account and assumes child Accounts inherit the policy. Invoice Runs against Orders on child Accounts produce zero invoices because the child Account records have no Billing Policy set.

**When it occurs:** Salesforce Billing does not implement any Account hierarchy inheritance for Billing Policy. Each Account must have its own `blng__BillingPolicy__c` set explicitly. This is counterintuitive because some other Salesforce Billing fields do respect account hierarchy, and CPQ handles certain pricing lookups hierarchically.

**How to avoid:** Set `blng__BillingPolicy__c` explicitly on every Account record that will have Orders invoiced through Billing. For large account sets, use a Flow or batch Apex to auto-populate child Accounts from their parent at record creation. Add Account Billing Policy population to the account creation process and any account migration runbook.

---

## Gotcha 5: Evergreen Billing Schedules Do Not Self-Cancel on Contract End Date

**What happens:** An Evergreen billing schedule is set up for a month-to-month customer. The customer later signs a fixed-term addendum with an end date. The admin updates the Contract end date and Order end date but the Evergreen `blng__BillingSchedule__c` continues generating new period items past the intended end date indefinitely.

**When it occurs:** Evergreen schedules are designed to have no end date by platform definition — the `blng__BillingType__c = Evergreen` type does not read Order end dates or Contract end dates to self-terminate. Updating related record dates does not cascade to stop the Evergreen schedule. This is expected behavior but surprises admins who assume end dates propagate.

**How to avoid:** To stop an Evergreen schedule, the admin must explicitly cancel the `blng__BillingSchedule__c` record or terminate the Order. Build a process (Flow or Apex) that watches for Order end date population on Evergreen Orders and automatically cancels the corresponding schedule. Document this in the renewal/termination runbook for the business team.
