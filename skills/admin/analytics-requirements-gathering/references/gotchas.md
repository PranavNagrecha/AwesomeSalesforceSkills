# Gotchas — Analytics Requirements Gathering

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Synced Objects Are Not Immediately Queryable — Dataset Step Required

**What happens:** Enabling Salesforce object sync in CRM Analytics Data Manager brings data into the analytics storage layer, but it does not create a queryable dataset. A dataflow or recipe must run to create a named dataset. Requirements that say "connect to the Opportunity object" without specifying the dataset creation step leave the developer with an unclear implementation path. Practitioners who navigate to Analytics Studio and try to query the synced object directly find that it does not appear in the dataset browser.

**When it occurs:** Every time a new Salesforce object sync is added and the developer or stakeholder assumes it is immediately available for lens/dashboard use.

**How to avoid:** Requirements must specify: (1) which Salesforce objects are data sources, (2) which fields are needed per object (minimize scope), and (3) that a dataflow or recipe step is required to create a named dataset before the data can be queried. Include dataset creation in the project scope.

---

## Gotcha 2: Data Cloud Direct Queries Have Scope Limitations

**What happens:** Spring '25+ introduced Data Cloud Direct connection for CRM Analytics, allowing real-time queries of Data Cloud Data Model Objects (DMOs) without creating a dataset. However, not all SAQL operations are supported in Data Cloud Direct mode — recipe transformations, certain GROUP BY patterns, and write-back operations are not available. Requirements that specify Data Cloud Direct as the data source for complex transformations fail at implementation.

**When it occurs:** When requirements gather that a Data Cloud DMO is the data source and assume full CRM Analytics functionality is available for real-time queries without a dataset.

**How to avoid:** Requirements that include Data Cloud as a data source must verify whether Data Cloud Direct is sufficient for the needed query patterns or whether a recipe-based dataset creation is required. Document the specific query operations needed and confirm whether they are supported in Data Cloud Direct mode.

---

## Gotcha 3: External Connector Full Refresh Is the Default — Incremental Is Not Automatic

**What happens:** External data connectors (Snowflake, BigQuery, S3) run a full table scan on every recipe execution by default. For large external tables (millions of rows), full refreshes take hours and can cause recipe timeout failures. Requirements that specify a frequent refresh cadence (hourly or daily) for large external tables are not achievable with the default full-refresh pattern.

**When it occurs:** When requirements specify an external data source with a high refresh frequency without investigating whether the external source has a reliable watermark field that can support incremental refresh.

**How to avoid:** Requirements must specify the refresh frequency AND whether incremental refresh is required. For large external sources, verify that the source table has a reliable updated_at or created_at timestamp field that can serve as a watermark for incremental extraction. Document this as a technical requirement before development.
