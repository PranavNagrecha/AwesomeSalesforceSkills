# LLM Anti-Patterns — Sales Reporting Data Model

Common mistakes AI coding assistants make when generating or advising on Sales Reporting Data Model.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Historical Trend Reporting for Multi-Year History

**What the LLM generates:**
"Use Historical Trend Reporting to build a report comparing this year's Q4 pipeline to Q4 two years ago. Enable HTR on Opportunity and add a date range filter for the past 24 months."

**Why it happens:** LLMs see "historical" in the feature name and assume it stores indefinite history. Training data contains Salesforce HTR documentation without always surfacing the retention cap prominently. The LLM generalizes "HTR shows history" to "HTR shows all history."

**Correct pattern:**
HTR retains approximately 3 months of trending data on Opportunity (up to 4 months for some objects). Data older than the retention window is automatically purged. For multi-year comparisons, use Reporting Snapshots to a custom object — run daily or weekly, accumulate records indefinitely, and filter by `Snapshot_Date__c` to reconstruct prior-year pipeline state.

```
HTR retention: ~90 days on Opportunity (not configurable)
For > 90 days of history: use Reporting Snapshots
```

**Detection hint:** Any recommendation to use HTR with date ranges exceeding 3 months, or phrases like "HTR stores unlimited history" or "HTR gives you historical data going back years."

---

## Anti-Pattern 2: Omitting the 2,000-Row Cap When Recommending Reporting Snapshots

**What the LLM generates:**
"Configure a Reporting Snapshot with your full open pipeline report as the source. This will write all your Opportunities into the snapshot target object each day."

Or: "Reporting Snapshots can capture your entire pipeline regardless of size — just set up the source report and schedule it."

**Why it happens:** The 2,000-row source report cap is a non-obvious platform constraint that is easy to miss in documentation. LLMs trained on general Salesforce content often describe the feature without surfacing this hard limit, especially in response to questions that imply large data volumes.

**Correct pattern:**
The Reporting Snapshot source report must return 2,000 rows or fewer at run time. Exceeding this cap causes silent truncation — the snapshot run appears successful but only the first 2,000 rows are written. For orgs with more than 2,000 open Opportunities, segment the source report into multiple views (by region, record type, or owner group) with separate Reporting Snapshot configurations each below the cap. Alternatively, use Apex scheduled logic or Data Cloud for large-volume point-in-time snapshots.

```
Reporting Snapshot source report row cap: 2,000 rows (hard limit)
Silent truncation on excess — run appears "Successful"
Workaround: segment into multiple source reports
```

**Detection hint:** Any Reporting Snapshot recommendation that does not mention the 2,000-row cap or that suggests the mechanism can handle "all" Opportunities without row-count qualification.

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

Or: "Use `SELECT Field, OldValue, NewValue, CreatedDate FROM OpportunityHistory` to build your trending report."

**Why it happens:** `OpportunityHistory` is a real sObject that tracks field changes, and LLMs trained on Salesforce development content know it exists. The LLM conflates "field change history exists" with "it can serve as a pipeline reporting mechanism," without understanding the critical differences.

**Correct pattern:**
`OpportunityHistory` records field-level changes (old value → new value) for tracked fields, but it is not suitable as a direct replacement for pipeline trend reporting for several reasons:
1. It records changes only when a field value changes — it does not record the field value on a specific date if no change occurred on that date. You cannot reconstruct "what was the amount on December 31st" unless a change was logged on or before that date.
2. It does not aggregate across deals — reconstructing pipeline-wide totals requires SOQL aggregation across all Opportunity records and their history, which is complex and hits governor limits for large orgs.
3. It is not surfaceable in Lightning reports via standard report types — you cannot build a Lightning dashboard chart from an `OpportunityHistory` query without custom Apex or CRM Analytics.

For point-in-time pipeline snapshots: use Reporting Snapshots. For field-level change auditing (who changed what and when): `OpportunityHistory` is correct. For trend visualization in dashboards: use HTR or Reporting Snapshots.

```
OpportunityHistory: change audit log (not a daily snapshot)
Cannot reconstruct "value on date X" unless a change was logged on/before that date
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
