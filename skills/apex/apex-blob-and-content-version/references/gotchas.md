# Gotchas — Apex Blob And ContentVersion

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `VersionData` Is Not Returned By Default

**What happens:** A SOQL query `SELECT Id, Title FROM ContentVersion WHERE Id = :cvId` returns the record, but accessing `cv.VersionData` throws `NullPointerException`.

**When it occurs:** Any time you forget to add `VersionData` to the field list. The platform treats it like a large text field and omits it unless requested.

**How to avoid:** Explicitly `SELECT Id, VersionData, Title FROM ContentVersion WHERE Id = :cvId` when you need the bytes. Null-check the field before calling `.toString()` or `.size()`.

---

## Gotcha 2: `FirstPublishLocationId` Is Silently Ignored When `ContentDocumentId` Is Set

**What happens:** A developer adds a new version of an existing file and includes `FirstPublishLocationId` hoping to also share it to another record. The version inserts, but no new link appears.

**When it occurs:** Combining "add new version" (`ContentDocumentId`) with "create first publish location" (`FirstPublishLocationId`) — the platform treats these as exclusive and the latter loses.

**How to avoid:** After inserting the new version, `insert new ContentDocumentLink(...)` explicitly for any additional record you want to share to.

---

## Gotcha 3: `Visibility = 'InternalUsers'` Blocks Community Users

**What happens:** A Case trigger attaches a PDF to a Case. Internal users see the file in the Files related list. Experience Cloud (community) users owning the Case see nothing.

**When it occurs:** Any `ContentDocumentLink` insert without an explicit `Visibility = 'AllUsers'` for community-facing records.

**How to avoid:** For any file that must be visible in an Experience Cloud site, set `Visibility = 'AllUsers'` on the link.

---

## Gotcha 4: Base64 Data URL Prefixes Corrupt The Decode

**What happens:** An LWC uses `FileReader.readAsDataURL`, which returns strings like `data:application/pdf;base64,JVBERi0...`. Passing this directly to `EncodingUtil.base64Decode` returns garbage bytes (the prefix is treated as payload).

**When it occurs:** The developer expects Apex to ignore the prefix (browsers often do).

**How to avoid:** Strip everything up to and including the `,` before decoding:

```apex
String body = fullString.startsWith('data:') ? fullString.substringAfter(',') : fullString;
Blob bytes = EncodingUtil.base64Decode(body);
```

---

## Gotcha 5: Heap Doesn't Release Between Loop Iterations

**What happens:** A Batch processes 200 records, builds a 1 MB ContentVersion per record in heap, and hits the 12 MB heap ceiling around record #11 even though `execute` loops once per batch.

**When it occurs:** Any loop that holds `Blob` references across iterations; GC is conservative on `Blob` and doesn't reclaim until scope exits.

**How to avoid:** Null the Blob reference after adding the ContentVersion to the insert list. Alternatively, insert in smaller sub-batches (50 at a time) and let the list reset.

---

## Gotcha 6: `ContentVersion.ContentLocation = 'E'` For Direct-URL Files

**What happens:** A team tries to create a "file" that is really just a URL reference (like a YouTube link). They set `PathOnClient` and `Title` and expect a clickable link in the Files related list; instead the insert fails with `FIELD_INTEGRITY_EXCEPTION`.

**When it occurs:** External URL references must be created with `ContentLocation = 'L'` (social link) and `ContentUrl` populated — not `VersionData`.

**How to avoid:** If the intent is a URL reference, use `ContentLocation = 'L'` with `ContentUrl` set. If the intent is a real file, omit `ContentLocation` (defaults to `'S'` for Salesforce-hosted).

---

## Gotcha 7: `insert` On ContentVersion Without `FirstPublishLocationId` Files To The User's Private Library

**What happens:** A developer creates a ContentVersion with just `Title`, `PathOnClient`, and `VersionData`, intending it to live on a Case. The file is created but only visible to the inserting user.

**When it occurs:** Any insert that omits both `FirstPublishLocationId` and a subsequent `ContentDocumentLink`.

**How to avoid:** Always set `FirstPublishLocationId` or insert a link immediately after. If the file is meant to be private, document why.

---

## Gotcha 8: Attachment And ContentDocument Are Not Interchangeable

**What happens:** A team inherits a codebase that uses `Attachment` for some files and ContentVersion for others. A reporting query that tries to union both surfaces by `ParentId` / `LinkedEntityId` returns inconsistent results.

**When it occurs:** Mixed-era orgs where legacy automation still writes `Attachment` records while modern features produce ContentVersion.

**How to avoid:** Migrate `Attachment` data to `ContentVersion` + `ContentDocumentLink` with a one-time job; retire the `Attachment` usage at the code level. The two objects have different sharing, version, and preview behavior.
