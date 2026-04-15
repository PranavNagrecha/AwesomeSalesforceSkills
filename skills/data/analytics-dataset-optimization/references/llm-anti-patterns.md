# LLM Anti-Patterns — Analytics Dataset Optimization

Common mistakes AI coding assistants make when generating or advising on Analytics Dataset Optimization.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating CRM Analytics Dataset "Partitioning" with Database Partition Indexes

**What the LLM generates:** "To improve query performance on your large CRM Analytics dataset, partition it by year using a partition key on the CloseDate field. CRM Analytics will then skip rows from partitions that don't match your filter, reducing scan time automatically."

**Why it happens:** LLMs trained on database and data warehouse content learn that partition pruning is a standard technique for large table performance. They apply the concept uniformly across storage systems without checking whether the target platform supports it. CRM Analytics datasets are flat binary stores — they have no index structures, partition metadata, or scan-pruning capabilities.

**Correct pattern:**

```
CRM Analytics has no native partition index. "Partitioning" in this context means physically
splitting data into separate named datasets — for example, Opportunity_2022, Opportunity_2023,
Opportunity_2024 — and routing dashboard queries to the appropriate named dataset.

Queries against a single year-specific dataset scan only that dataset's rows. There is no
automatic pruning when a single large dataset is filtered — every query scans all rows.
```

**Detection hint:** Any output that uses the phrase "partition key," "partition pruning," "CRM Analytics will skip rows," or "partition the dataset" without explaining that it means creating separate named datasets is likely applying database concepts incorrectly to CRM Analytics.

---

## Anti-Pattern 2: Recommending `SELECT *` or All-Field Digests for Convenience

**What the LLM generates:** "In your sfdcDigest node, include all fields from the Opportunity object so your dataset stays flexible for future dashboard needs. You can always filter fields at query time in SAQL."

**Why it happens:** LLMs frequently optimize for ease of setup and flexibility in generated configurations. They apply a "pull everything and filter later" pattern that works well in transactional databases where column access is selective. In CRM Analytics, the schema is materialized at ingest time and wider schemas cost more at every subsequent query — you cannot "filter fields" at query time to reclaim performance.

**Correct pattern:**

```json
// sfdcDigest should include ONLY fields actually referenced in dashboard SAQL,
// security predicates, and downstream join keys.

{
  "digest_Opportunity": {
    "action": "sfdcDigest",
    "parameters": {
      "object": "Opportunity",
      "fields": [
        { "name": "Id" },
        { "name": "OwnerId" },
        { "name": "Amount" },
        { "name": "CloseDate" },
        { "name": "StageName" }
      ]
    }
  }
}
// Produce a whitelist of actually-used fields before writing this configuration.
```

**Detection hint:** Any `sfdcDigest` configuration that omits the `fields` array entirely, or that recommends including fields "for future flexibility," is applying the wrong pattern. Every field should be justifiable by a specific SAQL reference or operational requirement.

---

## Anti-Pattern 3: Advising Runtime `date_to_epoch()` for Duration Calculations on Large Datasets

**What the LLM generates:** "To calculate days to close in SAQL, use `(date_to_epoch(CloseDate) - date_to_epoch(CreatedDate)) / 86400` as your average expression. This computes the duration dynamically for each record when the dashboard is loaded."

**Why it happens:** This advice is technically correct — the SAQL expression produces the right result. LLMs generate it because it is the direct translation of the business requirement into SAQL syntax and it requires no changes to the data pipeline. The problem is efficiency: the advice ignores that `date_to_epoch()` runs for every row on every user query, which becomes expensive at scale with concurrent users.

**Correct pattern:**

```
Pre-compute duration fields at ELT time using computeExpression in the dataflow or Recipe.

The auto-generated epoch companion fields (CloseDate_sec_epoch, CreatedDate_sec_epoch)
are available when the Date fields are declared with "type": "Date" in the schema node.

computeExpression node:
  DaysToClose = (CloseDate_sec_epoch - CreatedDate_sec_epoch) / 86400

SAQL then reads the pre-computed field:
  avg(DaysToClose) as avg_days_to_close

This computation runs once per dataflow run, not once per row per user query.
```

**Detection hint:** SAQL expressions that apply `date_to_epoch()` to fields in datasets with millions of rows and no corresponding pre-computation in the dataflow are candidates for this anti-pattern, especially when the SAQL expression appears inside an `avg()`, `sum()`, or other aggregation that will execute across the full row set.

---

## Anti-Pattern 4: Treating 60-Run Limit as a Calendar-Day Reset

**What the LLM generates:** "The CRM Analytics 60-run limit resets at midnight, so you can schedule up to 60 dataflows per day safely. If you need more, schedule some runs late at night and others early in the morning of the following day."

**Why it happens:** LLMs pattern-match "daily limit" to "resets at midnight" because this is how most daily rate limits work in web APIs, billing systems, and consumer platforms. The CRM Analytics run limit is a true rolling 24-hour window, which means behavior does not match calendar-day expectations.

**Correct pattern:**

```
The 60-run limit is a rolling 24-hour window, not a calendar-day reset.

If 60 runs fire between 08:00 and 10:00:
  - No more runs can start until 08:00 the following day (first slot clears)
  - Slots clear one by one as each run ages out of the 24-hour window
  - Scheduling some runs "late at night" and some "early morning" does not help
    if those windows are within 24 hours of each other

Correct capacity planning:
  - Count total runs per 24-hour window across ALL sources (custom + managed packages)
  - Leave at least 5–10 slots of headroom for ad-hoc runs and error retries
  - Consolidate single-object dataflows into multi-object dataflows to reduce slot consumption
```

**Detection hint:** Any advice that references "midnight reset," "daily quota resets at 00:00," or encourages splitting runs across morning and evening windows as a budget bypass is applying the wrong mental model to the rolling window limit.

---

## Anti-Pattern 5: Recommending Datetime Storage for All Date Fields Without Evaluating Use Case

**What the LLM generates:** "Store all date and datetime fields from Salesforce as Datetime type in the CRM Analytics schema node using the full ISO-8601 format `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'` to preserve maximum precision."

**Why it happens:** "Preserve maximum precision" is a reasonable general data engineering principle. LLMs apply it uniformly without evaluating whether dashboard use cases actually need time-of-day precision or whether the additional precision adds complexity to SAQL grouping expressions.

**Correct pattern:**

```
Choose date storage type based on actual dashboard use:

Date (yyyy-MM-dd) — Use for business date fields where time-of-day is not relevant:
  CloseDate, BirthDate, StartDate, ContractEndDate
  → Simpler SAQL grouping: group by (CloseDate, "year")
  → Works natively with dashboard date pickers
  → Lower storage cost than Datetime

Datetime (yyyy-MM-dd'T'HH:mm:ss.SSS'Z') — Use only when time-of-day is used
  in a dashboard filter or grouping:
  CreatedDate (for intraday activity tracking)
  LastModifiedDate (for freshness monitoring)

Epoch integer — Use when the field feeds duration math in SAQL or computeExpression:
  Pre-compute the epoch at ELT time; store as Numeric.
  Avoids runtime date_to_epoch() conversion.

Do not default to Datetime for all temporal fields. Evaluate each field by use case.
```

**Detection hint:** A schema node that declares every temporal field in the dataset as Datetime with the full millisecond-precision format string, without reviewing which fields are used for time-of-day filtering vs. date-level grouping, is applying this anti-pattern. Look for blanket declarations of all date-type fields with the same Datetime format string.

---

## Anti-Pattern 6: Claiming Recipe Runs Are Incremental by Default

**What the LLM generates:** "Schedule your Recipe to run every 2 hours. CRM Analytics Recipes will automatically process only new or modified records since the last run, so each run will be fast."

**Why it happens:** LLMs learn from documentation and forum content that CRM Analytics supports "incremental" data loading (which is true for Dataflows with Data Sync). They apply this property to Recipes without checking whether Recipes support the same behavior. They do not.

**Correct pattern:**

```
CRM Analytics Recipes do NOT support native incremental loads.

Every Recipe run reads its full input dataset from scratch and writes a full-replacement
output dataset. There is no built-in mechanism to process only changed rows.

Consequences of high-frequency Recipe scheduling:
  - Each run consumes one slot from the 60-run rolling window
  - Each run processes the full source dataset regardless of how little changed
  - Runtime is constant (proportional to full input size), not shorter on quiet periods

Incremental behavior in Recipes requires the snapshot-join workaround (see
analytics-data-architecture skill). For true incremental extraction, use a Dataflow
with Data Sync in incremental mode on the source Salesforce object.
```

**Detection hint:** Any recommendation to schedule a Recipe at high frequency (hourly or more) with the expectation that "only changed data is processed" is applying this anti-pattern. Verify whether the data source is a Dataflow with Data Sync (which supports incremental) or a Recipe (which does not).
