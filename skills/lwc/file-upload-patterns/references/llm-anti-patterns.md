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

Source: the LWC Developer Guide routes this case itself — `lightning-file-upload` is "a file
selector for uploading a file that's associated with a record ID. To upload a file without a
record ID, use `lightning-input` with `type="file"` instead." (`lwc_guide base-components-all L4603`).
Attribute-level detail: lightning-file-upload component reference —
https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-file-upload.html
UNVERIFIED (2026-09-05): that component reference is not in the grounding corpus, so the
`uploadedFiles` payload fields named above (documentId, name, contentVersionId, contentBodyId)
are unconfirmed — log `event.detail` once in a scratch org before depending on a field name.

## Anti-Pattern 2: Quoting a single file-size number from memory

Assistants state a maximum with total confidence and no source, and the number is usually
stale. Three different ceilings get confused for each other: the component's own per-file
limit, the API upload limit, and the storage limit on the object.

UNVERIFIED (2026-09-05): the frequently quoted `lightning-file-upload` figures — a **10 GB**
maximum, **128 MB** in an Experience Builder site on a Salesforce-provided `my.site.com` URL
and **500 MB** on a custom domain — come from the Lightning Component Library, which is not in
the grounding corpus for this package. They are recorded here because they are the numbers
teams cite, not because they were confirmed.

What *is* confirmed: "the maximum file size you can upload via the SOAP API is 50 MB… this
conversion increases the document size by approximately 37%. Account for the base64 conversion
increase so that the file you plan to upload is less than 50 MB after conversion."
(`object_reference L79771-L79774`). And on the storage side, `ContentVersion.ContentSize` is
"the size of the document in bytes for documents smaller than 2 GB", superseded from API 66.0
by `ContentSizeLong`, which covers "up to 10 GB" (`object_reference L79260-L79272`) — which is
where the 2 GB figure in older material actually comes from.

❌ "The limit is 2 GB" (or 10 GB) asserted flatly for every context.
✅ State the surface with the number. A component embedded in an internal Lightning record
page and the same component embedded in a customer-facing Experience site do not have the
same ceiling, and the site's URL configuration changes it again. Check the component
reference for the current figure rather than repeating one — this is a value Salesforce has
moved.

Sources: ContentVersion object reference, `VersionData` and `ContentSize` / `ContentSizeLong`
(`object_reference L79260-L79272`, `L79771-L79774`) —
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf ;
component-level figures: lightning-file-upload specifications —
https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-file-upload.html

## Anti-Pattern 3: Ignoring the heap ceiling that forces chunking to exist

When the Apex path is genuinely required, the reason chunked upload exists gets skipped.
Apex total heap is **6 MB synchronous, 12 MB asynchronous** (`apexdev L19577`), and an
`@AuraEnabled` call from an LWC runs in the synchronous bucket. Salesforce documents the
base64 conversion as increasing document size **by approximately 37%**
(`object_reference L79833`) — not the 33 % the 4/3 arithmetic suggests. The request body, the
decoded `Blob` and the string
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

Sources: Apex Developer Guide, Execution Governors and Limits — total heap size 6 MB
synchronous / 12 MB asynchronous (`apexdev L19577`) —
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf ;
ContentVersion `VersionData`, ~37 % base64 increase (`object_reference L79833`).
UNVERIFIED (2026-09-05): whether the encoded String and the decoded Blob are simultaneously
resident on the heap is an inference about Apex memory management, not a documented statement.
It is the conservative reading; measure with `Limits.getHeapSize()` before raising a cap.

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

Sources: ContentDocumentLink object reference — `ShareType` is Required and `C` cannot be
created from an Apex trigger (`object_reference L77269`, `L77276-L77277`); `Visibility` values
and the external-user restriction (`object_reference L77302-L77317`); `ContentVersion`
`FirstPublishLocationId` single-transaction sharing (`object_reference L79403-L79405`) —
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf

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

Public-facing intake is where this fails, and it fails after the design is agreed.

UNVERIFIED (2026-09-05): the specifics normally quoted here — that **guest users can't upload
files** by default, that enabling it takes an org preference plus sharing configuration, that
the component returns a `ContentVersionId` rather than a `ContentDocumentId` for a guest
upload, and that the `record-id` approach does not work under secure guest user record access
— are help.salesforce.com and Component Library claims, and help.salesforce.com is not
fetchable. They are recorded as the working assumption, not as confirmed behaviour.

What the corpus does confirm is the same asymmetry on the read side: "authenticated users can
download files they have access to. Guest users can download only `ContentDocument` files that
they have access to through Library membership."
(`lwc_guide reference-wire-adapters-generate-url L17173`). And access to the Apex fallback is
itself gated: an `@AuraEnabled` method is reachable by a guest user "only when the user's
profile or an assigned permission set allows access to the Apex class"
(`lwc_guide apex-security L7436`).

❌ Promise an unauthenticated upload form built on `record-id` and discover this at UAT.
✅ Treat guest upload as its own design with its own approval, not a configuration detail.
Confirm the org preference, the sharing model and the post-upload association path before
committing, and expect to associate the file yourself from the returned
`ContentVersionId`.

## Anti-Pattern 7: Assuming the component renders everywhere it is placed

UNVERIFIED (2026-09-05): the specific claims that `lightning-file-upload` **isn't supported in
Lightning Out or standalone apps and displays as a disabled input**, and that it does not
support uploading multiple files at once on Android, are Lightning Component Library claims
outside the grounding corpus.

The general failure mode is confirmed for a neighbouring module, which is why it is worth
checking rather than assuming: `lightning/platformShowToastEvent` "uses an event-based
mechanism to display a toast, and it's not supported in environments like LWR sites for
Experience Cloud or standalone apps." (`lwc_guide base-components-patterns L4773`). Neither
case throws — the user simply gets nothing, and the bug arrives as "the button is greyed out
on the site" long after the component was signed off.

❌ Assume a working record page proves the component works on every target.
✅ Check the target container before designing around the component. Where it is
unsupported the fallback is the custom input plus Apex path, with the heap constraint from
anti-pattern 3 applying in full.


## Anti-Pattern 8: Marking the upload method `cacheable=true`

An easy reflex, because most `@AuraEnabled` samples an assistant has seen are cacheable
readers, and because `cacheable=true` is what `@wire` requires. Applied to an upload it is
wrong in a way that produces intermittent, unreproducible bugs: the second identical upload
returns the cached result of the first without touching the server.

The rule is explicit: "To improve runtime performance, annotate the Apex method with
`@AuraEnabled(cacheable=true)`, which caches the method results on the client. **To set
`cacheable=true`, a method must only get data, it can't mutate (change) data.**"
(`lwc_guide apex-result-caching L7254`). And imperative invocation exists precisely for this
case — you call a method imperatively "to call a method that isn't annotated with
`cacheable=true`, which includes any method that inserts, updates, or deletes data."
(`lwc_guide apex-call-imperative L7190`).

❌ `@AuraEnabled(cacheable=true) public static Id uploadFile(...)`
✅ `@AuraEnabled public static UploadResult uploadFile(...)`, imported and awaited imperatively.

`scripts/check_file_upload_patterns.py` rule R4 fails the build on this.

Source: LWC Developer Guide, Use Apex Method Result Caching (`lwc_guide apex-result-caching L7254-L7256`)
and Call Apex Methods Imperatively (`lwc_guide apex-call-imperative L7190`) —
https://developer.salesforce.com/docs/platform/lwc/guide/apex-result-caching.html

## Anti-Pattern 9: Confirming success with an unfiltered ContentDocumentLink query

The generated verification step is almost always `SELECT Id FROM ContentDocumentLink` or a
`SELECT Id FROM ContentDocument` with no filter, and it either errors or quietly returns a
subset that makes a working upload look broken.

"In API versions 59.0 and later, turn on the Query All Files permission to query without a
filter on id, LinkedEntityId, and documentID fields. The View All Data permission is required
to turn on Query All Files." (`object_reference L77161-L77162`). The same shape applies one
object over: "depending on how files are shared, queries on `ContentDocument` and
`ContentVersion` without specifying an ID don't return all files a user has access to"
(`object_reference L79117-L79119`), and for a record-shared file "either the
`ContentVersionId` or the `ContentDocumentId` must be compounded by an `AND` operator"
(`object_reference L79850-L79852`).

❌ `SELECT Id, Title FROM ContentDocument` to prove the upload landed.
✅ Filter on the thing you actually created:

```soql
SELECT ContentDocumentId, ShareType, Visibility, ContentDocument.Title
FROM ContentDocumentLink
WHERE LinkedEntityId = '<the record id>'
```

Source: ContentDocumentLink and ContentVersion object references, Special Access Rules and
Usage (`object_reference L77161-L77162`, `L79117-L79119`, `L79850-L79852`) —
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
