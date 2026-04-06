# Gotchas — Sales Reporting Data Model

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Reporting Snapshot Source Report Row Cap Is Silently Enforced at 2,000 Rows

**What happens:** When a Reporting Snapshot source report returns more than 2,000 rows at run time, Salesforce writes only the first 2,000 rows to the target object and does not raise a visible error in the standard UI. The snapshot run is marked as "Successful" in the run history log, but the target object contains an incomplete dataset for that day.

**When it occurs:** Any org where the open pipeline (scoped by the source report filters) grows past 2,000 Opportunity records. This often happens gradually — the snapshot starts working correctly when the org is small, and the silent truncation begins months or years later when the pipeline grows beyond the cap.

**How to avoid:** After each Snapshot run, query the target object for records with `Snapshot_Date__c = TODAY` and compare the count to the expected pipeline count. Build a monitoring report or scheduled alert if today's snapshot count is less than a known minimum threshold. If the source report exceeds 2,000 rows, segment it into multiple source reports (by region or record type) with separate Snapshot configurations writing to the same target object.

---

## Gotcha 2: HTR Field Cap of 8 Is Shared Across Standard and Custom Fields on the Same Object

**What happens:** Salesforce allows tracking of up to 8 fields per object in Historical Trend Reporting. For Opportunity, 5 standard fields are available by default (Amount, CloseDate, ForecastCategoryName, StageName, OwnerId). This leaves only 3 slots for custom fields. Practitioners who want to track a 4th, 5th, or 6th custom field discover that the Setup UI will not allow additional selections once 8 total are chosen.

**When it occurs:** Sales Cloud orgs with complex custom deal qualification fields (Deal_Score__c, Segment__c, Territory__c, Weighted_Amount__c, Competitor__c) frequently hit this limit when asked to add a new custom field to HTR-powered pipeline trend reports.

**How to avoid:** Audit and prioritize HTR field selections carefully at activation time. Remove a lower-priority field to free a slot before adding a new one — the change takes effect going forward but does not recover historical data for the removed field. Fields that are formula fields cannot be tracked at all in HTR — track underlying component fields and compute at report time. Use Reporting Snapshots as a supplement if more than 8 fields of history are required.

---

## Gotcha 3: Custom Report Type "Without" Join Logic Applies Only to the Immediately Adjacent Relationship

**What happens:** In a CRT with an Account > Opportunity > Opportunity Line Item chain, if a practitioner sets the Opportunity-to-OLI relationship as "A records may or may not have related B records" (outer join), the report returns Opportunities with or without line items — not Accounts with no Opportunities. Practitioners who expected the report to show Accounts with no Opportunities set the wrong join step.

**When it occurs:** Any time a practitioner builds a multi-level CRT for exception reporting and reads the join configuration wizard too quickly. The wizard labels each step by the child object name, and it is easy to configure the wrong step's join type.

**How to avoid:** Work from the exception requirement backward: "I want Accounts WITHOUT Opportunities" means the outer join must be at the Account → Opportunity step. Test the CRT by creating a known Account with no Opportunities and confirming it appears in the resulting report. Also confirm that Accounts with Opportunities appear or are excluded as intended.

---

## Gotcha 4: HTR Activation Does Not Capture Retroactive History

**What happens:** After HTR is enabled, the first trending data available is from the day of activation onward. A practitioner who enables HTR in January and then tries to build a trend report in April asking "show me how this deal's stage changed since October of last year" will find that only January-through-April data exists. October-through-December data is simply not there.

**When it occurs:** Post-implementation reviews, end-of-quarter retrospectives, or any use case where the stakeholder needs historical data from before HTR was activated.

**How to avoid:** Enable HTR as early as possible in the org's lifecycle — ideally at go-live or during the initial Sales Cloud implementation. If HTR was not enabled historically and multi-month trending is immediately needed, use a Reporting Snapshot going forward combined with a one-time data load of current Opportunity history (from the `OpportunityHistory` sObject via SOQL) into the target custom object to bootstrap the archive.

---

## Gotcha 5: Reporting Snapshot Run Failure Due to Inactive Source Report Owner or Running User

**What happens:** Reporting Snapshots run as the user designated as the "Running User." If that user is deactivated, the snapshot fails at the next scheduled run time. The failure is logged in the Reporting Snapshot run history, but no automated notification is sent to admins by default. All snapshot records stop being written, and pipeline history has a silent gap for every day the snapshot was failing.

**When it occurs:** When the user who was set as the Reporting Snapshot's Running User leaves the company or has their account deactivated. In multi-year snapshot configurations, the original Running User may have left years after the snapshot was set up.

**How to avoid:** Designate a dedicated integration user or non-person admin service account as the Running User for all Reporting Snapshots. This user should not be associated with a specific employee. Monitor the Reporting Snapshot run history — build a report or monitoring flow that alerts the admin team if a run fails or produces zero records for Snapshot_Date__c = TODAY.
