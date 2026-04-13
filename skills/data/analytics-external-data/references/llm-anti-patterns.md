# LLM Anti-Patterns — Analytics External Data

Common mistakes AI coding assistants make when generating or advising on Analytics External Data.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Remote Connections as Equivalent to Dataset Uploads

**What the LLM generates:** "Create a Remote Connection to Snowflake in Data Manager — this will sync your Snowflake data into CRM Analytics automatically."

**Why it happens:** LLMs conflate the configuration step (Remote Connection) with the data movement step (Recipe, Dataflow, or Live Dataset). The word "connection" implies active data flow, which is misleading in the CRM Analytics model where the Remote Connection is purely a credential store.

**Correct pattern:**

```
A Remote Connection in Data Manager stores credentials and connectivity details only.
To actually move or access data, you must create one of:
- A Recipe with an Input node referencing the Remote Connection (materialized sync)
- A Dataflow node referencing the Remote Connection (legacy ETL path)
- A Live Dataset referencing the Remote Connection (read-through at query time)

Creating a Remote Connection alone moves zero data into CRM Analytics.
```

**Detection hint:** If the output says a Remote Connection "syncs," "imports," or "loads" data into CRM Analytics without mentioning a Recipe, Dataflow, or Live Dataset, the claim is wrong.

---

## Anti-Pattern 2: Claiming Live Datasets Behave Like Refreshed Materialized Datasets

**What the LLM generates:** "Live Datasets give you real-time data in CRM Analytics — they refresh automatically so your dashboard always has current data."

**Why it happens:** LLMs pattern-match "live" to "always refreshed" because that is the most common meaning of the word in analytics product documentation. CRM Analytics Live Datasets are architecturally different — they are read-through query pass-throughs, not refresh-cycle datasets with a live refresh setting.

**Correct pattern:**

```
Live Datasets are NOT a faster refresh mechanism.
They execute queries against the external system (Snowflake, BigQuery, etc.) at dashboard load time.
There is no data stored in CRM Analytics — no local copy, no cache, no refresh cycle.
Performance is entirely dependent on the external system's response time and availability.
If the external system is unavailable, the dashboard fails — unlike materialized datasets, which
serve from local storage independent of the external system.
```

**Detection hint:** If the output says a Live Dataset "refreshes," "syncs," or "pulls data on a schedule," the architecture is wrong. Live Datasets have no refresh schedule — they query live on demand.

---

## Anti-Pattern 3: Skipping the Metadata JSON Schema Step Before InsightsExternalData Row Upload

**What the LLM generates:** Code that directly creates `InsightsExternalDataPart` records with CSV data before creating the parent `InsightsExternalData` header with a `MetadataJson` field.

**Why it happens:** LLMs trained on Bulk API 2.0 patterns may apply that model to the External Data API. Bulk API 2.0 allows the job to start receiving data before schema validation is complete in some flows. The External Data API has a strict sequential dependency: schema record first, data parts second.

**Correct pattern:**

```python
# WRONG: Skip metadata, upload data immediately
# POST InsightsExternalDataPart with CSV data  <-- will fail or cause processing error

# CORRECT sequence:
# 1. POST InsightsExternalData with MetadataJson (field definitions, dataset name)
#    Capture the returned Id
# 2. POST InsightsExternalDataPart records referencing that Id with gzip-compressed CSV chunks
# 3. PATCH InsightsExternalData: set Action = "Process"
# 4. Poll Status field until Completed or Failed
```

**Detection hint:** If generated code uploads `InsightsExternalDataPart` before creating or referencing a parent `InsightsExternalData` record with `MetadataJson`, the sequence is wrong.

---

## Anti-Pattern 4: Conflating Data Connectors (Materialized) with Live Datasets (Read-Through)

**What the LLM generates:** "You can connect Snowflake to CRM Analytics using a Data Connector or a Live Dataset — both give you access to Snowflake data, so choose whichever is easier to set up."

**Why it happens:** Both paths use a Remote Connection to Snowflake, which makes them appear interchangeable to an LLM. The architectural difference — materialized storage vs. read-through queries — is not visible in the configuration surface and is easy to miss.

**Correct pattern:**

```
Data Connectors (via Recipes or Dataflows):
- Pull data from Snowflake on a scheduled refresh cycle
- Materialize data inside CRM Analytics as a dataset
- Dashboard queries run against the local CRM Analytics dataset
- External system availability does not affect dashboard availability after refresh
- Data freshness is bounded by refresh schedule

Live Datasets:
- No data is materialized in CRM Analytics
- Every dashboard query executes against Snowflake at runtime
- Dashboard availability is coupled to Snowflake availability
- Data is always current (no refresh lag)
- Performance depends entirely on Snowflake response time

These are not interchangeable. Choose based on freshness requirements vs. performance/reliability tradeoffs.
```

**Detection hint:** If the output treats Data Connectors and Live Datasets as equivalent alternatives without explaining the materialized vs. read-through distinction, the guidance is misleading.

---

## Anti-Pattern 5: Recommending Data Loader or Bulk API to Push Data into CRM Analytics Datasets

**What the LLM generates:** "Export your data as a CSV and use Data Loader to import it into the CRM Analytics dataset."

**Why it happens:** Data Loader and Bulk API are the canonical tools for CSV data import in Salesforce. LLMs generalize from the Salesforce object import context without recognizing that CRM Analytics datasets are not SObjects and are not accessible via Data Loader or Bulk API.

**Correct pattern:**

```
Data Loader and Bulk API (v1 and v2) operate on Salesforce SObjects only:
Accounts, Contacts, Leads, custom objects, etc.
CRM Analytics datasets are NOT SObjects — they live in a separate analytics storage layer.

To push CSV data into a CRM Analytics dataset programmatically:
- Use the Analytics External Data API (InsightsExternalData SObject + InsightsExternalDataPart SObject)
- This is a REST API endpoint, not the standard Bulk API endpoint
- The endpoint pattern is /services/data/vXX.X/sobjects/InsightsExternalData

Data Loader cannot target InsightsExternalData in the way needed for dataset ingestion.
```

**Detection hint:** Any recommendation to use Data Loader, Bulk API, or `sfdx force:data:bulk:upsert` to populate CRM Analytics datasets is wrong.

---

## Anti-Pattern 6: Recommending an External Data Path Without Assessing Query Performance Tradeoffs

**What the LLM generates:** "Use a Live Dataset — it's simpler to set up than a Data Connector and you'll always have current data."

**Why it happens:** LLMs optimize for setup simplicity and the appeal of "always current data" without surfacing the runtime performance risk. The setup for a Live Dataset is genuinely simpler than building and scheduling a Recipe — the LLM is not wrong about that. But it omits the critical production risk.

**Correct pattern:**

```
Before recommending Live Dataset vs. Data Connector, always assess:
1. How many concurrent users will load dashboards referencing this dataset?
2. What is the external system's p95 query latency under concurrent load?
3. What is the tolerance for dashboard failure if the external system is unavailable?
4. Does the data freshness requirement justify the runtime dependency?

If freshness can tolerate any lag (even 15–30 minutes), a materialized Data Connector with a
scheduled refresh provides more reliable dashboard performance and decouples dashboard availability
from external system availability.

Live Datasets are the right choice only when freshness is critical AND the external system
can reliably serve concurrent queries within dashboard load time budgets (typically under 5 seconds).
```

**Detection hint:** If a Live Dataset recommendation does not mention external system latency, concurrency impact, or dashboard availability risk, the recommendation is incomplete.
