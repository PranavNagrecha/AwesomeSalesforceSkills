# Well-Architected Notes — Apex Blob And ContentVersion

## Relevant Pillars

### Reliability

File operations fail in ways that are hard to reproduce in unit tests: heap exhaustion on large payloads, silent truncation when the wrong pattern is used, missing ContentDocumentLinks that make the file invisible to the expected users. Reliable file code tests at realistic sizes and uses explicit sharing.

Tag findings as Reliability when:
- ContentVersion is inserted without a share and the file is orphaned in a private library
- `VersionData` is assumed to be populated without being selected in SOQL
- Heap approaches the sync or async ceiling during a bulk file operation
- `Attachment` and ContentVersion coexist in the same flow with inconsistent sharing

### Performance

Blobs are the largest objects in any Apex transaction. Heap management and DML sizing matter far more than for normal records.

Tag findings as Performance when:
- multiple large Blobs are held simultaneously in heap
- a loop builds Blobs and inserts in one bulk DML for large payloads
- ContentVersion inserts happen synchronously when the payload would fit async

### Security

Sharing a file to the wrong target exposes it to unintended users. `Visibility = 'AllUsers'` on an InternalUsers-only entity leaks to portal users; `ShareType = 'V'` bypasses record sharing and hands viewing to anyone with the link.

Tag findings as Security when:
- `ShareType = 'V'` or `'C'` is used where `'I'` (inferred) would have sufficed
- `Visibility = 'AllUsers'` is used on a link to a non-community record
- files containing PII are stored without `Security.stripInaccessible` or explicit access checks

## Architectural Tradeoffs

- **ContentVersion vs Attachment:** ContentVersion is the strategic target for all new file work. Attachment still exists for backwards compatibility but lacks version, preview, and mobile parity.
- **`FirstPublishLocationId` (single share) vs explicit ContentDocumentLink (multi-record share):** use the former when one record needs the file; use the latter when the file is shared across multiple records or needs non-inferred sharing.
- **Base64 through `@AuraEnabled` vs `lightning-file-upload`:** base64 is simple but caps around 4 MB binary; `lightning-file-upload` scales to multi-GB but requires LWC-side configuration.

## Anti-Patterns

1. **Base64-in-a-text-field** — storing file bytes in a custom Long Text field caps at ~95 KB and silently truncates.
2. **Orphaned file insert** — ContentVersion without a share lives in the uploader's private library.
3. **Attachment for new features** — lacks version and preview support; creates inconsistent file behavior across the org.

## Official Sources Used

- Apex Developer Guide — Working with Files: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_files.htm
- ContentVersion Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentversion.htm
- ContentDocumentLink Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentdocumentlink.htm
- Apex Governor Limits — Heap Size: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
