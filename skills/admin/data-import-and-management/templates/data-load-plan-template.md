# Data Load Plan Template

Use this before any significant import, migration, or bulk update.

---

## Load Overview

| Property | Value |
|----------|-------|
| Load name | TODO |
| Object(s) | TODO |
| Load type | Insert / Update / Upsert / Delete / Hard Delete |
| Tool | Data Import Wizard / Data Loader / Bulk API / ETL |
| Owner | TODO |
| Target environment | Sandbox / Production |
| Planned window | TODO |

## Source and Matching Strategy

| Item | Value |
|------|-------|
| Source system | TODO |
| Source file(s) | TODO |
| External ID / match key | TODO |
| Is the match key unique in source? | Yes / No |
| Parent lookup resolution method | TODO |

## Load Order

| Sequence | Object | Operation | Depends On |
|----------|--------|-----------|------------|
| 1 | TODO | TODO | — |
| 2 | TODO | TODO | TODO |
| 3 | TODO | TODO | TODO |

## Automation and Data Quality Controls

| Control | Decision | Notes |
|---------|----------|-------|
| Validation rules | Keep on / Bypass / Maintenance window | TODO |
| Duplicate rules | Block / Alert / Temporary exception | TODO |
| Record-triggered flows | Keep on / Bypass / Post-load backfill | TODO |
| Sharing recalculation | Accept / Schedule around / Mitigate | TODO |

## Reconciliation

- [ ] Source row count captured
- [ ] Success and error file counts captured
- [ ] SOQL verification queries prepared
- [ ] Duplicate review query prepared
- [ ] Spot-check records identified

## Rollback Plan

| Failure scenario | Rollback action | Owner |
|------------------|-----------------|-------|
| TODO | TODO | TODO |
| TODO | TODO | TODO |
