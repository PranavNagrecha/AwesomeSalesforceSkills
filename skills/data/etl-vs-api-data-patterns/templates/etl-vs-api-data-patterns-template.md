# ETL vs API Data Patterns — Decision Template

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
| Data volume per run | | Records per execution |
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

- [ ] Selected tool uses Bulk API 2.0 for operations > 200 records
- [ ] NOT using standard REST API CRUD endpoints for bulk operations

---

## Architecture Notes

Describe the data flow: _______________
