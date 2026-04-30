# Well-Architected Notes — Attachment to Files Migration

## Relevant Pillars

- **Operational Excellence** — Classic Attachments and Notes are legacy storage models without versioning, content collaboration features, or modern API surfaces. Salesforce continues to support them but no longer adds capabilities. Modern features — Files Connect, Quip integration, Salesforce Files Sync, content libraries, Files in Slack — only work with `ContentDocument`. Every Attachment retained is technical debt that grows: it cannot be surfaced in modern UI, indexed by Einstein, or shared via Files-aware integrations. Migration is operational hygiene that aligns the org with the platform's current direction.

- **Security** — Files sharing is more granular than Attachment sharing. Attachments had only `IsPrivate` (visible to owner + admins) vs inherits-from-parent. Files have independent `ShareType` (capability) and `Visibility` (audience scope), plus per-link sharing rows that can be audited via `ContentDocumentLink` queries. Migration is the moment to right-size sharing: a private Attachment that has been migrated with `Visibility='InternalUsers'` is more securely scoped than the original. The migration process must include an explicit sharing decision per row, not a blind copy of the IsPrivate flag.

- **Reliability** — A re-runnable, idempotent migration is operationally safer than a one-shot job. The `Source_Attachment_Id__c` origin tracking pattern allows partial failures to be re-tried without duplication, supports incremental verification, and provides an audit trail for compliance. A migration without origin tracking forces all-or-nothing execution and risks data corruption if the job fails mid-run.

## Architectural Tradeoffs

**Live cutover (trigger + batch) vs scheduled batch only:** Live cutover deploys a trigger that mirrors new Attachments to Files in real time, while a background batch processes history. This eliminates the "last day's Attachments missed the migration" gap, but adds a runtime cost (every Attachment insert spawns a Queueable) that persists until Attachment creation is disabled at the org level. Scheduled batch only is cheaper at runtime but requires either a maintenance window with disabled Attachment creation or accepting a known gap that needs a follow-up batch. Choose live cutover for production orgs with active users; scheduled batch only for dev/sandbox environments or strict change windows.

**Preserve original CreatedDate vs let migration timestamp prevail:** Preserving `CreatedDate` requires the "Set Audit Fields upon Record Creation" permission and explicit field assignments, and is essential for compliance contexts (legal hold, SOX evidence retention, regulatory audit). Letting the migration timestamp prevail simplifies the code and the test matrix but loses historical context. The choice is not technical — it's a compliance-driven decision that must come from the document/records governance team. Default for compliance-bound industries: preserve. Default for productivity migrations: don't preserve.

**Selective predicate vs migrate everything:** A selective migration (e.g., only Attachments from the last 3 years on active records) controls Files storage cost and scope. Migrating everything is simpler but commits the org to a larger storage footprint and includes Attachments that may have lived past their retention policy. The right answer is governance: review the org's records retention schedule before migrating. Migrating data that should have been archived is a well-architected anti-pattern.

**Cleanup of source Attachments vs permanent dual-storage:** Deleting source Attachments after verification is the canonical end state — it eliminates the legacy storage and the dual-write code paths. Permanent dual-storage (keep both) is sometimes used as a "rollback insurance" pattern but accumulates storage cost forever and creates a confusing user experience (which related list is canonical?). The recommendation is: delete sources after a defined soak period (typically 30 days post-verification), with full export to external storage as the rollback insurance.

## Anti-Patterns

1. **Treating the migration as a one-time script with no re-run capability.** A migration without `Source_Attachment_Id__c` origin tracking cannot be re-run after partial failure without producing duplicates. The "first attempt must be perfect" mentality is fragile. Build idempotency from day one — it costs one custom field and a few lines of dedup logic, and pays back the first time anything goes wrong.

2. **Auto-deleting source Attachments in the same transaction as the migration insert.** This couples cleanup to migration success and removes the safety window in which verification can run. A failure between insert-success and delete leaves orphaned ContentDocuments with no source to retry from. Cleanup is always a separate, gated step.

3. **Defaulting `ContentDocumentLink.Visibility='AllUsers'` without checking OWD.** Public-by-default sharing on a private-OWD parent throws errors and breaks the migration; on a public-OWD parent, it may over-share files that were intentionally private. The safe default is `'InternalUsers'`; escalate to `'AllUsers'` only after an explicit OWD check or business decision.

4. **Migrating Classic Notes as ContentVersion with `.html` extension instead of ContentNote.** This puts Notes in the wrong UI surface (Files related list instead of Notes related list) and breaks the inline-edit experience. ContentNote is the dedicated sObject; using it preserves the user-facing semantics.

5. **Leaving permanent dual-storage as a "safety net".** Once verification has confirmed migration completeness, source Attachments should be archived (export to external storage) and deleted. Keeping both indefinitely doubles storage cost, confuses users about which is canonical, and means future Files-only features can't be adopted because the legacy data path is still active.

6. **Skipping the EmailMessage parent-type carve-out in cleanup.** Email inline content references attachments by ID. Blanket cleanup that includes EmailMessage parents breaks the inline rendering of historical emails. Treat EmailMessage as a separate cohort with its own cleanup decision (typically: keep both, or update inline URIs at migration time).

## Official Sources Used

- ContentVersion sObject Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentversion.htm
- ContentDocument sObject Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentdocument.htm
- ContentDocumentLink sObject Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentdocumentlink.htm
- ContentNote sObject Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentnote.htm
- Salesforce Files Concepts — https://help.salesforce.com/s/articleView?id=sf.collab_files_about.htm
- Migrate Attachments to Salesforce Files — https://help.salesforce.com/s/articleView?id=sf.admin_files_migration.htm
- Set Audit Fields upon Record Creation — https://help.salesforce.com/s/articleView?id=sf.audit_fields_create.htm
- Apex Batch Processing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_interface.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
