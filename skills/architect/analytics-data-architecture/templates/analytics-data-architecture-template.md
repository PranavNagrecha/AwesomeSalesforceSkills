# Analytics Data Architecture — Work Template

Use this template when designing or reviewing CRM Analytics data architecture.

---

## Scope

**Skill:** `analytics-data-architecture`

**Request summary:** (describe what the user/stakeholder is asking for)

**Salesforce org:** (sandbox / production / scratch org name)

---

## Dataset Inventory

List every dataset that will be created or affected by this architecture.

| Dataset Name | Source (Object / External / Recipe / Dataflow) | Estimated Current Rows | Annual Growth Rate | Time-to-2B-Row-Cap (years) | Split Strategy Required? |
|---|---|---|---|---|---|
| | | | | | [ ] Yes [ ] No |
| | | | | | [ ] Yes [ ] No |
| | | | | | [ ] Yes [ ] No |

**Row-limit risk summary:** (flag any dataset within 5 years of the 2-billion-row cap)

---

## Run Budget Analysis

Map all scheduled dataflow and Recipe runs against the 60-run rolling 24-hour window.

| Job Name | Type (Dataflow / Recipe) | Scheduled Frequency | Runs Per 24 Hours | Priority |
|---|---|---|---|---|
| | [ ] Dataflow [ ] Recipe | | | Critical / Supporting / Low |
| | [ ] Dataflow [ ] Recipe | | | Critical / Supporting / Low |
| | [ ] Dataflow [ ] Recipe | | | Critical / Supporting / Low |

**Total runs per 24-hour window:** (sum of column above)

**Budget remaining:** (60 minus total, must be >= 10 for reruns/recovery)

**Action required if over budget:** (consolidate jobs, reduce frequency for low-priority jobs)

---

## ELT Strategy Map

Document where each transformation lives: ELT layer (correct) or SAQL runtime (flag for refactoring).

| Transformation | Type (Join / Filter / Augment / Computed Field) | Current Location | Target Location | Action |
|---|---|---|---|---|
| | | [ ] ELT [ ] SAQL | [ ] ELT [ ] SAQL | Move to ELT / Keep in SAQL |
| | | [ ] ELT [ ] SAQL | [ ] ELT [ ] SAQL | Move to ELT / Keep in SAQL |
| | | [ ] ELT [ ] SAQL | [ ] ELT [ ] SAQL | Move to ELT / Keep in SAQL |

**Rule:** Joins, augments, and static computed fields belong in the ELT layer. Only final aggregations and user-driven filters belong in SAQL.

---

## Incremental Strategy

For each dataset, document the incremental approach.

| Dataset | Source Type | Incremental Method | Snapshot Dataset Name | Comparison Field | Tested? |
|---|---|---|---|---|---|
| | Salesforce Object | [ ] Data Sync incremental (SystemModstamp) [ ] Full replace | N/A | SystemModstamp | [ ] Yes [ ] No |
| | Recipe | [ ] Snapshot-join (simulate incremental) [ ] Full reprocess accepted | | LastModifiedDate | [ ] Yes [ ] No |
| | External (Remote Connection) | [ ] Full reprocess (no incremental option) | N/A | N/A | [ ] Yes [ ] No |

**Note:** Recipes do NOT support native incremental loads. If "snapshot-join" is selected above, the snapshot dataset schema must exactly match the Recipe output schema.

---

## External Source Configuration

Complete this section if any data source is Snowflake, BigQuery, or Redshift.

| Source Name | Platform | Remote Connection Name (in Data Manager) | Authentication Method | IP Allowlisting Confirmed? | Connection Test Passed? |
|---|---|---|---|---|---|
| | [ ] Snowflake [ ] BigQuery [ ] Redshift | | [ ] OAuth [ ] Username/Password | [ ] Yes [ ] No | [ ] Yes [ ] No |

**Reminder:** Remote Connections are configured in Analytics Studio → Data Manager → Connections. They are NOT configured in dataflow JSON. Remote Connection output always writes to CRM Analytics internal storage — not back to the external lake.

---

## Architecture Decision Log

Record key design decisions and the rationale.

| Decision | Options Considered | Selected Approach | Rationale |
|---|---|---|---|
| Incremental strategy for [dataset] | Data Sync incremental / Snapshot-join / Full reprocess | | |
| ELT tool for [transform] | Dataflow Augment / Recipe Join / SAQL runtime | | |
| Run frequency for [job] | Hourly / 4-hour / Daily | | |

---

## Checklist

- [ ] All dataset projected row counts verified against the 2-billion-row per-dataset cap
- [ ] Total daily run count verified against the 60-run rolling 24-hour window (not calendar-day reset)
- [ ] All joins, augments, and computed fields confirmed in ELT layer (not SAQL runtime)
- [ ] Incremental strategy documented per dataset (Data Sync incremental for dataflows; snapshot-join for Recipes)
- [ ] External source Remote Connections created in Data Manager before Recipe build
- [ ] Snapshot-join Recipes tested across two consecutive runs (no row duplication or data loss)
- [ ] Run budget buffer of 10+ slots confirmed for reruns and failure recovery
- [ ] Dataset row-limit monitoring alerts configured for datasets within 5 years of the 2B cap
- [ ] Checker script run: `python3 skills/architect/analytics-data-architecture/scripts/check_analytics_data_architecture.py --manifest-dir <path>`

---

## Notes

(Record any deviations from the standard patterns and the reason why.)
