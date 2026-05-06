# Examples — Salesforce Files Architecture

## Example 1 — Three-step Apex insert: upload + link

**Context.** Apex receives a base64 file payload from a custom
endpoint and needs to attach it to a Case.

**Code.**

```apex
public static Id attachFileToCase(Id caseId, String fileName, Blob body) {
    // Step 1: insert the binary content (auto-creates ContentDocument).
    ContentVersion cv = new ContentVersion(
        Title = fileName,
        PathOnClient = fileName,
        VersionData = body,
        FirstPublishLocationId = caseId  // shortcut: links via ContentDocumentLink for us
    );
    insert cv;

    // Step 2: query back the ContentDocumentId.
    ContentVersion saved = [
        SELECT ContentDocumentId FROM ContentVersion WHERE Id = :cv.Id
    ];
    return saved.ContentDocumentId;
}
```

`FirstPublishLocationId` is the shortcut — set it on the
ContentVersion insert and the platform creates the
`ContentDocumentLink` for you. Without it, you'd insert
ContentVersion first, then explicitly insert ContentDocumentLink in
a second step.

---

## Example 2 — Linking an existing file to a second record

**Context.** A file was uploaded against an Opportunity. Now needs
to also appear on the Account.

**Code.**

```apex
public static void linkFileToRecord(Id contentDocumentId, Id recordId) {
    ContentDocumentLink cdl = new ContentDocumentLink(
        ContentDocumentId = contentDocumentId,
        LinkedEntityId = recordId,
        ShareType = 'V',           // Viewer
        Visibility = 'AllUsers'    // Community / portal users included
    );
    insert cdl;
}
```

`ShareType = 'V'` because we're explicitly granting view access on
this second link. The Opportunity's link can stay as `'I'` (inferred
from the parent record's sharing).

---

## Example 3 — Listing files attached to a record

**Context.** Lightning Component / Apex controller needs to render
the file list for a record.

**Code.**

```apex
public static List<ContentVersion> getLatestVersionsForRecord(Id recordId) {
    Set<Id> docIds = new Set<Id>();
    for (ContentDocumentLink cdl : [
        SELECT ContentDocumentId
        FROM ContentDocumentLink
        WHERE LinkedEntityId = :recordId
    ]) {
        docIds.add(cdl.ContentDocumentId);
    }

    return [
        SELECT Id, Title, FileType, ContentSize,
               ContentDocumentId, VersionData
        FROM ContentVersion
        WHERE ContentDocumentId IN :docIds
          AND IsLatest = true
    ];
}
```

Note the `IsLatest = true` filter — without it you get every
version. Note also that `ContentDocumentLink` is the only object
queryable directly by parent record; you cannot SOQL-filter
`ContentDocument` by `ParentId` (there is no such field).

---

## Example 4 — Migrating Attachment to Files

**Context.** Org has 1.2 M legacy `Attachment` rows. Plan: migrate
to ContentVersion / ContentDocumentLink and retire `Attachment`.

**Pattern.**

```apex
public class AttachmentMigrator implements Database.Batchable<sObject> {
    public Database.QueryLocator start(Database.BatchableContext ctx) {
        return Database.getQueryLocator(
            'SELECT Id, ParentId, Name, Body, ContentType FROM Attachment'
        );
    }

    public void execute(Database.BatchableContext ctx, List<Attachment> rows) {
        List<ContentVersion> versions = new List<ContentVersion>();
        for (Attachment a : rows) {
            versions.add(new ContentVersion(
                Title = a.Name,
                PathOnClient = a.Name,
                VersionData = a.Body,
                FirstPublishLocationId = a.ParentId
            ));
        }
        insert versions;
        // Delete originals only after verifying the migration.
    }

    public void finish(Database.BatchableContext ctx) {}
}
```

Caveats:

- 25 MB max per Attachment — fits in a single ContentVersion (which
  allows up to 2 GB).
- Heap usage: each batch loads `Body` blobs into memory; tune batch
  size accordingly. Default batch of 200 with average 5 MB per
  Attachment = 1 GB heap which exceeds the per-execution limit (12
  MB sync, 36 MB async). Use a small batch size for blob-heavy data.
- Validate end-to-end before deleting Attachments.

---

## Example 5 — Visibility = InternalUsers vs AllUsers

**Context.** Experience Cloud (community) site with portal users.
Files attached to a Case should be visible to the customer; files
attached to an internal Knowledge article should not.

**Configuration.**

| ContentDocumentLink | ShareType | Visibility | Result |
|---|---|---|---|
| Customer-visible Case file | `'I'` | `'AllUsers'` | Portal users with Case access can see |
| Internal-only Knowledge file | `'I'` | `'InternalUsers'` | Portal users cannot see, even with parent access |

`Visibility = 'InternalUsers'` is the safety lever. Default to it
for any file linked to a record that may be shared with portal /
guest users until explicitly authorized otherwise.

---

## Example 6 — File size limits in practice

| Upload path | Practical limit | Note |
|---|---|---|
| Lightning UI drag-drop | 2 GB | Subject to edition / license |
| `lightning-file-upload` LWC | 38 MB | Larger needs custom chunked upload |
| Apex `ContentVersion.VersionData` | 2 GB | Heap limits constrain batch operations |
| REST API `multipart/form-data` | 2 GB | Recommended for files > 38 MB |
| Chatter feed comment | 10 MB | Distinct path |
| Legacy Attachment | 25 MB | Object deprecated for new development |
