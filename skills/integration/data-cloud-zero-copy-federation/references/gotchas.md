# Gotchas — Data Cloud Zero Copy Federation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Identity resolution silently degrades on federated DLOs

**What happens:** A federated DLO mapped to the `Individual` DMO produces partial or empty unified-individual rows. No error appears; the resolution job runs longer than usual and reports the same record counts but the cluster sizes are wrong. Marketing notices missing audience members weeks later.

**When it occurs:** The matching keys (email, phone, customer ID) used by the identity-resolution rules live on a federated object without a query-acceleration cache materializing those keys.

**How to avoid:** Always materialize identity-resolution keys into a query-acceleration cache even when the rest of the table stays federated. Verify resolution by spot-checking 20 known-duplicate records before declaring the federation production-ready.

---

## Gotcha 2: Source schema changes break federation without a Data Cloud event

**What happens:** A data engineer drops a column from the federated Snowflake / BigQuery table or renames a field. Federated queries from segments and calculated insights start erroring with a backend message that names a field practitioners can't find in Setup.

**When it occurs:** Whenever the source-of-truth team changes the federated object's schema without coordinating with Data Cloud. Most common after database refactors and "small cleanups" of unused columns.

**How to avoid:** Document a schema-change SLA with the source team. The federated DLO definition is a published contract — treat it like an API. Add automated drift detection by querying `INFORMATION_SCHEMA` on the source on a schedule and comparing column lists to the DLO mapping.

---

## Gotcha 3: Cross-connector joins do not push down

**What happens:** A segment that filters on a Snowflake DLO AND a BigQuery DLO compiles successfully but takes minutes-to-hours to run. Source-warehouse query logs show full-table scans on each side. Costs spike on both warehouses.

**When it occurs:** Any segment, calculated insight, or activation rule that joins federated data from two different connectors. The Data Cloud query engine cannot push a join down across two warehouses, so it pulls partial result sets and joins them locally.

**How to avoid:** Either pre-join in the source warehouse (one side authors a view that already incorporates the other side's data via a cross-cloud share or replication step) or physically ingest the smaller side so only one connector is in the join path. Forbid cross-connector joins in segmentation review.

---

## Gotcha 4: Source-side row-access policies cause invisible record loss

**What happens:** Segments under-count by an unexplained margin. Practitioners suspect identity resolution. Logs show no error.

**When it occurs:** The source warehouse (Snowflake row-access policies, Databricks Unity Catalog row filters, BigQuery authorized views) restricts the federation principal from rows that downstream segmentation expects to see. The query executes successfully — just with fewer rows than the practitioner believes exist.

**How to avoid:** Catalog the source-side governance applied to every federated table during onboarding. When debugging missing data, log into the source warehouse as the federation principal and run the same predicate. If rows are missing there, the fix is on the source side, not in Data Cloud.

---

## Gotcha 5: The query-acceleration cache has its own freshness clock

**What happens:** A practitioner enables acceleration on a federated DLO assuming "live" semantics, then runs a segment that should reflect a record updated 10 minutes ago. The record is not in the segment.

**When it occurs:** Acceleration cache refresh interval is longer than the user's mental model of "live." Default refresh schedules (commonly hourly or every few hours) lag the source.

**How to avoid:** Make the cache refresh cadence visible in the segment-builder UI (via DLO description / labels) and document it in the runbook. For sub-cache-interval freshness, either tighten the refresh schedule (and accept the source-cost increase) or query the federated DLO without acceleration for that specific use case.

---

## Gotcha 6: Snowflake region mismatch produces "empty share" symptom

**What happens:** Setup wizard accepts the Snowflake account credentials, mounts the database, but no tables appear under the share. There's no error, just an empty list.

**When it occurs:** The customer's Snowflake account and the Salesforce-managed Snowflake account are in different cloud regions (e.g., AWS us-east-1 vs. AWS us-west-2). Snowflake Secure Data Sharing requires same-region accounts; cross-region sharing requires database replication on the customer side.

**How to avoid:** Confirm region alignment before attempting Snowflake federation. If the customer must keep their data in a non-matching region, set up Snowflake replication of the share-source database to a same-region account and federate from the replica.

---

## Gotcha 7: Federation reduces raw storage, not derived storage

**What happens:** A team federates 50 TB of source data expecting Data Cloud storage to drop. It does — but the storage panel shows new growth from calculated-insight tables and segment-membership tables that materialize derived results from the federated source.

**When it occurs:** Calculated insights and large segments built off federated DLOs persist their results in Data Cloud-managed storage. The bigger the federated source, the bigger the materialized derivatives can grow.

**How to avoid:** Audit calculated insights and segments downstream of every federated DLO. Limit cardinality (filters, time windows, dimension counts) to keep derived storage proportional. Track derived-storage growth in the same dashboard as raw-storage growth.

---

## Gotcha 8: Auth rotation is on the source, not on Data Cloud

**What happens:** Federation breaks at 02:00 a Tuesday morning when a Databricks recipient token, BigQuery service-account key, or Redshift database password expires. Segments stop compiling. The on-call admin checks Data Cloud and finds no expired credential there.

**When it occurs:** The credential lives on the source side; Data Cloud only stores the reference. Source-side rotation policies (90-day defaults are common) silently invalidate it.

**How to avoid:** Track every federation credential's expiry in the same secret-rotation calendar that the rest of the integration estate uses. Schedule rotation in Data Cloud Setup before the source-side expiry, not after.
