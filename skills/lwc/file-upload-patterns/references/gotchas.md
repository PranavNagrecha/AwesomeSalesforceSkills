# Gotchas — LWC File Upload Patterns

Platform behaviours that surprise people building upload UI. Every numeric or behavioural
claim carries its source: `object_reference L<n>` / `apexdev L<n>` / `apexrefguide L<n>` are
the Summer '26 PDF text extracts, and `lwc_guide <page-slug> L<n>` is the crawled Lightning
Web Components Developer Guide.

---

## Gotcha 1: A ContentVersion with no ContentDocumentLink succeeds and is invisible

**What happens:** The Apex inserts cleanly, returns an id, the test passes, and the file
never appears in the record's Files related list. Nothing errors, nothing logs. The file is
sitting in the uploader's personal library.

**When it occurs:** Any hand-rolled upload path that inserts `ContentVersion` and stops.
`ContentVersion.FirstPublishLocationId` defaults to the running user's id when left blank
(`object_reference L79599-L79600`), so the file always lands *somewhere* — just not on the
record. `ContentDocument` itself cannot be created to fix this after the fact: its supported
calls are `delete()`, `describeLayout()`, `describeSObjects()`, `query()`, `retrieve()`,
`search()`, `undelete()`, `update()` — there is no `create()` (`object_reference L76648-L76649`).

**How to avoid:** Either set `FirstPublishLocationId` on the insert, which "allows you to
create a file and share it with an initial record/group in a single transaction"
(`object_reference L79403-L79405`), or re-query the generated `ContentDocumentId` and insert a
`ContentDocumentLink`. `scripts/check_file_upload_patterns.py` rule R2 fails the build when
neither is present.

---

## Gotcha 2: FirstPublishLocationId is a one-shot field

**What happens:** A team ships the one-statement version, then later needs the file moved to a
different parent. Setting `FirstPublishLocationId` on the next version does nothing useful, and
the field starts changing on its own when ownership moves.

**When it occurs:** "This field is only set the first time a version is published via the API.
`FirstPublishLocationId` can't be set to another ID when a new content version is inserted."
(`object_reference L79406-L79409`). Worse, Salesforce "updates the `FirstPublishLocationId`
automatically when a new `OwnerId` is added to the `ContentVersion`" — publishing a new version
under a different owner rewrites the field on *all previous versions*
(`object_reference L79411-L79416`).

**How to avoid:** Treat `FirstPublishLocationId` as a convenience for the create-and-attach
case only. Anywhere the association may change, or where more than one record must see the
file, use explicit `ContentDocumentLink` rows — a file can be linked to many entities, and the
link is the thing you can add, remove and audit.

---

## Gotcha 3: ShareType is required, and the value you probably want cannot come from a trigger

**What happens:** The insert fails with a required-field error, or it succeeds with a
permission level nobody chose.

**When it occurs:** `ContentDocumentLink.ShareType` is documented as **Required**
(`object_reference L77269`). Its values are `V` (viewer: view but not edit), `C`
(collaborator: view and edit) and `I` (inferred from the related record)
(`object_reference L77271-L77285`). Two constraints bite: "you can't create a
`ContentDocumentLink` with a `ShareType` of `C` from an Apex trigger"
(`object_reference L77276-L77277`), and inferred permission on shares with standard objects is
only available from API 36.0 (`object_reference L77281-L77283`) and "can't be used on shares
with the `Organization` object" (`object_reference L77283-L77284`).

**How to avoid:** Set `ShareType` explicitly at every insert site. Default to `V` for
attachment UI. If a trigger is doing the linking and the requirement is collaborator access,
move the insert out of the trigger — no retry will make `C` work from there.

---

## Gotcha 4: Visibility is how an internal document reaches an external audience

**What happens:** A file attached to a Case is visible to Experience Cloud users nobody
intended to share it with, and no sharing rule was changed to cause it.

**When it occurs:** `ContentDocumentLink.Visibility` takes `AllUsers`, `InternalUsers` or
`SharedUsers` (`object_reference L77302-L77313`). For posts to a record feed, `Visibility` is
set to `InternalUsers` for all internal users by default (`object_reference L77315-L77316`),
but an insert that sets `AllUsers` overrides that, and "external users can set `Visibility`
only to `AllUsers`" (`object_reference L77317`) — so a guest or community-user upload path
lands on the permissive value by construction. Only internal users can update it afterwards
(`object_reference L77322`), and where multiple references to the same file exist in a feed,
"the file's visibility is determined by the most visible setting"
(`object_reference L77327-L77328`).

**How to avoid:** Write `Visibility` on every `ContentDocumentLink` insert and make
`InternalUsers` the default in code, not a value inherited from a sample. Where an
Experience Cloud audience is genuinely intended, make that a reviewed decision with the
record's sharing model checked alongside it.

---

## Gotcha 5: Base64 costs about 37 %, and the Apex heap is 6 MB — not 6 MB of file

**What happens:** The uploader works on the developer's 2 MB sample and throws
`System.LimitException: Apex heap size too large` on the first real document.

**When it occurs:** Apex total heap is **6 MB synchronous / 12 MB asynchronous**
(`apexdev L19577`), and an `@AuraEnabled` call from an LWC runs in the synchronous bucket.
Salesforce documents the base64 conversion as increasing document size "by approximately 37%"
(`object_reference L79833-L79834`) — not the 33 % the 4/3 arithmetic suggests. So a 4 MB file
is already about 5.5 MB of `String` before anything decodes it.
UNVERIFIED (2026-09-05): whether the encoded `String` and the decoded `Blob` are resident on
the heap simultaneously is an inference about Apex memory management, not a documented
statement; the conservative reading is that they are.

**How to avoid:** Cap the raw file in Apex, not only in JavaScript, and measure rather than
guess: `Limits.getHeapSize()` against `Limits.getLimitHeapSize()`
(`apexrefguide L220711, L220729`). If the requirement is a file that does not fit that budget,
the answer is `lightning-file-upload` or a direct API upload, not a cleverer chunker.

---

## Gotcha 6: The chunked-append pattern raises the ceiling, it does not remove it

**What happens:** A chunked uploader passes acceptance at 20 MB and fails at 40 MB, and the
failure is the same heap exception the chunking was supposed to fix.

**When it occurs:** The common append implementation re-queries `ContentVersion.VersionData`,
concatenates the new chunk and updates the record. Heap then grows with the *total* file size,
not the chunk size. Two documented constraints compound it: "you can only update a version if
it is the latest version and if it is published" (`object_reference L79828`), and
`ContentVersion.VersionData` "can't be set for links" (`object_reference L79770`) — an update
against a link-type version silently has nowhere to go.

**How to avoid:** Do not represent chunked append as a route to arbitrarily large files.
Size the ceiling from the heap budget in gotcha 5 and state it in the design. There is no
documented fixed chunk size to copy; a number lifted from a blog post is not a constant.

---

## Gotcha 7: PathOnClient without the extension breaks Preview, not the upload

**What happens:** The file is stored, the link is correct, and the Preview tab shows nothing.
The upload code looks fine because it is.

**When it occurs:** "Specify a complete path including the file extension in order for the
document to be visible in the Preview tab." (`object_reference L79628-L79629`). `FileType` is
"determined by either `ContentUrl` for links or `PathOnClient` for documents, but not both"
(`object_reference L79156`), so a `PathOnClient` of `contract` rather than `contract.pdf`
leaves the platform with no type to render.

**How to avoid:** Pass the browser's `file.name` straight into both `Title` and
`PathOnClient`, extension included, and never sanitise the extension off in the name of
tidiness.

---

## Gotcha 8: Verifying the upload with an unfiltered ContentDocumentLink query needs View All Data

**What happens:** The developer runs `SELECT Id FROM ContentDocumentLink` to check the upload
worked and gets an error, or writes a report that only works for admins.

**When it occurs:** "In API versions 59.0 and later, turn on the Query All Files permission to
query without a filter on id, LinkedEntityId, and documentID fields. The View All Data
permission is required to turn on Query All Files."
(`object_reference L77161-L77162`). The neighbouring objects behave the same way: queries on
`ContentDocument` and `ContentVersion` "without specifying an ID don't return all files a user
has access to… if a user only has access to a file because they have access to a record that
the file is shared with, the file won't be returned" (`object_reference L79117-L79120`).

**How to avoid:** Always filter the verification query by `LinkedEntityId` or
`ContentDocumentId`. When querying `ContentVersion` for a record-shared file, "either the
`ContentVersionId` or the `ContentDocumentId` must be compounded by an `AND` operator"
(`object_reference L79850-L79852`).

---

## Gotcha 9: The success toast is silently absent on the surface that needs it most

**What happens:** The uploader works in Lightning Experience, ships to an Experience Cloud
site, and users report there is no confirmation that anything happened.

**When it occurs:** `lightning/platformShowToastEvent` "uses an event-based mechanism to
display a toast, and it's not supported in environments like LWR sites for Experience Cloud or
standalone apps. We recommend that you use `lightning/toast` instead."
(`lwc_guide base-components-patterns L4773`; the same restriction is stated in the component
table at `lwc_guide base-components-all L4649`). Nothing throws — the event is dispatched into
a container that does not listen for it.

**How to avoid:** Decide the confirmation mechanism from the target, not from habit. On LWR
sites use `lightning/toast`, or render the confirmation inside the component's own template so
it does not depend on the container at all.

---

## Gotcha 10: The upload succeeds and the Apex method still returns "no access"

**What happens:** The component deploys, the class deploys, and every user outside the admin
profile gets an error on the first click.

**When it occurs:** "An authenticated or guest user can access an `@AuraEnabled` Apex method
only when the user's profile or an assigned permission set allows access to the Apex class."
(`lwc_guide apex-security L7436`). Apex class access is a separate grant from object and field
permissions, so an upload permission set that gets `ContentVersion` create right and omits the
class is a working configuration that cannot run.

**How to avoid:** Ship the class-access grant in the same permission set and the same
deployment as the component. In API version 67.0 and later Apex also runs in user mode by
default (`lwc_guide apex-security L7434`), so the record-level side of the same permission set
has to be right too.

---

## Gotcha 11: Publishing volume is a per-24-hour org limit, and sandboxes get 2,500

**What happens:** A migration or a bulk-attach job runs fine in production planning and dies
partway through in a Developer Edition org or a trial.

**When it occurs:** "Contact Manager, Group, Professional, Enterprise, Unlimited, and
Performance Edition customers can publish a maximum of 200,000 new versions per 24-hour
period. Developer Edition and trial users can publish a maximum of 2,500 new versions per
24-hour period." (`object_reference L76637-L76639`, repeated at `L79868-L79870`). The org-wide
ceiling is 30,000,000 published documents, and "archived files count toward this limit and
toward storage usage limits" (`object_reference L76634-L76636`).

**How to avoid:** Size any bulk-attach step against the *edition of the org it will run in*.
An upload component that a user drives one file at a time will never touch this; a Flow or
batch that attaches a generated PDF per record will.

---

## Gotcha 12: ContentSize is bytes, and the field you should read changed in API 66.0

**What happens:** A size check or a progress display is wrong for large files, or reads zero.

**When it occurs:** `ContentSize` is "the size of the document in bytes for documents smaller
than 2 GB. The value is zero for links." — and "in API version 66.0 and later, we recommend
that you use the `ContentSizeLong` field even for documents smaller than 2 GB"
(`object_reference L79260-L79264`). `ContentSizeLong` is a `long` covering "up to 10 GB" and is
only available from API version 66.0 (`object_reference L79269-L79272`).

**How to avoid:** Read `ContentSizeLong` on API 66.0+ code and keep `ContentSize` only for
older callers. Either way the value is raw bytes, so never compare it against the length of
the base64 string you sent.
