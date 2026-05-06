# LLM Anti-Patterns — Salesforce Backup and Restore

Common mistakes AI coding assistants make when generating or advising
on Salesforce backup-and-restore strategy.

---

## Anti-Pattern 1: Recommending Recycle Bin as a "backup"

**What the LLM generates.**

> To recover deleted records in Salesforce, restore them from the
> Recycle Bin. The Recycle Bin keeps deleted records for up to 15
> days, providing a built-in backup mechanism.

**Why it happens.** Training data conflates "soft delete" with
"backup". Recycle Bin is a delete buffer, not a backup. It has no
coverage for modified records, no coverage past 15 days, no coverage
for hard deletes.

**Correct pattern.**

> The Recycle Bin holds soft-deleted records for up to 15 days
> (capacity-bounded; the oldest entries auto-purge once the bin fills).
> It does not cover modified records, hard deletes, or losses
> discovered after the window. For real recovery, use Salesforce
> Backup, a third-party tool, or self-rolled Bulk API extracts.

**Detection hint.** "Recycle Bin" appearing in a recommended backup
strategy is a red flag. The LLM is not distinguishing delete-buffer
from backup.

---

## Anti-Pattern 2: Suggesting Weekly Data Export as the answer

**What the LLM generates.**

> Schedule the Weekly Data Export from Setup → Data Export. This is
> Salesforce's built-in backup feature.

**Why it happens.** The Weekly Data Export was the canonical answer
for years. The LLM has not absorbed the deprecation announcement and
its replacement guidance.

**Correct pattern.**

> The Weekly Data Export Service has been retired. The native
> replacement is Salesforce Backup. The developer-facing alternative
> is to script a Bulk API 2.0 export to external storage. Confirm the
> retirement timeline for your edition in the latest Release Notes.

**Detection hint.** Any recommendation referencing "Setup → Data
Export" or "Weekly Data Export Service" as the recovery plan needs
review.

---

## Anti-Pattern 3: A naive Bulk API restore script that ignores relationships

**What the LLM generates.**

```python
# "Restore" by re-inserting CSVs
for obj in ['Account', 'Contact', 'Opportunity']:
    bulk_api.insert(obj, read_csv(f'{obj}.csv'))
```

**Why it happens.** The LLM treats restore as "load CSVs in some
order". It does not handle the new-Id problem (children's lookup
fields point at deleted Ids), self-relationships, or polymorphic
lookups.

**Correct pattern.** Insert parents first, capture the Id mapping
(old-Id → new-Id), update children's lookup CSVs to reference new
Ids, then insert children. For self-relationships (`Account.ParentId`)
do a two-pass insert. For polymorphic lookups (`Task.WhatId`),
preserve the type prefix when remapping.

**Detection hint.** Any restore script that inserts more than one
related object without an explicit Id-mapping step is broken.

---

## Anti-Pattern 4: Promising a sub-daily RPO with native Salesforce Backup

**What the LLM generates.**

> Salesforce Backup runs continuously and provides near-zero RPO.

**Why it happens.** Marketing-tone training data with no specific
cadence number. The LLM extrapolates "automated" to mean "real-time".

**Correct pattern.**

> Salesforce Backup runs on a daily schedule. Sub-daily RPO requires
> a third-party tool that supports more frequent snapshots, or a
> Change Data Capture stream consumed into an external store.

**Detection hint.** Any unqualified "near-zero RPO" claim in a
backup-strategy recommendation needs the cadence pinned down.

---

## Anti-Pattern 5: Confusing sandbox refresh with disaster recovery

**What the LLM generates.**

> For disaster recovery, refresh a Full sandbox from production daily
> and use the sandbox as the restore source if production is lost.

**Why it happens.** Sandboxes are the most-discussed copy-of-production
mechanism in Salesforce training data. The LLM does not distinguish
"copy for development" from "recovery point".

**Correct pattern.** Sandbox refresh is a development tool; it is not
a supported disaster-recovery flow. There is no native sandbox →
production data restore. DR requires a real backup tool (Salesforce
Backup or a third-party).

**Detection hint.** Any DR plan that lists "refresh sandbox" as a
recovery step is wrong.

---

## Anti-Pattern 6: Ignoring file content in backup sizing

**What the LLM generates.** A backup recommendation focused entirely
on record counts, with no mention of file storage (ContentVersion
binary content).

**Why it happens.** The LLM treats Salesforce data as relational rows
only. File storage is a parallel, often larger, dimension.

**Correct pattern.** Confirm whether the backup tool captures
ContentVersion file content (binary), how it is priced, and the
restore semantics for files (re-uploading a binary versus restoring
a record). For orgs with significant file storage this is a major
cost / time factor.

**Detection hint.** A backup plan that omits "files / attachments"
as a line item.

---

## Anti-Pattern 7: Assuming `query` captures soft-deleted rows

**What the LLM generates.**

```apex
List<Account> snapshot = [SELECT Id, Name FROM Account];
// "snapshot for backup"
```

**Why it happens.** The LLM does not surface that `query` (and SOQL
without `ALL ROWS`) silently filters out `IsDeleted = true` rows.

**Correct pattern.** For a complete snapshot use `queryAll` in the
REST / Bulk API, or `SELECT ... ALL ROWS` in Apex. Then explicitly
choose whether to include or exclude soft-deleted rows.

**Detection hint.** Any backup-extract code using `query` (not
`queryAll`) or SOQL without `ALL ROWS` is incomplete.
