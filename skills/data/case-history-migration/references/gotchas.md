# Gotchas — Case History Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: EmailMessage Status='3' Permanently Locks the Record — No Override Exists

**What happens:** Setting `Status='3'` (Sent) on an EmailMessage record at insert time marks the record as permanently read-only. After insert, the record cannot be updated, patched, or deleted by any means — not via the UI, Apex DML, REST API, SOAP API, Bulk API, or even with System Administrator profile. The lock is enforced at the platform level and cannot be bypassed by any permission, profile, or setting.

**When it occurs:** Whenever a migration CSV sets `EmailMessage.Status = '3'` for records that are being loaded as historical data. It most commonly happens when a practitioner directly maps the source system's "Sent" status to the numeric Salesforce equivalent without understanding the locking semantics.

**How to avoid:** Never use `Status='3'` in a migration load. Use `Status='1'` (Read) for inbound emails and `Status='2'` (Replied) for outbound emails. Status='3' is reserved for records that Salesforce itself marks as sent through the native email-sending infrastructure. If you have already loaded records with `Status='3'`, the only remediation path involves a Salesforce Support-assisted data recovery, which is time-consuming and not guaranteed.

---

## Gotcha 2: ContentDocumentLink Does Not Support Bulk API 2.0

**What happens:** Bulk API 2.0 jobs that include ContentDocumentLink rows either fail immediately with a job-level error or process silently — the job reports success but no ContentDocumentLink records are created. Files appear to exist (ContentVersion and ContentDocument records are present) but no links to the Case or EmailMessage are created. From the user's perspective, no attachments appear on the Case record.

**When it occurs:** Any time a practitioner includes ContentDocumentLink in a Bulk API 2.0 ingest job, regardless of batch size or job configuration. The restriction applies to both the older Bulk API v1 and the current Bulk API 2.0.

**How to avoid:** Always insert ContentDocumentLink via the standard REST API (`POST /services/data/vXX.X/sobjects/ContentDocumentLink`) or SOAP API. For large volumes (10,000+ files), write a scripted loop that issues REST calls in parallel threads while respecting per-org API rate limits. Plan for this step to take significantly longer than Bulk API loads: at 5 concurrent REST threads with 200ms per call, 10,000 links take approximately 100 minutes.

---

## Gotcha 3: CaseHistory Is Not Insertable

**What happens:** Any attempt to insert a CaseHistory record via any Salesforce API returns `INVALID_TYPE_FOR_OPERATION: entity type Case History does not support create`. This is not a permissions issue — it is a hard platform constraint. CaseHistory is a system-generated audit object that Salesforce populates automatically when tracked fields on a Case change.

**When it occurs:** When a practitioner exports CaseHistory from a source Salesforce org (or a legacy system's audit log) and attempts to insert those records into the target Salesforce org. This is a very common assumption in migrations because OpportunityHistory has the same non-insertable property, but practitioners sometimes expect special admin-level overrides to exist.

**How to avoid:** Use Task records or FeedItem records on the Case to represent historical field changes. Tasks appear in the Case activity timeline, are queryable via SOQL, and support Bulk API 2.0 loads. Accept that the native Case History related list will only reflect changes made after the migration cutover. Document this limitation in the migration acceptance criteria so stakeholders are not surprised.

---

## Gotcha 4: EmailMessageRelation Is Required — ToAddress Does Not Auto-Link to Contact

**What happens:** EmailMessage records store recipient addresses as plain text strings in `ToAddress`, `FromAddress`, `CcAddress`, and `BccAddress`. These strings are not automatically matched to Contact, Lead, or User records. If `EmailMessageRelation` rows are not explicitly loaded, the emails appear in the case timeline but no Contact records are linked. Any reporting or analytics that relies on email-to-contact relationships returns incomplete data.

**When it occurs:** Whenever EmailMessage records are loaded without a corresponding `EmailMessageRelation` load step. This is easily overlooked because the emails are visually correct in the UI — the address strings are displayed — but the underlying relational data is missing.

**How to avoid:** After loading EmailMessage records, build and load an `EmailMessageRelation` CSV. For each email, create at least one row for the primary contact (`RelationObjectType = 'Contact'`, `RelationId = <ContactId>`, `Type = 'toAddress'`). Additional rows for CC and BCC addressees that map to Contacts or Users should also be included. `EmailMessageRelation` supports Bulk API 2.0.

---

## Gotcha 5: ContentDocumentId Is Not Available Until After ContentVersion Insert

**What happens:** When a ContentVersion is inserted, Salesforce auto-creates a parent ContentDocument and populates the `ContentVersion.ContentDocumentId` field. This Id is not available before the insert — it is generated by Salesforce at insert time. As a result, ContentDocumentLink rows cannot be pre-built and loaded in the same batch as ContentVersion rows.

**When it occurs:** When a practitioner tries to build ContentDocumentLink rows before or during the ContentVersion load, expecting to reference a pre-known ContentDocumentId. The workflow breaks because the Id does not exist until ContentVersion is inserted.

**How to avoid:** Always split the file loading into two steps: (1) insert ContentVersion via Bulk API 2.0, (2) query `SELECT Id, ContentDocumentId FROM ContentVersion WHERE Id IN (...)` to resolve the auto-created ContentDocumentIds, (3) build ContentDocumentLink rows using those resolved Ids, (4) insert ContentDocumentLink via REST API. This two-step resolution is mandatory and cannot be collapsed into a single load operation.
