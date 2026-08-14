# Gotchas — Sales Reporting Data Model

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Reporting Snapshot 2,000 Cap Is on Target-Object Inserts Per Run, Not on Source Report Rows

**What happens:** Salesforce documents the limit as an insert cap on the target object, not a row cap on the source report: "When a reporting snapshot runs, it can add up to 2000 new records to the target object. If there are more than 2000 new records, the additional records are not recorded, and the notification indicates that some rows failed." The target object therefore contains an incomplete dataset for that day — but the platform *does* say so, in the run notification and in Run History. The failure mode is an unread partial-error notification, not a silent success.

**When it occurs:** Any org where the open pipeline (scoped by the source report filters) grows past 2,000 Opportunity records. This often happens gradually — the snapshot works correctly when the org is small, and truncation begins months or years later when the pipeline grows beyond the cap and nobody is reading the notifications.

**How to avoid:** Route snapshot notifications to a monitored alias, and check Run History for partial errors rather than assuming a completed run is a complete run. After each Snapshot run, query the target object for records with `Snapshot_Date__c = TODAY` and compare the count to the expected pipeline count. If a run would insert more than 2,000 new records, segment the source report into multiple views (by region or record type) with separate Snapshot configurations writing to the same target object.

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

---

## Gotcha 6: Reporting Snapshot Run History Is the Only Place the Real Failure Reason Appears

**What happens:** A snapshot run can fail, half-fail, or abort before the report even finishes, and each state looks different in Run History. A blank **Total Row Number** means the run failed before the report completed (for example, the report was invalid or the running user is inactive). If only the field mappings failed, the snapshot still runs and Run History records a *partial* error. The Result column carries the exact platform string, which names the cause precisely:

```
Running user does not have permission to run reports.
Running user is inactive.
Running user does not have permission to access source report.
Running user does not have permission to edit target object.
Target object has been deleted or is inaccessible to running user.
One or more required fields on the target object are not mapped.
```

**When it occurs:** Most often after an unrelated change — a permission set removed from the service account, a report moved to a folder the running user cannot see, a required field added to the target object, or the target object made a detail in a master-detail relationship.

**How to avoid:** Read the Result string before theorising. Confirm the running user has **Run Reports** (or **Create and Customize Reports**), folder access to the source report, and **Create** on the target object; confirm the account is active. Creating, saving, and scheduling snapshots at all requires the **Manage Reporting Snapshots** user permission — an admin who can run the report may still be unable to configure the snapshot.

---

## Gotcha 7: Turning Historical Trending Off Deletes the Data, the Report Type, and Every Report Built on It

**What happens:** Historical Trending is a one-way door in the destructive direction. Turning it off for an object deletes all of that object's historical data and configuration settings, including the object's historical trending report type and any reports created with it. Turning it off for a single *field* deletes that field's historical data; if the field is then deleted, that history is gone for good even if trending is re-enabled later. Re-enabling collects forward from the moment of re-enablement — there is no restore.

**When it occurs:** During org cleanup ("nobody uses this trending object"), when freeing headroom against the 5,000,000-row-per-object trending limit, or when swapping one tracked field for another to stay inside the 8-field cap. It also bites teams who toggle trending in a sandbox refresh rehearsal and assume production behaves reversibly.

**How to avoid:** Treat the Historical Trending checkbox as an irreversible change with change-control approval, not a Setup toggle. Before disabling, export what is needed from the trending reports and inventory every report built on the object's historical trending report type — those reports are deleted with it, not orphaned. Because re-enabling only starts fresh collection, "we can just turn it back on" is never a valid rollback plan.
