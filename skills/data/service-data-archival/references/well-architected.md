# Well-Architected Notes — Service Data Archival

## Relevant Pillars

- **Security** — Archival and deletion operations on Case data are irreversible and operate on potentially sensitive customer service records. Access to run deletion scripts must be restricted to named administrators using permission sets that grant the Bulk API Hard Delete permission only when needed. Legal-hold enforcement is a security and compliance control: bypassing it — even accidentally by not filtering — exposes the org to regulatory liability. Export pipelines must encrypt data in transit and at rest.
- **Trust and Reliability** — The three deletion sequences (ContentDocumentLink → ContentDocument → EmailMessage → Case) are a dependency chain. Any step that runs out of order or fails mid-run leaves the org in a partially archived state that is difficult to diagnose and may require manual reconciliation. A reliable archival process must be idempotent: re-running after a partial failure should not cause duplicate deletes or destroy records that were already successfully processed.
- **Performance** — EmailMessage and ContentDocument deletions at scale must use Bulk API 2.0, not synchronous DML. Synchronous DML in Apex is capped at 10,000 rows per transaction. For orgs with millions of EmailMessage records, synchronous deletion is not viable. Bulk API 2.0 supports up to 100 million records per job with parallel processing and does not consume Apex governor limits.
- **Operational Excellence** — Archival is a recurring operation in any long-lived Service Cloud org. Document the deletion sequence, retention matrix, legal-hold refresh process, and post-deletion validation steps in a runbook. Automate the Recycle Bin empty step. Track storage baselines before and after each archival run so trends are visible and future capacity can be planned.

## Architectural Tradeoffs

**Bulk deletion vs. Salesforce Archive feature:** Bulk deletion permanently removes records and reclaims storage immediately (after Recycle Bin purge). The Salesforce Archive feature moves records to a lower-cost storage tier, retaining queryability at reduced cost, but does not eliminate storage consumption entirely — archived records still count against archive storage quota. For compliance-driven "right to erasure" scenarios, deletion is required; archival alone is insufficient. For long-tail retention (records that must be retained for 7+ years but rarely accessed), the Archive feature reduces cost while maintaining accessibility.

**Apex batch delete vs. Bulk API 2.0:** Apex batch jobs are easier to integrate with custom logic (e.g., legal-hold checks, export triggers) but consume Apex CPU time, heap, and DML limits per batch execution. For pure deletion at scale, Bulk API 2.0 is preferred: it runs outside the Apex governor limit framework, supports parallel batch processing, and provides job-level status tracking without requiring a deployed Apex class. Use Apex batch only when the deletion logic requires per-record conditional processing that cannot be expressed in a SOQL WHERE clause.

**EmailMessage-only purge vs. full Case archival:** If the storage problem is data storage (EmailMessage bloat) and there is no compliance requirement to delete Case records, an EmailMessage-only purge is lower risk and faster to validate than a full Case archival. Full Case archival introduces additional complexity: Case records carry SLA history, CSAT data, and serve as the parent for Tasks and Events that may also need to be handled. Scope the operation to the smallest set of objects required to solve the storage problem.

## Anti-Patterns

1. **Delete Cases first, assume children will clean up** — This is the most common archival anti-pattern. Practitioners submit a Case delete job and assume the platform will cascade-delete all child records and reclaim storage. In reality, ContentDocumentLink and ContentDocument records are not reliably cascade-deleted, and EmailMessage behavior depends on configuration. File storage is unaffected. The correct approach is to process child records in dependency order before or after Case deletion, with explicit validation at each step.

2. **Treat file storage and data storage as a single pipeline** — EmailMessage bloat is a data storage problem; ContentDocument bloat is a file storage problem. They require separate SOQL queries, separate Bulk API jobs, and separate storage metrics to validate. An archival pipeline that only targets one pool leaves the other unchanged. Always baseline both storage pools separately before and after archival.

3. **Run archival without a legal-hold refresh** — Legal-hold lists change: new litigation holds are added and old ones are released regularly. Running an archival script with a stale legal-hold exclusion list — even one from a week earlier — risks deleting records that were placed on hold after the list was last refreshed. Always pull a current legal-hold list from the source of truth immediately before generating the deletion job input file.

## Official Sources Used

- Salesforce Well-Architected Overview — architecture quality framing, Trust and Reliability pillar
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — EmailMessage, ContentDocument, ContentDocumentLink, ContentVersion sObject behavior and relationship semantics
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Bulk API 2.0 Developer Guide — bulk delete job mechanics, batch limits, hard-delete behavior
  https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Store Data Externally with Legacy Salesforce Archive — Archive feature behavior, retention policy configuration, storage tier mechanics
  https://help.salesforce.com/s/articleView?id=sf.data_storage_archiving.htm&type=5
- Email-to-Case Considerations — Email-to-Case EmailMessage creation behavior, attachment processing
  https://help.salesforce.com/s/articleView?id=sf.cases_email_to_case_considerations.htm&type=5
- Create Retention Policies — Salesforce Archive retention policy setup and object scope
  https://help.salesforce.com/s/articleView?id=sf.data_storage_archiving_retention_policies.htm&type=5
