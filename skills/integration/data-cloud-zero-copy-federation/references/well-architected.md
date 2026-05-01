# Well-Architected Notes — Data Cloud Zero Copy Federation

## Relevant Pillars

- **Performance** — Federated query latency includes a network round-trip plus source-warehouse compute time. Cross-connector joins cannot push down. Query-acceleration caches are the primary performance lever and must be sized against the actual hot working set, not the full dataset.
- **Security** — Federation inherits source-side governance (Snowflake row-access policies, Databricks Unity Catalog grants, BigQuery authorized views). This is a strength when source governance is mature and a debugging hazard when it is not. The federation principal must be granted least-privilege; over-broad grants undermine source-side controls.
- **Scalability** — Federation removes the 100M-row / 50 GB physical-ingestion ceiling for the *source* but does not relieve Data Cloud-side derived-storage growth (calculated insights, segment membership). Derived-storage growth must be modeled separately.
- **Reliability** — Source-side schema changes and credential rotation can break federation without surfacing a Data Cloud event. Drift detection and credential-expiry tracking belong on the source-system observability stack.
- **Cost Optimization** — Every federated query is billed on the source warehouse. Without acceleration caches, repeated identical predicates from segment compiles can drive thousands of dollars per month at the source. Cost ceilings and per-query alerts on the source warehouse are mandatory operational practice.

## Architectural Tradeoffs

**Live federation vs. acceleration cache.** Pure federation gives the freshest data and the lowest Data Cloud storage footprint, but pays source-warehouse compute on every query. Acceleration caches eliminate repeated source compute but introduce a freshness lag and a Data Cloud-managed materialization. The right answer is usually "federation as the default, cache the hot subset."

**Federation vs. physical ingestion for identity-resolution participants.** Federation preserves the single-source-of-truth property but degrades identity resolution unless keys are materialized. Physical ingestion gives Data Cloud first-class control of the keys but creates a duplicate authority. Materializing keys via acceleration cache while leaving non-key columns federated is the usual middle path.

**Inheriting source governance vs. owning Data Cloud governance.** When the source warehouse already enforces row- and column-level policies (mature data-engineering team, regulated industry), federation is the path of least friction. When source governance is loose, physical ingestion shifts the policy surface to Data Cloud where Trust Layer and Data Spaces govern access.

**Cross-connector joins vs. pre-joining at source.** Joining federated objects across connectors (Snowflake + BigQuery) is supported but slow and expensive. Pre-joining at the source (cross-cloud share, replication) or physically ingesting one side both eliminate the slow path. Forbid cross-connector joins in segment review unless explicitly justified.

## Anti-Patterns

1. **Treating federation as free** — Federation removes Data Cloud raw-storage cost, but query cost lives on the source warehouse. Teams that frame federation as "no incremental cost" discover a four- or five-figure Snowflake / BigQuery bill at the end of the month. Cost lives on the source side and must be modeled accordingly.

2. **Identity resolution against bare federation** — Mapping a federated DLO to the `Individual` DMO without materializing keys breaks identity resolution silently. Always materialize the keys IR rules read.

3. **Cross-connector segments in production** — Building hot-path segments that join federated data across two warehouses is an architectural smell. Either pre-join at one of the sources or physically ingest the smaller side.

4. **Federation without a source-team SLA** — Federation creates an external dependency on a system Data Cloud doesn't control. Without a documented schema-change SLA and credential-rotation calendar with the source-team owner, federation will eventually break unannounced.

## Official Sources Used

- Data 360 Architecture Strategy — https://architect.salesforce.com/docs/architect/fundamentals/guide/data-cloud-architecture-strategy
- Data Cloud Connectors and Integrations Help — https://help.salesforce.com/s/articleView?id=c360_a_sources_targets.htm
- Data 360 Integration Guide — https://developer.salesforce.com/docs/data/data-cloud-int/guide/c360-a-developer-overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Architects: Cross-Cloud Data Strategy — https://architect.salesforce.com/decision-guides/cross-cloud-data
