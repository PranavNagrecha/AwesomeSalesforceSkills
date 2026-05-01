---
name: data-cloud-zero-copy-federation
description: "Use this skill when configuring or troubleshooting Data Cloud Zero Copy / Lakehouse Federation against Snowflake, Databricks, BigQuery, or Redshift — including external Data Lake Object setup, query semantics through federation, refresh and cache behavior, and choosing federation versus physical ingestion. Triggers on: Data Cloud federated DLO setup, query latency against external warehouse, Snowflake/Databricks/BigQuery integration with Data Cloud, federation vs ingestion decision. NOT for physical Ingestion API streaming/bulk patterns (use data-cloud-integration-strategy), not for CRM Analytics external connectors (use analytics-external-data), not for outbound Data Cloud activation to external systems (use data-cloud-activation-development)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Security
  - Scalability
triggers:
  - "configure Data Cloud zero copy federation to Snowflake or Databricks"
  - "federated DLO query is slow or times out against external warehouse"
  - "decide between Data Cloud ingestion versus zero copy federation for a 200 GB dataset"
  - "BigQuery external object not visible in Data Cloud segmentation"
  - "Data Cloud federated query running up Snowflake credit consumption"
tags:
  - data-cloud
  - zero-copy
  - lakehouse-federation
  - snowflake
  - databricks
  - bigquery
  - redshift
  - data-federation
  - external-dlo
  - query-acceleration
inputs:
  - "External lakehouse platform (Snowflake / Databricks / BigQuery / Redshift) with credentials"
  - "Source schema / table list to expose as federated DLOs"
  - "Latency tolerance for downstream segmentation, calculated insights, and activation"
  - "Estimated query volume and external warehouse compute cost ceiling"
outputs:
  - "Federation configuration plan (target platform, auth, networking, query acceleration)"
  - "External DLO mapping document with field types and refresh metadata"
  - "Federation-vs-ingestion recommendation per dataset with cost and latency rationale"
  - "Operational runbook for federated query monitoring and cost guardrails"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-01
---

# Data Cloud Zero Copy Federation

This skill activates when a practitioner is configuring or debugging Salesforce Data Cloud Lakehouse Federation (also called Zero Copy) against an external cloud warehouse — Snowflake, Databricks, Google BigQuery, or Amazon Redshift. It covers connection setup, the federated Data Lake Object query path, refresh and cache behavior, governance (RLS, masking), and the decision boundary between federation and physical ingestion. It does NOT cover physical Ingestion API patterns, CRM Analytics external connectors, or outbound activation.

---

## Before Starting

Gather this context before designing or troubleshooting a federation:

- Federation is a **query-time** integration, not a copy. Each query against a federated DLO pushes SQL down to the source warehouse and consumes that warehouse's compute. Salesforce does not store the data.
- Not every Data Cloud feature works on federated DLOs. Identity resolution, calculated insights with non-pushdown functions, and certain segmentation operators require materialized data — they either fail, fall back to a slow path, or are blocked outright on federated objects.
- The four supported platforms have different connector mechanics. Snowflake and Databricks use native data-sharing protocols (Snowflake Secure Data Sharing, Databricks Delta Sharing) which means no copy and no staging. BigQuery and Redshift use a connector-mediated path that authenticates and runs federated queries through service-account credentials.
- Federation changes the cost model. Practitioners moving from "ingest everything" mental models will be surprised when a poorly-targeted segment build runs thousands of queries against Snowflake and produces a credit bill at the source.

---

## Core Concepts

### Federation vs. Physical Ingestion

Data Cloud has two ingestion paradigms: **physical ingestion** (the data lands in Salesforce-managed storage as a Data Lake Object) and **federation / zero copy** (the data stays in the external warehouse and is exposed as an *external* Data Lake Object that proxies queries through). Both produce DLOs and can be mapped to Data Model Objects, but their runtime behavior diverges sharply.

| Dimension | Physical Ingestion | Zero Copy Federation |
|---|---|---|
| Where data lives | Data Cloud-managed lake | External warehouse |
| Storage cost | Salesforce billing | External warehouse billing |
| Query latency | Salesforce-controlled, predictable | Depends on source warehouse + network round-trip |
| Refresh model | Stream / bulk loads update DLO | Always live (or cached, see below) |
| Compute cost on query | Included | Source warehouse credits per query |
| Identity resolution | Fully supported | Limited — requires materialized fields |
| Maximum size | 100M rows / 50 GB per object (batch) | Effectively unbounded |

### Connector Mechanics by Platform

**Snowflake** — uses Snowflake Secure Data Sharing. The Snowflake admin grants a share to the Salesforce-managed Snowflake account; Data Cloud mounts the share as a database. Queries push SQL through the share. No data is copied or staged. The share lives entirely inside Snowflake's perimeter.

**Databricks** — uses Delta Sharing (open protocol). The Databricks side creates a share and a recipient profile; Data Cloud authenticates with the bearer token from that profile and queries Delta tables directly.

**BigQuery** — uses a Google Cloud service account. The service account is granted IAM roles on target datasets. Federated queries run as that service account and are billed to the configured BigQuery project.

**Redshift** — uses a JDBC-style connection through a Salesforce-provisioned VPC peering or PrivateLink path. Auth is via Redshift database user; federation runs read-only queries against tables or views the user can see.

### Query Pushdown and Acceleration

Data Cloud attempts to push as much of the query as possible down to the source warehouse. Filters, projections, joins between federated tables on the same connector, and many aggregates push down. Cross-connector joins (e.g., joining a Snowflake DLO with a BigQuery DLO) cannot push down — Data Cloud pulls partial results into its own engine and joins locally, which is slow.

Some platforms support a query-acceleration cache. Frequently-queried federated data can be materialized into a Data Cloud-managed cache for faster downstream segmentation. The cache is opt-in per object and refreshes on a schedule.

### Governance Inheritance

External warehouse access controls — Snowflake Row Access Policies, Databricks Unity Catalog grants, BigQuery Authorized Views — flow through to federated queries because the queries execute in the source warehouse under the federation principal. This is a security feature: a user who is blocked from a Snowflake row will not see it in Data Cloud either. It is also a debugging trap: missing rows in segmentation may not be a Data Cloud issue at all.

---

## Common Patterns

### Pattern 1: Federate a Large Reference Table That Doesn't Need Identity Resolution

**When to use:** A multi-terabyte product catalog, transaction ledger, or telemetry table lives in Snowflake or Databricks. You need to filter on it for segmentation but you do not need to identity-resolve its rows into the Unified Profile.

**How it works:**

1. On the source side, create a share / Delta share / authorized view containing only the columns Data Cloud needs.
2. In Data Cloud Setup, create the lakehouse connector (Snowflake / Databricks). Authenticate using the share credentials or recipient profile.
3. Mount the source database, select the target table, and create an external DLO.
4. Map the external DLO to a Data Model Object. Mark it as a *related* object to the unified profile (lookup), not a participant in identity resolution.
5. Use the external DMO as a filter input in segments.

**Why not physical ingestion:** Tables in this size class exceed the 100M row / 50 GB batch ingestion ceiling and would otherwise need chunked bulk jobs and a re-load discipline. Federation removes the data-movement entirely.

### Pattern 2: Federate Live Transaction Data, Cache the Hot Subset

**When to use:** A live-updating fact table (orders, payments, ad-spend) sits in BigQuery. Marketing builds segments off the last 90 days many times a day. Data Cloud is paying BigQuery on every segment compile.

**How it works:**

1. Create the federated DLO over the BigQuery table.
2. Create a query-acceleration cache scoped to the last-90-day window (filter expression on the cache definition).
3. Schedule cache refresh (e.g., every 4 hours) aligned with the data freshness business actually needs.
4. Segments and calculated insights query the cache; ad-hoc deep-history queries go through the federated path.
5. Monitor BigQuery billing tags to confirm hot-path queries hit the cache.

**Why not pure federation:** Without the cache, every segment compile re-runs the same query in BigQuery. With the cache, BigQuery is touched only on refresh.

### Pattern 3: Read-Through to Snowflake for Identity-Resolved Source

**When to use:** A subset of golden customer attributes lives in a curated Snowflake table that the data-engineering team owns. Sales / Marketing / Service in Salesforce all need it, and physical ingestion would create an authoritativeness conflict.

**How it works:**

1. Create a Snowflake share over the golden customer table.
2. Federate the share into Data Cloud as an external DLO.
3. Materialize *only the identity-resolution keys* (email, phone, customer ID) into a query-acceleration cache so identity resolution can run against them.
4. Leave non-key columns federated (live).
5. Map the federated DLO to the Individual DMO; let Data Cloud's identity resolution use the cached keys.

**Why not full materialization:** Pulling the full golden table into Data Cloud creates two copies of the source of truth. Cache-on-keys keeps the resolution path performant without breaking the single-authority model.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Source dataset > 50 GB or > 100M rows | Federation | Exceeds physical ingestion ceiling |
| Sub-second segmentation latency required | Physical ingestion (or federation + acceleration cache) | Federated round-trip adds variable network + warehouse latency |
| Identity resolution must run on the table | Physical ingestion (or federation with materialized keys) | Identity resolution requires materialized fields for deterministic + probabilistic matching |
| Source data already governed in Snowflake / Databricks RLS | Federation | Inherits source governance — single point of policy enforcement |
| Cross-connector joins are a hot path | Physical ingestion of one side | Cross-connector joins cannot push down; will be slow and expensive |
| Data freshness must be sub-minute | Federation (live) | Physical ingestion has DSO → DLO → DMO multi-hop lag |
| Cost optimization is the dominant concern | Federation + acceleration cache for hot subset | Avoid repeated warehouse-side compute on identical predicates |

---

## Recommended Workflow

1. Confirm the source warehouse is one of the four supported platforms (Snowflake, Databricks, BigQuery, Redshift) and check Salesforce release notes for any newly-GA targets before designing the connector.
2. Decide federation vs. ingestion per dataset using the decision table above. Document the call — federation is hard to reverse cleanly once downstream segments depend on the federated DLO.
3. Provision the source-side share, recipient profile, IAM service account, or DB user. Apply the principle of least privilege: expose the minimum tables / columns Data Cloud needs.
4. Create the lakehouse connector in Data Cloud Setup. Authenticate, mount the catalog, and create external DLOs for the chosen tables.
5. Map external DLOs to DMOs. For identity-resolution participants, plan whether to use a query-acceleration cache on the resolution keys.
6. Run a test segment that filters on the federated DLO. Verify query latency, confirm the source-warehouse query log shows pushdown happened, and capture the per-query cost on the source.
7. Configure cache refresh schedules and monitoring (cost dashboards on the source warehouse, federated-query SLA alerts in Data Cloud).
8. Document the operational runbook: how to revoke the share, how to rotate auth, what to do when source schema changes.

---

## Review Checklist

- [ ] Federation-vs-ingestion decision documented per dataset with a written rationale
- [ ] Source-side share / recipient / service account uses least-privilege grants
- [ ] External DLO mapping reviewed for column-level inclusion (no over-exposure)
- [ ] Cross-connector joins identified and either eliminated or accepted as slow paths
- [ ] Identity resolution participation explicitly resolved (materialized keys vs. full ingestion)
- [ ] Query-acceleration cache scope and refresh cadence aligned to business freshness need
- [ ] Source-warehouse cost ceiling and alert thresholds set
- [ ] Source-side governance (RLS / Unity Catalog grants / authorized views) verified to enforce as expected after federation
- [ ] Auth rotation runbook documented (Snowflake share grant lifecycle, Databricks recipient token, BigQuery service-account key, Redshift DB user)
- [ ] Schema-change protocol agreed with the data-engineering team that owns the source

---

## Salesforce-Specific Gotchas

1. **Federated DLOs are not a drop-in for ingested DLOs in identity resolution.** Identity resolution rules require materialized keys. If you map a federated DLO to the Individual DMO without a query-acceleration cache on the matching fields, resolution either silently skips records or runs unbearably slowly. Always materialize the keys you intend to match on.

2. **Cross-connector joins kill performance.** A segment that filters on `Snowflake.Orders` AND `BigQuery.AdSpend` cannot push the join down to either warehouse. Data Cloud pulls partial results and joins them locally. The result is N×M in the worst case and bills compute on both source warehouses. Either physically ingest one side or pre-join in the source warehouse.

3. **Source-side schema changes break federation silently.** Dropping a column or renaming a table in Snowflake / BigQuery does not automatically propagate to the external DLO. Subsequent queries fail with confusing errors that name a column the practitioner can no longer see. The source-team handoff must include "tell us before you change the share schema."

4. **Query-acceleration cache is not transparent — it has its own freshness clock.** A practitioner who federated a table assuming "always live" is surprised when they enable acceleration and segment results stop reflecting recent source changes until the next cache refresh. Make the cache's refresh cadence visible to anyone who builds segments off the cached object.

5. **Source RLS / row policies cause "missing data" symptoms in Data Cloud.** A Snowflake row-access policy that filters by tenant ID will execute under the federation principal. If the principal isn't entitled to all rows, segments will mysteriously under-count. The fix lives in Snowflake, not in Data Cloud — debug source-side first.

6. **Snowflake Secure Data Sharing has region constraints.** If the Salesforce-managed Snowflake account and the customer's Snowflake account are in different regions, data sharing requires a replication step on the customer side. This is a Snowflake constraint, not a Data Cloud constraint, but it surfaces as a "share is empty" symptom inside Data Cloud Setup.

7. **Federation does not bypass Salesforce data-storage limits for everything.** Calculated insights and segment membership tables are still stored in Data Cloud. A federated source feeding a calculated insight will produce stored CI rows that count against Data Cloud storage. Federation reduces *raw* storage, not derived storage.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Federation decision matrix | Per-dataset table: ingest / federate / federate+cache, with rationale, cost ceiling, and freshness SLA |
| Source-side grant runbook | Step-by-step share / recipient / IAM / DB-user setup with least-privilege commands per platform |
| External DLO mapping document | Federated DLO → DMO mapping, identity-resolution participation, materialization plan |
| Federation observability dashboard | Source-warehouse cost panel, federated-query latency panel, cache hit-rate panel |

---

## Related Skills

- data-cloud-integration-strategy — for the broader connector landscape and Ingestion API streaming/bulk decisions
- data-cloud-data-streams — for physical DSO design when federation is rejected
- data-cloud-query-api — for SQL access to the unified profile and DLOs (federated and ingested) over Query V2 / Query Connect
- data-cloud-activation-development — for outbound activation patterns once the federated data is segmentable
- cross-cloud-data-deployment — for the architecture-level decision on whether Data Cloud is the right hub at all
