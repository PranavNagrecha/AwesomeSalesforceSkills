# Examples — Sales Reporting Data Model

## Example 1: Activating Historical Trend Reporting and Building a Stage-Change Pipeline Report

**Context:** A SaaS company's sales operations team wants to see how deal stages and amounts shifted over the last 60 days for all open Opportunities in their "Enterprise" segment. The pipeline contains ~300 open deals. Leadership asks: "Which deals have been stuck in Proposal/Price Quote for more than 30 days?"

**Problem:** A standard Opportunities report only shows current stage and amount — there is no built-in way to see what the stage or amount was on a prior date using standard report types.

**Solution:**

Step 1 — Enable HTR in Setup:

```
Setup > Historical Trend Reporting
  Object: Opportunity
  Fields to track (select up to 8):
    ✓ Amount
    ✓ CloseDate
    ✓ StageName
    ✓ ForecastCategoryName
    ✓ OwnerId
    ✓ Probability
    [+ up to 2 custom fields, e.g. Deal_Score__c, Segment__c]
  Save
```

Step 2 — Build the trending report in Report Builder:

```
New Report > Report Type: "Opportunities with Historical Trending"

Filters:
  - Close Date: current FY
  - Segment__c (Historical) = Enterprise
  - Historical Date: Last 60 Days

Columns added:
  - Opportunity Name
  - Stage (Historical)       <- historical value at each tracked date
  - Stage (Current)          <- current value for comparison
  - Amount (Historical)
  - Amount (Current)
  - Historical Date

Group by: Opportunity Name, Historical Date
Sort by: Opportunity Name ASC, Historical Date ASC
```

Step 3 — Surface stalled deals:

Add a filter: `Stage (Historical) = "Proposal/Price Quote"` to narrow to deals that have been in that stage across multiple historical date rows.

**Why it works:** HTR captures a daily snapshot of the tracked fields internally. The "Opportunities with Historical Trending" report type exposes each day's value as a separate row, enabling stage-change analysis without any custom object or Apex code. The 60-day window fits within the ~90-day retention cap.

---

## Example 2: Designing a Reporting Snapshot for Multi-Year Pipeline History

**Context:** A financial services firm runs an annual "Year in Review" comparing current Q4 pipeline to Q4 in prior years. They have 1,200 open Opportunities at any given time in the scoped view. Historical Trend Reporting's 3-month cap means Q4 data from two years ago is long gone from HTR.

**Problem:** Without a Reporting Snapshot, the only way to retrieve prior-year pipeline state is via external BI tools or data exports. Standard Salesforce reports can only show current values.

**Solution:**

Step 1 — Create the target custom object `Pipeline_Snapshot__c`:

```
Object Label:    Pipeline Snapshot
Object Name:     Pipeline_Snapshot__c
Sharing:         Private

Fields:
  Opportunity_Name__c   Text(255)
  Stage__c              Text(100)
  Amount__c             Currency(16, 2)    <- Currency, not Text
  Close_Date__c         Date               <- Date, not Text
  Owner_Name__c         Text(255)
  Account_Name__c       Text(255)
  Forecast_Category__c  Text(100)
  Probability__c        Percent(3, 0)      <- Percent, not Text
  Snapshot_Date__c      Date               <- auto-populated by Salesforce with run date
```

Step 2 — Create the source Tabular report:

```
Report type: Opportunities
Filters:
  - Stage NOT IN (Closed Won, Closed Lost)
  - Close Date: Current FY and Next FY
Columns: Opportunity Name, Account Name, Stage, Amount, Close Date, Owner Full Name,
         Forecast Category, Probability
Confirm row count < 2,000 before activating snapshot.
```

Step 3 — Configure the Reporting Snapshot in Setup:

```
Setup > Reporting Snapshots > New

Name:          Daily Pipeline Archive
Source Report: [the tabular report from Step 2]
Target Object: Pipeline Snapshot (Pipeline_Snapshot__c)
Running User:  [dedicated service/integration user — not an employee]
Schedule:      Daily, 11:55 PM org time

Field Mapping:
  Opportunity Name     -> Opportunity_Name__c
  Account Name         -> Account_Name__c
  Stage                -> Stage__c
  Amount               -> Amount__c
  Close Date           -> Close_Date__c
  Owner Full Name      -> Owner_Name__c
  Forecast Category    -> Forecast_Category__c
  Probability (%)      -> Probability__c
```

Step 4 — Build the comparison report:

```
Report type: Pipeline Snapshots (auto-created for Pipeline_Snapshot__c)
Filters: Snapshot Date = [2024-12-31] OR Snapshot Date = [2023-12-31]
Columns: Snapshot Date, Account Name, Opportunity Name, Stage, Amount, Forecast Category
Group by: Snapshot Date
Summary: SUM of Amount
```

**Why it works:** The snapshot writes a static record for each open deal at the time of the run. The target object accumulates records over time — filter `Snapshot_Date__c` to any past date to reconstruct exactly what the pipeline looked like on that day.

---

## Anti-Pattern: Using a Text Field for Amount in a Reporting Snapshot Target Object

**What practitioners do:** When creating the target custom object for a Reporting Snapshot, they add `Amount__c` as a Text(255) field instead of a Currency field, reasoning that "the report just shows it as a number anyway."

**What goes wrong:** Text fields store monetary values as unformatted strings. Aggregations (SUM, AVG) in reports are unavailable for Text fields. Sorting by amount gives lexicographic order, not numeric order. Multi-currency orgs may store different currency symbols in the same column.

**Correct approach:** Define all monetary columns as Currency field type. Define date columns as Date type. Define percentage columns as Percent type. Only use Text for genuinely free-form text (Opportunity Name, Stage name, Owner name).
