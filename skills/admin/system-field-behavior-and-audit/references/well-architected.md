# Well-Architected Notes — System Field Behavior and Audit

## Relevant Pillars

- **Security** — System fields provide the foundational audit trail for every record in the org. CreatedById and LastModifiedById establish attribution — who created and last modified each record. Correctly preserving these values during data migration maintains the integrity of compliance reporting and access reviews. Misusing Create Audit Fields (e.g., setting CreatedById to a generic admin user) defeats the audit purpose.

- **Performance** — SystemModstamp is on the platform's default index list (large_data_volumes_bp 264 L404). UNVERIFIED (2026-10-20): that LastModifiedDate is unindexed and that filtering on it causes full scans and timeouts. Delta sync implementations should use SystemModstamp to leverage the index.

- **Reliability** — Delta sync and replication systems that filter on LastModifiedDate instead of SystemModstamp can miss records changed by automated processes (object_reference 264 L2563 vs L2566). This creates data drift between systems that is difficult to detect and diagnose. Reliable pipelines must also account for values one object retrieves from another, which do not move the retrieving object's SystemModstamp (L2581-2583).

- **Operational Excellence** — Documenting the watermark strategy for delta sync (where the checkpoint is stored, how failures are retried, what the expected sync frequency is) is essential for operability. Teams that skip this documentation face difficult debugging when integrations fall behind or miss records.

## Architectural Tradeoffs

**SystemModstamp completeness vs. volume:** SystemModstamp captures user and automated-process modifications but, per object_reference 264 L2581-2583, not every field change. UNVERIFIED (2026-10-20): that formula or roll-up recalculation inflates delta volumes. Size integration batch windows and API call budgets from a measured sample, not from this assumption.

**Create Audit Fields vs. data integrity:** Enabling Create Audit Fields is powerful for preserving migration history, but it also allows any user with the permission to fabricate record timestamps. Limit the permission to a dedicated migration user, assign it via a dedicated permission set, and remove the permission set after migration is complete.

**ALL ROWS scope vs. precision:** ALL ROWS is the SOQL way to query soft-deleted records (apex dev guide 264 L8446), and it also returns archived activities (L10124). Architects must pair it with explicit `IsDeleted` filters to avoid mixing deleted and archived records in recovery workflows.

## Anti-Patterns

1. **Using LastModifiedDate for integration sync** — This is the most common architectural error. It produces a false sense of data currency because the integration appears to work but silently misses automated changes. The correct approach is to always use SystemModstamp for any system-to-system sync.

2. **Leaving Create Audit Fields enabled permanently** — The permission should be enabled for migration windows and disabled after completion. Leaving it on increases the attack surface — a compromised integration user could fabricate historical records with misleading timestamps.

3. **No watermark persistence for delta sync** — Storing the sync checkpoint only in memory or in a transient variable means that any process restart loses the position, forcing a full re-sync or missing records. The watermark must be persisted to a durable store (Custom Setting, Custom Metadata, external database).

## Official Sources Used

- Object Reference: System Fields — supports the LastModifiedDate vs SystemModstamp definitions, the "doesn't capture every field change" caveat and the Create Audit Fields steps and object list: object_reference 264 L2563, L2566, L2581-2583, L2592-2603, L3125, L3132-3133 — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/system_fields.htm
- Help: Set Audit Fields upon Record Creation — https://help.salesforce.com/s/articleView?id=sf.enable_set_audit_fields.htm — help.salesforce.com is not in the corpus; the Setup steps are grounded instead in object_reference 264 L2599-2603 (UNVERIFIED (2026-10-20) for anything only this article says).
- REST API Developer Guide: queryAll — supports the `/queryAll` URI: api_rest 264 L17247; Bulk API queryAll operation and archived Task/Event records: api_asynch 264 L6670-6671 — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_queryall.htm
- Apex Developer Guide: ALL ROWS and undelete — supports ALL ROWS covering deleted records and archived activities, no FOR UPDATE, and the 15-day Recycle Bin: apex dev guide 264 L8358, L8446, L10124-10130 — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dml_undelete.htm
- Large Data Volumes Best Practices — supports the default index list (SystemModstamp, CreatedDate, Name, Id) and Recycle Bin soft-deletion behaviour: salesforce_large_data_volumes_bp 264 L309, L404-411, L738-742.
- Metadata API: FieldHistoryArchive `archiveAfterMonths` (18-month default) — supports the 18-month note in Related Skills: api_meta 264 L46331-46332.
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
