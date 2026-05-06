# Examples — Salesforce Backup and Restore

## Example 1 — Recycle Bin is not a backup strategy

**Context.** Admin runs Data Loader update with the wrong column
mapping; sets `Stage__c = 'Closed Lost'` on 12,000 active opportunities.
Discovered three weeks later when revenue forecasts crater.

**What the Recycle Bin gives you.** Nothing. Recycle Bin only holds
**deleted** records, not updated ones. Even for deletes it is bounded:

- 15-day retention window.
- Per-org capacity of 25 times storage allocation (in records).
- Hard deletes (`emptyRecycleBin`, Bulk API hard delete) skip the bin entirely.

**What you actually need.** A point-in-time backup from before the bad
update ran. Native Salesforce Backup retains daily snapshots; third-party
tools typically retain 30+ days; self-rolled depends on your retention
policy.

**Right answer.** Identify the timestamp of the bad load, restore the
12,000 affected opportunities from the prior day's snapshot, manually
reconcile any legitimate updates that happened after the bad load.

---

## Example 2 — The 15-day Recycle Bin window for hard deletes

**Context.** Integration sets `IsDeleted = true` via Bulk API hard
delete on 800,000 closed cases as part of a "data cleanup" job. Six
months later, audit asks for those cases.

**What the Recycle Bin gives you.** Nothing — hard deletes never enter
the Recycle Bin.

**Salesforce-native retention beyond the bin.** None. Salesforce keeps
no hidden tier. Once `IsDeleted = true` is committed and the 15-day
soft-delete window passes (or hard delete is used), the platform has
discarded the row.

**Right answer.** Source from a backup that captured the records before
the cleanup job. If no backup existed, the data is gone. Document this
loss and use it as the business case for funding a backup tool.

---

## Example 3 — Restoring parent-child relationships

**Context.** Account `0010K00001ABCxx` was accidentally deleted along
with its 47 Contacts and 12 Opportunities. You restore from a third-
party backup tool 9 days later (past Recycle Bin retention, so cascade
restore from the bin is not an option).

**The relationship problem.** When you re-insert the Account, it gets a
new Id. The 47 Contacts referenced the **old** Id in their `AccountId`
field. Naive restore = orphaned children.

**What good backup tools handle.** OwnBackup / Salesforce Backup /
Druva all do "relationship-aware restore": they re-insert parents
first, capture the new Ids, then update children's lookup fields to
point to the new Ids before re-inserting. They also handle:

- Self-relationships (`Account.ParentId`).
- Many-to-many through junction objects.
- Polymorphic lookups (`Task.WhatId`).
- External Id fields (preferred join key when configured).

**Self-rolled trap.** A homegrown Bulk API restore script that just
re-inserts CSVs in alphabetical order will produce orphans on every
lookup. Doing this correctly is non-trivial — it is the main reason
people pay for backup tools.

---

## Example 4 — Decision matrix: native vs third-party vs self-roll

| Need | Native Salesforce Backup | Third-Party (Own / Druva / Spanning) | Self-Rolled (Bulk API + S3) |
|---|---|---|---|
| Daily snapshot | Yes | Yes | Yes (with scheduled job) |
| Sub-daily RPO | No (daily floor) | Some vendors offer hourly | Possible (scheduled hourly) |
| Relationship-aware restore | Yes | Yes (mature) | Build it yourself |
| Sandbox seeding from production | No | Yes (key vendor differentiator) | No |
| Cross-org compare / DR | No | Yes | No |
| Anomaly / mass-delete alerting | Limited | Yes | No |
| Files & attachments | Yes | Yes | Bulk API can fetch ContentVersion |
| Cost | Per-license | Per-org or per-record | Storage + engineering |
| Restore UX for a non-developer admin | Good | Excellent | Poor (CLI / scripts) |

**Default recommendation.** For orgs over 500K records or any org
holding regulated data (PHI / PCI / financial), pay for a backup tool.
The engineering cost of a correct self-rolled restore is higher than
people estimate, and the cost is paid in a crisis when nobody has time.

---

## Example 5 — RPO / RTO worked example

**Business commitment.** "We can lose at most 24 hours of customer
support data, and we must be back to normal operations within 8 hours
of a recovery decision."

- **RPO = 24 hours.** Daily backup is sufficient.
- **RTO = 8 hours.** Restore tooling must complete in less than 8 hours.

**Volume sanity check.** 2.5M cases, 500K accounts, 8M activities.
A relationship-aware restore of all three through the Bulk API at
typical throughput (~10K records/min) is roughly 18 hours best case —
exceeds the 8-hour RTO.

**Implication.** Either (a) RTO must be relaxed, or (b) restore must be
scoped to the affected slice rather than full-org, or (c) tooling that
restores in parallel across objects is required. This conversation
must happen with the business **before** the recovery event, not
during.

---

## Example 6 — Weekly Data Export Service deprecation

**Context.** Org has been relying on Setup → Data Management → Data
Export, scheduled weekly. Salesforce announced retirement of the
service.

**What it was.** Free CSV export of all standard and custom objects,
weekly cadence, attachments optional, downloaded as ZIP files via
Setup. Maximum cadence was weekly (Unlimited / Performance Edition;
monthly for lower editions).

**What replaces it.** Salesforce Backup (the native paid product) is
positioned as the successor. Bulk API 2.0 is the developer-facing
alternative for self-rolling.

**Migration path.** If you currently rely on Weekly Data Export:

1. Confirm the retirement timeline for your edition / region in Trust /
   Release Notes.
2. Decide whether to license Salesforce Backup, adopt a third-party,
   or self-roll on Bulk API.
3. Run parallel exports during the transition until the new tool's
   first full snapshot is verified.
4. Update your DR runbook — the Weekly Data Export step no longer
   exists.
