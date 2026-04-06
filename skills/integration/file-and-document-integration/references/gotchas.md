# Gotchas — File And Document Integration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: ContentDocument Cannot Be Inserted Directly

**What happens:** An `INSERT_UPDATE_DELETE_NOT_ALLOWED` error is thrown when code attempts to insert a ContentDocument record. The operation is rejected entirely.

**When it occurs:** Developers unfamiliar with the Salesforce file model assume ContentDocument is the primary object for file storage, similar to how Document worked in Salesforce Classic. They write `insert new ContentDocument(...)` and hit a hard platform restriction.

**How to avoid:** Always insert ContentVersion. The platform auto-creates the parent ContentDocument. Query back the ContentDocumentId from the inserted ContentVersion record when you need it for linking: `SELECT ContentDocumentId FROM ContentVersion WHERE Id = :cvId`.

---

## Gotcha 2: Base64 VersionData Hits Request Body Limit at 28 MB (Not the Advertised File Limit)

**What happens:** A `REQUEST_ENTITY_TOO_LARGE` error occurs when uploading files via base64-encoded VersionData, even though the file is well under the 2 GB file size limit.

**When it occurs:** The REST API request body limit is 37.5 MB. Base64 encoding inflates binary data by approximately 33%. A 28 MB binary file becomes ~37.3 MB when encoded — right at the limit. Developers who test with small files never encounter this until production workloads include larger documents.

**How to avoid:** Use REST multipart form-data upload for any file that might exceed 20 MB. Reserve base64 insert for scenarios where files are guaranteed to be small (e.g., profile photos, thumbnails). Always test with production-realistic file sizes.

---

## Gotcha 3: FirstPublishLocationId Is Write-Once on Insert

**What happens:** Attempting to update `FirstPublishLocationId` after the ContentVersion is created has no effect — the field is silently ignored on update (no error, but no change either).

**When it occurs:** Developers who forget to set `FirstPublishLocationId` during the initial insert try to update it later, expecting the file to appear on the target record. It never does. They waste debugging time because no error is thrown.

**How to avoid:** Always set `FirstPublishLocationId` at insert time when the target record is known. If you miss it, create a `ContentDocumentLink` manually to associate the file with the record after the fact.

---

## Gotcha 4: ContentDocumentLink ShareType Defaults Vary by Context

**What happens:** Files are shared with broader or narrower access than intended because the `ShareType` field on ContentDocumentLink behaves differently depending on the org's content sharing settings and the linked entity type.

**When it occurs:** When `ShareType` is set to `C` (Collaborator) but the org has restricted content delivery settings, the effective access may be downgraded. When linking to a Library (ContentWorkspace), `ShareType` must be `I` (Inferred). Setting `V` or `C` when linking to a Library throws `FIELD_INTEGRITY_EXCEPTION`.

**How to avoid:** Always set `ShareType` explicitly. Use `V` (Viewer) for read-only access on standard records, `C` (Collaborator) when edit access is needed, and `I` (Inferred) when linking to Libraries. Test the actual effective permissions — do not assume the value you set is the access level users experience.

---

## Gotcha 5: Files Connect Does Not Support Write-Back to External Systems

**What happens:** Developers configure Files Connect expecting bidirectional file sync — reading external files in Salesforce and writing Salesforce files to the external system. Files Connect only supports reading external files into Salesforce. There is no write-back, upload, or sync-to-external capability.

**When it occurs:** Requirements specify that Salesforce-generated documents (quotes, contracts, reports) should be stored in SharePoint or Google Drive. The team configures Files Connect, discovers it is read-only, and must build a custom integration to push files outbound.

**How to avoid:** Clarify the requirement direction early. Files Connect = read external files in Salesforce. Outbound file push requires a custom Apex callout, MuleSoft integration, or Industries CLM External Document Management (EDM). Do not conflate "connect" with "sync."

---

## Gotcha 6: Querying ContentVersion VersionData in Bulk Hits Heap Limits

**What happens:** A `System.LimitException: Apex heap size too large` error occurs when a SOQL query retrieves VersionData (the file binary) for multiple ContentVersion records simultaneously.

**When it occurs:** Batch Apex or trigger logic queries multiple ContentVersion records with `SELECT Id, VersionData FROM ContentVersion WHERE ...` and iterates over the results. Each VersionData blob consumes heap memory. Even a few multi-MB files exceed the 6 MB synchronous or 12 MB async heap limit.

**How to avoid:** Query ContentVersion records without VersionData first. Process files one at a time in a Queueable chain or Batch Apex with batch size 1. When using batch Apex, set the scope size to 1 for jobs that access VersionData.

---

## Gotcha 7: Deleting a ContentDocument Deletes All Versions and All Links

**What happens:** Deleting a ContentDocument record cascades to all ContentVersion records under it and all ContentDocumentLink records pointing to it. Every linked record loses its file reference instantly.

**When it occurs:** An integration or cleanup job deletes ContentDocument records without realizing the cascade scope. Files that were linked to multiple records disappear from all of them simultaneously. There is no partial version delete — it is all or nothing at the ContentDocument level.

**How to avoid:** To remove a file from a specific record without affecting other linked records, delete the `ContentDocumentLink` — not the ContentDocument. Only delete ContentDocument when you truly want to remove the file from the entire org. Consider Recycle Bin implications — deleted ContentDocuments go to the Recycle Bin for 15 days before permanent deletion.
