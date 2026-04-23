---
name: apex-blob-and-content-version
description: "Use when Apex must create, persist, stream, or serve binary files — including uploading from LWC/REST, generating ContentVersion records, chunking large bodies, relating files to records via ContentDocumentLink, and handling the heap/payload limits that trip binary workflows. Triggers: 'ContentVersion VersionData Blob', 'upload file from LWC to Apex', 'large file heap limit Apex', 'ContentDocumentLink sharing'. NOT for generating PDFs (use pdf-generation-patterns); NOT for email attachment parsing (use apex-email-services)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
tags:
  - apex-blob-and-content-version
  - contentversion
  - contentdocumentlink
  - blob-handling
  - heap-limit
triggers:
  - "how do I upload a file from LWC to Apex and attach it to a record"
  - "ContentVersion VersionData heap limit with large files"
  - "create a File in Salesforce and share it to a specific record"
  - "streaming or chunking a large binary payload in Apex"
  - "EncodingUtil.base64Decode from a data URL and store as file"
inputs:
  - "binary source: LWC upload, REST payload, external URL, or generated in-Apex"
  - "target record that should see the file via ContentDocumentLink"
  - "expected file size range and whether the path is sync or async"
outputs:
  - "Apex code creating ContentVersion + ContentDocumentLink correctly"
  - "review findings on heap usage, sharing mistakes, and large-file handling"
  - "chunked-upload design when payloads exceed synchronous limits"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Apex Blob And ContentVersion

Use this skill when Apex is the producer or consumer of binary file data — creating Files (ContentVersion), relating them to records (ContentDocumentLink), or moving Blobs between heap, DML, and callouts. The purpose is to keep the transaction under the heap ceiling, land the file under the right sharing, and avoid silent truncation when payloads are larger than they look.

---

## Before Starting

Gather this context before touching `ContentVersion`, `ContentDocumentLink`, or raw `Blob` DML:

- **Expected file size** — under 3 MB, 3–12 MB, 12 MB+? Synchronous Apex has a 6 MB heap ceiling; async (Queueable, Batch, Future) has 12 MB. ContentVersion itself supports up to 2.1 GB, but you cannot land one through a single synchronous `insert` if the Blob is already in heap.
- **Sharing model for the file** — public to all internal users (`AllUsers`), tied to a record (inferred via ContentDocumentLink), or private to the uploader? The `ShareType` and `Visibility` flags on `ContentDocumentLink` are the control plane, not ContentVersion itself.
- **Round-trip requirements** — does the file need to come back down from Apex unchanged? If so, any intermediate `Blob.toString()` conversion will corrupt non-UTF-8 bytes.
- **Transaction boundary** — DML that inserts ContentVersion counts toward your DML row limit. Chained inserts of 50 large files exhaust heap well before the DML cap.

---

## Core Concepts

### ContentVersion Is The File, ContentDocument Is The Envelope, ContentDocumentLink Is The Share

Every "File" in Salesforce is three linked records:

1. **ContentDocument** — metadata envelope (title, latest version Id, owner).
2. **ContentVersion** — the actual bytes in `VersionData`, plus version metadata (`Title`, `PathOnClient`, `ReasonForChange`).
3. **ContentDocumentLink** — the share: ties a `ContentDocumentId` to a `LinkedEntityId` (record, user, library) with a `ShareType` and `Visibility`.

When you `insert` a ContentVersion with no `ContentDocumentId`, Salesforce **creates** a new ContentDocument and assigns its Id — visible only by querying back after insert. When you set `ContentDocumentId` on a ContentVersion insert, you are adding a new version to an existing file.

### `VersionData` Is The Blob — And It Counts Toward Heap Twice

Setting `cv.VersionData = someBlob` keeps `someBlob` in heap. The DML that inserts `cv` serializes the blob into the request, but the heap entry persists until scope exits. If you loop and insert one ContentVersion per iteration with a 5 MB blob each, heap climbs monotonically — the GC behavior on `Blob` is conservative and rarely releases intermediate blobs before the transaction ends.

Practically: never hold more than one large `Blob` in scope at a time. Build the ContentVersion, insert it, set the local `Blob` reference to `null`, and let heap recover before the next iteration.

### ContentDocumentLink ShareType Controls Access Mode

`ShareType` values: `V` (Viewer), `C` (Collaborator), `I` (Inferred — visibility via the LinkedEntity record). `I` is the correct value for the "users who can see the Case can see the file" pattern; `V` and `C` are explicit grants that bypass record sharing.

`Visibility` on ContentDocumentLink: `AllUsers`, `InternalUsers`. Setting `AllUsers` on a file linked to a Community user record is what makes that file visible to the Experience Cloud community — a common gotcha for developers who link correctly but set Visibility = `InternalUsers` and see empty file lists in the community.

### Base64 Decode Is The LWC → Apex Upload Boundary

When an LWC reads a file via `FileReader` and sends the base64 string to an `@AuraEnabled` Apex method, the payload crosses the Apex Web Service limit at about 6 MB base64 (4.5 MB binary after decode). For larger files, the correct path is `lightning-file-upload`, the Content Create Form, or UI API `/sobjects/ContentVersion` — not a custom `@AuraEnabled` method.

---

## Common Patterns

### Upload From LWC, Land As Record File

**When to use:** LWC posts a base64 string to Apex; Apex persists the file and shares it with the originating record.

**How it works:**

```apex
public with sharing class RecordFileService {
    @AuraEnabled
    public static Id saveFile(Id recordId, String fileName, String base64Body) {
        Blob body = EncodingUtil.base64Decode(base64Body);
        if (body.size() > 4_500_000) {
            throw new AuraHandledException('File exceeds synchronous Apex limit; use lightning-file-upload for larger files.');
        }
        ContentVersion cv = new ContentVersion(
            Title = fileName,
            PathOnClient = fileName,
            VersionData = body,
            FirstPublishLocationId = recordId   // auto-creates ContentDocumentLink
        );
        insert cv;
        return [SELECT ContentDocumentId FROM ContentVersion WHERE Id = :cv.Id].ContentDocumentId;
    }
}
```

**Why not the alternative:** Inserting a separate `ContentDocumentLink` works but requires two DMLs and an extra query. `FirstPublishLocationId` asks the platform to create the link with inferred sharing automatically. If you need `V` or `C`, omit `FirstPublishLocationId` and insert the link explicitly.

### Attach A File Generated In Apex (Report / Export / Rendered PDF)

**When to use:** A Queueable or Batch generates a report or CSV and must attach it to a record.

**How it works:**

```apex
public with sharing class ReportExportQueueable implements Queueable {
    private final Id accountId;
    public ReportExportQueueable(Id accountId) { this.accountId = accountId; }

    public void execute(QueueableContext ctx) {
        Blob csvBody = Blob.valueOf(AccountCsvBuilder.build(accountId));
        ContentVersion cv = new ContentVersion(
            Title = 'Account_Export_' + accountId,
            PathOnClient = 'export.csv',
            VersionData = csvBody
        );
        insert cv;

        Id docId = [SELECT ContentDocumentId FROM ContentVersion WHERE Id = :cv.Id].ContentDocumentId;
        insert new ContentDocumentLink(
            ContentDocumentId = docId,
            LinkedEntityId = accountId,
            ShareType = 'V',
            Visibility = 'AllUsers'
        );
    }
}
```

**Why not the alternative:** Attaching via the legacy `Attachment` object works on paper but lacks version history, preview, and mobile support. ContentVersion is the modern path for every file requirement.

### Stream A Large File From An External System Into A ContentVersion

**When to use:** A nightly Batch job pulls large binaries (PDFs, images) from a partner API and stores them in Salesforce.

**How it works:**

```apex
public with sharing class AssetImportQueueable implements Queueable, Database.AllowsCallouts {
    private final String assetUrl;
    private final Id recordId;

    public AssetImportQueueable(String assetUrl, Id recordId) {
        this.assetUrl = assetUrl;
        this.recordId = recordId;
    }

    public void execute(QueueableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(assetUrl);
        req.setMethod('GET');
        req.setTimeout(120_000);
        HttpResponse res = new Http().send(req);

        if (res.getStatusCode() != 200) {
            throw new CalloutException('Asset fetch failed: ' + res.getStatus());
        }
        Blob body = res.getBodyAsBlob();
        if (body.size() == 0) {
            throw new CalloutException('Empty asset body');
        }

        ContentVersion cv = new ContentVersion(
            Title = assetUrl.substringAfterLast('/'),
            PathOnClient = assetUrl.substringAfterLast('/'),
            VersionData = body,
            FirstPublishLocationId = recordId
        );
        insert cv;
    }
}
```

**Why not the alternative:** Attempting this synchronously from an `@AuraEnabled` method will fail either at the 120-second callout timeout, the 6 MB heap ceiling, or the Apex CPU ceiling for 10+ MB downloads. Queueable with `Database.AllowsCallouts` buys you the async heap limit (12 MB) and the 120-second per-callout timeout.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| LWC upload under 4 MB binary | `@AuraEnabled` method receiving base64 | Fits in sync heap; simplest code |
| LWC upload over 4 MB | `lightning-file-upload` or UI API direct | Bypasses Apex payload limit |
| Apex-generated file attached to a record | ContentVersion with `FirstPublishLocationId` | One insert, auto-links |
| Multiple records need the same file | Insert once, then one ContentDocumentLink per record | Avoid duplicating bytes |
| File must be visible in a community | `ContentDocumentLink.Visibility = 'AllUsers'` | `InternalUsers` hides it from Experience Cloud |
| File must follow the record's share | `ContentDocumentLink.ShareType = 'I'` | Inferred sharing respects record access |
| File generated on a schedule | Queueable with `Database.AllowsCallouts` | 12 MB async heap + callout support |
| Legacy `Attachment` object | Migrate to ContentVersion | No version history, deprecated for new work |

---

## Recommended Workflow

Step-by-step instructions for an AI agent activating this skill:

1. Confirm the **size envelope** — under 4 MB is synchronous-safe; otherwise force async or direct-to-UI-API upload.
2. Decide the **sharing model** — `FirstPublishLocationId` for inferred sharing, or explicit `ContentDocumentLink` with `ShareType` / `Visibility`.
3. Keep **only one Blob** in scope at a time — insert, null the reference, loop.
4. After `insert cv`, **query back** for `ContentDocumentId` if you need to add additional links.
5. Test with a **realistic payload size**; test harnesses that use 10-byte fixtures miss every heap bug.

---

## Review Checklist

- [ ] Every ContentVersion insert sets `Title`, `PathOnClient`, and `VersionData`.
- [ ] Sharing is explicit: `FirstPublishLocationId` OR `ContentDocumentLink` with `ShareType` + `Visibility`.
- [ ] No loop holds more than one large `Blob` in scope at a time.
- [ ] LWC uploads over 4 MB binary are routed to `lightning-file-upload` or UI API, not a custom `@AuraEnabled`.
- [ ] Callout-sourced imports run in a Queueable with `Database.AllowsCallouts`, not sync Apex.
- [ ] Community-facing files use `Visibility = 'AllUsers'`.
- [ ] Base64 encoding is not round-tripped through `Blob.toString()`.
- [ ] Heap usage is tested with realistic file sizes, not trivial fixtures.

---

## Salesforce-Specific Gotchas

1. **`FirstPublishLocationId` is ignored if `ContentDocumentId` is also set** — setting both tells Salesforce to add a new version, not create a new file. The `FirstPublishLocationId` silently drops.
2. **`ContentVersion.VersionData` is blanked on query unless you explicitly select it** — `SELECT Id, Title FROM ContentVersion` returns the row without the bytes. Code that assumes the bytes are there will NullPointerException.
3. **`ContentDocumentLink.Visibility = 'InternalUsers'` hides the file from Experience Cloud users even when they own the linked record** — a common "why can't my community user see the file" misfire.
4. **Base64 encoding inflates payloads by ~33%** — a 6 MB binary becomes ~8 MB base64 over the wire. The LWC → Apex Web Service payload limit is measured on the base64 form.
5. **`insert` on ContentVersion with `FirstPublishLocationId = userId`** files the document to that user's private library, not a shared record — useful when deliberate, confusing when not.
6. **The legacy `Attachment` object still works but cannot coexist cleanly with modern file sharing** — Files promoted to ContentVersion cannot go back to Attachment; the migration is one-way.
7. **`EncodingUtil.base64Decode` on a string that includes header prefix `data:image/png;base64,...` silently returns corrupted bytes** — strip the prefix before decoding.
8. **Sharing a file via ContentDocumentLink requires visibility of the ContentDocument** — a trigger handler running as an unprivileged user can fail to add links it could logically see.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| File upload / save Apex | `@AuraEnabled` or REST method creating ContentVersion + link with correct sharing |
| Async file import class | Queueable / Batch for large files, callouts, or scheduled imports |
| Review findings | List of heap risks, sharing misconfigurations, and legacy `Attachment` uses |

---

## Related Skills

- `apex/pdf-generation-patterns` — use when generating PDFs via Visualforce `renderAs="pdf"` before landing them as files.
- `apex/apex-email-services` — use when the binary source is an inbound email attachment.
- `apex/apex-cpu-and-heap-optimization` — use alongside when the path carries multiple large blobs per transaction.
- `apex/callouts-and-http-integrations` — use when the binary comes from an outbound HTTP GET.
- `apex/apex-encoding-and-crypto` — use alongside when the Blob must be encrypted, signed, or hashed before storage.
