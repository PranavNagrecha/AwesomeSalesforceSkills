# Well-Architected Notes — LWC File Upload Patterns

**Reliability:** the tier decision is a limits decision, and it should be made from the
documented ceiling of the target surface rather than from a remembered number. The
`lightning-file-upload` maximum and the Apex base64 maximum are not the same order of
magnitude — the base component's documented ceiling is 10 GB, while the Apex path is bounded
by a 6 MB synchronous / 12 MB asynchronous heap that a base64 payload consumes faster than
its byte count suggests. Choosing the Apex path for "more control" imports the smaller
ceiling for free, which is why the failure always arrives on the one document the business
cares about.

**Reliability, second order:** the ceiling also moves with the container. In Experience
Builder sites the per-file limit is 128 MB on a Salesforce-provided URL and 500 MB on a
custom domain, and the component is not supported in Lightning Out or standalone apps at
all — it renders as a disabled input rather than failing loudly. A design validated only on
an internal record page has not been validated for the surface the users are on.

**Security:** the extension and the client-supplied MIME type are attacker-controlled, and
the `accept` attribute is a file-picker filter rather than a control. The only check that
holds is on the decoded bytes, server-side, together with a size cap Apex enforces rather
than trusts. Guest upload is a separate design decision with its own approval: by default
guest users cannot upload files and have no access to objects and their related records,
and the `record-id` route specifically does not work for them under secure guest user record
access.

**Security, sharing:** the two `ContentDocumentLink` fields that decide who can see a file
are `ShareType` and `Visibility`, and generated code habitually omits both or copies
`AllUsers` from a sample. On a record surfaced in an Experience Cloud site that is exactly
how an internal document becomes externally visible. Set both explicitly, and default to
`InternalUsers` unless an external audience is intended.

**Performance:** chunking exists to keep a transaction under the heap ceiling, not to make
the upload faster — it is strictly more round trips. Adopt it when the ceiling requires it,
and recognise where it stops helping: an append-style chunker that re-reads the accumulated
body grows heap with total file size, so it raises the ceiling without removing it.

## Official Sources Used

- lightning-file-upload component reference — maximum file size, Experience Builder site limits (128 MB / 500 MB), simultaneous upload limits, guest user behaviour, and the Lightning Out / standalone restriction — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-file-upload.html
- Apex Governor Limits — total heap size, 6 MB synchronous and 12 MB asynchronous — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- ContentDocumentLink object reference — `ShareType` and `Visibility` values and semantics — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentdocumentlink.htm
- ContentVersion object reference — `VersionData`, `PathOnClient`, `FirstPublishLocationId` — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentversion.htm
- File Size and Sharing Limits — platform-wide file limits, which differ from the component's own ceiling — https://help.salesforce.com/s/articleView?id=sf.collab_files_size_limits.htm
