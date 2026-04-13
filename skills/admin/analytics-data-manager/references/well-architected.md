# Well-Architected Notes — Analytics Data Manager

## Relevant Pillars

- **Reliability** — Data Manager is the foundational sync layer for all CRM Analytics data pipelines. Sync failures, stale connected objects, or credential expiry cascade into stale datasets and incorrect dashboard data. Reliability requires monitoring sync runs, alerting on failure, documenting credential rotation schedules, and scheduling periodic full syncs for objects with cross-object formula dependencies that incremental sync cannot detect.

- **Performance** — Sync performance is constrained by the 3-concurrent-sync limit and the volume of enabled fields per object. Enabling high-field-count objects (Account, Opportunity with many custom fields) increases sync duration and risks breaching the concurrency window. Staggering sync schedules, enabling only fields actively used downstream, and separating high-volume objects to off-peak windows are the primary performance levers available to an admin.

- **Operational Excellence** — Data Manager configuration is not self-documenting. Without a maintained sync runbook (object list, sync mode per object, schedule, downstream recipe dependencies, credential expiry dates), future admins cannot safely change configuration without risking data freshness regressions. Operational excellence requires treating sync configuration as infrastructure-as-documentation.

- **Security** — Remote connections (Snowflake, BigQuery, Redshift) require credential storage in Data Manager. Credentials should use service accounts with minimum necessary permissions, key pair authentication where supported, and rotation schedules enforced externally. Salesforce CRM Analytics IP egress ranges must be allowlisted in external database firewall and network policies — connecting without an IP allowlist exposes credentials to connection failures that may reveal internal hostnames in error messages.

## Architectural Tradeoffs

**Incremental vs. Full Sync per Object**
Incremental sync is faster and consumes fewer platform resources, but it is unreliable for any object that has fields driven by related-object changes (roll-up summaries, cross-object formulas). Full sync is slower and increases sync duration, but it guarantees data correctness. The well-architected tradeoff is to default to incremental sync and add a scheduled periodic full sync specifically for objects identified as having cross-object formula dependencies. Blanket full syncs on all objects waste sync windows unnecessarily.

**Connected Object Granularity vs. Recipe Complexity**
Enabling many small objects and joining them in recipes gives more flexibility but produces larger, more complex recipe graphs that are harder to maintain and debug. Enabling broader objects with more fields simplifies the recipe layer but increases sync volume. The correct balance is to enable the minimal set of fields needed by active downstream recipes, reviewed quarterly as recipe logic evolves.

**Remote Connections vs. Data Loading via API**
External data can reach CRM Analytics either via a Remote Connection (Data Manager managed) or via direct dataset API uploads (bypassing Data Manager entirely). Remote connections are preferred for recurring external data because they provide consistent monitoring, credential management, and incremental sync capability. Direct API uploads are appropriate for one-time imports or sources that do not support JDBC/ODBC connectivity.

## Anti-Patterns

1. **Querying Connected Objects Directly in SAQL or Dashboards** — Connected objects are internal staging replicas and are not accessible via SAQL, lens builder, or dashboard dataset selectors. Referencing a connected object by name in a dashboard query will fail or silently query an unrelated dataset of the same name. All connected objects must be materialized into named datasets via recipes or dataflows before any analytics layer component can use them.

2. **Relying Solely on Incremental Sync for Objects with Cross-Object Formula Fields** — Incremental sync uses `LastModifiedDate` as its sole change detection mechanism. Any field value that changes as a result of a related object update — without bumping the parent object's `LastModifiedDate` — will drift silently. Production orgs that depend on roll-up summary or cross-object formula fields for dashboard metrics must supplement incremental sync with periodic full syncs on affected objects.

3. **Configuring Remote Connections in Dataflow JSON or Recipe Nodes** — Remote connections to external databases are a Data Manager construct configured under Connect > Remote Connections. They cannot be defined inside a dataflow JSON file or a recipe transformation node. Attempting to configure credentials inside recipe logic results in either hard failures or unmaintainable workarounds. Always configure remote connections in Data Manager first; recipes reference the resulting connected objects by name.

## Official Sources Used

- Connect and Sync Your Data to CRM Analytics — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_running_a_dataflow.htm
- Data Sync Limits and Considerations — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_data_sync_limits.htm
- CRM Analytics REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
