# Well-Architected Notes — Case History Migration

## Relevant Pillars

- **Reliability** — The strict load order (Case → CaseComment → EmailMessage → EmailMessageRelation → ContentVersion → ContentDocumentLink) is a reliability requirement, not a convenience. Violating it produces referential integrity errors that are difficult to diagnose in bulk jobs. Every child object load must be preceded by a parent count verification. File linkage via ContentDocumentLink must use the REST API path to avoid silent failures that appear as success but produce no links.

- **Performance** — ContentDocumentLink must be loaded via REST API, which is slower than Bulk API 2.0. For large file volumes (50,000+), parallel REST threads and extended load windows (potentially multiple days) must be planned from the start. ContentVersion can be loaded via Bulk API 2.0 at full throughput — only the link step is rate-limited.

- **Operational Excellence** — EmailMessage Status='3' locking is an irreversible operation. Migrations that set Status='3' and must be corrected require destructive recovery processes with Salesforce Support involvement. Operational Excellence requires that the Status field mapping is reviewed and approved before any production load, and that a sandbox validation run confirms no Status='3' rows are in the load set.

- **Security** — ContentDocumentLink `ShareType` controls file visibility. `ShareType='V'` (Viewer) is the default and appropriate for most migrations. Using `ShareType='I'` (Inferred) means access is controlled by the parent record's sharing rules. Verify the intended sharing model before loading — changing ShareType after insert requires deleting and re-inserting ContentDocumentLink rows.

---

## Architectural Tradeoffs

**Task records vs. FeedItem for CaseHistory approximation:**
Task records are the most flexible option — they support cross-reference WhatId, appear in the activity timeline, and are queryable via standard SOQL. FeedItem (Chatter) records appear in the Case feed and are searchable via SOSL but require Chatter to be enabled in the org and are harder to query programmatically. For most migrations, Task records are the right choice unless the business explicitly uses Chatter feeds as the primary case communication channel.

**Sequential updates to generate real CaseHistory vs. Task approximation:**
Generating real CaseHistory by issuing sequential updates to `Status` on each Case record is technically accurate but extremely expensive. For 10,000 cases with an average of 4 status changes each, this requires 40,000 additional API update operations and proportionally increases the load window. This approach is only appropriate for small case volumes (under 10,000) where the business has a strict requirement for the native Case History related list to reflect historical states.

**ContentVersion FirstPublishLocationId vs. ContentDocumentLink ShareType:**
Setting `FirstPublishLocationId` to the Case Id on ContentVersion during insert creates an implicit link to the Case. However, for migrations where files also need to be linked to EmailMessage records, explicit ContentDocumentLink rows are required regardless. Using explicit ContentDocumentLink for all links is the more consistent and auditable approach.

---

## Anti-Patterns

1. **Loading EmailMessage with Status='3' for historical outbound emails** — This permanently locks every loaded record, making future corrections impossible. The correct pattern is `Status='1'` for inbound and `Status='2'` for outbound historical emails. Status='3' is reserved for records that Salesforce itself marks as sent through its native email delivery pipeline.

2. **Using Bulk API 2.0 for ContentDocumentLink** — Bulk API 2.0 does not support ContentDocumentLink. The result is either immediate job failure or silent non-creation of links, producing cases that appear to have no attachments even though ContentVersion records exist. Always use the REST or SOAP API for ContentDocumentLink.

3. **Attempting to insert CaseHistory directly** — CaseHistory is a system-generated read-only object. Direct insert attempts always fail with `INVALID_TYPE_FOR_OPERATION`. Skipping a Task-based approximation strategy because "we'll figure it out later" results in a migration where the business discovers months post-cutover that no audit trail exists for the historical data period.

---

## Official Sources Used

- EmailMessage Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_emailmessage.htm
- CaseComment Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_casecomment.htm
- ContentVersion Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentversion.htm
- ContentDocumentLink Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentdocumentlink.htm
- EmailMessageRelation Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_emailmessagerelation.htm
- CaseHistory Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_casehistory.htm
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
