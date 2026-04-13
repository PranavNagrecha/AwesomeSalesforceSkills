# LLM Anti-Patterns — Analytics Data Architecture

Common mistakes AI coding assistants make when generating or advising on CRM Analytics data architecture. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming Recipes Support Native Incremental Loads

**What the LLM generates:** An architecture recommendation stating that a CRM Analytics Recipe will "automatically detect and process only changed records since the last run" or that Recipes support "incremental mode" via a setting in the Recipe configuration UI. The LLM may also describe a Recipe node or toggle called "Incremental Load" or "Delta Sync."

**Why it happens:** Training data conflates CRM Analytics Recipes with traditional ETL tools (Informatica, Talend, DataStage, dbt) that do support native CDC or watermark-based incremental loads. The LLM also conflates Recipes with Data Sync, which does support incremental mode — but Data Sync is a separate layer from Recipes.

**Correct pattern:**

```
Recipes have NO native incremental mode. Every Recipe run reads the complete
input dataset from scratch.

To simulate incremental behavior in a Recipe:
1. Maintain a prior-run snapshot dataset (e.g., "opp_snapshot").
2. Each run: join current source data against snapshot on record ID.
3. Compare LastModifiedDate from source against snapshot_date from snapshot.
4. Union changed rows (from source) with unchanged rows (from snapshot).
5. Overwrite the snapshot dataset with the merged result.

For true native incremental extraction from Salesforce objects, use a
dataflow with Data Sync configured in incremental mode (SystemModstamp-based).
```

**Detection hint:** Flag any response containing "Recipe incremental mode", "Recipe delta load", "Recipe will only process changed records", or "incremental toggle in Recipe."

---

## Anti-Pattern 2: Configuring Snowflake / BigQuery / Redshift Connections in Dataflow JSON

**What the LLM generates:** A dataflow JSON snippet that includes a node with a type like `"snowflake"`, `"bigquery"`, `"redshift"`, or `"external_source"` with connection parameters (host, database, credentials) embedded in the JSON:

```json
{
  "snowflake_input": {
    "action": "snowflake",
    "parameters": {
      "account": "myorg.snowflakecomputing.com",
      "database": "SALES_DB",
      "schema": "PUBLIC",
      "table": "OPPORTUNITIES"
    }
  }
}
```

**Why it happens:** The LLM is aware that CRM Analytics dataflows use JSON for configuration and that Snowflake/BigQuery/Redshift integration exists, but incorrectly synthesizes these facts into a JSON-configurable connector node that does not exist.

**Correct pattern:**

```
External data sources (Snowflake, BigQuery, Redshift) are configured as
Remote Connections in Analytics Studio → Data Manager → Connections.

Dataflow JSON does NOT have connector nodes for external warehouses.
Only Recipes can consume Remote Connections, and only after the
Remote Connection is created in Data Manager first.

Correct flow:
1. Data Manager → Connections → New Remote Connection (select warehouse type)
2. Enter credentials, warehouse URL, database, schema
3. Save and test the connection
4. In a Recipe, add the Remote Connection as an input node
5. Select the target table or view within the Recipe
```

**Detection hint:** Flag any dataflow JSON containing node types referencing `snowflake`, `bigquery`, `redshift`, `external`, or `remote_connection` as action values in a dataflow (not Recipe) context.

---

## Anti-Pattern 3: Treating the 60-Run Limit as a Calendar-Day Reset

**What the LLM generates:** Capacity planning or scheduling advice that states the run limit "resets at midnight" or "resets daily at the start of the business day." The LLM may also describe a strategy for front-loading runs in the morning because "the counter resets overnight."

**Why it happens:** "Daily limit" language is common in software APIs and platform constraints. LLMs default to calendar-day reset semantics because that is the most common implementation pattern (e.g., API rate limits resetting at midnight UTC). The rolling 24-hour window is a less common pattern that conflicts with the default assumption.

**Correct pattern:**

```
The 60-run limit is a ROLLING 24-hour window, not a calendar-day reset.

Each run slot clears exactly 24 hours after it was consumed.

Example:
- 10:00 AM Monday: 60 runs consumed
- 10:01 AM Monday: no more runs available
- 10:00 AM Tuesday: first run slot clears
- By 11:00 AM Tuesday: all slots from 10:00–11:00 AM Monday have cleared

Correct capacity planning:
- Plot scheduled runs on a rolling 24-hour timeline
- Leave 10–15 slots as buffer for manual reruns and failure recovery
- Do NOT assume runs consumed before midnight are "free" after midnight
```

**Detection hint:** Flag any scheduling advice using phrases like "resets at midnight", "daily reset", "resets at the start of each day", or "front-load runs in the morning."

---

## Anti-Pattern 4: Placing Joins and Complex Aggregations in SAQL Instead of the ELT Layer

**What the LLM generates:** SAQL queries that join two or more datasets at runtime to produce the final result for a dashboard widget:

```saql
q = load "Opportunity";
a = load "Account";
q = cogroup q by 'AccountId', a by 'Id';
q = foreach q generate q.'Amount', a.'Industry', a.'Region';
```

The LLM may also generate SAQL with complex window functions, computed fields, or multi-step aggregations that could be pre-computed in a dataflow transformation.

**Why it happens:** LLMs trained on SAQL documentation learn that SAQL supports joins and complex aggregations. They apply SQL-like query design patterns where the query layer is responsible for joins and transformations. This pattern is correct for relational databases where query results are not stored — but in CRM Analytics, the dataset is stored and reusable, so compute-once ELT is almost always preferable.

**Correct pattern:**

```
Expensive operations belong in the ELT layer (dataflow or Recipe),
not in SAQL at query time.

Dataflow: use Augment transformation for joins
Recipe: use Join node for multi-source merges
Recipe/Dataflow: use Formula or Computeexpression for derived fields

SAQL should only perform:
- Final aggregations (group by, sum, count)
- User-driven filters that vary per interaction
- Simple field selections from a pre-joined, pre-computed flat dataset

If SAQL contains 'cogroup', multi-dataset loads, or complex formula
chains — flag for refactoring into the ELT layer.
```

**Detection hint:** Flag SAQL containing `cogroup`, multiple `load` statements in one query, or complex formula chains (`case when`, nested `foreach`) that could be pre-computed.

---

## Anti-Pattern 5: Assuming Remote Connection Output Writes Back to the External Lake

**What the LLM generates:** An architecture diagram or description where CRM Analytics reads from Snowflake via a Remote Connection, transforms the data, and then writes the result back to a Snowflake table for consumption by downstream systems. The LLM may describe this as a "round-trip ELT" or "bidirectional integration."

**Why it happens:** The LLM correctly identifies that CRM Analytics can read from Snowflake via Remote Connections, then incorrectly generalizes "connection" to imply bidirectional data flow. This is a common assumption with data platform connectors in general — tools like Fivetran, dbt, and Informatica do support read/write. CRM Analytics Remote Connections are read-only.

**Correct pattern:**

```
CRM Analytics Remote Connections are READ-ONLY.

Data flow:
  External lake (Snowflake/BigQuery/Redshift)
    → Remote Connection (read)
    → Recipe transformation
    → CRM Analytics dataset (internal storage only)

CRM Analytics does NOT write back to external lakes.

If downstream systems need the transformed data:
- Use the CRM Analytics REST API to export dataset records
- Or build a separate ETL pipeline outside CRM Analytics to
  read from the analytics dataset and write to the external lake

Do not design any architecture that expects CRM Analytics to
populate an external warehouse table as part of its output.
```

**Detection hint:** Flag any architecture description where CRM Analytics "writes to Snowflake", "publishes to BigQuery", "exports to Redshift", or performs "bidirectional sync" with an external warehouse.

---

## Anti-Pattern 6: Ignoring the 2-Billion-Row Cap Until It Causes a Production Failure

**What the LLM generates:** A dataset design that loads all historical records into a single dataset without any time-based partitioning or row-count risk assessment. The LLM may advise "just load everything and filter in SAQL" or describe the row limit as a future concern rather than a design constraint.

**Why it happens:** LLMs are aware of CRM Analytics row limits in the abstract but do not apply them as architectural design constraints during solution design. They default to the simplest dataset model (one dataset per object) without projecting future growth against the cap.

**Correct pattern:**

```
The per-dataset row cap is 2 billion rows (org allocation-dependent).
Exceeding this cap causes the dataflow or Recipe write to FAIL —
there is no automatic truncation or graceful degradation.

Design-time requirements:
1. Estimate current row count and annual growth rate for each dataset
2. Project time-to-cap: rows / (growth_rate * current_rows)
3. If time-to-cap < 5 years: design a split strategy now
   - Split by time window: current-year dataset + historical dataset
   - Split by business dimension: region, product line, business unit
4. Document the row-limit threshold and set up monitoring alerts
   before the org approaches 80% of the cap

Never recommend loading all historical data into a single dataset
without a row-limit risk assessment.
```

**Detection hint:** Flag any dataset design that loads unbounded historical data into a single dataset, or any advice that defers row-limit planning to "when we get closer to the limit."
