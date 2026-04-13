# Gotchas — Analytics Data Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Recipes Do NOT Support Native Incremental Loads — Every Run Is a Full Reprocess

**What happens:** Every CRM Analytics Recipe run reads its complete input dataset from the beginning. There is no built-in change-detection, watermark, or delta-load mechanism in Recipes. An architect who schedules a Recipe expecting it to process only records modified since the last run will find that every run reprocesses the entire source, regardless of how many records actually changed.

**When it occurs:** Any time a practitioner designs a high-frequency Recipe refresh for a large dataset (hundreds of thousands to millions of rows) without implementing the snapshot-join workaround. The assumption that Recipes behave like CDC-enabled ETL tools is the root cause. This also occurs when teams migrate from traditional ETL platforms (Informatica, Talend, DataStage) where incremental loads are native capabilities.

**How to avoid:** Use the snapshot-join technique for Recipes where full reprocessing is too expensive. For Salesforce-sourced data where true native incremental is required, use a dataflow with Data Sync incremental mode (SystemModstamp-based) instead of a Recipe. Always validate expected run duration and run-budget impact before finalizing a Recipe refresh schedule.

---

## Gotcha 2: The 60-Run Limit Is a Rolling 24-Hour Window, Not a Calendar-Day Reset

**What happens:** The platform enforces a limit of 60 combined dataflow and Recipe runs per rolling 24-hour window. Each run slot clears exactly 24 hours after it was consumed. If 60 runs are consumed between 09:00 and 10:00 AM, no additional runs can start until 09:00 AM the following day (when the earliest slots begin to clear). Calendar-day assumptions — "the limit resets at midnight" — produce incorrect capacity planning and cause unexpected run failures in the afternoon or evening.

**When it occurs:** Orgs with many high-frequency scheduled refreshes. The mistake surfaces most often after a new batch of datasets is onboarded without auditing the existing run schedule. It also occurs after a dataflow failure triggers manual reruns, which consume additional slots from the same window.

**How to avoid:** Audit the full run schedule across all dataflows and Recipes before finalizing any refresh cadence. Plot scheduled runs on a rolling 24-hour timeline, not a calendar-day grid. Leave buffer capacity (10–15 runs) for manual reruns and failure recovery. The Dataflow Monitor in Analytics Studio shows run history and can be used to visualize consumption patterns.

---

## Gotcha 3: External Data Sources (Snowflake, BigQuery, Redshift) Use Remote Connections in Data Manager — Not Dataflow JSON

**What happens:** Architects attempting to connect CRM Analytics to an external data warehouse (Snowflake, BigQuery, or Amazon Redshift) sometimes look for a connector node in dataflow JSON — there is none. Dataflow JSON does not have a native node type for external warehouse connections. Only Recipes support external data sources, and those sources must be pre-configured as Remote Connections in Data Manager before they can be referenced in a Recipe.

**When it occurs:** When an architect familiar with traditional dataflow authoring attempts to extend the existing dataflow with an external source, or when documentation conflates "dataflow" and "Recipe" as equivalent. Also common when teams assume that because Recipes and dataflows are both ELT tools in CRM Analytics, they have feature parity.

**How to avoid:** Create the Remote Connection first in Analytics Studio → Data Manager → Connections. Confirm the connection credentials, network access (Salesforce IP ranges must be allowlisted by the external warehouse's firewall), and authentication method before building any Recipe. Only then add the Remote Connection as an input node in a Recipe. Do not attempt to encode connection parameters in dataflow JSON.

---

## Gotcha 4: Remote Connections Only Read — They Do Not Write Back to the External Data Lake

**What happens:** Architects sometimes design a CRM Analytics pipeline that they expect to write transformed data back to Snowflake, BigQuery, or Redshift for use by other downstream systems. CRM Analytics Remote Connections are read-only. The output of any Recipe that reads from a Remote Connection is always written to CRM Analytics internal dataset storage — it cannot be directed back to the external warehouse.

**When it occurs:** When CRM Analytics is expected to function as a general-purpose data transformation layer for the broader data platform. Teams that want a round-trip (read from Snowflake → transform in CRM Analytics → write back to Snowflake) discover there is no write-back capability in the platform.

**How to avoid:** Clarify the data flow direction early in architecture design. If write-back to an external lake is required, a separate ETL/ELT pipeline (MuleSoft, Informatica, dbt, or a custom Apex/External Services integration) must handle the write. CRM Analytics datasets can be exported via the CRM Analytics REST API for downstream consumption, but this is not the same as a native write-back.

---

## Gotcha 5: Data Sync Incremental Mode Requires SystemModstamp — Silent Full-Load on Misconfiguration

**What happens:** Data Sync incremental mode uses the `SystemModstamp` field on Salesforce objects to identify records that changed since the last sync. If the Data Sync connection is accidentally set to full-replace mode, or if the object does not surface `SystemModstamp` (rare, but possible with certain external objects), no error is thrown. The dataflow runs successfully, but processes a full data load on every run — silently negating the incremental benefit.

**When it occurs:** After a Data Sync connection is re-created or reset (full-replace is the default mode). Also when a Salesforce administrator changes the connection settings without notifying the analytics team. Custom objects always have `SystemModstamp`; some external objects and certain platform event objects may not.

**How to avoid:** After configuring Data Sync incremental mode, verify the configuration in Data Manager → Connected Sources → select the object → confirm "Incremental" is shown as the sync mode (not "Full"). On the first scheduled incremental run, compare the record count processed against the expected delta — a full-load count on an incremental schedule is the diagnostic signal. Build a monitoring check that compares rows-processed per run against baseline expectations.
