# Gotchas — ETL vs API Data Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Using REST API for Bulk ETL Exhausts Daily API Limit

**What happens:** ETL tools or integrations that use standard REST API sObjects endpoints for bulk inserts or updates rapidly consume the daily REST API request limit. Each record requires a separate REST API call.

**Impact:** Nightly batch jobs that process hundreds of thousands of records fail mid-run with REQUEST_LIMIT_EXCEEDED. Subsequent jobs that day also fail because the limit is shared.

**How to avoid:** All bulk ETL operations must use Bulk API 2.0 (which processes records in batches and has a separate 150M row per 24-hour window). Any ETL tool selected for Salesforce integration must support Bulk API 2.0.

---

## Gotcha 2: Conflating One-Time Migration with Ongoing ETL Pipeline

**What happens:** Teams use their ETL pipeline design decisions (tool selection, architecture) for one-time data migration projects, or vice versa.

**Impact:** One-time migrations optimized for bulk speed (using tools like SFDMU or Data Loader) are not appropriate for ongoing pipelines that need scheduling, error retry, and lineage governance. Ongoing ETL tools may be overkill for a one-time migration.

**How to avoid:** Explicitly classify the project as one-time migration or ongoing recurring pipeline before selecting tools or architecture. One-time migrations go to `data-migration-planning`; this skill covers ongoing pipelines only.

---

## Gotcha 3: Expecting Sub-Minute Latency from ETL Batch Processing

**What happens:** Teams use an ETL tool with a 5-minute batch interval expecting "near-real-time" behavior. Business users report that data "isn't showing up fast enough."

**Impact:** The architecture cannot meet latency requirements regardless of scheduling frequency because ETL batch processing has inherent overhead: job startup, data extraction, transformation, load.

**How to avoid:** If the latency requirement is < 5 minutes for individual record changes, API-led integration (MuleSoft, direct REST API) is required. ETL batch processing has a minimum effective latency of several minutes even with the shortest scheduling interval.
