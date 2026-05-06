# Gotchas — Salesforce Backup and Restore

Non-obvious Salesforce platform behaviors that bite real backup-and-
restore practitioners.

---

## Gotcha 1: Recycle Bin only holds **deleted** records, not modified ones

**What happens.** Admin runs a Data Loader update that overwrites
fields on 50,000 records. Discovers the mistake the next day and tries
to "restore from Recycle Bin". The records are not in the Recycle Bin
because they were never deleted.

**When it occurs.** Any time someone treats Recycle Bin as a generic
"undo" mechanism for data changes.

**How to avoid.** Recycle Bin is delete-only. Modified records require
a backup tool that captures field-level history or daily snapshots.
Field History Tracking is a partial mitigation but only retains 18
months and only on tracked fields (max 20 per object).

---

## Gotcha 2: Hard deletes skip the Recycle Bin entirely

**What happens.** Bulk API hard delete (`hardDelete=true`) or Apex
`Database.emptyRecycleBin()` removes records with no soft-delete
window. The records do not pass through Recycle Bin and cannot be
restored within 15 days.

**When it occurs.** Cleanup jobs frequently use hard delete to avoid
filling the Recycle Bin. Apex with `Database.delete(records, false)`
followed by `emptyRecycleBin` is also a hard delete in effect.

**How to avoid.** Reserve hard delete for genuinely disposable data
(test records, expired temp). Treat any production hard-delete job as
a destructive deployment that must be backed up beforehand and
peer-reviewed.

---

## Gotcha 3: 15-day Recycle Bin retention is **rolling** and capacity-bounded

**What happens.** Recycle Bin appears empty even though deletes
happened 10 days ago. The bin has a per-org capacity of 25 times the
storage allocation in records — when it fills, the oldest deleted
records are auto-purged before 15 days elapse.

**When it occurs.** Mass-delete jobs that delete more than capacity
allows. The platform silently purges the oldest entries to make room
for new ones.

**How to avoid.** Treat Recycle Bin as a 15-day-or-less safety net,
never as a 15-day guarantee. Real recovery for deletes older than a
day should come from backups, not the bin.

---

## Gotcha 4: Restoring a record assigns a new Id

**What happens.** Account is deleted, then restored from a third-party
backup. Lightning links and integrations using the original Id break,
because restored records receive a new Id.

**When it occurs.** All restore tools that re-insert deleted records.
Even the Recycle Bin's "Undelete" preserves the original Id only
within the 15-day window — once purged and restored from a backup,
the record is a new row.

**How to avoid.** Use External Id fields as the durable join key for
integrations. Document for the business that bookmark URLs to deleted
records will not survive a restore.

---

## Gotcha 5: Salesforce Backup runs daily; sub-daily RPO is not native

**What happens.** Business commits to a 4-hour RPO. Native Salesforce
Backup runs once per day and cannot meet this. Discovery happens
post-purchase.

**When it occurs.** Reading marketing collateral that emphasizes
"automated backups" without checking the cadence.

**How to avoid.** Confirm the backup cadence in the official Salesforce
Backup documentation before sizing your RPO commitment. For sub-daily
RPO, evaluate third-party tools (some offer hourly) or supplement with
Change Data Capture into an external store.

---

## Gotcha 6: ContentVersion / ContentDocument files balloon backup size

**What happens.** A 2 GB file uploaded as a Salesforce File becomes a
ContentVersion record. Most backup tools include file content by
default. Org with 500 GB of files takes an order of magnitude longer
to back up than the record-count alone suggests.

**When it occurs.** Orgs that store large attachments (engineering
drawings, contracts, video). The file storage allowance is separate
from data storage in Salesforce, but for backup purposes both must be
captured.

**How to avoid.** Confirm with the backup vendor whether file content
is in scope and how it is priced (per-GB versus per-record). Plan
storage capacity at the backup tier accordingly.

---

## Gotcha 7: Self-rolled Bulk API extracts cannot capture deleted-but-not-yet-purged rows without `queryAll`

**What happens.** A self-rolled nightly export uses `query` rather
than `queryAll`. Records soft-deleted within the prior 24 hours are
missing from the export.

**When it occurs.** Engineers writing first-time backup scripts who
are not aware of the `IsDeleted` filter that `query` applies
implicitly.

**How to avoid.** Use `queryAll` (REST and Bulk API support it) when
the goal is a complete snapshot including soft-deleted rows. Then
filter on `IsDeleted = true` explicitly to record what was deleted in
the window — useful as an audit signal.

---

## Gotcha 8: Restoring a record does not re-fire triggers, flows, or workflow rules in your control

**What happens.** Restore tool re-inserts 12,000 Opportunities. None
of the dependent Apex triggers, flows, or assignment rules fire in
the way the records expect — sometimes they do (re-insert is an
insert event from Apex's perspective), sometimes the tool uses
`disable triggers` mode to avoid duplicate side effects.

**When it occurs.** Every restore. Behavior varies by tool. Some
defaults are silent.

**How to avoid.** Read the backup tool's restore documentation for
trigger / flow handling. Decide explicitly whether your restore should
re-run automation (likely "no" for a corruption recovery) or skip it
(likely "yes" for an after-the-fact reconstruction). Test in a
sandbox.

---

## Gotcha 9: There is no native cross-org restore

**What happens.** Production org is corrupted. Plan was to "restore
from sandbox". Sandboxes are point-in-time copies but not synchronized
restore targets, and restoring metadata + data from a sandbox into
production is not a supported recovery flow.

**When it occurs.** Teams confusing sandbox refresh with disaster
recovery. They are different things — sandbox is for development;
backup is for recovery.

**How to avoid.** Treat sandboxes as development resources only. For
DR, use a real backup product. Document this distinction in the
runbook so on-call engineers don't confuse the two during an
incident.
