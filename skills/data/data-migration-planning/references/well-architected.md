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

**Trigger bypass via Custom Setting vs. deployment-based deactivation**: Deployment-based deactivation (commenting out trigger code and deploying) is safe but requires two deployments (before and after migration) and code review cycles. The Custom Setting flag approach requires no deployment and is togglable in seconds. However, it requires that every trigger and flow checks the flag — so the pattern belongs in the org's standard automation design, not a retrofit just before migration. Set a hierarchy setting at the migration user's level (`getInstance()` merges the user's values) rather than org-wide, so other users' automation keeps running.

**Soft delete rollback vs. hard delete rollback**: A soft delete leaves rows restorable for 15 days, which is a safety net, but they still have to be excluded from queries (Recycle Bin rows don't count against storage). Hard delete is irreversible, needs the Bulk API Hard Delete permission, and should be rehearsed in a sandbox first.

---

## Anti-Patterns

1. **No external ID field; insert-only load** — Any re-run after a partial failure creates duplicates. Recovery requires manual deduplication, which is expensive, error-prone, and risks breaking existing relationships. External ID upsert is non-negotiable for production migrations.

2. **Migrating all objects in parallel without a dependency sequence** — Master-detail children inserted before their parents fail with hard errors. Lookup children inserted before their parents may silently create records with blank parent references (if the lookup is not required), leading to orphan records that are difficult to detect without explicit integrity queries.

3. **Leaving automation bypass active after migration** — A Custom Permission or Custom Setting flag that suppresses validation rules, triggers, or flows remains active after cutover if not explicitly cleared. End-user record saves after migration bypass the same controls, allowing invalid data to enter production. The bypass reversal step must be a named, signed-off action in the migration runbook — not an optional checklist item.

4. **Loading data without a post-migration validation gate** — Assuming that a zero-error Bulk API job means the migration succeeded. Bulk API 2.0 partial success can mask row-level failures. Record counts, field-level spot checks, and relationship integrity queries must run before migration sign-off.

---

## Official Sources Used

Read for this revision (2026-10-19):

- Bulk API 2.0 and Bulk API Developer Guide (`api_asynch.txt`): relationship fields in a header row, one level only, indexed parent fields, `__r` names (L1491-1531); external ID matched multiple times returns a 300 error (L2500); 10,000-record batches and 150,000,000 daily records (L1242); hard delete permission off by default (L1644-1647); workflow actions increase processing time (L5034).
- Data Loader Guide (`salesforce_data_loader.txt`): up to 150,000,000 records with Bulk API 2.0 (L90, L117-118); batch size settings for SOAP, Bulk API, and Bulk API 2.0 (L351-360); Bulk API, serial mode, and Bulk API 2.0 options (L484-533).
- Best Practices for Deployments with Large Data Volumes (`salesforce_large_data_volumes_bp.txt`): Loading Data from the API: 2,000-record guidance, insert faster than update faster than upsert, clean data because batch errors trigger single-row processing, delta-only updates, Public Read/Write during initial load, roles before records, sharing rules one at a time, disable triggers, workflow rules, and validations during loads, group children by parent, defer sharing calculation (L815-900); Recycle Bin retention, storage, and hard delete (L733-742).
- Object Reference (`object_reference.txt`): Set Audit Fields upon Record Creation and Update Records with Inactive Owners, objects supporting audit fields, SystemModstamp not settable, audit date range (L2555-2568); master-detail behaviour: cascade delete, owner from master, required on the detail page layout, reparenting off by default (L3254-3266).
- Apex Reference Guide (`salesforce_apex_reference_guide.txt`): hierarchy custom setting `getInstance()` returns values merged for the current user (L205053-205072); `FeatureManagement.checkPermission` (L215449-215454).
- Metadata API Developer Guide (`api_meta.txt`): ValidationRule fields `active`, `errorConditionFormula`, `errorMessage` (L45370-45400); CustomField `externalId`, `unique`, `caseSensitive` (L43328, L43402, L43702).

Listed in the original version and not re-read:

- Salesforce Help: Import Data — https://help.salesforce.com/s/articleView?id=sf.data_about_import.htm
- Salesforce Help 000382856: "Required Fields Are Missing" when importing — https://help.salesforce.com/s/articleView?id=000382856&language=en_US&type=1
- Apex Developer Guide: DML Upsert — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_dml_upsert.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
