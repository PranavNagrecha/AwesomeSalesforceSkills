---
name: salesforce-files-architecture
description: "Working with Salesforce Files at the data layer — `ContentVersion` (the binary content + version metadata), `ContentDocument` (the parent / shareable handle), `ContentDocumentLink` (the sharing / parent-record join), the 2 GB single-file size limit and the 10 MB feed-attached limit, the deprecated `Attachment` object, the `Document` object (Classic-only), and Files Connect for external file sources. Covers SOQL patterns to enumerate files attached to a record, Apex insert / link patterns, sharing implications of `ShareType` and `Visibility`, and the migration path from the legacy Attachment object. NOT for LWC file upload UI components (see lwc/lwc-file-upload-patterns), NOT for static-resource bundling (see lwc/static-resources)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Reliability
triggers:
  - "contentversion contentdocument contentdocumentlink salesforce files"
  - "attachment object deprecated migrate to files"
  - "salesforce file size limit 2gb attachment 25mb"
  - "files connect google drive box external sharepoint"
  - "soql files attached to record contentdocumentlink"
  - "share type visibility contentdocumentlink"
  - "files vs attachments vs documents salesforce object"
tags:
  - files
  - content-version
  - content-document
  - attachments-legacy
  - files-connect
inputs:
  - "Use case (per-record attachment, library, external file source, large media)"
  - "Whether legacy Attachment data exists and needs migration"
  - "Sharing model required (per-record vs library vs external user access)"
outputs:
  - "ContentVersion / ContentDocument / ContentDocumentLink data-model walkthrough"
  - "SOQL query patterns for record-attached files"
  - "Migration plan from Attachment to Files (if applicable)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Salesforce Files Architecture

Salesforce Files is the modern file-storage primitive on the
platform, replacing the legacy `Attachment` object. The data model
is more flexible than `Attachment` (a single file can be linked to
many records, versioned, and shared via libraries), and it is more
complex (three sObjects participate in every linked-file
relationship). LLMs and inexperienced practitioners frequently
misunderstand which object holds the binary, which holds the parent
link, and how sharing is computed.

This skill is the data-layer walkthrough. It covers the three-object
model, the size limits practitioners hit in production, the
deprecated objects (Attachment, Document) you may inherit, and Files
Connect for external file sources.

## The three-object model

A "file" linked to a record involves three sObjects:

| Object | Holds | Cardinality |
|---|---|---|
| `ContentVersion` | The binary content (`VersionData`), file name, type, and version metadata | One row per version of the file |
| `ContentDocument` | The shareable handle / "file identity" | One row per file (across all versions) |
| `ContentDocumentLink` | The link from the `ContentDocument` to a parent record | Many rows per file (one per linked record) |

The relationship is:

```
ContentVersion (binary + version metadata)
   |
   v
ContentDocument (file identity)  <-- ContentDocumentLink --> Account, Case, Custom__c, etc.
   ^
   ContentVersion v2 (later upload of the same file)
```

When you upload a new file, you insert a `ContentVersion`. The
platform creates the `ContentDocument` automatically. To link the
file to a record, you insert a `ContentDocumentLink` with
`LinkedEntityId = recordId`, `ContentDocumentId = contentDocId`,
and a `ShareType` / `Visibility`.

When you upload a *new version* of an existing file, insert a
`ContentVersion` with `ContentDocumentId` set to the existing file's
`ContentDocument.Id` — the platform appends the version.

## Size limits

- **2 GB** — maximum file size for a single Salesforce File (uploaded
  via UI, REST, or SOAP API; subject to edition / license caveats).
- **38 MB** — maximum size when uploaded via Lightning component
  (`lightning-file-upload`) without chunking; larger needs Apex /
  REST chunked upload.
- **10 MB** — maximum size for a file attached to a Chatter feed
  comment.
- **25 MB** — maximum for the legacy `Attachment.Body` field, one
  reason `Attachment` is deprecated.

These limits are platform constraints; some can be raised via
Salesforce Support, but expect the defaults in any greenfield design.

## Sharing — `ShareType` and `Visibility`

`ContentDocumentLink` carries two fields that determine how a file
is shared:

- `ShareType` — `'V'` (Viewer), `'C'` (Collaborator), `'I'`
  (Inferred / parent-record-driven).
- `Visibility` — `'AllUsers'` (anyone with parent-record access can
  see the file) or `'InternalUsers'` (internal users only;
  Experience Cloud / portal users excluded).

`ShareType = 'I'` (Inferred) is the most common default — it makes
file access mirror the parent record's sharing. `'V'` and `'C'`
override that for explicit grant scenarios.

## Deprecated objects you may inherit

- **`Attachment`** — the legacy object. Body field max 25 MB, no
  versioning, no multi-record link, no library support. New
  development should not use it. Migration path: read each
  Attachment's `Body` blob, insert as `ContentVersion`, link via
  `ContentDocumentLink`, then delete the original Attachment.
- **`Document`** — Salesforce Classic-only object for static org-
  level documents. Replaced by Files / static resources / CMS for
  modern UIs.

## Files Connect

Files Connect lets a Salesforce org browse / link files that live
in external sources (Google Drive, SharePoint, Box, etc.) without
copying them into Salesforce storage. Like External Objects for
files: the file content stays at the source; Salesforce shows a
reference. Auth is via named credential.

## Recommended Workflow

1. **Confirm whether legacy `Attachment` data exists.** Query `SELECT COUNT(Id) FROM Attachment`. If non-zero, plan a migration — the object remains supported but is deprecated for new development.
2. **Choose the right object for the use case.** Per-record file = ContentVersion + ContentDocumentLink. Org-wide library file = ContentVersion in a Library. External file source = Files Connect.
3. **Plan the sharing model.** Most use cases want `ShareType = 'I'` (inferred from parent record). Explicit grants (`'V'` Viewer or `'C'` Collaborator) for cross-record sharing.
4. **Size the file storage budget.** Salesforce Files counts against File Storage allocation, distinct from Data Storage. Check Setup -> System Overview for the org's file storage and forecast against expected upload volumes.
5. **For Apex inserts.** First insert `ContentVersion` with `VersionData = blob`, then query `ContentDocumentId` from the inserted ContentVersion, then insert `ContentDocumentLink` to link to the record. Three-step pattern, not one.
6. **For SOQL "files attached to this record".** Query `ContentDocumentLink WHERE LinkedEntityId = :recordId`, then traverse to `ContentDocument` and (if needed) the latest `ContentVersion`.
7. **Guard against the 2 GB single-file ceiling.** For media / video / large datasets above this, use external storage with Files Connect or another integration and link rather than upload.

## What This Skill Does Not Cover

| Topic | See instead |
|---|---|
| LWC file upload UI components | `lwc/lwc-file-upload-patterns` |
| Static resources for LWC bundling | `lwc/static-resources` |
| Salesforce CMS for marketing content | `experience/salesforce-cms-patterns` |
| Big-file media streaming use cases | App-layer (S3 + signed URLs, etc.) |
