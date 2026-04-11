# LLM Anti-Patterns — Analytics Dataset Management

Common mistakes AI coding assistants make when generating or advising on Analytics Dataset Management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Date Fields as Automatically Typed from the Source Object

**What the LLM generates:** "Your `sfdcDigest` node will pull `CloseDate` as a Date field because it is a Date field in Salesforce. You can use it directly in timeseries charts."

**Why it happens:** LLMs conflate the Salesforce object field type with the CRM Analytics dataset column type. They assume type fidelity is preserved end-to-end. Training data about dataflows often omits the schema transformation step because it is easy to overlook in documentation examples.

**Correct pattern:**

```json
{
  "schema_Opportunities": {
    "action": "schema",
    "parameters": {
      "fields": [
        {
          "name": "CloseDate",
          "newName": "CloseDate",
          "type": "Date",
          "format": "yyyy-MM-dd",
          "fiscalMonthOffset": 0
        }
      ],
      "source": "digest_Opportunities"
    }
  }
}
```

A `schema` transformation node with an explicit `type: "Date"` and `format` string is required immediately after the `sfdcDigest` node. Without it, the column is stored as Text regardless of the source field type.

**Detection hint:** Look for any SAQL query or dashboard config that uses `timeseries` or a date range filter on a field that lacks a corresponding `schema` node in the dataflow JSON. That is a guaranteed failure scenario.

---

## Anti-Pattern 2: Advising Hourly Refresh for All Datasets Without Quota Analysis

**What the LLM generates:** "To keep your CRM Analytics data fresh, schedule each dataflow to run every hour. This ensures your dashboards reflect near-real-time data."

**Why it happens:** LLMs default to "more frequent = better" for data freshness without accounting for platform quotas. The 60-run/24-hour limit is a less-visible platform constraint that does not appear in many introductory CRM Analytics guides.

**Correct pattern:**

```
Before scheduling any dataflow, calculate current quota consumption:
  (number of dataflows) × (runs per day each) + managed package flows = total runs/day
  Must be < 60

Hourly refresh: 1 flow × 24 = 24 quota slots consumed per flow per day
Nightly refresh: 1 flow × 1 = 1 quota slot per flow per day

Reserve high-frequency schedules for dashboards that support intraday decisions.
Most operational dashboards are actioned once a day — nightly refresh is sufficient.
```

**Detection hint:** Any recommendation to schedule more than 2–3 dataflows at sub-daily frequency in an org that already has managed-package analytics products is a red flag. Ask: "How many total dataflow runs per day does this org already have?"

---

## Anti-Pattern 3: Recommending a Separate Dataflow for Every Source Object

**What the LLM generates:** "Create one dataflow for Opportunity, a second for Account, a third for Contact, and a fourth for Case. Schedule each independently so you can refresh them at different rates."

**Why it happens:** A per-object decomposition looks modular and clean. LLMs favor patterns that feel architecturally tidy. The quota cost of multiple single-object flows is not surfaced in most training material.

**Correct pattern:**

```
For related objects that will be joined in a dataset, use a single combined dataflow:
  - sfdcDigest node per object
  - augment or join node to merge them
  - single schema node for date fields
  - single register node

Cost: 1 quota slot per run instead of N slots for N objects.
Monitoring: one job to watch instead of N jobs.
```

**Detection hint:** If a proposed design has more than 3–4 dataflows all targeting the same domain (e.g., all sales pipeline objects), and if the org already has managed-package flows, flag the quota arithmetic before accepting the design.

---

## Anti-Pattern 4: Ignoring the 500M Row Ceiling for Append-Mode Datasets

**What the LLM generates:** "Use append mode so that you keep full historical data in the dataset. New records will be added on each run and you will always have a complete history for trend analysis."

**Why it happens:** Append mode sounds like an obviously correct choice for historical trend analysis. LLMs do not commonly model the hard row ceiling or its org-wide impact when breached.

**Correct pattern:**

```
Append mode is appropriate ONLY when:
  1. A row-count projection over 12 months stays well below 100M rows for the specific dataset, AND
  2. The org has sufficient headroom in the 500M org-wide ceiling for all datasets combined.

For high-cardinality objects (Activities, Events, Email interactions):
  - Use full-replace with a date-range filter node
  - Restrict to rolling 12-month or 13-month window
  - Document the trim window in the dataflow and in the dataset description

Example filter node (keep last 13 months of Activity data):
  "filter": { "field": "ActivityDate", "operator": ">=", "value": "last_13_months" }
```

**Detection hint:** Any recommendation of append mode for objects with more than ~50,000 records per month should trigger a row-count projection calculation before the recommendation is accepted.

---

## Anti-Pattern 5: Claiming That toDate() in SAQL Can Fix a Text-Typed Date Column at Query Time

**What the LLM generates:** "Even if CloseDate is stored as Text in the dataset, you can wrap it in `toDate(CloseDate, 'yyyy-MM-dd')` in your SAQL query and it will work as a date for filtering and timeseries."

**Why it happens:** SAQL does have a `toDate()` function. LLMs sometimes generalize from other SQL dialects where cast-at-query-time is a valid pattern. The CRM Analytics query engine does not support runtime casting of Text columns to Date for `timeseries` or range filter operations.

**Correct pattern:**

```
toDate() in SAQL works ONLY within computeExpression transformations in the dataflow,
not in ad-hoc SAQL queries against a dataset that has already stored the column as Text.

Fix for an existing dataset with a Text-typed date:
  1. Add a computeExpression node in the dataflow:
     "newCloseDate": "toDate(CloseDate, 'yyyy-MM-dd')"
  2. Update downstream references to use newCloseDate instead of CloseDate
  3. Re-run the dataflow
  4. Confirm the column type shows Date in Data Manager

There is no query-time workaround. The fix must happen in the dataflow.
```

**Detection hint:** Any SAQL snippet that uses `toDate()` directly in a `q = load` or `q = filter` expression (rather than inside a dataflow `computeExpression`) is applying the function in the wrong context and will not produce correct date filtering or timeseries results.
