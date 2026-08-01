# LLM Anti-Patterns — LWC File Upload Patterns

Scope: getting bytes from a browser into Salesforce Files from an LWC, and attaching the
result to the right record. Querying and rendering existing files belongs elsewhere; this
file covers the upload path and the limits that decide which tier of it you can use.

## Anti-Pattern 1: Writing an Apex base64 uploader when the base component would do

The most expensive mistake in the domain, because the generated code is plausible and long.
Asked for "file upload in LWC", assistants produce an `<input type="file">`, a `FileReader`,
a base64 string and an `@AuraEnabled` method — reproducing by hand what
`lightning-file-upload` already does, and inheriting a heap ceiling the base component does
not have.

**Wrong** — hand-rolled, and it will fail on any file of consequence:

```javascript
handleFile(event) {
    const file = event.target.files[0];
    const reader = new FileReader();
    reader.onloadend = () => {
        const base64 = reader.result.split(',')[1];   // whole file, one string
        saveFile({ recordId: this.recordId, fileName: file.name, base64Data: base64 });
    };
    reader.readAsDataURL(file);
}
```

**Right** — the base component uploads, links to the record and reports back:

```html
<template>
    <lightning-file-upload
        label="Attach signed contract"
        name="contractUploader"
        accept={acceptedFormats}
        record-id={recordId}
        onuploadfinished={handleUploadFinished}>
    </lightning-file-upload>
</template>
```

```javascript
acceptedFormats = ['.pdf', '.docx'];

handleUploadFinished(event) {
    // uploadedFiles entries carry documentId, name, contentVersionId, contentBodyId
    const files = event.detail.files;
    this.uploadedCount = files.length;
}
```

Reach for the Apex path only when you need something the component does not give you —
uploading with no target record and no `recordId`, custom pre-processing, or a guest-user
flow the component cannot support. "More control" is not a reason on its own.

Source: lightning-file-upload — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-file-upload.html

## Anti-Pattern 2: Quoting a single file-size number from memory

Assistants state a maximum with total confidence and no source, and the number is usually
stale. The documented maximum for `lightning-file-upload` is **10 GB**, but that is not the
number that applies everywhere: in Experience Builder sites the limit is **128 MB** on a
Salesforce-provided `my.site.com` URL and **500 MB** on a custom domain. The 2 GB figure
that appears in a great deal of older material is not the current component documentation.

❌ "The limit is 2 GB" (or 10 GB) asserted flatly for every context.
✅ State the surface with the number. A component embedded in an internal Lightning record
page and the same component embedded in a customer-facing Experience site do not have the
same ceiling, and the site's URL configuration changes it again. Check the component
reference for the current figure rather than repeating one — this is a value Salesforce has
moved.

Source: lightning-file-upload specifications, including the Experience Builder site limits — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-file-upload.html

## Anti-Pattern 3: Ignoring the heap ceiling that forces chunking to exist

When the Apex path is genuinely required, the reason chunked upload exists gets skipped.
Apex total heap is **6 MB synchronous, 12 MB asynchronous**. A base64 string is roughly 4/3
the size of the bytes it encodes, and the request body, the decoded `Blob` and the string
can all be live at once — so the file size that fits is a fraction of the raw heap figure,
not close to it.

❌ Read the whole file, send one base64 string, discover the ceiling in production on the
one document that matters.
✅ Send the file in pieces, appending each to the same `ContentVersion`, so no single
transaction holds the whole payload:

```apex
@AuraEnabled
public static Id appendChunk(Id contentVersionId, String fileName,
                             String base64Chunk, String contentType) {
    if (contentVersionId == null) {
        ContentVersion cv = new ContentVersion(
            Title            = fileName,
            PathOnClient     = fileName,
            VersionData      = EncodingUtil.base64Decode(base64Chunk),
            ContentLocation  = 'S'
        );
        insert cv;
        return cv.Id;
    }
    ContentVersion existing = [
        SELECT Id, VersionData FROM ContentVersion
        WHERE Id = :contentVersionId WITH USER_MODE LIMIT 1
    ];
    // Concatenate as base64 so nothing is decoded twice, then decode once.
    String merged = EncodingUtil.base64Encode(existing.VersionData) + base64Chunk;
    existing.VersionData = EncodingUtil.base64Decode(merged);
    update existing;
    return existing.Id;
}
```

Do not copy a chunk size from a blog post as if it were a documented constant — it is not.
The binding constraint is the heap limit above; size the chunk so the encoded string plus
the decoded blob fits, and confirm it with `Limits.getHeapSize()` against
`Limits.getLimitHeapSize()` rather than by guessing. Note that this append pattern re-reads
the accumulated body each call, so heap grows with total file size — it is a bridge to a
moderate ceiling, not a route to an arbitrarily large file. Past that, the file does not
belong in an Apex transaction at all.

Source: Apex Governor Limits — total heap size 6 MB synchronous / 12 MB asynchronous — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm

## Anti-Pattern 4: Inserting a ContentVersion and calling the file "attached"

A `ContentVersion` with no `ContentDocumentLink` is a file in the uploader's private
library. It exists, the Apex returns an Id, the test passes, and it is invisible on the
record. This is the top support ticket for hand-rolled uploaders and it is silent — nothing
errors.

❌ `insert cv;` then return success.
✅ Requery for the generated `ContentDocumentId` and link it deliberately:

```apex
ContentVersion saved = [
    SELECT ContentDocumentId FROM ContentVersion WHERE Id = :cv.Id LIMIT 1
];
insert new ContentDocumentLink(
    ContentDocumentId = saved.ContentDocumentId,
    LinkedEntityId    = recordId,
    ShareType         = 'V',            // V viewer, C collaborator, I inferred from record
    Visibility        = 'AllUsers'      // or InternalUsers / SharedUsers
);
```

`ShareType` and `Visibility` are the two fields that decide who sees the file, and defaults
are not safe assumptions. `Visibility = 'AllUsers'` on a file linked to a record in an
Experience Cloud site is how internal documents reach external users. Choose both
explicitly, and choose `InternalUsers` unless an external audience is intended. Setting
`FirstPublishLocationId` on the `ContentVersion` at insert creates the link in one step and
is the shorter form when the target record is known up front.

Source: ContentDocumentLink object reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentdocumentlink.htm

## Anti-Pattern 5: Treating the `accept` attribute as validation

`accept` is a file-picker filter. It changes which files the dialog offers; it does not stop
anything. A renamed file passes it, and a request assembled outside the browser never sees
it. Assistants present it as the security control, which is how executables end up in a
Files library labelled `.pdf`.

❌ `accept=".pdf"` as the only check.
✅ Two layers, and the second is the real one. `accept` for usability, then a server-side
check on the actual bytes — the leading magic-number sequence — plus a size cap enforced in
Apex. The extension and the client-supplied MIME type are both attacker-controlled;
`EncodingUtil.base64Decode` gives you the bytes, so inspect the first few and reject on
mismatch before the insert, not after.

## Anti-Pattern 6: Recommending the base component for a guest-user flow

Public-facing intake is where this fails, and it fails after the design is agreed. By
default **guest users can't upload files** and have no access to objects and their related
records; enabling it takes an org preference and sharing configuration, and the component
returns a `ContentVersionId` rather than a `ContentDocumentId` for a guest upload. The
`record-id` approach specifically does not work for guest users under secure guest user
record access.

❌ Promise an unauthenticated upload form built on `record-id` and discover this at UAT.
✅ Treat guest upload as its own design with its own approval, not a configuration detail.
Confirm the org preference, the sharing model and the post-upload association path before
committing, and expect to associate the file yourself from the returned
`ContentVersionId`.

## Anti-Pattern 7: Assuming the component renders everywhere it is placed

`lightning-file-upload` **isn't supported in Lightning Out or standalone apps, and displays
as a disabled input**. It also does not support uploading multiple files at once on Android.
Neither throws — the user simply cannot upload, and the bug arrives as "the button is
greyed out on the site" long after the component was signed off.

❌ Assume a working record page proves the component works on every target.
✅ Check the target container before designing around the component. Where it is
unsupported the fallback is the custom input plus Apex path, with the heap constraint from
anti-pattern 3 applying in full.
