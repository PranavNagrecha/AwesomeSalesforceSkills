# Data Load Plan

Use this before any significant import, migration, or bulk update. Replace the bracketed placeholders.
Rows are filled with a worked example — a legacy-CRM Account/Contact/Case cutover — so the intended
level of specificity is visible. A cell that still says "decide" is an unanswered question, not a
finished plan.

---

## Load Overview

| Property | Value |
|----------|-------|
| Load name | `[LEGACY-CUTOVER-01 Accounts]` |
| Object(s) | `[Account]` |
| Load type | Insert / Update / **Upsert** / Delete / Hard Delete |
| Tool | Data Import Wizard / **Data Loader (CLI)** / Bulk API 2.0 / ETL |
| API in use | SOAP / **Bulk API** / Bulk API 2.0 — *this changes what batch size means and whether `insertNulls` exists* |
| Batch size | `[5000]` — max 200 for SOAP, 10,000 for Bulk API, ignored by Bulk API 2.0 |
| Serial mode | **On** / Off — on when the load touches a shared parent or changes ownership |
| Owner | `[name, and who covers them if the window runs long]` |
| Target environment | Sandbox / Production — `[full-copy sandbox "migration", then prod]` |
| Planned window | `[Sat 2026-09-05 22:00 – Sun 06:00 UTC]` |
| Config file | `[C:\Migration\Config\process-conf.xml]`, bean id `[accountUpsert]` |
| Password encrypted? | Yes / No — must be Yes; `encrypt.bat -e <pwd><token> <keyfile>` |

## Source and Matching Strategy

| Item | Value |
|------|-------|
| Source system | `[Legacy CRM, being retired]` |
| Source file(s) | `[C:\Migration\In\accounts.csv, 400,000 rows, UTF-8, CRLF]` |
| Row count captured | `[400,000 — from wc -l, minus header]` |
| External ID / match key | `[Legacy_Account_Id__c]` |
| Field is `externalId` **and** `unique`? | Yes / No — both, or upsert fails with a 300 on any repeated key |
| Is the match key unique in source? | Yes / No — prove it: `sort -t, -k1,1 file.csv \| cut -d, -f1 \| uniq -d` |
| Are there blanks in the match key? | Yes / No — a blank key inserts, it does not match |
| Parent lookup resolution method | `[Parent.External_Id__c column header — no ID re-join pass needed]` |
| Date columns and their format | `[CloseDate, LastActivityDate — written as yyyy-MM-ddTHH:mm:ss.SSS+0000]` |
| `sfdc.timezone` pinned to | `[GMT]` |
| Fields to be cleared | `[none]` — if any, `#N/A` under Bulk API, `insertNulls=true` under SOAP |

## Load Order

Each row names the key it matches on and how its lookups resolve. Insert-only rows are not re-runnable
— note how you would delete what landed.

| Sequence | Object | Operation | Match key | Lookups resolved by | Depends On | Re-runnable? |
|---|---|---|---|---|---|---|
| 1 | `[User]` | upsert | `[FederationIdentifier]` | — | — | Yes |
| 2 | `[Account]` | upsert | `[Legacy_Account_Id__c]` | `[Owner.FederationIdentifier]` | 1 | Yes |
| 3 | `[Contact]` | upsert | `[Legacy_Contact_Id__c]` | `[Account.Legacy_Account_Id__c]` | 2 | Yes |
| 4 | `[Case]` | insert | none | `[Account.Legacy_Account_Id__c]` | 2, 3 | No — delete by CreatedById + CreatedDate |
| 5 | `[Account.ParentId]` | update | `[Legacy_Account_Id__c]` | `[Legacy_Account_Id__c]` | 2 | Yes — self-reference needs its own pass |

## Automation and Data Quality Controls

Every row here is a decision that must be made before the window, not discovered during it.

| Control | Decision | Notes |
|---------|----------|-------|
| Validation rules | Keep on / **Bypass** / Maintenance window | `[3 active rules on Account; load user holds Bypass_Validation_Rules Custom Permission]` |
| Duplicate rules | Block / **Alert** / Temporary exception | `[Account Name+City rule is Alert; 1 named owner reviews alerts in-window]` |
| Record-triggered flows | Keep on / **Bypass** / Post-load backfill | `[Account_AfterSave bypassed via custom setting; roll-ups backfilled at step 6]` |
| Trigger static recursion guards | Checked / Not checked | `[Checked — guards are per-Id, so all 200-record chunks run]` |
| Assignment rule | **None** / Rule Id | `[none — CSV OwnerId must win; sfdc.assignmentRule left empty]` |
| Sharing recalculation | Accept / **Schedule around** / Mitigate | `[ownership changes deferred to a separate step 7 load]` |
| Field truncation | Trim in extract / Let rows fail | `[NOTES trimmed to 32,768 in extract SQL — Bulk API will not truncate]` |
| Account Teams | N/A / Preserve | `[N/A — no owner change in this load]` |

## Reconciliation

- [ ] Source row count captured — `[400,000]`
- [ ] Success file row count captured
- [ ] Error file row count captured
- [ ] Unprocessed-records file pulled (Bulk API 2.0 — a third file, not the same as failed)
- [ ] The four numbers reconcile: source == success + failed + unprocessed
- [ ] Target-org `COUNT()` matches the success count
- [ ] Orphan query run: children whose parent lookup stayed null
- [ ] Duplicate-key query run: `GROUP BY <key> HAVING COUNT(Id) > 1`
- [ ] Error file grouped by error class, not read row by row
- [ ] Spot-check records identified and opened in the UI — `[5 named records per object]`
- [ ] Results downloaded within 7 days (Bulk API results expire)

## Rollback Plan

"Restore from backup" only counts if the backup exists and has been restored at least once in
rehearsal. Name the query that finds what this load created.

| Failure scenario | Rollback action | Owner |
|------------------|-----------------|-------|
| `[Upsert wrote wrong values to existing Accounts]` | `[Restore from the pre-load export of the same field set, keyed on Legacy_Account_Id__c]` | `[name]` |
| `[Case insert half-failed]` | `[Delete WHERE CreatedById = <loader> AND CreatedDate >= <window start>; soft delete only, so Recycle Bin is the safety net]` | `[name]` |
| `[Job died mid-run, state unknown]` | `[Pull all three result files, re-run only unprocessed + fixed failed rows; upsert makes this idempotent for steps 1-3, 5]` | `[name]` |
| `[Duplicates created because the key was not unique]` | `[Run the duplicate-key query, merge per admin/duplicate-management, then fix the field to unique before re-running]` | `[name]` |

## Pre-Flight Sign-Off

- [ ] Rehearsed in `[full-copy sandbox]` at production-shaped volume with production automation on
- [ ] Rehearsal wall-clock time recorded — `[__ min]` — and it fits the window with margin
- [ ] `scripts/check_load_plan.py --manifest-dir <config dir>` run clean against `process-conf.xml` and the `.sdl` files
- [ ] `scripts/check_load_plan.py <csv> --external-id <key> --required <cols>` run clean against every source file
- [ ] Load user's permissions verified for the operation (and `Bulk API Hard Delete` if hard-deleting)
- [ ] Allocation budget calculated against the 15,000-batch / 150,000,000-record 24-hour limits
- [ ] Each uploaded file is under the size ceiling for the API in use
