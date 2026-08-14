# LLM Anti-Patterns — Sales Reporting Data Model

Common mistakes AI coding assistants make when generating or advising on Sales Reporting Data Model.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Historical Trend Reporting for Multi-Year History

**What the LLM generates:**
"Use Historical Trend Reporting to build a report comparing this year's Q4 pipeline to Q4 two years ago. Enable HTR on Opportunity and add a date range filter for the past 24 months."

**Why it happens:** LLMs see "historical" in the feature name and assume it stores indefinite history. Training data contains Salesforce HTR documentation without always surfacing the retention cap prominently. The LLM generalizes "HTR shows history" to "HTR shows all history."

**Correct pattern:**
Salesforce retains historical data for the previous 3 months plus the current month. That window is the same for every trending-enabled object — there is no longer retention for Cases or Forecasting Items. The one documented extension is Historical Trending in Pipeline Inspection, which stores up to 12 months of Opportunity history. Data older than the window is automatically purged. For multi-year comparisons, use Reporting Snapshots to a custom object — run daily or weekly, accumulate records indefinitely, and filter by `Snapshot_Date__c` to reconstruct prior-year pipeline state.

```
HTR retention: previous 3 months + current month (not configurable)
Exception: Historical Trending in Pipeline Inspection -> 12 months of Opportunity history
For longer history: use Reporting Snapshots
```

**Detection hint:** Any recommendation to use HTR with date ranges exceeding 3 months, or phrases like "HTR stores unlimited history" or "HTR gives you historical data going back years."

---

## Anti-Pattern 2: Omitting the 2,000-Record Per-Run Cap When Recommending Reporting Snapshots

**What the LLM generates:**
"Configure a Reporting Snapshot with your full open pipeline report as the source. This will write all your Opportunities into the snapshot target object each day."

Or: "Reporting Snapshots can capture your entire pipeline regardless of size — just set up the source report and schedule it."

**Why it happens:** The 2,000-record per-run cap is a non-obvious platform constraint that is easy to miss in documentation, and secondary sources routinely restate it as a source-report row cap. LLMs trained on general Salesforce content often describe the feature without surfacing the limit at all, especially in response to questions that imply large data volumes.

**Correct pattern:**
The cap is on the target side and is stated as such: a snapshot run can add up to 2,000 *new records to the target object*, and if there are more than 2,000 new records the additional records are not recorded and the notification indicates that some rows failed. So the correct framing is a per-run insert cap with a partial-error notification — not a source-report row cap with a silent success. For orgs with more than 2,000 open Opportunities, segment the source report into multiple views (by region, record type, or owner group) with separate Reporting Snapshot configurations each below the cap. Alternatively, use Apex scheduled logic or Data Cloud for large-volume point-in-time snapshots.

```
Cap dimension: 2,000 NEW RECORDS inserted into the target object per run
Surplus rows are not recorded; notification + Run History show a partial error
Workaround: segment into multiple source reports
```

**Detection hint:** Any Reporting Snapshot recommendation that does not mention the 2,000-record per-run cap, that attaches the 2,000 to the source report instead of the target object, or that suggests the mechanism can handle "all" Opportunities without row-count qualification. Also flag "the run still shows as Successful" — the documented behavior is a partial-failure notification.

---

## Anti-Pattern 3: Telling Users to Track More Than 8 Fields in HTR via Formula Fields

**What the LLM generates:**
"To track more fields in Historical Trend Reporting, create formula fields on Opportunity that roll up or combine other fields, and add the formula fields to your HTR tracked fields list."

**Why it happens:** Formula fields are often used elsewhere to expose derived values for reporting. The LLM generalizes this pattern to HTR without knowing that formula fields are explicitly excluded from HTR tracking.

**Correct pattern:**
Formula fields are not eligible for Historical Trend Reporting. Only standard and custom non-formula fields can be added to the HTR tracked fields list. The 8-field cap applies to non-formula fields only. To track a computed value over time (e.g., weighted pipeline = Amount × Probability), track the underlying component fields (Amount, Probability) separately in HTR and apply the calculation at report time using a report formula column. If more than 8 fields of history are required, supplement HTR with a Reporting Snapshot that writes all desired fields to a custom object.

```
HTR eligible fields: standard and custom non-formula fields only
Formula fields: NOT trackable in HTR
Workaround: track components, compute at report time; or use Reporting Snapshots
```

**Detection hint:** "Add a formula field to your HTR tracked fields" or "create a rollup formula to work around the HTR field limit."

---

## Anti-Pattern 4: Advising That CRT "Without" Join Makes All Parent Records Appear Regardless of Child Filters

**What the LLM generates:**
"Set the Opportunity-to-Opportunity Line Item relationship to 'A records may or may not have related B records' in your Custom Report Type. This will show all Accounts even if they have no Opportunities."

Or: "The 'without' option in a Custom Report Type means the parent records always appear regardless of whether children exist."

**Why it happens:** The LLM understands the general concept of outer joins but does not correctly map it to the CRT wizard's per-step configuration. It conflates setting "without" at one relationship step with enabling outer-join behavior across the entire report chain.

**Correct pattern:**
The "without" (outer join) setting in a CRT applies only at the specific relationship step where it is configured. In a chain of Account → Opportunity → Opportunity Line Item:
- "Without" at Account → Opportunity: shows Accounts with or without Opportunities (gap report for cold accounts).
- "Without" at Opportunity → OLI: shows Opportunities with or without Line Items (gap report for deals missing products).

These produce fundamentally different report scopes. Always verify which step is being configured and test with known data (a parent record with no children) to confirm the correct records appear.

```
CRT "without" join applies at the specific step configured — not globally
Always test with a known account/opportunity with no children
```

**Detection hint:** Any CRT guidance that implies "without" at one step cascades to all upstream parents, or that does not specify which step's join type is being set.

---

## Anti-Pattern 5: Recommending SOQL on `OpportunityHistory` as a Replacement for HTR or Reporting Snapshots

**What the LLM generates:**
"Instead of setting up Reporting Snapshots, you can query `OpportunityHistory` in SOQL to get pipeline history. This gives you all field changes going back to the Opportunity's creation date."

Or: "Use `SELECT Field, OldValue, NewValue, CreatedDate FROM OpportunityHistory` to build your trending report." (This query is invalid as written — `OpportunityHistory` has no `Field`/`OldValue`/`NewValue` columns; that schema belongs to `OpportunityFieldHistory`.)

**Why it happens:** two related sObjects get conflated. `OpportunityHistory` is the **stage/pipeline-history** object — it stores a row when a forecast field changes, with columns `StageName`, `Amount`, `Probability`, `CloseDate`, `ForecastCategory`, `ExpectedRevenue` (no `Field`/`OldValue`/`NewValue`). `OpportunityFieldHistory` is the **field-history** object, with `Field`/`OldValue`/`NewValue` rows for tracked fields. LLMs blur the two, and separately conflate "change history exists" with "it can serve as a pipeline reporting mechanism."

**Correct pattern:**
Both objects are *change logs*, not daily snapshots, so neither is a direct replacement for pipeline trend reporting:
1. They record a row only when a value changes — not the value on a date with no change. You cannot reconstruct "what was the amount on December 31st" unless a change was logged on or before that date.
2. They do not aggregate across deals — reconstructing pipeline-wide totals requires SOQL aggregation across all Opportunity records and their history, which is complex and hits governor limits for large orgs.
3. They are not surfaceable in Lightning reports via standard report types — you cannot build a Lightning dashboard chart from such a query without custom Apex or CRM Analytics.

Choose by intent: point-in-time pipeline snapshots → Reporting Snapshots; forecast/stage change tracking → `OpportunityHistory`; who-changed-which-field auditing → `OpportunityFieldHistory`; trend visualization in dashboards → HTR or Reporting Snapshots.

```
OpportunityHistory       = stage/pipeline change log (StageName/Amount/CloseDate/...)
OpportunityFieldHistory  = field change log (Field/OldValue/NewValue)
Neither is a daily snapshot: can't reconstruct "value on date X" without a logged change
HTR and Reporting Snapshots are the correct tools for trend analysis
```

**Detection hint:** "Use OpportunityHistory to build a pipeline trend report" or "query OpportunityHistory to see deal values on a specific past date."

---

## Anti-Pattern 6: Claiming HTR Data Is Available Via API or SOQL

**What the LLM generates:**
"Query the OpportunityHistory or OpportunityTrending object in SOQL to retrieve the data captured by Historical Trend Reporting."

Or: "HTR data is stored in a custom object you can query — just look for the `__hd` suffix table in your org."

**Why it happens:** LLMs sometimes hallucinate the existence of an sObject for HTR data, or confuse HTR with Reporting Snapshots (which do write to a queryable custom object). HTR data is stored in an internal platform store that is not queryable via SOQL or Bulk API.

**Correct pattern:**
Historical Trend Reporting data is NOT accessible via SOQL, Bulk API, or REST API. It is only surfaceable through the Lightning Report Builder using the "Opportunities with Historical Trending" report type (or equivalent HTR-enabled report types for other objects). There is no `__hd` sObject, no `OpportunityTrending` object, and no API endpoint for HTR data. If programmatic access to historical pipeline values is required, use Reporting Snapshots — those write to a standard custom object that is fully queryable via SOQL and accessible via all standard Salesforce APIs.

```
HTR data: report-only — NOT queryable via SOQL or any API
Reporting Snapshots: write to custom object — fully SOQL queryable
```

**Detection hint:** "Query HTR data via SOQL," "OpportunityTrending object," "the HTR table has an API name ending in __hd," or any instruction to use a Data Loader export on HTR data.

---

## Anti-Pattern 7: Debugging an Invisible Custom Report Type Through Object Permissions and Folder Sharing

**What the LLM generates:**
Asked "why can't my users see the custom report type I just built?", the model works through object-level Read access, field-level security, profile permissions, and report folder sharing — and often suggests re-sharing the folder or granting View All Data.

**Why it happens:** The model pattern-matches "users can't see X" to the record-and-folder visibility model it has seen most often. Report types are not shared by folder and are not FLS-gated, so none of that advice applies. Deployment Status is a single field on the report type itself, and it rarely appears in the training text next to visibility troubleshooting.

**Correct pattern:**
Check Setup > Report Types > [type] > **Deployment Status** first. While the value is **In Development**, "the report type and its reports are hidden from all users except those with the Manage Custom Report Types permission" — in most orgs that means only System Administrators, which is exactly why the author can see it and nobody else can. Set it to **Deployed** to release it. Then check the cascade: a custom report type's deployment status changes from Deployed back to In Development if its primary object is a custom or external object whose own deployment status changes the same way, so a report type that worked yesterday can disappear because someone flipped the primary object in Setup.

```
Report type invisible to users -> Deployment Status = In Development (not FLS, not folder sharing)
Only "Manage Custom Report Types" can see In Development types
Cascade: primary custom/external object -> In Development flips the report type back too
```

**Detection hint:** Any report-type visibility answer that names object permissions, field-level security, or folder sharing without first naming Deployment Status, or that calls the non-deployed value "Draft" (the actual value is "In Development").
