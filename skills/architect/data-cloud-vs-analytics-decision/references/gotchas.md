# Gotchas — Data Cloud vs CRM Analytics Decision

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. Data Cloud is documented as Data 360 in current developer guides; both names appear below.

## Gotcha 1: "Replace Data Cloud with CRM Analytics" ignores activation and identity scope

**What happens:** Teams cancel or defer Data Cloud because CRM Analytics can visualize external data once it is pushed into datasets. They then discover they still lack identity resolution, unified profiles, segment publication to ad platforms, and consent-aware activation.

**When it occurs:** During budget consolidation, when products are compared on charting features instead of on ingestion, harmonization, identity, and activation requirements.

**How to avoid:** Score each use case against ingestion, harmonization, identity, activation, and analytics. If any activation or cross-source identity requirement scores high, Data Cloud stays in scope regardless of CRM Analytics. Check the contract too: segmentation and activation are described as capabilities "if you have purchased Segmentation and Activation".

**Source:** Data Cloud Developer Guide, Data 360 Architecture (identity resolution with match and reconciliation rules producing a unified profile; activations to Marketing Cloud, ad platforms, and core CRM) and Data 360 Features Brief Overview. developer.salesforce.com/docs/data/data-cloud-dev/guide/dc-architecture.html and dc-features-overview.html, read 2026-10-03.

---

## Gotcha 2: There are two ways CRM Analytics reaches Data 360, and they behave differently

**What happens:** Architects promise analysts "everything in Data Cloud, live in CRM Analytics" without naming the path. One documented path converts Data 360 data model objects into CRM Analytics datasets, which is a copy with a refresh schedule. The other, Direct Data, queries Data 360 in place. Scope and freshness differ, and so does who maintains what.

**When it occurs:** During workshops where lakehouse terms are used loosely and the DMO boundary is skipped.

**How to avoid:** Name the concrete DMOs and the path for each subject area in the decision record. Stage a proof of concept on one narrow subject area. UNVERIFIED (2026-10-03): which objects Direct Data supports, and whether it reads DMOs only, is documented in Salesforce Help, which does not fetch; confirm in the org before committing scope.

**Source:** CRM Analytics REST API Developer Guide (Spring '26), overview: "Convert Data 360 data model objects to datasets" (local corpus `knowledge/imports/salesforce-analytics-rest-api.md`).

---

## Gotcha 3: Latency stacks across layers

**What happens:** Stakeholders expect near-real-time dashboards on metrics that depend on batch harmonization, identity resolution runs, calculated insight refreshes, and CRM Analytics schedules. Missed freshness gets blamed on "the wrong product" instead of the pipeline.

**When it occurs:** When marketing promises sub-hour activation and sales operations expects the same freshness in CRM Analytics without modeling cumulative lag.

**How to avoid:** Document end-to-end latency as a chain: ingestion mode, DLO-to-DMO transformation (batch or streaming), identity resolution, calculated insight mode (batch or streaming), CRM Analytics dataflow, recipe, or sync schedule. Record the slowest hop per persona.

**Source:** Data 360 Architecture (batch and streaming transformations; calculated insights "through a batch process and streaming"); CRM Analytics REST API Developer Guide, Schedule Resource ("a schedule for a dataflow, recipe, or connection sync").

---

## Gotcha 4: Data 360 is consumption-metered; the cost model is not per seat

**What happens:** The business case prices Data Cloud like CRM Analytics, as licences per user. Data 360 usage is tracked as credit consumption, so ingestion volume, identity runs, segmentation, and queries move the bill. A design that re-processes everything nightly costs more than one that processes changes.

**When it occurs:** When the finance model is built from seat counts, or when a proof of concept's usage is extrapolated without measuring consumption.

**How to avoid:** Put consumption in the decision record as a named risk with an owner, and review the digital wallet during the proof of concept. UNVERIFIED (2026-10-03): the per-operation credit rates and whether CRM Analytics queries against Data 360 consume credits are not stated in the fetched developer guides.

**Source:** Data 360 Architecture, Governance: "The digital wallet offers transparency into usage types and credit consumption." Salesforce Architects, Data 360 Architecture (architect.salesforce.com/docs/architect/fundamentals/guide/data-360-architecture, read 2026-10-03): batch transforms support "a highly efficient incremental processing mode" that "significantly reduces processing time and resource consumption by only processing records that have changed since the last successful run."

---

## Gotcha 5: SOQL against Data 360 objects has its own limits

**What happens:** A custom report or Lightning component that queries DMOs with SOQL fails or truncates. Data 360 limits SOQL results to 12 MB, returns a query-more link beyond that, and rejects a query whose single result exceeds the limit. Aggregate queries do not support currency fields, even outside the aggregate function. Calculated insight objects cannot be queried with SOQL at all.

**When it occurs:** When a team chooses "query Data 360 from the CRM side" as the analytics path instead of CRM Analytics or a BI tool, or builds a currency KPI with `SUM()` over a DMO.

**How to avoid:** Use SOQL on DMOs for record lookups and small aggregates. Use SQL, CRM Analytics, or an enterprise BI tool through the Data 360 JDBC driver for analytics. Keep calculated insights out of SOQL designs.

**Source:** SOQL and SOSL Reference, Version 66.0 (Spring '26), SOQL Object Limits and Limitations, "Data 360 Objects" (local corpus `knowledge/imports/salesforce-soql-sosl.md`); Data 360 Architecture, Reporting and Query.

---

## Gotcha 6: An existing warehouse may mean federate, not ingest

**What happens:** The plan copies every warehouse table into Data Cloud, duplicating storage and modeling work that already exists. Data 360 offers zero copy connectors that federate read-only access to partner platforms, and Data Shares that expose derived data to external systems without copying.

**When it occurs:** In enterprises with Snowflake, Databricks, BigQuery, or Redshift already holding modeled customer data.

**How to avoid:** For each source, record ingest, federate, or leave out. Federate when the warehouse model is trusted and only needs to join identity; ingest when the data must drive segments or streaming insights. Record what the federation is read-only for.

**Source:** Data 360 Architecture: "Zero copy connectors provide data federation through read-only access to data from existing partner platforms"; "Data Shares: Share derived data, segmentations, and activations from Data 360 to external systems without copying it." Salesforce Architects, Data 360 Architecture (architect.salesforce.com/docs/architect/fundamentals/guide/data-360-architecture, read 2026-10-03): "bidirectional Zero Copy federation with Snowflake, Databricks, BigQuery, and Redshift avoiding data migration or duplication"; "Data which is made available through Zero Copy Data Federation is represented directly as DLOs." The Data Cloud Integration Guide's navigation lists the federation setup pages.

---

## Gotcha 7: A CRM Analytics sync is not a dataset

**What happens:** The team schedules a data sync, sees the object in CRM Analytics, and reports the analytics layer as done. Synced data lands as a connected object, which cannot be visualized directly. A recipe or dataflow must still build the dataset that dashboards use.

**When it occurs:** On the first CRM Analytics build for CRM-only data, when "turn on sync" is mistaken for "build the dataset".

**How to avoid:** Plan three artifacts per subject area: the sync (or Data 360 conversion), the recipe or dataflow, and the dataset with its schedule. Put each in the latency chain from Gotcha 3.

**Source:** CRM Analytics REST API Developer Guide (Spring '26), Replicated Dataset Resources: "A data sync loads source object data as a connected object in Analytics. Connected objects can't be visualized directly, but are used like a cache to speed up other jobs."
