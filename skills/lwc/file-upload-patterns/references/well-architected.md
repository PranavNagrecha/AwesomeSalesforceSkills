# Well-Architected Notes — LWC File Upload Patterns

**Reliability:** the tier decision is a limits decision, and it should be made from the
documented ceiling of the target surface rather than from a remembered number. The Apex path
is bounded by a total heap of 6 MB synchronous and 12 MB asynchronous
(`apexdev L19577`), and the base64 form of a document is about 37 % larger than the document
(`object_reference L79833`). Choosing the Apex path for "more control" imports that ceiling
for free, which is why the failure always arrives on the one document the business cares
about. UNVERIFIED (2026-09-05): the per-file ceiling of `lightning-file-upload` itself is
documented in the Lightning Component Library, which is not in the grounding corpus; the
adjacent, verifiable number is that `ContentVersion.ContentSizeLong` covers documents "up to
10 GB" from API version 66.0 (`object_reference L79269-L79272`), and that the SOAP API upload
ceiling is 50 MB measured after base64 conversion (`object_reference L79771-L79774`).

**Reliability, second order:** the ceiling also moves with the container.
UNVERIFIED (2026-09-05): the Experience Builder site per-file limits (128 MB on a
Salesforce-provided URL, 500 MB on a custom domain) and the statement that the component is
unsupported in Lightning Out and standalone apps both come from the Lightning Component
Library and could not be confirmed against the corpus. What the corpus does confirm is that
container support genuinely varies for adjacent modules: `lightning/platformShowToastEvent`
"isn't supported in LWR sites" and in standalone apps (`lwc_guide base-components-all L4649`,
`base-components-patterns L4773`). A design validated only on an internal record page has not
been validated for the surface the users are on.

**Reliability, association:** the file and the link are two objects, and only one of them is
created by the insert. `ContentDocument` supports `delete()`, `describeLayout()`,
`describeSObjects()`, `query()`, `retrieve()`, `search()`, `undelete()` and `update()` — there
is no `create()` (`object_reference L76648-L76649`). An upload path that produces a
`ContentVersion` and no `ContentDocumentLink` has produced something that cannot be repaired
by creating the missing parent; it has to be linked or deleted.

**Security:** the extension and the client-supplied MIME type are attacker-controlled, and the
`accept` attribute is a file-picker filter rather than a control. The only check that holds is
on the decoded bytes, server-side, together with a size cap Apex enforces rather than trusts.
Apex class access is its own grant: "an authenticated or guest user can access an
`@AuraEnabled` Apex method only when the user's profile or an assigned permission set allows
access to the Apex class" (`lwc_guide apex-security L7436`), and from API version 67.0 Apex
runs in user mode by default (`lwc_guide apex-security L7434`).

**Security, guest access:** UNVERIFIED (2026-09-05): the claims that guest users cannot upload
files by default, and that `lightning-file-upload` returns a `ContentVersionId` rather than a
`ContentDocumentId` for a guest upload, are help.salesforce.com and Component Library claims
that the corpus does not contain. The corpus does show the asymmetry is real on the read side:
"authenticated users can download files they have access to. Guest users can download only
`ContentDocument` files that they have access to through Library membership"
(`lwc_guide reference-wire-adapters-generate-url L17173`). Treat guest upload as its own design
with its own approval, not a configuration detail.

**Security, sharing:** the two `ContentDocumentLink` fields that decide who can see a file are
`ShareType` — documented as Required (`object_reference L77269`) — and `Visibility`
(`object_reference L77302-L77313`). Generated code habitually omits both or copies `AllUsers`
from a sample. External users can set `Visibility` only to `AllUsers`
(`object_reference L77317`), only internal users can update it afterwards
(`object_reference L77322`), and where a file has multiple references in a feed "the file's
visibility is determined by the most visible setting" (`object_reference L77327-L77328`). Set
both explicitly and default to `InternalUsers` unless an external audience is intended.

**Performance:** chunking exists to keep a transaction under the heap ceiling, not to make the
upload faster — it is strictly more round trips. Adopt it when the ceiling requires it, and
recognise where it stops helping: an append-style chunker that re-reads the accumulated body
grows heap with total file size, so it raises the ceiling without removing it. Two documented
constraints bound the pattern further: a version can only be updated "if it is the latest
version and if it is published" (`object_reference L79828`), and `VersionData` "can't be set
for links" (`object_reference L79770`).

**Operations:** publishing volume is an org-level, per-24-hour limit that differs by edition —
200,000 new versions for Contact Manager through Performance Edition, 2,500 for Developer
Edition and trial orgs (`object_reference L76637-L76639`) — against an org ceiling of
30,000,000 published documents, with archived files counting toward it
(`object_reference L76634-L76636`). A user-driven uploader never approaches this; a batch that
attaches a generated document per record can exhaust a sandbox in an afternoon.

## Official Sources Used

- **ContentDocumentLink, Object Reference** — `ShareType` is Required and its `V` / `C` / `I`
  semantics, the prohibition on creating `C` from an Apex trigger, the `Visibility` value list
  and its exceptions, and the API 59.0 Query All Files rule for unfiltered queries
  (`object_reference L77150-L77330`) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **ContentVersion, Object Reference** — `VersionData` as base64 with the ~37 % conversion
  increase and the 50 MB SOAP ceiling, `PathOnClient` and the Preview-tab extension rule,
  `FirstPublishLocationId` single-transaction sharing and its one-shot behaviour,
  `ContentLocation` values, `Origin` defaults, `ContentSize` vs `ContentSizeLong`, and the
  latest-and-published constraint on version updates (`object_reference L79112-L79880`) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **ContentDocument, Object Reference** — no `create()` call, the 30,000,000 published-document
  ceiling, and the 200,000 / 2,500 versions-per-24-hours limits by edition
  (`object_reference L76632-L76649`) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Apex Developer Guide, Execution Governors and Limits** — total heap size 6 MB synchronous
  and 12 MB asynchronous, and `insert as user` for user-mode DML
  (`apexdev L19577`, `L8050`) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Reference Guide** — `EncodingUtil.base64Decode(String)` returning a `Blob`,
  `base64Encode(Blob)`, `convertToHex` / `convertFromHex` for magic-number checks, `Blob.size()`
  in bytes, and `Limits.getHeapSize()` / `getLimitHeapSize()` for measuring the real budget
  (`apexrefguide L214194-L214256`, `L201262`, `L220711-L220729`) —
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/
- **LWC Developer Guide, Base Components Categories** — the routing rule between
  `lightning-file-upload` (associated with a record ID) and `lightning-input type="file"`
  (no record ID), and the LWR-site restriction on `lightning/platformShowToastEvent`
  (`lwc_guide base-components-all L4603`, `L4611`, `L4649`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/base-components-all.html
- **LWC Developer Guide, Secure Apex Classes** — Apex class access as a separate grant for
  authenticated and guest users, user-mode default from API 67.0, implicit `with sharing` on
  `@AuraEnabled` classes, and `WITH USER_MODE` (`lwc_guide apex-security L7430-L7460`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/apex-security.html
- **LWC Developer Guide, Use Apex Method Result Caching** — a cacheable method "must only get
  data, it can't mutate (change) data", which is why an upload method is called imperatively
  (`lwc_guide apex-result-caching L7254-L7256`, `apex-call-imperative L7190`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/apex-result-caching.html
- **LWC Developer Guide, Test Lightning Web Components with Jest** — `createElement`, the
  shared jsdom instance and `afterEach` cleanup, `element.shadowRoot` as the test-only query
  root, the `moduleNameMapper` entries for `@salesforce/apex` and
  `lightning/platformShowToastEvent`, and mocking imperative Apex
  (`lwc_guide unit-testing-using-jest-create-tests L12328-L12460`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest-create-tests.html
- **LWC Developer Guide, API Versioning and Deploy Using Your Own Tools** — `apiVersion` is
  mandatory from Spring '25, and `LightningComponentBundle` is the Metadata API type for
  `package.xml` (`lwc_guide create-version-components L797-L798`,
  `get-started-with-your-tools L559`) —
  https://developer.salesforce.com/docs/platform/lwc/guide/create-version-components.html
- **lightning-file-upload component reference** — the per-file ceiling, the Experience Builder
  site limits, the attribute list and the `uploadfinished` payload shape. UNVERIFIED
  (2026-09-05): this reference is not part of the grounding corpus and could not be fetched;
  every claim sourced only from it is marked in place —
  https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-file-upload.html
