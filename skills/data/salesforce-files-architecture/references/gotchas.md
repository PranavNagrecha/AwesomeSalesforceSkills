# Gotchas — Salesforce Files Architecture

Real-world surprises that bite practitioners working with the
ContentVersion / ContentDocument / ContentDocumentLink trio.

---

## Gotcha 1: ContentDocument has no `ParentId` field

**What happens.** Engineer writes `SELECT Id FROM ContentDocument
WHERE ParentId = :recordId`. The query fails — `ParentId` does not
exist on `ContentDocument`.

**When it occurs.** Mirroring intuition from `Attachment`, which
does have a `ParentId`.

**How to avoid.** Always join via `ContentDocumentLink`. The link
object is the only path from a parent record to its files.

---

## Gotcha 2: Inserting `ContentVersion` auto-creates `ContentDocument`

**What happens.** Engineer inserts a `ContentDocument` first
(expecting to chain), gets a confused error or duplicate parent.

**When it occurs.** First-time use of the API.

**How to avoid.** Insert `ContentVersion` first; the platform
creates `ContentDocument` for you. To upload a *new version* of an
existing document, set `ContentDocumentId` on the new
`ContentVersion`.

---

## Gotcha 3: `IsLatest = true` filter required to avoid duplicates

**What happens.** Query `SELECT Id FROM ContentVersion WHERE
ContentDocumentId IN :ids` returns N rows per file (one per
version). UI renders duplicates.

**When it occurs.** Naive enumerations that forget the version
dimension.

**How to avoid.** Filter `IsLatest = true` for the "current" view.
Omit it for a version-history view.

---

## Gotcha 4: `lightning-file-upload` 38 MB ceiling

**What happens.** User tries to upload a 100 MB file via the
out-of-the-box `lightning-file-upload`; it fails silently or with a
size error.

**When it occurs.** Files larger than the LWC component's documented
ceiling.

**How to avoid.** For larger files, implement chunked upload via
Apex / REST. Alternatively, use external storage with Files
Connect.

---

## Gotcha 5: Heap limits constrain bulk file operations in Apex

**What happens.** Batch class loading `VersionData` for many files
hits a heap-limit governor. Per-execution heap is 12 MB sync, 36 MB
async.

**When it occurs.** Migration jobs, file export jobs, Apex that
processes file content in bulk.

**How to avoid.** Use small batch sizes (1–5 records per execution)
when `VersionData` is loaded. Stream content where possible
(`HttpRequest.setBodyAsBlob`) instead of materializing the whole
blob.

---

## Gotcha 6: `Visibility = 'AllUsers'` exposes file to community / portal users

**What happens.** A file attached to a Case is visible in the
customer-facing community without explicit consent because the
default `ContentDocumentLink.Visibility` was `'AllUsers'`.

**When it occurs.** Apex / API inserts that omit `Visibility` (or
let it default).

**How to avoid.** Set `Visibility` explicitly on every
`ContentDocumentLink` insert. Default to `'InternalUsers'` for
internal-only contexts.

---

## Gotcha 7: `ContentDocumentLink` insert without `ShareType` fails on deploy

**What happens.** Apex insert of `ContentDocumentLink` without
`ShareType` produces an "Insufficient access" or required-field
error in some contexts.

**When it occurs.** Quick scripts / examples that omit `ShareType`.

**How to avoid.** Always set `ShareType` explicitly. `'I'` (Inferred)
is the most common; `'V'` (Viewer) and `'C'` (Collaborator) for
explicit grants.

---

## Gotcha 8: File storage allocation is separate from data storage

**What happens.** Org runs out of file storage even though data
storage is well below allocation. Uploads start failing.

**When it occurs.** Any file-heavy use case (engineering drawings,
recordings, contracts).

**How to avoid.** Monitor file storage in Setup -> System Overview
distinct from data storage. Forecast file storage growth from
expected upload volume * average file size.

---

## Gotcha 9: Restoring a deleted file reassigns the `ContentDocumentId`

**What happens.** A `ContentDocument` is deleted (cascading the
versions), then restored from Recycle Bin. The restored document
gets a different `Id`, breaking any external references that
captured the original Id.

**When it occurs.** Any "delete then undelete" workflow on Files.

**How to avoid.** Treat the `ContentDocument.Id` as not-restorable.
For cross-system references, store a stable external reference
(custom external Id field on a related record) rather than the
Salesforce Id.
