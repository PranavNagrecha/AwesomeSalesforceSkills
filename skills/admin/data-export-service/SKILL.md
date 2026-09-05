---
name: data-export-service
description: "Use when configuring or operating the native Salesforce Data Export Service (Setup → Data Export) — weekly or monthly CSV export, attachment inclusion, file-size split, the 48-hour download window, and the gap between this free utility and the paid Salesforce Backup and Restore product. Triggers: 'data export service', 'weekly export', 'export attachments', 'data export 48 hour download', 'data export missing objects', 'is weekly export a backup', 'bulk api 2.0 query job export', 'data loader extract batch', 'process-conf.xml export', 'incremental export systemmodstamp', 'export inventory retention owner'. NOT for the paid Salesforce Backup and Restore product (use that as a separate tool), NOT for Bulk API extraction (use data/bulk-api-patterns), NOT for HA/DR architecture (use architect/ha-dr-architecture)."
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
  - "export salesforce data to csv on a schedule"
  - "set up a bulk api 2.0 query job to extract records"
  - "write a data loader process-conf.xml export batch"
  - "build an incremental export watermarked on systemmodstamp"
  - "grant a service user permission to export data without edit access"
  - "reconcile exported row counts against what the org holds"
  - "bulk api query job got slow after i added order by"
  - "exported csv is missing records changed by a roll-up or trigger"
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
  - "an export-inventory.json naming every object's filter, schedule, retention, owner and masking note"
  - "a read-only operator PermissionSet, and either a Data Loader process-conf.xml or a Bulk API 2.0 query job script"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Salesforce Data Export Service

Activate when an admin or architect is configuring **Setup → Data Management → Data Export**, evaluating whether the free service is fit for purpose, or troubleshooting an expired/missing/incomplete export. The skill produces an export configuration, a download runbook the operator can follow, and an explicit honest answer about whether the service satisfies the customer's actual backup or compliance obligation. The "weekly export is our backup" assumption is the most common audit finding in this area; this skill is what saves a downstream conversation with auditors.

---

## Before Starting

> **Grounding status — read this before quoting a number.** Every behaviour of the Setup → Data Export screen in this skill is documented only on help.salesforce.com, which cannot be fetched. Searching the seven Salesforce developer PDFs used to ground this repo (Metadata API, Object Reference, Data Loader, Bulk API, REST API, App Limits Cheat Sheet, LDV Best Practices) for `data export`, `weekly export`, `export service` and `48 hour` returns **one** hit in total: the Data Loader guide's aside that "Data Loader currently does not support exporting attachments. As a workaround, use the weekly export feature in the online application to export attachments" (`salesforce_data_loader.txt:916–917`). The App Limits Cheat Sheet — the canonical home of Salesforce's numeric limits — mentions the Data Export Service **nowhere**. So every UI cadence, window, size and permission figure below carries an inline UNVERIFIED marker, and the deployable artefacts in `references/metadata-examples.md` are the parts of this skill that a reviewer can actually check.

- **Edition matters.** Enterprise, Performance, Unlimited, and Developer Editions can schedule weekly exports; Professional and Essentials are limited to monthly — UNVERIFIED (2026-09-05): edition-to-cadence eligibility is help-only; no grounding PDF states it. Confirm in the target org's own Setup screen before promising a cadence, not from this table. (For contrast, the Data Loader guide *does* state its own edition scope in an EDITIONS box — "Available in: Enterprise, Performance, Unlimited, and Developer editions", `salesforce_data_loader.txt:115–117` — so the artefacts in `references/metadata-examples.md` inherit that constraint, grounded.)
- **The 48-hour download window is non-negotiable.** Export ZIPs are deleted 48 hours after generation and the retention is not configurable — UNVERIFIED (2026-09-05): help-only; no grounding PDF states the 48-hour figure or that it is fixed. Treat the export as a delivery, not a store. The grounded contrast is worth knowing before you choose a path: Bulk API 2.0 query job results are retrievable "within 7 days of job completion" (`salesforce_app_limits_cheatsheet.txt:909–912`), which is a collection window an on-call rotation can actually meet.
- **"Backup" obligations rarely match what the service provides.** Native Data Export is *file-level CSV with attachment-export option* — not point-in-time restore, not record-level rollback, not metadata-aware. If the user said "use this for backup," restate the actual obligation (RPO, RTO, restore-granularity) before proceeding.
- **Permissions: Weekly Data Export.** The user setting up or downloading needs the Weekly Data Export permission, whose API name is commonly given as `WeeklyExport` — UNVERIFIED (2026-09-05): the string does not appear anywhere in the Metadata API guide text; `grep -in "weekly" api_meta.txt` returns only schedule/recurrence enum values. Deploy the permission set from `references/metadata-examples.md` § 2 to a scratch org to confirm the spelling before shipping it. What *is* grounded is the API-side requirement: `ApiEnabled` is the guide's own `userPermissions` example (`api_meta.txt:95216`), and the Data Loader guide names "Read on the records" — not `ViewAllData` — as the export permission (`salesforce_data_loader.txt:848–856`).

---

## Questions to Ask Before Configuring

Ask these before opening Setup or writing a line of SOQL. Each one traces to a gotcha in `references/gotchas.md`, and each one changes the artefact you produce — an LLM that skips them writes a plausible export that loses rows nobody misses until an audit.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is the obligation — record-level restore, evidence archive, one-off snapshot, or a discovery request?" | Only one of those four is a job Data Export Service can do; restore is not a thing it has | The tool decision, and the sentence that goes in the architecture doc instead of the word "backup" |
| "Who reads the output, and can they be running on Linux or in CI?" | The Data Loader command-line interface "is supported for Windows only" (`salesforce_data_loader.txt:1213`, `:1922`, `:2062`) | Which artefact you build: `process-conf.xml` (Windows host) or a Bulk API 2.0 query job (anywhere) — §3 vs §5 of `references/metadata-examples.md` |
| "Is this a full snapshot every run, or a delta — and who has ever verified the delta catches everything?" | A delta watermarked on `LastModifiedDate` misses every row changed by platform automation (Gotcha 9) | The watermark field (`SystemModstamp`), both window bounds, and the full-refresh cadence that covers cross-object derived values |
| "Do deletions have to be visible in the archive?" | `queryAll` "returns records that have been deleted because of a merge or delete" (`api_asynch.txt:2959–2961`); plain `query` filters them out | A per-object `query` / `queryAll` choice in `export-inventory.json`, and whether a delete-log reconciliation is needed at all (Gotcha 14) |
| "Which of these objects carry PII, and where does masking happen — in Salesforce, in flight, or at the destination?" | Shield-encrypted fields export in clear to anyone whose FLS allows read (Gotcha 3); the destination inherits the compliance obligation | A `maskingNote` per object naming the transform and the boundary, which the checker requires whenever `containsPii` is true |
| "How long does each object's output live at the destination, and who owns deleting it?" | Retention is per-object, not per-export; the PII object usually needs a shorter clock than the reference object | Per-object `retentionDays` and a named `owner`, both linted against the org's stated policy ceiling |
| "Does anyone downstream parse these CSVs on a fixed schema?" | Org customization changes the column set between runs (Gotcha 5) | Either a schema-tolerant loader or a version-pinned one plus a change-management hook when fields are added |

What a proper configuration adds over just running the export: the object list, its filters, its watermark, its retention and its owner live in a file a reviewer can diff and a script can lint, so the claim "we archive our Salesforce data" becomes checkable rather than believed.

---

## Core Concepts

### What Data Export actually produces

A scheduled or one-off Data Export generates a set of zipped CSV files — one zip per chunk capped at the export's size limit, configurable up to 512 MB per file in modern orgs — UNVERIFIED (2026-09-05): the 512 MB ceiling and the split behaviour are help-only; the App Limits Cheat Sheet does not carry them. Inside each zip, every selected sObject is one CSV with all retrievable fields and all retrievable rows. There is one zip set per export run; older runs are not retained beyond their 48-hour window — UNVERIFIED (2026-09-05): help-only, as above. Documents, Attachments, Salesforce Files (ContentVersion), Chatter Files, and Salesforce CRM Content are *opt-in* checkbox toggles, not default-included — UNVERIFIED (2026-09-05): the checkbox set and its defaults are help-only. The one adjacent grounded fact is that Data Loader cannot substitute for the binary path: "Data Loader currently does not support exporting attachments. As a workaround, use the weekly export feature in the online application to export attachments" (`salesforce_data_loader.txt:916–917`).

### What it does NOT produce

Each bullet here is a *help-only* claim — UNVERIFIED (2026-09-05): none of the seven grounding PDFs describes what the Data Export Service does or does not include, because none of them mentions the service at all.

- No metadata. Custom-object definitions, validation rules, flows, classes — none of it. Use Metadata API / Git for that.
- No Big Objects. Big Object archival data needs a separate strategy (Async SOQL, Bulk API). *(Corrected 2026-09-05: an earlier revision of this line said the service "does not export objects whose `recordType` is `BigObject`". No such mechanism is documented — the Metadata API guide text contains no `BigObject` token at all (`grep -n "BigObject" api_meta.txt` returns nothing), so there is no `recordType` value to test. The exclusion claim stands as help-only; the mechanism offered for it was invented.)*
- No External Objects (Salesforce Connect). External data lives elsewhere by definition.
- No restore. There is no inverse "Data Import Service" that re-applies a Data Export ZIP. Restoring requires Data Loader or Bulk API with manual reference resolution and is a multi-day operation for any org with relationships.
- No record-level point-in-time. Each export is "now"; delta from previous export must be inferred manually if needed. When a delta is what you actually need, build it with a `SystemModstamp` watermark through `references/metadata-examples.md` § 1 and § 5 rather than diffing two ZIP sets.

### Cadence eligibility

UNVERIFIED (2026-09-05): the whole table below is help-only — edition-to-cadence eligibility appears in none of the grounding PDFs. Read it as a prompt to check the org, not as a fact to quote to a customer.

| Edition | Cadence options |
|---|---|
| Essentials, Professional | Monthly only |
| Enterprise, Performance, Unlimited, Developer | Weekly or monthly |
| Sandbox (Developer / Developer Pro / Partial / Full) | Inherits parent license behavior; in practice weekly is allowed in Full and Partial Copy |

The "weekly" cadence is enforced at the service level — the next manual export cannot be requested until the previous one has aged 7 days, even if the prior file expired uncollected — UNVERIFIED (2026-09-05): the 7-day cooldown and its behaviour after an expired file are help-only.

### Where Data Export sits relative to Salesforce Backup and Restore (paid)

Salesforce Backup and Restore is a separately-licensed add-on. It provides daily snapshots, record-level restore with relationship resolution, point-in-time recovery, and a configurable retention period — UNVERIFIED (2026-09-05): the Backup and Restore feature set and its cadence are help-only; the product appears in none of the grounding PDFs. Confirm the current capability list with the account team before it lands in a proposal. Data Export Service is a delivery utility; Backup and Restore is a managed backup product. They are not substitutes — for any org with regulatory backup obligations, the answer is one of (a) license Backup and Restore, (b) license a third-party tool (Own, Odaseva, Spanning, Veeam), or (c) build a documented warehouse-pull pipeline. "Weekly Data Export" is none of those.

---

## Common Patterns

### Pattern: ad-hoc full-org snapshot for a one-time purpose

**When to use:** auditor asks for a CSV of all account/contact/opportunity rows as of today; one-time data-warehouse seed.

**How it works:** Setup → Data Export → Export Now. Select all standard and custom objects, check Include Documents/Attachments/Files only if the consumer needs binary content (it adds hours and gigabytes). Email arrives 1–24 hours later with the download link, and the operator must download within 48 hours — UNVERIFIED (2026-09-05): generation latency and the 48-hour window are help-only.

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

1. **Restate the obligation, then pick the artefact.** Real backup, evidence archive, one-off snapshot, or discovery request — only the middle two are jobs this service does. Then answer the Windows question from `## Questions to Ask Before Configuring`: a Windows batch host gets `references/metadata-examples.md` § 3 (`process-conf.xml`), anything else gets § 5 (Bulk API 2.0 query job), and the Setup UI gets neither because it produces no reviewable artefact.
2. **Write `export-inventory.json` first, before touching Setup or SOQL.** Use the shape in `references/metadata-examples.md` § 1: per object, an `apiName`, `mode`, `filter`, `soql`, `schedule`, `retentionDays`, `owner`, `containsPii` and — where PII is present — a `maskingNote` that names the transform and the boundary it happens at. Anything you cannot fill in is a question for the requester, not a default to guess.
3. **Set the watermark and the operation deliberately.** Every `mode: "incremental"` object filters on `SystemModstamp` with *both* bounds (Gotcha 9, Gotcha 11). Every object where deletions must survive into the archive uses `operation: "queryAll"` and selects `IsDeleted` (Gotcha 14). No export query carries `ORDER BY` or `LIMIT` (Gotcha 10).
4. **Build the operator permission set from `references/metadata-examples.md` § 2**, read-only by construction: `ApiEnabled`, `allowRead` on exactly the objects in the inventory, every write flag explicitly `false`. Deploy it with `--dry-run` first — a permission set naming a user permission that does not exist fails the whole deployment, and `WeeklyExport` is the name this skill cannot verify.
5. **Run `python3 scripts/check_data_export_service.py --manifest-dir <dir>`** over the directory holding the inventory, the permission set XML, the `process-conf.xml`, and the runbook markdown. It fails on: an object missing filter/schedule/retention/owner, an incremental filter not watermarked on `SystemModstamp`, retention above the declared policy ceiling, a PII object with no masking note, an extract bean missing `sfdc.extractionSOQL` or not set to `dataAccess.type=csvWrite`, a permission set granting write access, and a runbook that calls the service a backup without naming the no-restore gap. Fix every ERROR before anything is scheduled.
6. **Verify against the org, not against the job's own success message.** Run the four checks in `references/metadata-examples.md` § Verification: the `PermissionSetAssignment` query, the row-count reconciliation against the CSV line count minus the header, the `IsDeleted` count that proves `queryAll` actually ran, and the delete-log call whose `earliestDateAvailable` tells you what the window really covered.
7. **Record the gap and schedule the drill.** Put the honest framing ("evidence archive, not record-level backup") into the architecture doc via `templates/data-export-service-template.md`, and book a quarterly reload of the most recent archive into a sandbox. Most "we have backups" claims fail their first restore drill, which is the only reason the drill is worth its cost.

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

*(UNVERIFIED (2026-09-05) applies to items 1–5 and 9 below: every Data Export Service UI behaviour they describe is help-only. Items 6, 7 and 8 are platform behaviours that hold regardless of which export tool you use, and `references/gotchas.md` grounds those plus six more.)*

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

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing the actual artefacts — `export-inventory.json`, the operator `PermissionSet` XML, a Data Loader `process-conf.xml` extract bean, `config.properties`, or a Bulk API 2.0 query-job script — plus `package.xml`, the deploy commands, and the four verification queries |
| `references/gotchas.md` | Something ran green and produced a wrong archive: a delta that dropped trigger-changed rows, a query that got slow after `ORDER BY`, a widening window that stopped using its index, Console SOQL that Data Loader rejects, a 24-hour ceiling nobody read, or a delete-log reconciliation that errored instead of truncating |
| `references/well-architected.md` | You need the Reliability / Operational Excellence / Security framing for a review, the Data Export vs Backup-and-Restore vs Bulk API tradeoff tables, or the exact official source behind a claim in this skill |
| `references/llm-anti-patterns.md` | You are checking AI-generated export guidance — anything that calls this "backup", claims an API trigger for the UI service, omits the 48-hour window, or checks every binary box "to be safe" |
| `templates/data-export-service-template.md` | Before configuring anything, to capture the obligation restate, the config, the acknowledged gaps, the operator runbook and the archive destination in one reviewable place |
| `scripts/check_data_export_service.py` | After writing the artefacts and before scheduling — `--manifest-dir <dir>` lints the inventory JSON, the permission set XML and the `process-conf.xml`, and scans runbook prose for the framing gaps |

## Related Skills

- `architect/ha-dr-architecture` — for the strategic question (RPO/RTO, real backup tooling) above this skill's operational layer
- `data/bulk-api-patterns` — for delta-style scriptable extracts, the better fit when a single object needs scheduled outbound replication
- `admin/compliance-documentation-requirements` — for framing what a "compliance backup" actually requires
- `data/data-archival-strategies` — for archival of historical data (different from backup of current data)
- `security/platform-encryption` — for the FLS-clear-text-in-export concern
