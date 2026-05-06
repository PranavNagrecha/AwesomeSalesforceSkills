# Well-Architected Notes — Salesforce Files Architecture

## Relevant Pillars

- **Security** — `ContentDocumentLink.ShareType` and `Visibility`
  are the critical levers. A misconfigured Visibility on a
  community / Experience Cloud site can leak files to portal users.
  Default to the most-restrictive setting and grant up.
- **Performance** — File operations consume Apex heap when
  `VersionData` is materialized. Bulk operations require batch-size
  tuning to avoid heap-limit governor exceptions.
- **Reliability** — Migration from `Attachment` to Files is a
  one-time but high-stakes operation. Validation must happen
  end-to-end before deleting source rows; otherwise a partial
  migration loses data.

## Architectural Tradeoffs

- **Files vs Attachment.** Attachment is simpler to use (one object,
  `ParentId`, `Body`) but capped at 25 MB, no versioning, no
  multi-record link, deprecated. Files are the modern choice for
  every new use case.
- **Files vs Files Connect.** Files stores binary in Salesforce.
  Files Connect references binary in an external source. Pick by
  data residency, storage cost, and source-of-truth requirements.
- **`ShareType = 'I'` vs explicit `'V'`/`'C'`.** Inferred sharing
  is the simpler default — file access tracks parent record access.
  Explicit grants are needed for cross-record sharing and
  fine-grained control.
- **Visibility = `'AllUsers'` vs `'InternalUsers'`.** AllUsers
  surfaces files to community / portal users with parent access;
  InternalUsers restricts to internal. Default to InternalUsers in
  mixed-audience orgs and override deliberately.

## Anti-Patterns

1. **Using `Attachment` for new development.** Deprecated; size-
   limited; no multi-record link.
2. **Inserting `ContentDocument` directly.** Platform creates it
   from the `ContentVersion` insert.
3. **SOQL on `ContentDocument.ParentId`.** Field does not exist;
   use `ContentDocumentLink`.
4. **Loading `VersionData` in bulk without heap awareness.** Hits
   the 12 MB sync / 36 MB async governor.
5. **Omitting `Visibility` on `ContentDocumentLink` inserts in
   community-enabled orgs.** Risk of inadvertent disclosure.

## Official Sources Used

- ContentVersion Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentversion.htm
- ContentDocument Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentdocument.htm
- ContentDocumentLink Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentdocumentlink.htm
- Files in Salesforce — https://help.salesforce.com/s/articleView?id=sf.collab_files_about.htm&type=5
- Files Connect Overview — https://help.salesforce.com/s/articleView?id=sf.admin_files_connect_about.htm&type=5
- Salesforce Well-Architected Trustworthy — https://architect.salesforce.com/well-architected/trusted/secure
