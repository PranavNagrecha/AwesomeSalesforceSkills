# Analytics Data Manager — Work Template

Use this template when configuring, troubleshooting, or auditing the Data Manager layer of CRM Analytics.

---

## Scope

**Skill:** `analytics-data-manager`

**Request summary:** (describe what the user asked for — sync configuration, remote connection setup, error diagnosis, capacity audit, etc.)

**Layer confirmed:** [ ] Data Manager / sync layer    [ ] Recipe/dataflow layer (route to `analytics-dataset-management`)

---

## Context Gathered

### Org and License

- CRM Analytics license type: _______________
- Org instance: _______________
- Admin performing configuration: _______________

### Current Sync State

- Total objects currently enabled for sync: ___ / 100 (hard limit)
- Number of concurrent syncs currently running or scheduled at the same time: ___ / 3 (hard limit)
- Connections present (list all): _______________

### Request Details

- Target objects or external tables to add/modify: _______________
- External database type (if applicable): [ ] Snowflake  [ ] BigQuery  [ ] Redshift  [ ] S3  [ ] Other: ___
- Sync mode requested: [ ] Full  [ ] Incremental  [ ] Unsure (default to full for first sync)
- Downstream recipe/dataflow that will consume the connected object: _______________

---

## Pre-Configuration Checklist

- [ ] Total enabled objects < 100 (verified in Data Manager > Connect)
- [ ] No more than 3 syncs scheduled at the same time after this change
- [ ] For external databases: remote connection created and tested before enabling tables
- [ ] For external databases: Salesforce CRM Analytics IP egress ranges allowlisted in target database network policy
- [ ] For objects with cross-object formula fields: full sync scheduled periodically (not only incremental)

---

## Sync Configuration Plan

| Object / Table | Connection | Sync Mode | Schedule | Cross-Object Formulas? | Periodic Full Sync Needed? |
|---|---|---|---|---|---|
| | | Full / Incremental | | Yes / No | Yes / No |
| | | Full / Incremental | | Yes / No | Yes / No |
| | | Full / Incremental | | Yes / No | Yes / No |

---

## Remote Connection Details (if applicable)

| Field | Value |
|---|---|
| Connection name | |
| Connector type | Snowflake / BigQuery / Redshift / S3 / Other |
| Host / Account identifier | |
| Database | |
| Schema | |
| Authentication method | Password / Key Pair / OAuth |
| IP allowlist confirmed | Yes / No / N/A |
| Connection test result | Passed / Failed / Not yet run |

---

## Post-Sync Validation

After sync runs, verify each of the following:

- [ ] Monitor tab shows status = Completed (not Failed or Partial) for each object
- [ ] Row counts in Monitor tab match expected totals (cross-reference source object count)
- [ ] Critical fields are present in connected object schema (spot-check in Data Manager > Connect > [object] > Fields)
- [ ] No field-level errors in Monitor run log

---

## Downstream Materialization Confirmation

Connected objects are staging-layer replicas. A successful sync does NOT make data available in dashboards until a recipe or dataflow is run.

- [ ] Recipe / dataflow identified: _______________
- [ ] Recipe / dataflow re-run after sync completed
- [ ] Output dataset updated in Analytics Studio (verify Last Refreshed timestamp)
- [ ] Dashboard widget showing correct data after dataset refresh

---

## Monitoring and Alerting

- [ ] Data Manager monitoring notifications configured (Monitor > Notification Settings)
- [ ] Notification recipients: _______________
- [ ] Alert conditions: [ ] Sync Failure  [ ] Partial Sync  [ ] Other: ___

---

## Known Issues and Deviations

| Object | Issue | Mitigation |
|---|---|---|
| | Cross-object formula fields — incremental sync will miss related-object updates | Schedule periodic full sync |
| | | |

---

## Sync Runbook Summary

Document this for future admins:

- Total enabled objects: ___
- Objects using incremental-only sync: ___
- Objects requiring periodic full sync (cross-object formula dependency): ___
- Concurrent sync peak (max simultaneous runs): ___
- Remote connection credential expiry dates: ___
- Next capacity audit date: ___

---

## Notes

(Record any deviations from the standard pattern, escalated issues, or pending actions.)
