---
name: file-upload-patterns
description: "Upload files in LWC: lightning-file-upload, manual multipart, large-file chunked upload, and ContentDocument associations. NOT for ContentDocument query patterns — use data/salesforce-files-architecture. Trigger keywords: file upload, lightning-file-upload, uploadfinished, FileReader, base64, ContentVersion, ContentDocumentLink, ShareType, Visibility, VersionData, FirstPublishLocationId, Apex heap, guest user upload."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
triggers:
  - "lightning file upload lwc"
  - "chunked upload salesforce lwc"
  - "large file upload apex"
  - "contentdocumentlink lwc"
  - "attach a file to a record from a lightning web component"
  - "uploaded file does not show in the files related list"
  - "apex heap size too large when uploading a base64 file"
  - "upload a file before the record is saved in lwc"
  - "handle the uploadfinished event and show a toast"
  - "restrict which file types users can upload in lwc"
  - "set sharetype and visibility on contentdocumentlink"
  - "write a jest test for a file upload component"
  - "guest users cannot upload files on my experience site"
  - "convert a file to base64 with filereader and send it to apex"
  - "query contentdocumentlink to confirm the file attached"
tags:
  - file-upload
  - content-document
  - lwc
  - contentversion
  - contentdocumentlink
inputs:
  - "max file size"
  - "target record"
  - "whether the parent record exists at upload time"
  - "who must be able to see the stored file"
outputs:
  - "component with appropriate upload strategy + server-side Apex"
  - "ContentVersion / ContentDocumentLink design with explicit ShareType and Visibility"
  - "Jest and Apex test coverage for the upload path"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# LWC File Upload Patterns

Getting bytes from a browser into Salesforce Files, and attaching the result to the right
record. The whole domain turns on one question — does a record id exist at the moment of
upload — and on one limit, the Apex heap, which decides whether the bytes may pass through
Apex at all.

---

## Adoption Signals

Any file intake UI. Choose the tier by whether a record id exists, by file size, and by who
must see the result.

| Signal | Tier |
|---|---|
| Record already saved, no pre-processing needed | `lightning-file-upload` |
| No record id yet, or the bytes must be inspected or transformed first | custom input → `FileReader` → Apex |
| File larger than a couple of megabytes | `lightning-file-upload` — the Apex path cannot carry it |
| Guest or Experience Cloud audience | Neither, until the access design is settled first |

The guide routes the first two itself: `lightning-file-upload` is "a file selector for
uploading a file that's associated with a record ID. To upload a file without a record ID,
use `lightning-input` with `type="file"` instead."
(`lwc_guide base-components-all L4603`).

---

## Before Starting

- Does the record the file attaches to exist at the moment the user picks the file?
- What is the largest file the business actually sends, not the largest anyone imagines?
- Who is allowed to see the stored file — internal only, or an Experience Cloud audience?
- What surface is the component on: a Lightning record page, an LWR site, a standalone app?
- Is anything expected to inspect, scan or transform the bytes before they are stored?

---

## Questions to Ask Before Configuring

Ask these before writing markup. Each answer closes a branch that is expensive to reverse
once the component ships, and each one traces to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Does the parent record exist when the user picks the file?" | It is the whole tier decision. With a record id the platform does the association; without one you own it | The tier, and for the Apex path the moment at which the link is created (gotcha 1) |
| "What is the biggest file this has to accept in the next two years?" | Apex heap is 6 MB synchronous (`apexdev L19577`) and base64 adds about 37 % (`object_reference L79833`); past a couple of megabytes the Apex path is not available at any chunk size | A hard cap written into the Apex controller, not only the JavaScript (gotchas 5, 6) |
| "Who must be able to open the file once it is stored — internal staff only, or a customer?" | `ShareType` and `Visibility` decide it, and `AllUsers` on a record surfaced externally is how internal documents leak | Explicit values at every `ContentDocumentLink` insert site (gotchas 3, 4) |
| "Will the file ever need to move to a different parent record?" | `FirstPublishLocationId` is set only on first publish and cannot be changed later | Whether the one-statement form is safe or explicit links are required (gotcha 2) |
| "Which surface is this component on — Lightning Experience, an LWR site, a standalone app?" | Confirmation UX differs: `lightning/platformShowToastEvent` is not supported in LWR sites or standalone apps (`lwc_guide base-components-patterns L4773`) | The confirmation mechanism, chosen rather than defaulted (gotcha 9) |
| "Which file types must be refused, and what happens if a refused file gets through?" | `accept` is a picker filter; only a server-side check on decoded bytes rejects anything | The magic-number allowlist and the Apex rejection path (anti-pattern 5) |
| "Which permission set grants this, and does it include Apex class access?" | Class access is a separate grant: an `@AuraEnabled` method is reachable only when the profile or a permission set allows the class (`lwc_guide apex-security L7436`) | A permission set shipped in the same deployment as the component (gotcha 10) |

What a proper configuration adds over just wiring an uploader: the file is visible on the
record because the link was a deliberate insert rather than a hoped-for side effect, its
audience is a chosen value rather than an inherited one, the size ceiling is enforced where a
browser cannot bypass it, and the Jest and Apex tests fail when any of those three regress.

---

## Recommended Workflow

1. **Answer the record-id question first.** If the record exists, build Bundle A from
   `references/code-examples.md` — `lightning-file-upload` with `record-id`, an
   `uploadfinished` handler, and no Apex at all. Stop here unless something below forces the
   Apex path.
2. **If the Apex path is forced, size it before writing it.** Take the largest real file, add
   ~37 % for base64 (`object_reference L79833`), and check it against the 6 MB synchronous
   heap (`apexdev L19577`). If it does not clear that with margin, the requirement is wrong,
   not the implementation — go back to step 1 or to a direct API upload.
3. **Build Bundle B as a pair.** `references/code-examples.md` § B: client size guard →
   `FileReader` → `@AuraEnabled` (never `cacheable=true`) → `ContentVersion` →
   `ContentDocumentLink` with explicit `ShareType` and `Visibility` → return the
   `ContentDocumentId`. Validate the decoded bytes, not the extension.
4. **Write both tests before deploying.** The Jest suite dispatches a synthetic
   `uploadfinished` event and mocks `FileReader` and the Apex import; the Apex test uses a
   four-byte `Blob` and asserts the `ContentDocumentLink` row exists with the intended
   `ShareType`. Both are in `references/code-examples.md` §§ A.5, B.6, B.7.
5. **Run the checker over the source tree:**
   `python3 scripts/check_file_upload_patterns.py --manifest-dir force-app/main/default`.
   Use `--strict` in CI to fail on warnings. It catches an orphan `ContentVersion`, a
   cacheable upload method, a missing `ShareType`, an unguarded base64 payload and a
   `lightning-file-upload` with neither a `record-id` nor a documented alternative.
6. **Deploy Apex before the components,** and the permission set with class access in the
   same release. `@salesforce/*` imports are validated against org metadata
   (`lwc_guide get-started-oss L126`), so the component will not deploy against a class that is not there yet.
7. **Verify against `ContentDocumentLink`, not against the file.** Run the filtered query in
   `references/code-examples.md` § Verification. An unfiltered `ContentDocumentLink` query
   needs View All Data from API 59.0 on (`object_reference L77161-L77162`), so filter by
   `LinkedEntityId` and confirm `ShareType`, `Visibility` and the raw byte count.

---

## Key Considerations

| Fact | Source | Consequence |
|---|---|---|
| Apex total heap: 6 MB synchronous, 12 MB asynchronous | `apexdev L19577` | An `@AuraEnabled` upload runs in the synchronous bucket |
| Base64 conversion "increases the document size by approximately 37%" | `object_reference L79833` | The 4/3 arithmetic understates it; budget from the documented figure |
| Maximum file size uploadable via the SOAP API is 50 MB, measured *after* base64 conversion | `object_reference L79771-L79774` | The API ceiling and the component ceiling are different numbers |
| `ContentDocumentLink.ShareType` is Required; `C` cannot be created from an Apex trigger | `object_reference L77269`, `L77276-L77277` | Set it at every insert; move trigger-based collaborator links elsewhere |
| `Visibility` values are `AllUsers`, `InternalUsers`, `SharedUsers`; external users can only set `AllUsers` | `object_reference L77302-L77317` | Write it explicitly; default to `InternalUsers` in code |
| `FirstPublishLocationId` shares the file in a single transaction, but is set only on first publish | `object_reference L79403-L79409` | Use explicit links wherever the parent may change |
| `ContentDocument` has no `create()` call | `object_reference L76648-L76649` | You cannot manufacture a document to repair an orphan version |
| A cacheable Apex method "must only get data, it can't mutate (change) data" | `lwc_guide apex-result-caching L7254` | An upload method is never `cacheable=true` |
| `lightning/platformShowToastEvent` is unsupported in LWR sites and standalone apps | `lwc_guide base-components-patterns L4773` | Choose the confirmation mechanism from the target |

Virus scanning is not part of any of this. UNVERIFIED (2026-09-05): the claim that Salesforce
performs no automatic malware scan on uploaded Files is not stated in the grounding corpus
(Object Reference, Apex Developer Guide, LWC Developer Guide, App Limits cheat sheet); treat
scanning as a separate design and see `security/file-upload-virus-scanning`.

---

## Worked Examples (see `references/examples.md`)

- *Simple record attachment* — attach a signed PDF to a Case with no Apex
- *Large document through Apex* — where the heap ceiling actually binds, and where the
  chunked workaround stops helping

## Common Gotchas (see `references/gotchas.md`)

- **Orphan ContentVersion** — the insert succeeds, the file is invisible, nothing errors
- **`FirstPublishLocationId` is one-shot** — and it rewrites itself when ownership changes
- **`ShareType` is Required and `C` is trigger-hostile** — a documented, not incidental, limit
- **Base64 costs ~37 %, not 33 %** — the heap budget is smaller than the arithmetic suggests
- **Unfiltered `ContentDocumentLink` queries need View All Data** — from API 59.0

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Hand-rolling a base64 uploader when the base component already does the job
- Quoting a per-file size ceiling from memory
- Inserting `ContentVersion` and calling the file attached
- Treating `accept` as validation

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are writing the bundle: Bundle A (`lightning-file-upload` + `uploadfinished` + toast), Bundle B (custom input → `FileReader` → Apex → `ContentVersion` + `ContentDocumentLink`), both Jest suites, the Apex test, `js-meta.xml`, `package.xml`, deploy order and the verification SOQL |
| `references/gotchas.md` | A file uploaded successfully and something about it is wrong — invisible on the record, visible to the wrong audience, failing on heap, or unqueryable |
| `references/llm-anti-patterns.md` | You are reviewing generated upload code, or want the detection hints the checker implements |
| `references/well-architected.md` | You need the pillar framing, the tier tradeoff argument, or the sourced claims list |
| `templates/file-upload-patterns-template.md` | You are recording the tier decision, the size budget and the sharing choice for review |
| `scripts/check_file_upload_patterns.py` | Before deploy: run it with `--manifest-dir` over the LWC and Apex source tree, `--strict` in CI |

---

## Related Skills

- `data/salesforce-files-architecture` — use for the storage model itself: `ContentDocument`, versioning, libraries, and querying files that already exist.
- `security/file-upload-virus-scanning` — use for the scanning design this skill deliberately does not cover.
- `lwc/lwc-forms-and-validation` — use when the upload is one field inside a larger form; that skill owns the submit lifecycle and validation feedback.
- `lwc/lwc-error-boundaries` — use to decide how an upload failure degrades in the surrounding page rather than blanking it.
- `lwc/lwc-testing` — use for the broader Jest setup this skill's tests assume.
- `data/attachment-to-files-migration` — use when the requirement is moving legacy `Attachment` records into Files rather than accepting new uploads.

---

## Official Sources Used

See `references/well-architected.md` § Official Sources Used for the full list with the claim
each source supports.
