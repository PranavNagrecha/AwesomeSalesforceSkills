# Well-Architected Notes — Analytics Data Architecture

## Relevant Pillars

### Performance

CRM Analytics performance failures are almost always caused by misplaced computational work. The canonical performance principle is: **compute once at ELT time, not repeatedly at query time.** Any join, augment, filter, or computed column that appears in SAQL runs on every dashboard interaction for every user. Moving these operations into the dataflow or Recipe layer means they execute once per refresh cycle.

Specific performance design rules:
- Pre-join related datasets using Augment transformations in the dataflow before writing to the final dataset.
- Pre-calculate derived fields (e.g., age buckets, rolling averages, close rate) in Computeexpression transformations.
- Filter to the necessary time window in the ELT layer — do not load 10 years of history if dashboards only query 3 years.
- SAQL should only perform the final aggregation and user-driven filtering that varies per interaction.

### Reliability

Reliability in CRM Analytics data architecture means the refresh pipeline completes consistently and within the run budget, datasets never breach row limits, and incremental patterns do not produce duplicate or missing rows.

Key reliability design rules:
- Design against the 60-run rolling window with explicit buffer for reruns and failure recovery.
- Test snapshot-join Recipes across at least two consecutive full cycles before going to production to verify no row duplication or data loss.
- Document dataset row count thresholds and set up alerting before the org approaches the 2-billion-row cap — platform behavior at the cap is a hard failure, not a graceful degradation.
- Validate Data Sync incremental mode configuration after any Data Manager change (credential rotation, connection reset).

### Scalability

Scalability in CRM Analytics is defined by the ability to add new data sources, increase dataset volumes, and increase refresh frequency without hitting platform limits.

Key scalability design rules:
- Model datasets for future volume growth. If current row counts are 500M and the growth rate is 20% annually, the 2-billion-row cap is 6–7 years away. Design split strategies now rather than in crisis.
- Consolidate low-value dataflows into shared jobs to preserve run-budget headroom for high-priority refreshes.
- Use a tiered refresh strategy: mission-critical datasets on the highest frequency the budget allows; supporting reference data on daily or weekly schedules.
- Remote Connections for external data lakes should be designed as read-only inputs. If data needs to flow back to the external lake, build that capability outside CRM Analytics from the start.

## Architectural Tradeoffs

**Dataflow vs. Recipe for incremental loads:** Dataflows with Data Sync incremental mode are the correct tool for native incremental extraction from Salesforce objects. Recipes are more powerful for complex multi-source transformations and external data ingestion, but require the snapshot-join workaround for incremental behavior. The tradeoff is: dataflows for simple incremental Salesforce data, Recipes for complex transforms or external sources with the snapshot-join overhead accepted.

**Run frequency vs. run budget:** Higher refresh frequency means fresher data but exhausts the 60-run window faster. The tradeoff is always between data freshness requirements and platform capacity. The correct architecture maintains a documented refresh priority matrix — which datasets are business-critical for hourly freshness vs. which are acceptable at daily or weekly.

**ELT complexity vs. dataset maintainability:** Pushing all joins and computations into the dataflow/Recipe layer produces simpler SAQL and faster dashboards, but makes the dataflow/Recipe more complex. Adding a new field to a denormalized dataset requires updating the ELT job and re-running to include the field in the stored dataset. The tradeoff: accept ELT complexity in exchange for runtime performance.

## Anti-Patterns

1. **SAQL-as-ETL** — Using SAQL joins, complex SAQL formulas, and multi-dataset SAQL queries to perform transformations that belong in the ELT layer. This pattern generates per-user, per-interaction compute cost and scales poorly. Every new user who opens a dashboard repeats the same expensive computation. Move all non-interactive transformations upstream into dataflow or Recipe.

2. **Unbounded Recipe Frequency Without Incremental Simulation** — Scheduling a Recipe to run every 30–60 minutes against a large dataset without implementing the snapshot-join technique. Each run consumes a full slot from the 60-run window and processes the full dataset regardless of how few records changed. This pattern simultaneously exhausts the run budget and degrades pipeline performance for all other jobs.

3. **Hardcoded External Source Parameters in Dataflow JSON** — Attempting to embed Snowflake or BigQuery connection credentials and query parameters directly in dataflow JSON. Dataflow JSON has no connector node type for external warehouses. This approach fails at dataflow validation. External source configuration belongs exclusively in Data Manager Remote Connections.

## Official Sources Used

- Transformations for CRM Analytics Dataflows — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_dataflows_data_transformation.htm
- Verify Incremental Sync Settings for Salesforce Data — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_data_sync_incremental.htm
- CRM Analytics Limits — https://help.salesforce.com/s/articleView?id=sf.bi_limits.htm
- Analytics SAQL Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_saql.meta/bi_dev_guide_saql/bi_saql_intro.htm
- Connect and Sync Your Data to CRM Analytics — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_connectors.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
