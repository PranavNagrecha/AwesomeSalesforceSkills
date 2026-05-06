---
name: salesforce-backup-and-restore
description: "Designing a backup and restore strategy for a Salesforce org — Salesforce Backup (the native paid product), the deprecated weekly Data Export Service, third-party tools (OwnBackup / Druva / Gearset / Spanning), and self-rolled Bulk API extracts. Covers RPO / RTO targeting, restore-of-a-single-record vs full-org restore, parent / child relationship rebuilding, and cost / coverage tradeoffs across vendors. NOT for sandbox refresh strategy (see devops/sandbox-strategy), NOT for metadata source-control / DevOps backups (see devops/sfdx-source-control)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "salesforce backup and restore native product pricing"
  - "weekly data export service deprecated retired replacement"
  - "ownbackup druva gearset spanning third-party backup comparison"
  - "rpo rto recovery point objective recovery time objective salesforce"
  - "restore deleted records relationships rebuild parent child"
  - "self-roll backup bulk api scheduled export"
  - "ransomware accidental delete data loader undo"
tags:
  - backup
  - disaster-recovery
  - rpo-rto
  - data-export
  - third-party-tools
inputs:
  - "RPO / RTO targets the business committed to (e.g. 24h RPO, 4h RTO)"
  - "Org volume (record counts per top-N objects, file storage, attachments)"
  - "Existing tooling (Salesforce Backup license, third-party vendor, none)"
outputs:
  - "Backup-strategy decision matrix (native vs third-party vs self-roll)"
  - "Restore runbook covering single-record, hierarchical, and full-object scenarios"
  - "RPO / RTO gap analysis vs current state"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Salesforce Backup and Restore

Salesforce stores customer data on a multi-tenant platform with high
durability — but durability is not the same as recoverability. The
platform protects against hardware loss; it does not protect against the
admin who runs Data Loader against the wrong filter, the integration
that sets `Status__c = NULL` on 200,000 cases, or the Apex deploy that
silently `delete`s a million rows. Recovering from those events is a
data-management problem the customer owns.

This skill helps you reach a backup-and-restore strategy that matches
the business's RPO and RTO targets without overspending on coverage you
don't need.

The product landscape is messy. The legacy **Weekly Data Export
Service** (Setup → Data Export) is being retired — Salesforce announced
deprecation with replacement guidance pointing to Salesforce Backup.
**Salesforce Backup** is the native paid product (formerly "Backup &
Restore" / Salesforce Data Backup) and provides daily backups plus
relationship-aware restore. **Third-party tools** (OwnBackup —
acquired and rebranded as Own; Druva; Gearset; Spanning) compete on
restore UX, sandbox seeding, anomaly detection, and cross-org compare.
**Self-rolled** uses the Bulk API 2.0 to extract records on a schedule
and stores them in S3 / Azure Blob / GCS — cheapest, but you own
restore.

The hard part isn't the backup. It's the restore. Restoring a single
deleted Account from Recycle Bin is trivial (15-day window). Restoring
a parent-child hierarchy of Accounts → Contacts → Opportunities →
OpportunityLineItems → Quotes after a 30-day-old corruption — with
referential integrity preserved — is a project. Most teams don't
discover their backup strategy is inadequate until they need it.

## Recommended Workflow

1. **Establish the RPO and RTO with the business.** RPO is the maximum acceptable data loss window (e.g. 24 hours of changes). RTO is the maximum acceptable time-to-restored (e.g. 4 hours). These two numbers determine the entire strategy.
2. **Inventory the current state.** Is Salesforce Backup licensed? Is a third-party tool deployed? Is the Weekly Data Export still being used? When was the last successful backup verified by a real restore drill?
3. **Map the failure scenarios.** Single-record accidental delete (Recycle Bin handles 15 days). Mass update / mass delete by integration (Recycle Bin won't help past 15 days, and large hard-deletes skip Recycle Bin entirely). Ransomware / malicious actor (need point-in-time per-object restore). Org corruption / merger gone wrong (need full-org snapshot).
4. **Pick the tooling tier** based on the gap between current state and target. See the decision matrix in `references/examples.md` § 4.
5. **Define the restore runbook.** Who initiates, who approves, what's the priority order of objects (parents before children), how is referential integrity verified, how is the user-base notified. A backup tool without a runbook is dead weight.
6. **Run a restore drill.** Pick a non-critical custom object, delete some records in a sandbox, restore from backup, verify counts and relationships. Schedule this quarterly. If you have never restored from your backup, you do not have a backup.
7. **Document the residual risk.** Even with daily backups, there is a 24-hour RPO floor. Document where the gap is and which scenarios are not covered (e.g. configuration / metadata changes — those need source control, not data backup).

## What This Skill Does Not Cover

| Topic | See instead |
|---|---|
| Sandbox refresh strategy | `devops/sandbox-strategy` |
| Metadata source control and rollback | `devops/sfdx-source-control` |
| Field history tracking and audit trail | `data/field-history-tracking` |
| Big Objects archival | `data/big-objects-patterns` |
