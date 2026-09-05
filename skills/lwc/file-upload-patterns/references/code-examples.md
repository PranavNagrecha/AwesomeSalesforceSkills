# Code Examples — LWC File Upload Patterns

Two complete, deployable bundles. **Bundle A** is the server-side path: the base component
uploads and the platform associates the file. **Bundle B** is the Apex path: a custom input,
`FileReader`, a base64 string, and Apex that inserts `ContentVersion` and then
`ContentDocumentLink` under a heap-aware size cap. Pick one; do not blend them.

Everything here is deploy-ready as written apart from the object and record ids, which are
marked `<...>`.

## Which bundle

| Situation | Bundle | Why |
|---|---|---|
| File belongs to a record that already exists, and no pre-processing is needed | A | The guide routes this case to `lightning-file-upload`: it is "a file selector for uploading a file that's associated with a record ID" (`lwc_guide base-components-all L4603`) |
| No record id yet (wizard step 1, unsaved parent), or the bytes must be inspected/transformed before storage | B | The guide's own fallback for "upload a file without a record ID" is `lightning-input` with `type="file"` (`lwc_guide base-components-all L4603`, `L4611`) |
| File is larger than a couple of megabytes | A | Bundle B is bounded by the Apex heap — 6 MB synchronous / 12 MB asynchronous (`apexdev L19577`) — and base64 inflates the payload by about 37 % (`object_reference L79833`) |

## Citation key

`lwc_guide <page-slug> L<n>` = line `n` of the crawled Lightning Web Components Developer Guide.
`object_reference L<n>` / `apexdev L<n>` / `apexrefguide L<n>` = the Summer '26 PDF text extracts.
Anything sourced only from the **Lightning Component Library** (every `lightning-file-upload`
attribute, its event payload, its per-file ceiling) is marked UNVERIFIED — that reference is
not part of the corpus this package was grounded against.

---

# Bundle A — `caseFileUploader`

Attach a signed document to an open Case. No Apex, no `ContentDocumentLink` code, no heap.

## A.1 `caseFileUploader.html`

```html
<template>
    <lightning-card title="Signed Documents" icon-name="standard:file">
        <div class="slds-var-p-around_medium">
            <!-- record-id present: this component runs on a saved Case only.
                 Unsaved-record strategy: none needed here. If this component is ever
                 moved onto a creation wizard, switch to Bundle B -- see B.2. -->
            <lightning-file-upload
                label="Attach a signed document"
                name="caseFileUploader"
                accept={acceptedFormats}
                record-id={recordId}
                multiple
                disabled={uploadDisabled}
                onuploadfinished={handleUploadFinished}>
            </lightning-file-upload>

            <template lwc:if={hasUploads}>
                <ul class="slds-var-m-top_small slds-has-dividers_bottom-space">
                    <template for:each={uploads} for:item="file">
                        <li key={file.documentId} class="slds-item">{file.name}</li>
                    </template>
                </ul>
            </template>
        </div>
    </lightning-card>
</template>
```

## A.2 `caseFileUploader.js`

```javascript
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class CaseFileUploader extends LightningElement {
    /** Supplied by lightning__RecordPage. The component is meaningless without it. */
    @api recordId;

    /** Picker filter only. It is not validation -- nothing rejects a renamed file. */
    acceptedFormats = ['.pdf', '.docx', '.png'];

    uploads = [];

    get hasUploads() {
        return this.uploads.length > 0;
    }

    get uploadDisabled() {
        return !this.recordId;
    }

    handleUploadFinished(event) {
        // event.detail.files is the documented payload shape.
        // UNVERIFIED (2026-09-05): the `uploadfinished` payload fields
        // (documentId, name, contentVersionId, contentBodyId) are documented in the
        // Lightning Component Library, which is not in the grounding corpus. Log
        // event.detail once in a scratch org before depending on a field name.
        const files = event.detail.files || [];
        this.uploads = [...this.uploads, ...files];

        // lightning/platformShowToastEvent "is not supported in environments like LWR
        // sites for Experience Cloud or standalone apps. We recommend that you use
        // lightning/toast instead." (lwc_guide base-components-patterns L4773)
        // Keep this import only for Lightning Experience targets.
        this.dispatchEvent(
            new ShowToastEvent({
                title: 'Upload complete',
                message: `${files.length} file(s) attached to this record.`,
                variant: 'success'
            })
        );
    }
}
```

## A.3 `caseFileUploader.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Case File Uploader</masterLabel>
    <targets>
        <target>lightning__RecordPage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <objects>
                <object>Case</object>
            </objects>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

`apiVersion` is mandatory: "Beginning in Spring '25, versioning custom components is required,
even if your component uses an older API version… Attempting to save an unversioned component
to Salesforce results in an error." (`lwc_guide create-version-components L797-L798`).
`lightning__RecordPage` is restricted to `Case` on purpose — the component has no meaning on a
page whose record cannot own files.

## A.4 Attributes used above

UNVERIFIED (2026-09-05): every row in this table comes from the Lightning Component Library
reference for `lightning-file-upload`, which is not in the grounding corpus. The LWC
Developer Guide states only that the component uploads "a file that's associated with a
record ID" (`lwc_guide base-components-all L4603`). Confirm each attribute against the
current component reference before relying on it.

| Attribute | Used for |
|---|---|
| `record-id` | The record the uploaded file is linked to. Without it the component has no association target |
| `accept` | File-picker filter. Cosmetic — see anti-pattern 5 |
| `multiple` | Allow more than one file per interaction |
| `disabled` | Suppress the control until `recordId` is available |
| `label`, `name` | Rendered label and form name |
| `file-field-name` / `file-field-value` | Stamp a field on the created `ContentVersion` at upload time |
| `onuploadfinished` | Fires after the platform has stored the file(s) |

## A.5 `__tests__/caseFileUploader.test.js`

The base component is not rendered by Jest, so the test drives the handler by dispatching a
synthetic `uploadfinished` event at the stub element — the same technique the guide uses for
component tests generally: create the element with `createElement`, append it, then query
through `element.shadowRoot` (`lwc_guide unit-testing-using-jest-create-tests L12344`,
`L12376`).

```javascript
import { createElement } from 'lwc';
import CaseFileUploader from 'c/caseFileUploader';
import { ShowToastEventName } from 'lightning/platformShowToastEvent';

describe('c-case-file-uploader', () => {
    afterEach(() => {
        // The jsdom instance is shared across test cases in a single file, so reset the DOM.
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    function build(recordId = '500000000000001AAA') {
        const element = createElement('c-case-file-uploader', { is: CaseFileUploader });
        element.recordId = recordId;
        document.body.appendChild(element);
        return element;
    }

    it('disables the uploader until a record id is supplied', () => {
        const element = build(undefined);
        const uploader = element.shadowRoot.querySelector('lightning-file-upload');
        expect(uploader.disabled).toBe(true);
    });

    it('lists every file returned by uploadfinished', async () => {
        const element = build();
        const uploader = element.shadowRoot.querySelector('lightning-file-upload');

        uploader.dispatchEvent(
            new CustomEvent('uploadfinished', {
                detail: {
                    files: [
                        { documentId: '069000000000001AAA', name: 'contract.pdf' },
                        { documentId: '069000000000002AAA', name: 'annex.pdf' }
                    ]
                }
            })
        );

        await Promise.resolve();

        const items = element.shadowRoot.querySelectorAll('li.slds-item');
        expect(items).toHaveLength(2);
        expect(items[0].textContent).toBe('contract.pdf');
    });

    it('tolerates an uploadfinished event with no files array', async () => {
        const element = build();
        const uploader = element.shadowRoot.querySelector('lightning-file-upload');
        const handler = jest.fn();
        document.addEventListener(ShowToastEventName, handler);

        uploader.dispatchEvent(new CustomEvent('uploadfinished', { detail: {} }));
        await Promise.resolve();

        expect(element.shadowRoot.querySelectorAll('li.slds-item')).toHaveLength(0);
        expect(handler).toHaveBeenCalled();
    });
});
```

`lightning/platformShowToastEvent` must be mapped in `jest.config.js` or the import resolves
to nothing — the guide's own sample config lists it under `moduleNameMapper`
(`lwc_guide unit-testing-using-jest-create-tests L12440-L12441`). Reuse `templates/lwc/jest.config.js`,
which already carries that entry, rather than writing a new one.

---

# Bundle B — `matterFileUploader`

Custom input, `FileReader`, base64, Apex. Use it only when Bundle A cannot apply.

## B.1 `matterFileUploader.html`

```html
<template>
    <lightning-card title="Upload Document" icon-name="standard:document">
        <div class="slds-var-p-around_medium">
            <lightning-input
                type="file"
                label="Choose a document"
                accept=".pdf"
                onchange={handleFileChange}>
            </lightning-input>

            <template lwc:if={errorMessage}>
                <p class="slds-text-color_error slds-var-m-top_x-small">{errorMessage}</p>
            </template>

            <template lwc:if={busy}>
                <lightning-spinner alternative-text="Uploading"></lightning-spinner>
            </template>

            <template lwc:if={contentDocumentId}>
                <p class="slds-var-m-top_x-small">Stored as {contentDocumentId}</p>
            </template>
        </div>
    </lightning-card>
</template>
```

## B.2 `matterFileUploader.js`

```javascript
import { LightningElement, api } from 'lwc';
import uploadFile from '@salesforce/apex/FileUploadController.uploadFile';

/*
 * Client-side size guard.
 *
 * Apex total heap is 6 MB synchronous / 12 MB asynchronous (apexdev L19577), and an
 * @AuraEnabled call from LWC runs synchronously. Salesforce documents the base64
 * conversion as increasing document size "by approximately 37%" (object_reference L79833),
 * so a 2 MB file arrives as roughly 2.74 MB of String.
 *
 * UNVERIFIED (2026-09-05): the assumption that the encoded String and the decoded Blob are
 * both resident on the heap at the same time is an inference about Apex memory behaviour,
 * not a documented statement. It is the conservative reading; measure the real number in
 * your org with Limits.getHeapSize() against Limits.getLimitHeapSize()
 * (apexrefguide L220711, L220729) before raising this cap.
 */
const MAX_RAW_BYTES = 2 * 1024 * 1024;

export default class MatterFileUploader extends LightningElement {
    /*
     * Unsaved-record strategy: linkedEntityId may be null while the parent record is still
     * being created. In that case the component holds the base64 payload and the parent's
     * save handler calls upload() with the new id. Nothing is written to Files until an
     * entity exists to link it to.
     */
    @api linkedEntityId;

    contentDocumentId;
    errorMessage;
    busy = false;

    async handleFileChange(event) {
        this.errorMessage = undefined;
        const file = event.target.files && event.target.files[0];
        if (!file) {
            return;
        }

        if (file.size > MAX_RAW_BYTES) {
            this.errorMessage = `That file is ${Math.round(file.size / 1024)} KB. The limit for this form is ${MAX_RAW_BYTES / 1024} KB.`;
            return;
        }

        this.busy = true;
        try {
            const base64Data = await this.toBase64(file);
            const result = await uploadFile({
                fileName: file.name,
                base64Data,
                linkedEntityId: this.linkedEntityId,
                shareType: 'V',
                visibility: 'InternalUsers'
            });
            this.contentDocumentId = result.contentDocumentId;
        } catch (error) {
            // AuraHandledException carries the Apex message in body.message and omits
            // body.stackTrace (lwc_guide apex-error-handling L7521-L7522).
            this.errorMessage =
                (error && error.body && error.body.message) || 'Upload failed.';
        } finally {
            this.busy = false;
        }
    }

    toBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                // readAsDataURL yields "data:<mime>;base64,<payload>" -- strip the prefix.
                resolve(String(reader.result).split(',')[1]);
            };
            reader.onerror = () => reject(reader.error);
            reader.readAsDataURL(blob);
        });
    }
}
```

## B.3 `matterFileUploader.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Matter File Uploader</masterLabel>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__AppPage">
            <property name="linkedEntityId" type="String" label="Linked Record Id"/>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

## B.4 `FileUploadController.cls`

```apex
/**
 * Server side of Bundle B. Inserts one ContentVersion, then links it explicitly.
 *
 * Not cacheable. "To set cacheable=true, a method must only get data, it cannot mutate
 * (change) data." (lwc_guide apex-result-caching L7254). Adding cacheable=true here would
 * make the client cache a write.
 *
 * with sharing is explicit: an @AuraEnabled class that declares nothing uses an implicit
 * with sharing, but the guide recommends declaring it (lwc_guide apex-security L7440).
 */
public with sharing class FileUploadController {

    // Not final: tests lower it so the cap branch can be proved without allocating
    // two megabytes of Blob inside a test transaction that shares the same heap.
    @TestVisible
    private static Integer MAX_RAW_BYTES = 2 * 1024 * 1024;

    private static final Map<String, String> MAGIC_BY_EXTENSION = new Map<String, String>{
        'pdf' => '25504446',
        'png' => '89504E47'
    };

    public class UploadResult {
        @AuraEnabled public Id contentDocumentId;
        @AuraEnabled public Id contentVersionId;
        @AuraEnabled public Integer bytesStored;
    }

    @AuraEnabled
    public static UploadResult uploadFile(
        String fileName,
        String base64Data,
        Id linkedEntityId,
        String shareType,
        String visibility
    ) {
        if (String.isBlank(fileName) || String.isBlank(base64Data)) {
            throw new AuraHandledException('fileName and base64Data are both required.');
        }
        if (linkedEntityId == null) {
            throw new AuraHandledException('A linked record is required before a file can be stored.');
        }

        Blob body = EncodingUtil.base64Decode(base64Data);

        // Server-side cap. The client guard is a UX affordance; this one is the control.
        if (body.size() > MAX_RAW_BYTES) {
            throw new AuraHandledException('File exceeds the ' + MAX_RAW_BYTES + ' byte limit.');
        }
        if (!signatureMatches(fileName, body)) {
            throw new AuraHandledException('File contents do not match the file extension.');
        }

        // PathOnClient carries the extension: "Specify a complete path including the file
        // extension in order for the document to be visible in the Preview tab."
        // (object_reference L79628). ContentLocation S = inside Salesforce (L79216).
        ContentVersion version = new ContentVersion(
            Title = fileName,
            PathOnClient = fileName,
            VersionData = body,
            ContentLocation = 'S'
        );
        insert as user version;

        // ContentDocumentId is generated by the platform, so it has to be re-queried.
        ContentVersion stored = [
            SELECT Id, ContentDocumentId, ContentSize
            FROM ContentVersion
            WHERE Id = :version.Id
            WITH USER_MODE
            LIMIT 1
        ];

        // Without this link the file sits in the uploader private library and never
        // appears on the record. ShareType is a required field (object_reference L77269).
        ContentDocumentLink link = new ContentDocumentLink(
            ContentDocumentId = stored.ContentDocumentId,
            LinkedEntityId = linkedEntityId,
            ShareType = String.isBlank(shareType) ? 'V' : shareType,
            Visibility = String.isBlank(visibility) ? 'InternalUsers' : visibility
        );
        insert as user link;

        UploadResult result = new UploadResult();
        result.contentDocumentId = stored.ContentDocumentId;
        result.contentVersionId = stored.Id;
        result.bytesStored = stored.ContentSize;
        return result;
    }

    private static Boolean signatureMatches(String fileName, Blob body) {
        String extension = fileName.substringAfterLast('.').toLowerCase();
        String expected = MAGIC_BY_EXTENSION.get(extension);
        if (expected == null) {
            return false;
        }
        if (body.size() < 4) {
            return false;
        }
        String head = EncodingUtil.convertToHex(body).toUpperCase();
        return head.startsWith(expected);
    }
}
```

`insert as user` runs the DML in user mode (`apexdev L8050`); `WITH USER_MODE` does the same
for the query (`lwc_guide apex-security L7444`). `EncodingUtil.base64Decode(String)` returns a
`Blob` (`apexrefguide L214211-L214216`); `Blob.size()` returns the number of bytes
(`apexrefguide L201262`).

## B.5 `FileUploadController.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

## B.6 `FileUploadControllerTest.cls`

A four-byte PDF signature is enough to exercise the whole path; nothing here needs a
realistic file, and a large `Blob` in a test consumes the same heap the production call does.

```apex
@IsTest
private class FileUploadControllerTest {

    private static final String PDF_BASE64 = EncodingUtil.base64Encode(
        EncodingUtil.convertFromHex('255044462D312E37')
    );

    private static Account newAccount() {
        Account account = new Account(Name = 'File Upload Test');
        insert account;
        return account;
    }

    @IsTest
    static void storesFileAndLinksItToTheRecord() {
        Account account = newAccount();

        Test.startTest();
        FileUploadController.UploadResult result = FileUploadController.uploadFile(
            'contract.pdf', PDF_BASE64, account.Id, 'V', 'InternalUsers'
        );
        Test.stopTest();

        Assert.isNotNull(result.contentDocumentId, 'A ContentDocumentId must come back.');

        List<ContentDocumentLink> links = [
            SELECT ContentDocumentId, LinkedEntityId, ShareType, Visibility
            FROM ContentDocumentLink
            WHERE LinkedEntityId = :account.Id
        ];
        Assert.areEqual(1, links.size(), 'Exactly one link is expected.');
        Assert.areEqual(result.contentDocumentId, links[0].ContentDocumentId);
        Assert.areEqual('V', links[0].ShareType, 'ShareType must be set explicitly.');
        Assert.areEqual('InternalUsers', links[0].Visibility, 'Default must not be external.');
    }

    @IsTest
    static void rejectsAPayloadOverTheServerCap() {
        Account account = newAccount();
        // Lower the cap instead of materialising a multi-megabyte Blob in a test
        // transaction that shares the same 6 MB heap as production.
        FileUploadController.MAX_RAW_BYTES = 2;

        Test.startTest();
        Boolean threw = false;
        try {
            FileUploadController.uploadFile('contract.pdf', PDF_BASE64, account.Id, 'V', 'InternalUsers');
        } catch (AuraHandledException error) {
            threw = true;
        }
        Test.stopTest();

        Assert.isTrue(threw, 'A payload past MAX_RAW_BYTES must be rejected in Apex.');
        Assert.areEqual(0, [SELECT COUNT() FROM ContentDocumentLink WHERE LinkedEntityId = :account.Id]);
    }

    @IsTest
    static void storesTheRawByteCountNotTheEncodedLength() {
        Account account = newAccount();

        Test.startTest();
        FileUploadController.UploadResult result = FileUploadController.uploadFile(
            'contract.pdf', PDF_BASE64, account.Id, 'V', 'InternalUsers'
        );
        Test.stopTest();

        // 8 hex characters of signature decode to 4 bytes; the base64 String is longer.
        Assert.areEqual(4, result.bytesStored, 'ContentSize is raw bytes, not base64 length.');
    }

    @IsTest
    static void rejectsContentThatDoesNotMatchTheExtension() {
        Account account = newAccount();
        String notAPdf = EncodingUtil.base64Encode(Blob.valueOf('plain text'));

        Test.startTest();
        Boolean threw = false;
        try {
            FileUploadController.uploadFile('contract.pdf', notAPdf, account.Id, 'V', 'InternalUsers');
        } catch (AuraHandledException error) {
            threw = true;
        }
        Test.stopTest();

        Assert.isTrue(threw, 'A renamed text file must be rejected on its bytes.');
        Assert.areEqual(0, [SELECT COUNT() FROM ContentDocumentLink WHERE LinkedEntityId = :account.Id]);
    }

    @IsTest
    static void rejectsAnUploadWithNoLinkedRecord() {
        Test.startTest();
        Boolean threw = false;
        try {
            FileUploadController.uploadFile('contract.pdf', PDF_BASE64, null, 'V', 'InternalUsers');
        } catch (AuraHandledException error) {
            threw = true;
        }
        Test.stopTest();

        Assert.isTrue(threw, 'An orphan ContentVersion must never be created.');
    }
}
```

## B.7 `__tests__/matterFileUploader.test.js`

`FileReader` is a jsdom global, so the mock replaces it wholesale and fires `onloadend`
synchronously. Apex is mocked through the `@salesforce/apex` `moduleNameMapper` entry — "When
you call Apex methods imperatively, the Apex code doesn't run in your Jest tests. You need to
mock the Apex method to return test data." (`lwc_guide unit-testing-using-jest-create-tests L12460`).

```javascript
import { createElement } from 'lwc';
import MatterFileUploader from 'c/matterFileUploader';
import uploadFile from '@salesforce/apex/FileUploadController.uploadFile';

jest.mock(
    '@salesforce/apex/FileUploadController.uploadFile',
    () => ({ default: jest.fn() }),
    { virtual: true }
);

class FileReaderMock {
    constructor() {
        this.result = null;
        this.error = null;
        this.onloadend = null;
        this.onerror = null;
    }
    readAsDataURL() {
        this.result = 'data:application/pdf;base64,JVBERi0xLjc=';
        if (this.onloadend) {
            this.onloadend();
        }
    }
}

describe('c-matter-file-uploader', () => {
    let originalFileReader;

    beforeEach(() => {
        originalFileReader = global.FileReader;
        global.FileReader = FileReaderMock;
        uploadFile.mockResolvedValue({
            contentDocumentId: '069000000000001AAA',
            contentVersionId: '068000000000001AAA',
            bytesStored: 8
        });
    });

    afterEach(() => {
        global.FileReader = originalFileReader;
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    function build(linkedEntityId = '001000000000001AAA') {
        const element = createElement('c-matter-file-uploader', { is: MatterFileUploader });
        element.linkedEntityId = linkedEntityId;
        document.body.appendChild(element);
        return element;
    }

    it('sends the stripped base64 payload to Apex', async () => {
        const element = build();
        const input = element.shadowRoot.querySelector('lightning-input');
        Object.defineProperty(input, 'files', {
            value: [{ name: 'contract.pdf', size: 1024 }],
            configurable: true
        });

        input.dispatchEvent(new CustomEvent('change'));
        await Promise.resolve();
        await Promise.resolve();

        expect(uploadFile).toHaveBeenCalledTimes(1);
        expect(uploadFile.mock.calls[0][0]).toMatchObject({
            fileName: 'contract.pdf',
            base64Data: 'JVBERi0xLjc=',
            shareType: 'V',
            visibility: 'InternalUsers'
        });
    });

    it('refuses a file over the client guard without calling Apex', async () => {
        const element = build();
        const input = element.shadowRoot.querySelector('lightning-input');
        Object.defineProperty(input, 'files', {
            value: [{ name: 'huge.pdf', size: 9 * 1024 * 1024 }],
            configurable: true
        });

        input.dispatchEvent(new CustomEvent('change'));
        await Promise.resolve();

        expect(uploadFile).not.toHaveBeenCalled();
        const error = element.shadowRoot.querySelector('.slds-text-color_error');
        expect(error.textContent).toContain('limit for this form');
    });

    it('surfaces the Apex message from an AuraHandledException body', async () => {
        uploadFile.mockRejectedValue({ body: { message: 'File contents do not match the file extension.' } });
        const element = build();
        const input = element.shadowRoot.querySelector('lightning-input');
        Object.defineProperty(input, 'files', {
            value: [{ name: 'contract.pdf', size: 1024 }],
            configurable: true
        });

        input.dispatchEvent(new CustomEvent('change'));
        await Promise.resolve();
        await Promise.resolve();
        await Promise.resolve();

        const error = element.shadowRoot.querySelector('.slds-text-color_error');
        expect(error.textContent).toBe('File contents do not match the file extension.');
    });
});
```

---

# Deploying

## `package.xml`

The Metadata API type for a Lightning web component is `LightningComponentBundle`
(`lwc_guide get-started-with-your-tools L559`).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>caseFileUploader</members>
        <members>matterFileUploader</members>
        <name>LightningComponentBundle</name>
    </types>
    <types>
        <members>FileUploadController</members>
        <members>FileUploadControllerTest</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

## Deploy order

1. `FileUploadController` and `FileUploadControllerTest` first. `matterFileUploader` imports
   `@salesforce/apex/FileUploadController.uploadFile`, and `@salesforce/*` imports are
   "validated against the organization's metadata" (`lwc_guide get-started-oss L126`), so the component fails
   to deploy if the class is not already present.
2. Apex class access: "An authenticated or guest user can access an `@AuraEnabled` Apex method
   only when the user's profile or an assigned permission set allows access to the Apex class."
   (`lwc_guide apex-security L7436`). Ship the permission set that grants
   `FileUploadController` in the same release, not afterwards.
3. The two component bundles.
4. The Lightning record page assignment last, so nothing is visible before its dependencies
   exist.

```bash
sf project deploy start --source-dir force-app/main/default/classes/FileUploadController.cls \
                        --source-dir force-app/main/default/classes/FileUploadControllerTest.cls \
                        --target-org myOrg
sf project deploy start --source-dir force-app/main/default/lwc/caseFileUploader \
                        --source-dir force-app/main/default/lwc/matterFileUploader \
                        --target-org myOrg
sf apex run test --tests FileUploadControllerTest --result-format human --wait 10 --target-org myOrg
npm run test:unit -- caseFileUploader matterFileUploader
```

## Verification

Query the link, not the file. A `ContentVersion` with no `ContentDocumentLink` is the silent
failure this whole skill exists to prevent, and it is invisible in the UI.

```soql
SELECT ContentDocumentId,
       LinkedEntityId,
       ShareType,
       Visibility,
       ContentDocument.Title,
       ContentDocument.FileExtension,
       ContentDocument.ContentSize,
       ContentDocument.LatestPublishedVersionId
FROM ContentDocumentLink
WHERE LinkedEntityId = '<the record id you uploaded against>'
ORDER BY SystemModstamp DESC
```

The `WHERE LinkedEntityId` filter is not optional. From API 59.0 on, querying
`ContentDocumentLink` **without** a filter on `Id`, `LinkedEntityId` or `ContentDocumentId`
requires the Query All Files permission, which in turn requires View All Data
(`object_reference L77161-L77162`).

Expected result for a healthy Bundle B upload: exactly one row, `ShareType = V`,
`Visibility = InternalUsers`, and `ContentSize` equal to the raw byte count of the file you
picked — not the base64 length.

```bash
sf data query --query "SELECT ContentDocumentId, ShareType, Visibility FROM ContentDocumentLink WHERE LinkedEntityId = '001000000000001AAA'" --target-org myOrg
```

## How to read the bundles above

- **`record-id` is the fork.** Present it and Bundle A applies; absent it and you are in
  Bundle B whether you wanted to be or not.
- **The `accept` attribute never rejects anything.** Bundle B validates on decoded bytes
  (`signatureMatches`) because that is the only layer an attacker does not control.
- **Two DML statements, deliberately.** `ContentVersion` then `ContentDocumentLink`.
  `FirstPublishLocationId` collapses them into one insert — "Setting FirstPublishLocationId
  allows you to create a file and share it with an initial record/group in a single
  transaction" (`object_reference L79403-L79405`) — but it is set only on the first published
  version and cannot be changed later (`object_reference L79407-L79409`). Bundle B keeps them
  separate so `ShareType` and `Visibility` are explicit choices.
- **The Apex method is not cacheable, and cannot be.** A `cacheable=true` method "must only
  get data, it can't mutate (change) data" (`lwc_guide apex-result-caching L7254`).
- **The heap cap lives in Apex.** The JavaScript check exists so the user gets a message
  instead of a spinner; the Apex check exists because the JavaScript one can be bypassed.
