# Examples — Analytics Dataset Optimization

## Example 1: Field Pruning on an Over-Wide Opportunity Dataset

**Context:** A Revenue Operations team built a CRM Analytics dataset from the Opportunity object by including all 280 fields available on the object. The dataset refreshes nightly and feeds six dashboards. Dashboard queries are taking 8–12 seconds on simple aggregations like "total ARR by region."

**Problem:** The `sfdcDigest` node is pulling all 280 Opportunity fields from Salesforce on every run. The dataset write is proportionally wide. Every SAQL query — even those that reference only 8 fields — must address the full 280-column schema during execution. As row counts grew past 5 million records, query times became unacceptable.

**Solution:**

Step 1 — Export all dashboard definitions via the Analytics REST API to extract field references:

```bash
# Retrieve all dashboards in the org
GET /services/data/v63.0/wave/dashboards

# For each dashboard, retrieve its step queries
GET /services/data/v63.0/wave/dashboards/{dashboardId}
# Parse the "steps" array and extract SAQL strings from each step's "query" property
```

Step 2 — Produce the field whitelist. After parsing 6 dashboards, the referenced field list contained 34 unique field names. Adding `OwnerId` (used in the row-level security predicate) and `Id` (join key for a downstream augment) brought the total to 36 fields.

Step 3 — Update the `sfdcDigest` node in the dataflow JSON to include only the 36 whitelisted fields:

```json
{
  "digest_Opportunity": {
    "action": "sfdcDigest",
    "parameters": {
      "object": "Opportunity",
      "fields": [
        { "name": "Id" },
        { "name": "Name" },
        { "name": "OwnerId" },
        { "name": "AccountId" },
        { "name": "CloseDate" },
        { "name": "Amount" },
        { "name": "StageName" },
        { "name": "ForecastCategory" },
        { "name": "Region__c" },
        { "name": "ARR__c" }
      ]
    }
  }
}
```

(36 fields total; truncated here for brevity.)

Step 4 — Run the dataflow manually. Validate that the dataset has 36 columns (not 280) in Data Manager. Re-run a representative SAQL query from each dashboard and confirm no "field not found" errors.

**Why it works:** The Salesforce REST API call inside `sfdcDigest` reads only the declared fields for each row. A 36-field `sfdcDigest` reads roughly 87% less data from Salesforce than a 280-field one on the same object. The dataset write is proportionally smaller. Every SAQL query operates on a narrower schema, reducing memory allocation per query execution. In this case, average query time dropped from 10 seconds to under 2 seconds with no change to the SAQL expressions or dashboard structure.

---

## Example 2: Epoch Pre-Computation for Days-to-Close Metric

**Context:** A Sales Analytics dashboard shows "Average Days to Close" as a key metric on the pipeline view. The SAQL expression computes this at query time by calling `date_to_epoch()` on both `CloseDate` and `CreatedDate` and dividing the difference by 86400. The dataset has 8 million Opportunity rows.

**Problem:** The `date_to_epoch()` function is being evaluated for every row during every query execution. With 50+ concurrent dashboard users, the compute cost for this single expression is significant and degrades overall dashboard responsiveness.

**Solution:**

Add a `computeExpression` transformation in the dataflow immediately after the `sfdcDigest` node. Pre-calculate the duration as an integer stored in the dataset:

```json
{
  "compute_DaysToClose": {
    "action": "computeExpression",
    "parameters": {
      "mergeWithSource": true,
      "computedFields": [
        {
          "name": "DaysToClose",
          "label": "Days to Close",
          "saqlExpression": "case when CloseDate_sec_epoch > 0 and CreatedDate_sec_epoch > 0 then (CloseDate_sec_epoch - CreatedDate_sec_epoch) / 86400 else null end",
          "type": "Numeric",
          "precision": 18,
          "scale": 0
        }
      ],
      "source": "digest_Opportunity"
    }
  }
}
```

Note: `CloseDate_sec_epoch` and `CreatedDate_sec_epoch` are the epoch integer columns that CRM Analytics automatically generates when `CloseDate` and `CreatedDate` are declared as Date type in the schema node. They are available in `computeExpression` without additional declaration.

In the dashboard SAQL, replace the runtime calculation:

```saql
-- Before (runtime computation per query)
avg((date_to_epoch(CloseDate) - date_to_epoch(CreatedDate)) / 86400) as avg_days

-- After (read pre-computed field)
avg(DaysToClose) as avg_days
```

**Why it works:** The division runs once per row during the nightly dataflow run, not once per row per user query. The stored `DaysToClose` field is a plain numeric column. Reading and averaging a numeric column is the fastest possible SAQL operation — no function evaluation needed at query time. The query performance improvement scales with concurrent user count.

---

## Example 3: Year-Based Dataset Splitting for a Multi-Year Pipeline

**Context:** A CRM Analytics app tracks the full Opportunity history back to 2018. The combined dataset has 35 million rows. Most dashboards filter to the current fiscal year or the previous year. A few executive dashboards show 5-year trends.

**Problem:** Even when a dashboard is filtered to "FY2025 only," the SAQL query scans all 35 million rows because CRM Analytics has no partition pruning. Query times on the year-filtered dashboards are 15–20 seconds.

**Solution:**

Create separate Recipes for each year:

- `Opportunity_History_2018` through `Opportunity_History_2022` — full-replace, refreshed monthly (data is immutable)
- `Opportunity_History_2023` — full-replace, refreshed weekly
- `Opportunity_Current_2024_2025` — full-replace, refreshed nightly (current fiscal period)

Each Recipe applies a date filter before writing:

```
# Recipe filter node for Opportunity_History_2022
CloseDate >= "2022-01-01" AND CloseDate < "2023-01-01"
```

Year-specific dashboards target the appropriate named dataset. The FY2025 pipeline dashboard targets `Opportunity_Current_2024_2025` only.

For the 5-year trend executive dashboard, create a separate aggregation Recipe that reads from all year datasets, aggregates to month-level (sum of ARR, count of opportunities, average days to close), and writes a small `Opportunity_Trend_Monthly` summary dataset:

```
# Approximate row count: 12 months × 7 years × ~50 stage/region combinations = ~4,200 rows
```

The executive trend dashboard queries this 4,200-row summary, not the 35-million-row raw dataset.

**Why it works:** Queries against `Opportunity_Current_2024_2025` scan only 4–6 million rows (current year rows) instead of 35 million. Query times drop from 15–20 seconds to under 3 seconds. Prior-year datasets refresh rarely, freeing run-budget slots. The 5-year trend view operates on a tiny pre-aggregated dataset with negligible query cost.

---

## Anti-Pattern: Storing All Dates as Datetime When Date Precision Is Sufficient

**What practitioners do:** Accept all Salesforce Date and Datetime fields with a single dataflow schema node that declares every temporal field as Datetime with a full ISO-8601 format string (`yyyy-MM-dd'T'HH:mm:ss.SSS'Z'`). This is often copied from documentation examples or templates and applied uniformly without considering which fields actually need time-of-day precision.

**What goes wrong:** Datetime fields consume more storage bytes than Date fields. More importantly, grouping expressions in SAQL on Datetime fields are more complex — `group by (toDate(DateTimeField, "year"))` is required instead of `group by (DateField, "year")`. Dashboard date pickers that expect Date-type fields may behave unexpectedly when bound to Datetime columns. Practitioners then add SAQL wrapper functions to normalize the Datetime to a Date at query time, adding unnecessary runtime cost.

**Correct approach:** Declare Salesforce `Date` fields (like `CloseDate`, `BirthDate`, `StartDate`) with `"type": "Date"` and `"format": "yyyy-MM-dd"`. Reserve Datetime declarations for fields where time-of-day is genuinely used in dashboard filters or groupings (e.g., `CreatedDate` when tracking intraday activity, `LastModifiedDate` when building freshness monitors). Store duration fields as pre-computed epoch integers rather than as Datetime columns.
