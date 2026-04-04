# Well-Architected Notes — Data Migration Planning

## Relevant Pillars

### Reliability

Migration reliability is the primary architectural concern. A migration that produces incomplete, duplicated, or incorrectly related records is worse than no migration — it requires expensive remediation in production. Key reliability mechanisms:

- **Upsert with External ID** ensures re-runnability. Any partial failure can be retried without creating duplicates.
- **Migration_Batch_Id__c** enables targeted rollback of a specific load batch without touching unrelated records.
- **Parent-before-child sequencing** enforces referential integrity at insert time rather than relying on post-load correction.
- **Error file review** after every batch is mandatory — Bulk API 2.0 partial success masks row-level failures that would otherwise go undetected.

### Operational Excellence

Data migration is an operational event, not just a technical one. Well-architected migrations are documented, rehearsed, and reversible:

- The migration plan template captures every decision — tool choice, sequence, bypass approach, rollback steps — so any team member can execute or audit the migration.
- Automation bypass mechanisms (Custom Permission, Custom Setting flag) are explicitly toggled on and off with named owners. This makes the bypass state visible and auditable.
- Post-migration validation runs as a formal gate before sign-off — not an afterthought.
- Sandbox rehearsal of the full migration sequence (including rollback) is required before any production cutover.

### Security

Migration jobs often run with elevated privileges and suppressed controls. The security risk is that bypass mechanisms intended for migration may remain active or may be overly broad:

- **Custom Permission bypass** is the preferred approach because it is scoped to a specific user, not the entire org. Deactivating validation rules affects all users simultaneously.
- **Migration users** should be dedicated service accounts with only the permissions necessary for the migration. They should not be shared with other integrations.
- **Hard delete permission** (`Bulk API Hard Delete`) should be granted temporarily during migration testing and revoked afterward.
- **Audit trail**: All record changes during migration are logged in the Salesforce audit log. Ensure Field History Tracking is enabled on key fields before migration starts so that the migration's changes are distinguishable from later user changes.

### Performance

Migration throughput determines cutover window duration. Performance failures extend downtime:

- **Bulk API 2.0** with batches of up to 10,000 records is the highest-throughput option for unattended loads. Avoid SOAP API for large-volume migration.
- **Trigger and flow suppression** via the Custom Setting flag removes the most significant per-record processing overhead during load. Triggers calling external APIs or performing DML on related records can reduce Bulk API throughput dramatically.
- **Batch size tuning**: For objects with many fields or complex relationships, a lower batch size (2,000–5,000) can reduce timeout risk. For simple flat objects, 10,000 records per batch maximizes throughput.
- **Parallel jobs**: Bulk API 2.0 supports multiple concurrent jobs. Independent objects (no relationships to each other) can load in parallel to shorten the migration window. Only objects with dependencies must be sequenced strictly.

---

## Architectural Tradeoffs

**External ID upsert vs. insert + deduplication**: Upsert requires external ID fields to be designed and created before the first load, which is additional up-front setup. The alternative — insert-only with post-load deduplication — is simpler to start but catastrophic on re-runs. Upsert is the only production-safe approach.

**Custom Permission bypass vs. temporary deactivation**: Custom Permission bypass requires editing every validation rule formula — more setup work but no org-wide exposure window. Temporary deactivation is simpler but exposes the org to bad data from any user or automation that runs during the migration window. In production orgs with active users, always prefer Custom Permission bypass.

**Trigger bypass via Custom Setting vs. deployment-based deactivation**: Deployment-based deactivation (commenting out trigger code and deploying) is safe but requires two deployments (before and after migration) and code review cycles. The Custom Setting flag approach requires no deployment and is togglable in seconds. However, it requires that every trigger and flow has been updated to check the flag — which means the flag pattern must be part of the org's standard automation design, not retrofit just before migration.

**Soft delete rollback vs. hard delete rollback**: Soft delete (recycle bin) is simpler but leaves deleted records consuming storage and appearing in recycle bin queries. Hard delete is cleaner but requires explicit permission, is irreversible, and should be tested in sandbox before use in production.

---

## Anti-Patterns

1. **No external ID field; insert-only load** — Any re-run after a partial failure creates duplicates. Recovery requires manual deduplication, which is expensive, error-prone, and risks breaking existing relationships. External ID upsert is non-negotiable for production migrations.

2. **Migrating all objects in parallel without a dependency sequence** — Master-detail children inserted before their parents fail with hard errors. Lookup children inserted before their parents may silently create records with blank parent references (if the lookup is not required), leading to orphan records that are difficult to detect without explicit integrity queries.

3. **Leaving automation bypass active after migration** — A Custom Permission or Custom Setting flag that suppresses validation rules, triggers, or flows remains active after cutover if not explicitly cleared. End-user record saves after migration bypass the same controls, allowing invalid data to enter production. The bypass reversal step must be a named, signed-off action in the migration runbook — not an optional checklist item.

4. **Loading data without a post-migration validation gate** — Assuming that a zero-error Bulk API job means the migration succeeded. Bulk API 2.0 partial success can mask row-level failures. Record counts, field-level spot checks, and relationship integrity queries must run before migration sign-off.

---

## Official Sources Used

- Bulk API 2.0 Developer Guide — ingest job limits, batch size, upsert operation, relationship cross-references, hard delete
  https://developer.salesforce.com/docs/atlas.en-us.api_bulk_v2.meta/api_bulk_v2/introduction_bulk_api_2.htm

- Data Loader Guide — Data Loader configuration, Bulk API vs SOAP API mode, operation types, record limits
  https://developer.salesforce.com/docs/atlas.en-us.dataLoader.meta/dataLoader/data_loader.htm

- Salesforce Help: Import Data — import wizard behavior, data import limits, supported objects
  https://help.salesforce.com/s/articleView?id=sf.data_about_import.htm

- Apex Developer Guide: DML Upsert — upsert behavior, external ID matching semantics, insert-or-update logic
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_dml_upsert.htm

- Salesforce Well-Architected Overview — architecture quality model, reliability and operational excellence framing
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

- Object Reference: sObject Concepts — relationship types, referential integrity rules, master-detail behavior
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
