# ETL vs API Data Patterns: Decision Template

Use this template when selecting between ETL and API-based integration for an ongoing data pipeline.

---

## Scope

**Integration name:** _______________
**Type:** [ ] Ongoing recurring pipeline  [ ] One-time migration (use data-migration-planning instead)

---

## Selection Criteria Assessment

| Criterion | Value | Notes |
|---|---|---|
| Latency requirement | | Real-time (<1 min) / Near-real-time / Batch |
| Data volume per run | | Records per execution (2,000 is the Bulk API 2.0 line) |
| Data volume per day, all jobs | | Must stay under 150,000,000 ingest records and 15,000 batches |
| Data master per object | | Salesforce or remote system |
| External ID per target object | | Field API name |
| Data quality profiling required? | Y/N | |
| Lineage/governance required? | Y/N | |
| MuleSoft license available? | Y/N | |
| Informatica license available? | Y/N | |

---

## Decision

**Selected approach:** [ ] Informatica ETL  [ ] MuleSoft Batch  [ ] MuleSoft API-led  [ ] Direct Bulk API 2.0

**Rationale:** _______________

---

## Bulk API 2.0 Confirmation

- [ ] Operations over 2,000 records use Bulk API 2.0; smaller ones use Composite or sObject Collections
- [ ] No single-record REST writes in a loop
- [ ] Job specs and CSV files pass `python3 scripts/check_etl_vs_api_data_patterns.py --manifest-dir <folder>`
- [ ] Failed and unprocessed results are read within 7 days and fed to a retry path

---

## Architecture Notes

Describe the data flow: _______________
