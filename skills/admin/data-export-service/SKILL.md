---
name: data-export-service
description: "Use when configuring or operating the native Salesforce Data Export Service (Setup → Data Export) — weekly or monthly CSV export, attachment inclusion, file-size split, the 48-hour download window, and the gap between this free utility and the paid Salesforce Backup and Restore product. Triggers: 'data export service', 'weekly export', 'export attachments', 'data export 48 hour download', 'data export missing objects', 'is weekly export a backup'. NOT for the paid Salesforce Backup and Restore product (use that as a separate tool), NOT for Bulk API extraction (use data/bulk-api-patterns), NOT for HA/DR architecture (use architect/ha-dr-architecture)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "we use weekly data export as our backup strategy"
  - "data export service files expired before we downloaded them"
  - "data export missing big objects or external objects"
  - "monthly export not available on Developer Edition"
  - "schedule data export attachments documents content versions"
  - "what is the difference between data export service and salesforce backup and restore"
tags:
  - data-export-service
  - weekly-export
  - monthly-export
  - csv-export
  - backup-strategy
  - operational-excellence
inputs:
  - "the org edition (determines weekly vs monthly cadence eligibility)"
  - "the records and metadata to be exported"
  - "the retention/audit obligation driving the request (real backup, ad-hoc data dump, regulatory)"
  - "the operator who will download the files within the 48-hour window"
outputs:
  - "a configured Data Export schedule with the right object scope and content options"
  - "a download / archive runbook honoring the 48-hour expiration window"
  - "a documented gap between the free service and any backup/DR obligations the org actually has"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Salesforce Data Export Service

Activate when an admin or architect is configuring **Setup → Data Management → Data Export**, evaluating whether the free service is fit for purpose, or troubleshooting an expired/missing/incomplete export. The skill produces an export configuration, a download runbook the operator can follow, and an explicit honest answer about whether the service satisfies the customer's actual backup or compliance obligation. The "weekly export is our backup" assumption is the most common audit finding in this area; this skill is what saves a downstream conversation with auditors.

---

## Before Starting

- **Edition matters.** Enterprise, Performance, Unlimited, and Developer Editions can schedule weekly exports; Professional and Essentials are limited to monthly. Schedule visibility differs by edition. Confirm before promising a cadence.
- **The 48-hour download window is non-negotiable.** Export ZIPs are deleted 48 hours after generation. The retention is not configurable. Treat the export as a delivery, not a store.
- **"Backup" obligations rarely match what the service provides.** Native Data Export is *file-level CSV with attachment-export option* — not point-in-time restore, not record-level rollback, not metadata-aware. If the user said "use this for backup," restate the actual obligation (RPO, RTO, restore-granularity) before proceeding.
- **Permissions: Weekly Data Export.** The user setting up or downloading needs the Weekly Data Export permission (named `WeeklyExport`). Without it, even a System Administrator cannot start the request from a non-default profile.

---

## Core Concepts

### What Data Export actually produces

A scheduled or one-off Data Export generates a set of zipped CSV files — one zip per chunk capped at the export's size limit (configurable up to 512 MB per file in modern orgs). Inside each zip, every selected sObject is one CSV with all retrievable fields and all retrievable rows. There is one zip set per export run; older runs are not retained beyond their 48-hour window. Documents, Attachments, Salesforce Files (ContentVersion), Chatter Files, and Salesforce CRM Content are *opt-in* checkbox toggles, not default-included.

### What it does NOT produce

- No metadata. Custom-object definitions, validation rules, flows, classes — none of it. Use Metadata API / Git for that.
- No Big Objects. The service does not export objects whose `recordType` is `BigObject`. Big Object archival data needs a separate strategy (Async SOQL, Bulk API).
- No External Objects (Salesforce Connect). External data lives elsewhere by definition.
- No restore. There is no inverse "Data Import Service" that re-applies a Data Export ZIP. Restoring requires Data Loader or Bulk API with manual reference resolution and is a multi-day operation for any org with relationships.
- No record-level point-in-time. Each export is "now"; delta from previous export must be inferred manually if needed.

### Cadence eligibility

| Edition | Cadence options |
|---|---|
| Essentials, Professional | Monthly only |
| Enterprise, Performance, Unlimited, Developer | Weekly or monthly |
| Sandbox (Developer / Developer Pro / Partial / Full) | Inherits parent license behavior; in practice weekly is allowed in Full and Partial Copy |

The "weekly" cadence is enforced at the service level — the next manual export cannot be requested until the previous one has aged 7 days, even if the prior file expired uncollected.

### Where Data Export sits relative to Salesforce Backup and Restore (paid)

Salesforce Backup and Restore is a separately-licensed add-on. It provides daily snapshots, record-level restore with relationship resolution, point-in-time recovery, and a configurable retention period. Data Export Service is a delivery utility; Backup and Restore is a managed backup product. They are not substitutes — for any org with regulatory backup obligations, the answer is one of (a) license Backup and Restore, (b) license a third-party tool (Own, Odaseva, Spanning, Veeam), or (c) build a documented warehouse-pull pipeline. "Weekly Data Export" is none of those.

---

## Common Patterns

### Pattern: ad-hoc full-org snapshot for a one-time purpose

**When to use:** auditor asks for a CSV of all account/contact/opportunity rows as of today; one-time data-warehouse seed.

**How it works:** Setup → Data Export → Export Now. Select all standard and custom objects, check Include Documents/Attachments/Files only if the consumer needs binary content (it adds hours and gigabytes). Email arrives 1–24 hours later with the download link. Operator must download within 48 hours.

**Why not the alternative:** Bulk API 2.0 produces the same CSV faster for narrowly-scoped pulls but requires API tooling and per-object query design. For a true full-org snapshot one-off, Data Export is faster to operate.

### Pattern: scheduled monthly archive shipped to long-term storage

**When to use:** the org needs a monthly evidence-grade archive but has no backup-product budget.

**How it works:** schedule monthly Data Export with a fixed object scope; assign a named operator (and a documented backup operator). On notification, the operator downloads, verifies the ZIP set checksums, and ships to S3 / Azure Blob / on-prem archive within 48 hours. The runbook captures the lineage. **Do not** describe this as "backup" in any policy document — describe it as "monthly evidence archive."

**Why not the alternative:** licensing Backup and Restore is the right answer when budget exists; this pattern is the operational fallback when it doesn't, and explicit framing prevents auditors from being misled.

### Pattern: targeted export for compliance / discovery request

**When to use:** legal hold, regulatory request, or specific-object discovery; full-org export is overkill.

**How it works:** select only the in-scope objects (often Cases + Contacts + Tasks + EmailMessage), exclude attachments unless the request requires binary content, generate, ship to legal or compliance team within 48 hours.

**Why not the alternative:** Reports + scheduled email scale poorly past a few thousand rows and have row caps; Bulk API is harder to run for non-developers. Data Export's checkbox-driven scope fits the 1–10 object compliance ask.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Regulatory backup obligation (RPO < 7 days, restore in hours) | License Salesforce Backup and Restore or a third-party tool | Data Export does not satisfy any meaningful RPO/RTO |
| One-time full-org CSV snapshot | Data Export Service "Export Now" | Single-shot, no API plumbing |
| Monthly evidence archive on a tight budget | Scheduled monthly Data Export + automated S3 upload runbook | Best-effort archive; document the gap to a real backup product |
| Bulk extract of one or two objects to a warehouse weekly | Bulk API 2.0 with PK chunking | Faster, scriptable, no 48-hour expiration |
| Restore one accidentally-deleted record | Recycle Bin (15 days) → Field History → Backup and Restore (if licensed) | Data Export has no restore path |
| Export Big Object archival data | Async SOQL → Bulk API CSV | Data Export skips Big Objects entirely |

For "should we backup at all and how?" — read `architect/ha-dr-architecture` first; this skill is the operational mechanics layer beneath that strategic choice.

---

## Recommended Workflow

1. Restate the actual obligation (real backup, ad-hoc snapshot, regulatory request) before clicking anything. Data Export Service answers some of these, not others.
2. Confirm edition and `WeeklyExport` permission for the operator. On Pro/Essentials, weekly is unavailable — set expectations or escalate licensing.
3. Decide cadence and scope: full-org vs targeted; with vs without attachments/documents/files. Attachments/files dramatically inflate generation and download time; include only when needed.
4. Schedule (or click Export Now); document the named operator and the backup operator who watches the 48-hour window.
5. Build the post-generation runbook: notification handler → download → checksum-verify → ship-to-archive → record evidence-of-receipt. The runbook is the audit artifact, not the export itself.
6. Record the documented gap to a real backup product in the org's Reliability section of the architecture doc. If Backup and Restore is licensed in the future, retire this runbook.
7. Quarterly: dry-run a restore from the most recent archive to a sandbox to verify the CSVs are complete and reload-able. Most "we have backups" claims fail their first restore drill.

---

## Review Checklist

- [ ] Cadence (weekly / monthly) matches edition eligibility
- [ ] Object scope is intentional — full-org or explicit subset, not "everything by default" without justification
- [ ] Attachments / Documents / Files / Salesforce CRM Content checkboxes deliberately set
- [ ] Big Objects, External Objects, and metadata gaps acknowledged in the runbook
- [ ] Named operator + backup operator have `WeeklyExport` permission
- [ ] Runbook covers the 48-hour download window with monitoring/alerting
- [ ] Post-download archive destination is durable and access-controlled
- [ ] Restore drill scheduled quarterly; results recorded
- [ ] Architecture doc accurately frames this as evidence archive, not record-level backup
- [ ] Any claim of "regulatory backup compliance" reviewed against real RPO/RTO

---

## Salesforce-Specific Gotchas

1. **The 48-hour window is wall-clock, not business hours** — an export finishing Friday at 6pm expires Sunday at 6pm; if your ops team isn't on a weekend rotation, schedule for Monday morning.
2. **"Include all data" includes archived records but not deleted-and-purged ones** — Recycle Bin records that have aged out are gone; Data Export does not retrieve them.
3. **Attachment / File content adds gigabytes and hours** — a 5-million-row org with 100 GB of files goes from a 20-minute export to a 6-hour export with a multi-gigabyte multi-zip ZIP set. Most teams realize this only after their download fails partway through.
4. **Big Objects are silently skipped** — the export completes successfully and reports no error, but Big Object data is absent. Audit the manifest, not just the success email.
5. **External Objects (Salesforce Connect) and indirectly-referenced data live outside the org** — they cannot be backed up via Data Export; their backup is the source-system's responsibility.
6. **Field-level encryption (Shield Platform Encryption) values are exported in clear** — once the user has FLS read on encrypted fields, the export contains plaintext. This is correct platform behavior but is a *common audit finding* when the export ZIP lands on unencrypted laptop storage.
7. **There is no incremental export** — each weekly/monthly run is a full set; deltas must be computed externally if needed (CreatedDate / LastModifiedDate filters via Bulk API are the better path for delta).
8. **Org changes (custom field additions, object renames) silently change the schema of the export between runs** — downstream loaders that pinned to a 2024 schema break when a 2026 export adds columns. Version the receiver.
9. **A failed export does not auto-retry; the next run is the next scheduled one** — an export that errors mid-generation simply fails. Without monitoring, the operator may not notice for a full cycle.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Export schedule configuration | Cadence, scope, content options documented in the org's Setup-as-code repo or runbook |
| Download runbook | Named operator/backup, 48-hour SLA, archive destination, checksum-verify step |
| Restore drill record | Quarterly evidence that the CSVs are reload-able to a sandbox |
| Documented gap statement | Architecture doc passage acknowledging this is not a record-level backup product |
| Audit-ready evidence trail | Per-export: generation date, downloaded date, downloaded by, archive location |

---

## Related Skills

- `architect/ha-dr-architecture` — for the strategic question (RPO/RTO, real backup tooling) above this skill's operational layer
- `data/bulk-api-patterns` — for delta-style scriptable extracts, the better fit when a single object needs scheduled outbound replication
- `admin/compliance-documentation-requirements` — for framing what a "compliance backup" actually requires
- `data/data-archival-strategies` — for archival of historical data (different from backup of current data)
- `security/platform-encryption` — for the FLS-clear-text-in-export concern
