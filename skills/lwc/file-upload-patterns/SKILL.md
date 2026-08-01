---
name: file-upload-patterns
description: "Upload files in LWC: lightning-file-upload, manual multipart, large-file chunked upload, and ContentDocument associations. NOT for ContentDocument query patterns."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "lightning file upload lwc"
  - "chunked upload salesforce lwc"
  - "large file upload apex"
  - "contentdocumentlink lwc"
tags:
  - file-upload
  - content-document
  - lwc
inputs:
  - "max file size"
  - "target record"
outputs:
  - "component with appropriate upload strategy + server-side Apex"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-08-01
---

# LWC File Upload Patterns

LWC file upload has three tiers: (1) `<lightning-file-upload>` for files within the documented component maximum of 10 GB, associated with a record; (2) custom input + fetch for more control; (3) chunked upload for very large files using ContentVersion.VersionData. This skill picks the right tier and shows the minimal implementation.

## Adoption Signals

Any file intake UI. Choose tier by max size, auth model, and UX requirements.

- `lightning-file-upload` when the component's ceiling covers your files and the user already has CRUD on the parent record. The ceiling depends on the surface: 10 GB documented maximum, but 128 MB in an Experience Builder site on a `my.site.com` URL and 500 MB on a custom domain.
- Chunked upload via Apex when files exceed the platform single-call limit and progress feedback matters.

## Recommended Workflow

1. Start with `<lightning-file-upload record-id="…">` if the component ceiling for your surface (10 GB standard; 128 MB / 500 MB on Experience sites) covers the files and they are tied to one record.
2. For custom flows: `<input type="file" @change=...>` → FileReader → POST to @AuraEnabled Apex with base64.
3. When the Apex path is required, append chunks to one ContentVersion. Size the chunk from the heap limit (6 MB sync / 12 MB async, and base64 is ~4/3 of the bytes it encodes), confirmed with `Limits.getHeapSize()` — there is no documented fixed chunk size, so do not copy one from a blog post.
4. Always validate MIME type client-side AND server-side.
5. Enforce size caps in Apex; don't trust client.

## Key Considerations

- Apex heap is 6MB / 12MB (transaction). Base64 adds 33%. For larger files chunk or use the direct REST upload.
- `lightning-file-upload` creates ContentDocumentLink automatically; custom flows must do this.
- Virus scanning is not automatic; many orgs run a Lambda on ContentDocument insert.
- Content types: validate with magic-bytes, not extension.

## Worked Examples (see `references/examples.md`)

- *Simple record attachment* — Attach PDF to Case
- *Chunked 50MB upload* — Legal contract

## Common Gotchas (see `references/gotchas.md`)

- **Heap exceeded** — Error at 12MB file.
- **No MIME validation** — User uploads .exe renamed .pdf.
- **Missing ContentDocumentLink** — File uploaded but not visible on record.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Base64-in-Apex for 100MB
- Trusting client MIME
- Skipping ContentDocumentLink

## Official Sources Used

- Lightning Web Components Developer Guide — https://developer.salesforce.com/docs/platform/lwc/guide/
- lightning-file-upload (10 GB maximum; 128 MB / 500 MB Experience Builder site limits) — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-file-upload.html
- Apex Governor Limits (heap: 6 MB synchronous / 12 MB asynchronous) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Lightning Data Service — https://developer.salesforce.com/docs/platform/lwc/guide/data-wire-service-about.html
- LWC Recipes — https://github.com/trailheadapps/lwc-recipes
- SLDS 2 — https://www.lightningdesignsystem.com/2e/
