---
name: file-upload-virus-scanning
description: "Use when designing malware and content scanning for files uploaded to Salesforce (Files, Attachments, ContentVersion) — external scanning service callouts, quarantine patterns, and user-facing messaging. Triggers: 'virus scan salesforce upload', 'malware scan content version', 'quarantine uploaded file', 'clamav salesforce', 'file upload security'. NOT for field-level data validation."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - User Experience
triggers:
  - "scan uploaded files for malware"
  - "how to integrate clamav with salesforce files"
  - "quarantine infected contentversion"
  - "virus scan experience cloud uploads"
  - "customer-facing portal file scan"
tags:
  - security
  - files
  - malware-scanning
  - quarantine
  - content-version
inputs:
  - "upload surfaces (LWC, Experience Cloud, Email-to-Case, API)"
  - "scanning service (ClamAV, Cloudmersive, third-party)"
  - "quarantine policy and user-facing behavior"
outputs:
  - "scan integration design"
  - "quarantine state machine"
  - "user-facing messaging for infected/pending states"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# File Upload Virus Scanning

Salesforce does not scan files. Any file uploaded into ContentVersion, Attachment, or a Document object is trusted bytes until you prove otherwise. For internal-only orgs the risk is moderate; for Experience Cloud portals, Email-to-Case, partner portals, and any surface that accepts uploads from unauthenticated or lightly authenticated users, the risk is substantial. Ransomware, credential stealers, and polyglot files routinely ride in on expected-looking PDFs and spreadsheets.

The architecture is the same across scanning providers: intercept uploads, send the byte stream (or hash) to a scanning service, route based on the verdict, and expose state to consumers. The design choices are where to intercept, how to handle large files, what "pending" looks like to the user, and how to quarantine without deleting audit trail.

---

## Before Starting

- List every upload surface: LWC components, standard pages, Email-to-Case, Web-to-Case, API integrations, Experience Cloud, mobile app.
- Identify the file types and size ranges in scope.
- Choose scanning service (hosted ClamAV, Cloudmersive Virus Scan, MetaDefender, etc.) — confirm SLA and throughput.
- Define quarantine policy: block, allow-with-warning, or allow-after-review.

## Core Concepts

### Interception Points

1. **Pre-save trigger** on ContentVersion — inspects inserts before the file is indexed/shared.
2. **Post-save async** on ContentVersion — scans via a Queueable after commit; toggles a `ScanStatus__c` field.
3. **Flow on Attachment** — legacy object; same pattern.
4. **Middleware interception** — scan happens in MuleSoft / Apigee before Salesforce sees the bytes.

Pre-save interception is cleanest but blocks the user on scan latency. Post-save async avoids the block at the cost of a scan-pending window.

### State Machine

A scanned file should live in one of:

- `Scan_Pending` — uploaded, not yet scanned.
- `Scan_Clean` — passed; fully available.
- `Scan_Infected` — failed; quarantined.
- `Scan_Error` — scanner unreachable; policy decides (block or allow-with-warning).

Sharing, preview, and download must honor the state. `Scan_Pending` files should typically not be previewable or shareable externally.

### Quarantine Without Deletion

Deleting infected files destroys audit trail. Preferred: retain the ContentVersion record with restricted sharing, strip the preview, redact the blob (or move to a dedicated quarantine library), and mark the state.

### Large-File And Timeout Handling

Most scanning services cap at ~100 MB or ~10 minutes. For larger files use chunked scanning or a side-channel scanner that reads from the file storage directly (signed URL + external scanner + result webhook).

---

## Common Patterns

### Pattern 1: Post-Save Queueable With State Field

ContentVersion insert fires a trigger that enqueues a Queueable. The Queueable hashes or streams to the scanner and updates `ScanStatus__c`. Consumers read the state field.

### Pattern 2: Signed URL + External Scanner + Webhook

Salesforce hands the scanner a signed URL (via Content Distribution or a public ShareType), scanner reads directly, posts verdict to a webhook endpoint. Best for large files.

### Pattern 3: Middleware-Pre-Scan

Uploads route through MuleSoft or a front-proxy that scans before handing bytes to Salesforce. Clean separation but requires that all upload paths funnel through middleware.

### Pattern 4: Allow-With-Warning For Trusted Surfaces

Internal uploads get `Scan_Pending → Clean` fast path. Experience Cloud uploads block sharing until `Clean`. Differentiates risk by surface.

### Pattern 5: Scheduled Rescan

All files rescanned on a cadence against updated signature databases. Critical for files uploaded before a new malware signature existed.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Internal-only org, moderate sensitivity | Post-save async (Pattern 1) | Best UX with adequate coverage |
| Customer portal / Experience Cloud | Pre-save or middleware (Pattern 3) | Untrusted source |
| Files > 50 MB | Signed URL + webhook (Pattern 2) | Avoid callout timeouts |
| Highly regulated industry | Pre-save block + scheduled rescan (Pattern 5) | Defense in depth |
| Public-facing file downloads | Always `Clean`-gated | Do not serve unscanned bytes |

## Well-Architected Pillar Mapping

- **Security** — scan is a primary defense for any multi-tenant upload surface.
- **Reliability** — explicit state and rescan strategy prevent silent failures.
- **User Experience** — scan-pending messaging must be honest; users should know a file is not yet shareable.

## Review Checklist

- [ ] Every upload surface intercepts or the policy justifies skipping.
- [ ] State machine implemented on ContentVersion (or Attachment).
- [ ] Sharing and preview honor `Scan_Pending` / `Scan_Infected`.
- [ ] Infected files retained for audit; blob redacted or moved.
- [ ] Large-file handling (> 50 MB) uses out-of-band scanning.
- [ ] Scheduled rescan cadence defined.
- [ ] Monitoring on scan failures / queue depth.

## Recommended Workflow

1. Inventory upload surfaces and classify by trust level.
2. Choose scanning service; confirm SLA, throughput, file-size cap.
3. Design state machine on ContentVersion; add `ScanStatus__c`.
4. Implement pre-save or post-save interception appropriate to the surface.
5. Gate sharing, preview, and external download on `Clean` state.
6. Add monitoring and a scheduled rescan job.

---

## Salesforce-Specific Gotchas

1. ContentDocument is shared broadly by default; sharing honors Content Delivery settings, not your `ScanStatus__c`.
2. Email-to-Case attachments create ContentVersions out-of-band; the trigger fires, but the user may never see the quarantine.
3. Preview generation happens async — infected files can have a preview created before your scan completes.
4. `ContentVersion` is insert-only for the file blob; you cannot "clean" a file, only quarantine metadata and redact downstream.
5. Scanner timeouts produce `Scan_Error`; policy must specify fail-open vs fail-closed.

## Proactive Triggers

- ContentVersion trigger writes `Clean` without invoking a scanner → Flag Critical.
- Sharing rule not gated on `ScanStatus__c` → Flag High.
- Experience Cloud upload surface with no interception → Flag Critical.
- No scheduled rescan → Flag Medium.
- Quarantine that deletes the record → Flag High. Audit trail lost.

## Output Artifacts

| Artifact | Description |
|---|---|
| Upload surface inventory | Each surface, trust level, interception plan |
| State machine | States, transitions, and who can read each |
| Quarantine runbook | Steps to quarantine without losing audit |

## Related Skills

- `security/experience-cloud-security` — customer-facing surface hardening.
- `security/data-classification-labels` — classifying files by sensitivity.
- `integration/webhook-inbound-patterns` — scan-result webhooks.
- `security/platform-encryption` — encryption of stored files.
