---
name: file-and-document-integration
description: "Use when uploading, downloading, managing, or integrating files and documents with Salesforce — covering ContentVersion/ContentDocument, REST multipart uploads, base64 inserts, Files Connect for external storage reads, and virus scanning callout patterns. Triggers: 'upload file to Salesforce', 'ContentVersion REST API', 'Files Connect external storage', 'multipart file upload', 'document integration pattern', 'virus scan uploaded file'. NOT for Bulk API data loads, Chatter feed post content, email attachment handling via EmailMessage, or CRM Content classic libraries."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Scalability
tags:
  - file-upload
  - content-version
  - content-document
  - files-connect
  - multipart
  - virus-scanning
  - rest-api
  - external-storage
triggers:
  - "how do I upload a file to Salesforce using the REST API"
  - "what is the correct way to create a ContentVersion record with binary data"
  - "how do I connect Salesforce to an external file storage system like SharePoint or Google Drive"
  - "how do I scan uploaded files for viruses before storing them in Salesforce"
  - "what are the file size limits when uploading documents to Salesforce"
  - "how do I link an uploaded file to a specific record in Salesforce"
inputs:
  - "file source: local binary, base64 payload, external URL, or external storage system"
  - "target record ID to link the uploaded file via ContentDocumentLink"
  - "org edition and file storage limits — affects maximum file size and total storage"
  - "security requirements: virus scanning, file type restrictions, sharing model"
outputs:
  - "ContentVersion and ContentDocumentLink creation pattern for the given scenario"
  - "REST multipart or base64 upload request structure"
  - "Files Connect configuration guidance for external storage read access"
  - "virus scanning callout pattern with Apex trigger or Flow"
  - "review findings for an existing file integration implementation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# File And Document Integration

Use this skill when the task involves uploading, downloading, linking, or managing files and documents in Salesforce, or when integrating Salesforce with external document storage systems. This skill covers the ContentVersion/ContentDocument data model, REST API multipart and base64 upload patterns, Files Connect for reading external files inside Salesforce, and the virus scanning callout pattern that Salesforce does not provide natively.

---

## Before Starting

Gather this context before working on anything in this domain:

- What is the org's file storage allocation? Salesforce allocates per-user and per-org file storage. Exceeding it causes insert failures on ContentVersion with `STORAGE_LIMIT_EXCEEDED`.
- What is the maximum file size for this use case? REST API multipart upload supports files up to 2 GB. Base64 insert via sObject create is limited to approximately 37 MB (the base64 encoding inflates a 28 MB binary to the 37.5 MB request body limit). SOAP API has a strict 50 MB message size limit.
- Does the org require virus scanning? Salesforce has no built-in virus scanning for CRM file uploads. If security policy mandates scanning, you must implement an Apex callout to an external scanning service (ClamAV, VirusTotal, etc.) triggered on ContentVersion insert.
- Is the requirement to store files in Salesforce, or to surface external files inside Salesforce? Storing files uses ContentVersion. Surfacing external files uses Files Connect (Salesforce Connect for files). These are fundamentally different architectures.

---

## Core Concepts

### ContentVersion and ContentDocument Model

Salesforce stores files using a two-object model. `ContentVersion` represents a specific version of a file — it holds the binary data (VersionData), file name (Title, PathOnClient), and metadata. When a ContentVersion is inserted, the platform automatically creates a parent `ContentDocument` record. Subsequent versions of the same file create new ContentVersion records under the same ContentDocument. You never insert ContentDocument directly — it is system-managed.

To make a file visible on a record, you create a `ContentDocumentLink` that associates the ContentDocument with a target record (LinkedEntityId). A single ContentDocument can be linked to multiple records. The ShareType field on ContentDocumentLink controls whether linked users can view (`V`), collaborate (`C`), or have inferred access (`I`).

### REST API Multipart Upload

For files larger than a few megabytes, use the REST API multipart form-data endpoint. The request targets `/services/data/v63.0/sobjects/ContentVersion/` with a `Content-Type: multipart/form-data` header. The request body includes two parts: a JSON part containing the ContentVersion field values (Title, PathOnClient, FirstPublishLocationId) and a binary part containing the file data. This approach supports files up to 2 GB and avoids the base64 encoding overhead that inflates payload size by approximately 33%.

### Base64 Insert Pattern

For smaller files (under approximately 28 MB binary), you can insert a ContentVersion record using a standard sObject create with the VersionData field set to a base64-encoded string. This is simpler to implement but carries the encoding overhead and hits the REST API request body size limit of 37.5 MB. Use this pattern only when file sizes are predictably small and simplicity outweighs efficiency.

### Files Connect (External File Surfacing)

Files Connect allows users to browse and search files stored in external systems (SharePoint Online, OneDrive, Google Drive, Box, Quip) directly inside the Salesforce Files tab and record detail pages. Files Connect does not copy files into Salesforce — it provides a virtual read-only view. Configuration requires an Authentication Provider, an External Data Source of type Files Connect, and user-level or org-level authentication. Files Connect is available in Enterprise, Performance, Unlimited, and Developer editions.

### Virus Scanning Callout Pattern

Salesforce does not scan CRM-uploaded files for viruses. Organizations with compliance requirements must implement scanning via an Apex after-insert trigger on ContentVersion. The trigger sends the file binary (via HTTP callout) to an external scanning service. If the scan returns a positive detection, the trigger or a subsequent process deletes the ContentVersion or quarantines it by relinking it to a restricted library. Because Apex callouts cannot run synchronously in a trigger context without `@future` or Queueable, the scan is always asynchronous — meaning a brief window exists where an unscanned file is accessible.

---

## Common Patterns

### Multipart REST Upload with Record Linking

**When to use:** An external system needs to push a file into Salesforce and attach it to a specific record (e.g., an Account, Case, or custom object).

**How it works:** Issue a POST to `/services/data/v63.0/sobjects/ContentVersion/` with `Content-Type: multipart/form-data`. Include the JSON entity part with `Title`, `PathOnClient`, and optionally `FirstPublishLocationId` set to the target record ID. Include the binary file part. On success, the response returns the ContentVersion ID. Query back the ContentDocumentId from the new ContentVersion record. If `FirstPublishLocationId` was not set, create a `ContentDocumentLink` with `LinkedEntityId` set to the target record, `ContentDocumentId` from the query, and `ShareType` of `V` or `C`.

**Why not the alternative:** Using base64 encoding wastes bandwidth, inflates payload by 33%, and fails for files over 28 MB. Using Apex `EncodingUtil.base64Encode()` in a trigger or batch hits heap limits on files larger than a few MB.

### Asynchronous Virus Scan on Upload

**When to use:** Security policy requires that every uploaded file be scanned for malware before users can access it.

**How it works:** Create an after-insert trigger on ContentVersion that enqueues a Queueable Apex class. The Queueable reads the file binary from `ContentVersion.VersionData`, sends it via `HttpRequest` to an external virus scanning API endpoint (configured via Named Credential for credential management), and inspects the response. If the file is clean, a custom field (`Scan_Status__c`) is updated to `Clean`. If malicious, the ContentVersion is deleted or moved to a quarantine library, and an alert is sent to the security team.

**Why not the alternative:** Synchronous scanning in a trigger is not possible — callouts are prohibited in trigger context without async. Skipping scanning entirely leaves the org exposed to malware distribution via shared files.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| File under 28 MB, simple integration | Base64 sObject insert on ContentVersion | Simplest code path, no multipart complexity |
| File up to 2 GB | REST multipart form-data upload | Only method that supports large files without encoding overhead |
| Need to link file to a record at upload time | Set FirstPublishLocationId on ContentVersion | Avoids separate ContentDocumentLink insert |
| Link file to multiple records | Create multiple ContentDocumentLink records | One ContentDocument can link to many records |
| Read external files without copying into SF | Files Connect with External Data Source | No storage consumed, real-time external view |
| Store SF-generated docs externally | Industries CLM / External Document Management | SF Files are not designed for outbound storage sync |
| Virus scanning required on upload | Queueable callout from ContentVersion trigger | SF has no native CRM virus scanning |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Determine the file direction — is the requirement to upload files into Salesforce, surface external files inside Salesforce, or export Salesforce-generated documents externally? This determines whether you use ContentVersion, Files Connect, or an external document management pattern.
2. Check storage and size constraints — confirm the org file storage allocation, the maximum expected file size, and whether the integration will use REST multipart (up to 2 GB) or base64 insert (up to ~28 MB).
3. Implement the upload or connection pattern — for uploads, construct the ContentVersion insert with appropriate method; for external surfacing, configure the External Data Source and Authentication Provider for Files Connect.
4. Wire record linking — ensure ContentDocumentLink records are created with correct LinkedEntityId and ShareType to make files visible on the right records with the right access level.
5. Add virus scanning if required — implement the async Queueable callout pattern on ContentVersion after-insert, using a Named Credential for the scanning service endpoint.
6. Validate — run the checker script, confirm file uploads succeed within size limits, verify record linking, and test virus scan flow end-to-end if applicable.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] ContentVersion is used for file creation — ContentDocument is never inserted directly.
- [ ] Files over 28 MB use REST multipart upload, not base64 encoding.
- [ ] ContentDocumentLink records are created with explicit ShareType (V, C, or I) — not left to default.
- [ ] FirstPublishLocationId is used where possible to avoid a separate ContentDocumentLink insert.
- [ ] Virus scanning is implemented via async callout if security policy requires it.
- [ ] Named Credentials are used for any external service callouts (scanning APIs, external storage).
- [ ] File storage consumption is estimated and compared against org allocation before go-live.
- [ ] Files Connect configuration uses the correct Authentication Provider type for the external system.
- [ ] Error handling covers STORAGE_LIMIT_EXCEEDED, FILE_SIZE_LIMIT_EXCEEDED, and callout failures.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **ContentDocument is auto-created and cannot be inserted directly** — Attempting to insert a ContentDocument record fails. You must insert a ContentVersion, and the platform creates the ContentDocument. Querying the ContentDocumentId back from the ContentVersion is required for linking.

2. **Base64 encoding inflates file size by 33%** — A 28 MB file becomes approximately 37 MB when base64-encoded, hitting the REST API request body limit. Developers who test with small files miss this until production files fail.

3. **No built-in virus scanning for CRM file uploads** — Unlike Salesforce Shield (which provides event monitoring), there is no native malware scanning for files uploaded via ContentVersion. Organizations assuming Salesforce scans files are exposed to compliance violations.

4. **FirstPublishLocationId can only be set on insert, not update** — If you forget to set FirstPublishLocationId during the initial ContentVersion insert, you cannot update it later. You must create a ContentDocumentLink manually instead.

5. **Files Connect is read-only for external files** — Files Connect surfaces external files inside Salesforce but does not allow writing back to the external system from Salesforce. Developers expecting bidirectional sync must implement custom callouts.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| ContentVersion upload pattern | REST multipart or base64 request structure for the given file size |
| ContentDocumentLink wiring | Record linking configuration with correct ShareType and LinkedEntityId |
| Files Connect setup guide | External Data Source and Authentication Provider configuration for the target system |
| Virus scanning implementation | Queueable Apex class and ContentVersion trigger for async malware scanning |
| Storage estimation | File storage consumption projection based on volume and org allocation |

---

## Related Skills

- `integration/rest-api-patterns` — use when the integration involves general REST API CRUD operations beyond file-specific endpoints.
- `integration/named-credentials-setup` — use when configuring the authentication for external scanning services or external storage systems.
- `integration/oauth-flows-and-connected-apps` — use when the external system calling Salesforce needs OAuth token management for file uploads.
- `security/secure-coding-review-checklist` — use when reviewing the security posture of a file integration, including input validation and access control.
