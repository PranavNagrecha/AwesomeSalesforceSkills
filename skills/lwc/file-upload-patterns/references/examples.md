# Examples — LWC File Upload Patterns

## Example 1: Attaching a signed PDF to a Case with no Apex at all

**Context:** A service console component where an agent attaches a signed contract to the
open Case.

**Problem:** The first implementation posted the file to an external bucket and stored a
URL on the Case. That put a second copy of customer documents outside the org's sharing
model, outside its retention policy and outside anything the Files-related list can show —
all to avoid writing an uploader.

**Solution:** The base component, with the target record supplied so the link is created
for you.

```html
<!-- caseContractUpload.html -->
<template>
    <lightning-card title="Signed Contract">
        <div class="slds-var-p-around_medium">
            <lightning-file-upload
                label="Upload signed contract"
                name="contractUploader"
                accept={acceptedFormats}
                record-id={recordId}
                onuploadfinished={handleUploadFinished}>
            </lightning-file-upload>

            <template lwc:if={message}>
                <p class="slds-var-m-top_small">{message}</p>
            </template>
        </div>
    </lightning-card>
</template>
```

```javascript
// caseContractUpload.js
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class CaseContractUpload extends LightningElement {
    @api recordId;                       // the Case the file is linked to
    acceptedFormats = ['.pdf'];          // picker filter only — see anti-pattern 5
    message;

    handleUploadFinished(event) {
        const files = event.detail.files;
        this.message = `${files.length} file(s) attached.`;
        this.dispatchEvent(new ShowToastEvent({
            title: 'Uploaded',
            message: files.map((f) => f.name).join(', '),
            variant: 'success'
        }));
    }
}
```

**Why it works:** supplying `record-id` makes the platform create the
`ContentDocumentLink` — the step hand-rolled uploaders forget, which is why their files are
invisible on the record. The file lands in Salesforce Files, inside the org's sharing and
retention model, and appears in the Files related list without any further work.

**What the component will not do:** UNVERIFIED (2026-09-05) — the container restrictions
usually quoted (unsupported in Lightning Out and standalone apps, rendering as a disabled
input; guest users unable to upload by default) are Lightning Component Library and
help.salesforce.com claims that are not in the grounding corpus. Treat them as the working
assumption and check the target surface before designing around the component. The corpus
does confirm that container support varies for the module this example imports:
`lightning/platformShowToastEvent` "isn't supported in LWR sites"
(`lwc_guide base-components-all L4649`), so the toast above is silently absent on an
Experience Cloud LWR site — use `lightning/toast` there
(`lwc_guide base-components-patterns L4773`).

**On `accept`:** it filters the file picker. It is not validation. Anything that must not
be stored has to be rejected server-side, on the bytes.

---

## Example 2: A large document where the Apex path is genuinely required

**Context:** A legal-review component that must run pre-processing on the upload before the
file is associated with a Matter record, so `lightning-file-upload`'s straight-to-Files
behaviour is not usable.

**Problem:** The first attempt read the whole file with `FileReader`, base64-encoded it and
posted it to one `@AuraEnabled` method. It worked on the developer's 2 MB sample and hit
`System.LimitException: Apex heap size too large` on a real document. Apex total heap is
6 MB synchronous and 12 MB asynchronous (`apexdev L19577`), and Salesforce documents the
base64 conversion as increasing document size by approximately 37 %
(`object_reference L79833`) — so the file size that actually fits is well under the raw heap
number. UNVERIFIED (2026-09-05): the further assumption that the encoded string and the
decoded blob are live simultaneously is an inference about Apex memory behaviour, not a
documented statement.

**Solution:** Send the file in slices, appending each to the same `ContentVersion`, then
link it to the record explicitly once the last slice lands.

```javascript
// chunkedUpload.js — client side
import { LightningElement, api } from 'lwc';
import appendChunk from '@salesforce/apex/FileUploadService.appendChunk';
import linkToRecord from '@salesforce/apex/FileUploadService.linkToRecord';

const CHUNK_BYTES = 512 * 1024;   // sized so encoded chunk + decoded blob clears the heap
                                  // ceiling with margin — verify with Limits.getHeapSize()

export default class ChunkedUpload extends LightningElement {
    @api recordId;
    progress = 0;

    async handleFile(event) {
        const file = event.target.files[0];
        let contentVersionId = null;

        for (let start = 0; start < file.size; start += CHUNK_BYTES) {
            const slice = file.slice(start, start + CHUNK_BYTES);
            const base64Chunk = await this.toBase64(slice);
            contentVersionId = await appendChunk({
                contentVersionId,
                fileName: file.name,
                base64Chunk
            });
            this.progress = Math.round(((start + CHUNK_BYTES) / file.size) * 100);
        }

        // The link is a separate, deliberate decision — not a side effect of the upload.
        await linkToRecord({ contentVersionId, recordId: this.recordId });
        this.progress = 100;
    }

    toBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result.split(',')[1]);
            reader.onerror = () => reject(reader.error);
            reader.readAsDataURL(blob);
        });
    }
}
```

```apex
// FileUploadService.cls — server side
public with sharing class FileUploadService {

    private static final Integer MAX_BYTES = 25 * 1024 * 1024;   // policy cap, enforced here
    private static final String PDF_MAGIC  = '255044462D';       // %PDF- as hex

    @AuraEnabled
    public static Id appendChunk(Id contentVersionId, String fileName, String base64Chunk) {
        Blob chunk = EncodingUtil.base64Decode(base64Chunk);

        if (contentVersionId == null) {
            // Validate the real bytes on the first chunk, never the extension.
            String head = EncodingUtil.convertToHex(chunk).toUpperCase();
            if (!head.startsWith(PDF_MAGIC)) {
                throw new AuraHandledException('Only PDF files are accepted.');
            }
            ContentVersion cv = new ContentVersion(
                Title           = fileName,
                PathOnClient    = fileName,
                VersionData     = chunk,
                ContentLocation = 'S'
            );
            insert cv;
            return cv.Id;
        }

        ContentVersion existing = [
            SELECT Id, VersionData FROM ContentVersion
            WHERE Id = :contentVersionId WITH USER_MODE LIMIT 1
        ];
        String merged = EncodingUtil.base64Encode(existing.VersionData) + base64Chunk;
        Blob mergedBlob = EncodingUtil.base64Decode(merged);
        if (mergedBlob.size() > MAX_BYTES) {
            throw new AuraHandledException('File exceeds the 25 MB limit.');
        }
        existing.VersionData = mergedBlob;
        update existing;
        return existing.Id;
    }

    @AuraEnabled
    public static void linkToRecord(Id contentVersionId, Id recordId) {
        ContentVersion saved = [
            SELECT ContentDocumentId FROM ContentVersion
            WHERE Id = :contentVersionId WITH USER_MODE LIMIT 1
        ];
        insert new ContentDocumentLink(
            ContentDocumentId = saved.ContentDocumentId,
            LinkedEntityId    = recordId,
            ShareType         = 'V',
            Visibility        = 'InternalUsers'   // deliberate: not an external audience
        );
    }
}
```

**Why it works:** no single transaction holds the whole file, so the heap ceiling is never
the thing that decides whether the upload succeeds. Validation is on the decoded bytes of
the first chunk rather than on the filename, and the size cap is enforced server-side where
the client cannot bypass it.

**Where this pattern runs out:** the append re-reads the accumulated body on every call, so
heap consumption grows with the *total* file size, not the chunk size. It buys a much
higher ceiling than the single-request version, not an unlimited one. Past that point the
answer is not a cleverer chunker — it is that the file should not travel through an Apex
transaction at all.

**Why `Visibility` is spelled out:** the two `ContentDocumentLink` fields that decide who
can see the file are `ShareType` and `Visibility`, and neither has a default worth
inheriting. `AllUsers` on a record surfaced in an Experience Cloud site is the documented
route by which an internal document becomes visible externally.


---

## Example 3: Proving the upload actually landed

**Context:** Either bundle above has shipped and someone has to confirm, from the outside,
that a given record really has the file — before the business does it for you.

**Problem:** The reflexive check is to open the record and look at the Files related list.
That answers "is it visible to me", which is not the same question as "is it linked, with the
sharing values we intended". A file linked with `Visibility = AllUsers` looks identical to an
admin and is not identical to a customer.

**Solution:** Query the link, filtered, and read the two fields that decide the audience.

```soql
SELECT LinkedEntityId,
       ContentDocumentId,
       ShareType,
       Visibility,
       ContentDocument.Title,
       ContentDocument.FileExtension,
       ContentDocument.ContentSizeLong,
       ContentDocument.LatestPublishedVersionId
FROM ContentDocumentLink
WHERE LinkedEntityId IN ('<record id 1>', '<record id 2>')
ORDER BY LinkedEntityId
```

| Column | What a healthy row shows | What a defect shows |
|---|---|---|
| row count per `LinkedEntityId` | exactly 1 per intended attachment | 0 rows — the `ContentVersion` was inserted and never linked |
| `ShareType` | `V` for read-only attachment UI | blank, or `C` where nobody chose collaborator access |
| `Visibility` | `InternalUsers` unless an external audience was approved | `AllUsers` on a record surfaced in an Experience Cloud site |
| `ContentSizeLong` | the raw byte count of the picked file | roughly 1.37× that — you stored the base64 text, not the bytes |

**Why the filter is not optional:** from API version 59.0, querying `ContentDocumentLink`
without a filter on `Id`, `LinkedEntityId` or `ContentDocumentId` requires the Query All Files
permission, which itself requires View All Data (`object_reference L77161-L77162`). A
verification query written without the `WHERE` clause works for the admin who wrote it and
fails for everyone who has to run it afterwards.

**Why `ContentSizeLong` and not `ContentSize`:** `ContentSize` covers "documents smaller than
2 GB", and from API version 66.0 Salesforce recommends `ContentSizeLong` "even for documents
smaller than 2 GB" (`object_reference L79260-L79272`).
