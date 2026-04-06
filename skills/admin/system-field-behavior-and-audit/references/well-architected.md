# Well-Architected Notes — System Field Behavior and Audit

## Relevant Pillars

- **Security** — System fields provide the foundational audit trail for every record in the org. CreatedById and LastModifiedById establish attribution — who created and last modified each record. Correctly preserving these values during data migration maintains the integrity of compliance reporting and access reviews. Misusing Create Audit Fields (e.g., setting CreatedById to a generic admin user) defeats the audit purpose.

- **Performance** — SystemModstamp is indexed; LastModifiedDate is not. Choosing the wrong field for SOQL filters on high-volume objects causes full table scans, query timeouts, and degraded integration performance. Well-architected delta sync implementations use SystemModstamp to leverage the platform index and avoid governor limit issues.

- **Reliability** — Delta sync and replication systems that filter on LastModifiedDate instead of SystemModstamp silently miss records changed by automated processes. This creates data drift between systems that is difficult to detect and diagnose. Reliable data pipelines must account for all change vectors, including workflow field updates and formula recalculations.

- **Operational Excellence** — Documenting the watermark strategy for delta sync (where the checkpoint is stored, how failures are retried, what the expected sync frequency is) is essential for operability. Teams that skip this documentation face difficult debugging when integrations fall behind or miss records.

## Architectural Tradeoffs

**SystemModstamp completeness vs. volume:** SystemModstamp captures every change, including formula recalculations and roll-up summaries. This ensures no changes are missed, but it can inflate the volume of records returned in delta sync queries — especially on objects with cross-object formulas. Architects must size their integration batch windows and API call budgets accordingly.

**Create Audit Fields vs. data integrity:** Enabling Create Audit Fields is powerful for preserving migration history, but it also allows any user with the permission to fabricate record timestamps. Limit the permission to a dedicated migration user, assign it via a dedicated permission set, and remove the permission set after migration is complete.

**ALL ROWS scope vs. precision:** ALL ROWS is the only way to query soft-deleted records, but it also returns archived records. Architects must pair it with explicit `IsDeleted` filters to avoid mixing deleted and archived records in recovery workflows.

## Anti-Patterns

1. **Using LastModifiedDate for integration sync** — This is the most common architectural error. It produces a false sense of data currency because the integration appears to work but silently misses automated changes. The correct approach is to always use SystemModstamp for any system-to-system sync.

2. **Leaving Create Audit Fields enabled permanently** — The permission should be enabled for migration windows and disabled after completion. Leaving it on increases the attack surface — a compromised integration user could fabricate historical records with misleading timestamps.

3. **No watermark persistence for delta sync** — Storing the sync checkpoint only in memory or in a transient variable means that any process restart loses the position, forcing a full re-sync or missing records. The watermark must be persisted to a durable store (Custom Setting, Custom Metadata, external database).

## Official Sources Used

- Object Reference: System Fields — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/system_fields.htm
- Help: Set Audit Fields upon Record Creation — https://help.salesforce.com/s/articleView?id=sf.enable_set_audit_fields.htm
- REST API Developer Guide: queryAll — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_queryall.htm
- SOQL Reference: ALL ROWS — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_all_rows.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
