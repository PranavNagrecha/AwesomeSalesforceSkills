# LLM Anti-Patterns — Apex Blob And ContentVersion

Common mistakes AI coding assistants make when generating or reviewing Apex code that creates, persists, or serves binary files.

## Anti-Pattern 1: Inserting ContentVersion Without A Sharing Target

**What the LLM generates:**

```apex
@AuraEnabled
public static Id uploadFile(String fileName, String base64Body) {
    ContentVersion cv = new ContentVersion(
        Title = fileName,
        PathOnClient = fileName,
        VersionData = EncodingUtil.base64Decode(base64Body)
    );
    insert cv;
    return cv.Id;
}
```

**Why it happens:** Tutorials show the minimal ContentVersion insert. LLMs miss that the file lands in the uploader's private library, not on any record.

**Correct pattern:** Pass the record Id and set `FirstPublishLocationId`:

```apex
ContentVersion cv = new ContentVersion(
    Title = fileName, PathOnClient = fileName,
    VersionData = EncodingUtil.base64Decode(base64Body),
    FirstPublishLocationId = recordId
);
insert cv;
```

**Detection hint:** `new ContentVersion(` insert without `FirstPublishLocationId` and without a subsequent `ContentDocumentLink` insert in the same method.

---

## Anti-Pattern 2: Setting Both `ContentDocumentId` And `FirstPublishLocationId`

**What the LLM generates:**

```apex
ContentVersion cv = new ContentVersion(
    ContentDocumentId = existingDocId,
    FirstPublishLocationId = accountId,
    VersionData = body,
    Title = 'v2'
);
insert cv;
```

**Why it happens:** LLMs combine the "add new version" and "share to record" knobs assuming additive behavior.

**Correct pattern:** Use each for one purpose — add a separate `ContentDocumentLink` for additional sharing.

**Detection hint:** `ContentVersion` constructor that sets both `ContentDocumentId` and `FirstPublishLocationId`.

---

## Anti-Pattern 3: Looping With Large Blobs Held In Scope

**What the LLM generates:**

```apex
List<ContentVersion> versions = new List<ContentVersion>();
for (Account a : scope) {
    Blob body = AccountExporter.buildPdf(a.Id);
    versions.add(new ContentVersion(Title=a.Name, VersionData=body, PathOnClient='x.pdf'));
}
insert versions;
```

**Why it happens:** LLMs default to "build then bulk insert." For textual records this is correct; for large Blobs it exhausts heap.

**Correct pattern:** Null intermediate Blob references or use smaller sub-batches:

```apex
for (Account a : scope) {
    Blob body = AccountExporter.buildPdf(a.Id);
    versions.add(new ContentVersion(Title=a.Name, VersionData=body, PathOnClient='x.pdf'));
    body = null;
}
insert versions;
```

**Detection hint:** A `for` loop that creates a `Blob` variable each iteration and does not null it before the next iteration.

---

## Anti-Pattern 4: Not Stripping The `data:...;base64,` Prefix

**What the LLM generates:**

```apex
Blob body = EncodingUtil.base64Decode(dataUrlString);
```

**Why it happens:** LLMs treat any string ending in base64 data as decodable; they don't notice the `data:application/pdf;base64,` prefix from browser `FileReader.readAsDataURL`.

**Correct pattern:**

```apex
String clean = dataUrlString.startsWith('data:')
    ? dataUrlString.substringAfter(',') : dataUrlString;
Blob body = EncodingUtil.base64Decode(clean);
```

**Detection hint:** `EncodingUtil.base64Decode` called on a variable whose value originates from an LWC / client-side source without an intermediate substring.

---

## Anti-Pattern 5: Selecting ContentVersion Without `VersionData`

**What the LLM generates:**

```apex
ContentVersion cv = [SELECT Id, Title FROM ContentVersion WHERE Id = :cvId];
Blob body = cv.VersionData;  // null — not queried
```

**Why it happens:** LLMs treat SOQL field selection as exhaustive by default; they don't know `VersionData` is an excluded-by-default large-blob field.

**Correct pattern:** Explicitly include `VersionData` in the field list.

**Detection hint:** `SELECT` from ContentVersion without `VersionData` followed by code that reads `cv.VersionData` or calls a method on it.

---

## Anti-Pattern 6: Uploading Via `@AuraEnabled` When It Should Be `lightning-file-upload`

**What the LLM generates:** A custom `@AuraEnabled` method that accepts base64 payloads of arbitrary size from LWC.

**Why it happens:** LLMs default to imperative Apex calls; they don't know the payload hits the Aura Web Service body limit around 4–6 MB.

**Correct pattern:** Route the LWC to `lightning-file-upload` (which uploads directly to ContentVersion via REST), or provide a pre-signed URL via UI API. Use `@AuraEnabled` only for metadata or small thumbnails.

**Detection hint:** `@AuraEnabled` method signature `(Id recordId, String fileName, String base64Body)` with no size gate.

---

## Anti-Pattern 7: Using `Attachment` For New Features

**What the LLM generates:**

```apex
insert new Attachment(ParentId = caseId, Name = 'report.pdf', Body = pdfBlob);
```

**Why it happens:** Older tutorials still show `Attachment`. LLMs reach for the familiar API.

**Correct pattern:** Use ContentVersion + ContentDocumentLink. `Attachment` has no version history, no preview, no mobile support.

**Detection hint:** `new Attachment(` in any new Apex code.
