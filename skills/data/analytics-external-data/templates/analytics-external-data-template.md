# Analytics External Data — Work Template

Use this template when working on tasks involving external data ingestion or access in CRM Analytics.

## Scope

**Skill:** `analytics-external-data`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Before working, record answers to the Before Starting questions from SKILL.md:

- **External data source type:** (CSV file / Snowflake / BigQuery / Redshift / other)
- **Data path selected:** (External Data API / Data Connector / Live Dataset / Tableau Bridge)
- **Freshness requirement:** (real-time / hourly / daily / weekly)
- **Data volume:** (approximate row count and file size)
- **Authentication method:** (OAuth / username-password / named credential)
- **Known constraints:** (firewall restrictions, on-prem source, rate limits)

## Data Path Decision

Which path applies and why?

- [ ] **External Data API** — Source has no prebuilt connector; programmatic CSV push required
- [ ] **Data Connector (materialized)** — Snowflake / BigQuery / Redshift; freshness tolerance exists; fast query performance required
- [ ] **Live Dataset (read-through)** — Freshness is critical; external system can serve concurrent queries reliably
- [ ] **Tableau Bridge** — Data is behind firewall or on-premises

**Rationale:** (fill in)

## External Data API Checklist

Complete if External Data API path is selected:

- [ ] Metadata JSON schema designed — all fields named, typed, and validated
- [ ] `InsightsExternalData` header record created; `Id` captured before any part upload
- [ ] CSV data gzip-compressed and split into chunks under 10 MB compressed each
- [ ] All `InsightsExternalDataPart` records uploaded referencing correct parent `Id`
- [ ] `Action` set to `Process` on parent record
- [ ] `Status` polled until `Completed`; failure alert configured for `Failed` status
- [ ] Row count in resulting dataset validated against source

**Dataset name / EdgemartAlias:** _______________

**Part count (expected):** _______________

## Data Connector Checklist

Complete if Data Connector path is selected:

- [ ] Remote Connection created in Data Manager; connectivity tested
- [ ] Recipe or Dataflow input node references the Remote Connection
- [ ] Source table or view confirmed; column types mapped to CRM Analytics field types
- [ ] Incremental load filter configured (watermark field: _______________)
- [ ] Refresh schedule set: _______________
- [ ] Output dataset named: _______________
- [ ] First manual run completed; row count validated against source
- [ ] Data Manager job failure notification configured

## Live Dataset Checklist

Complete if Live Dataset path is selected:

- [ ] Remote Connection created in Data Manager; connectivity tested
- [ ] Live Dataset created referencing the Remote Connection and target table/view
- [ ] Test SAQL query executed against Live Dataset; latency measured: _______________ ms
- [ ] Concurrent load test performed (simulated N users): _______________ users
- [ ] Dashboard failure behavior confirmed when external system is unavailable
- [ ] SAQL constructs used validated as supported by Live Dataset query translation layer

## Metadata JSON Schema (External Data API)

```json
{
  "fileFormat": {
    "charsetName": "UTF-8",
    "fieldsDelimitedBy": ",",
    "linesTerminatedBy": "\n"
  },
  "objects": [
    {
      "connector": "CSV",
      "fullyQualifiedName": "<DatasetName>",
      "label": "<Human Readable Label>",
      "name": "<DatasetName>",
      "fields": [
        {
          "fullyQualifiedName": "<FieldName>",
          "name": "<FieldName>",
          "type": "Text | Numeric | Date | Dimension",
          "label": "<Field Label>"
        }
      ]
    }
  ]
}
```

## Remote Connection Details (Data Connector or Live Dataset)

| Parameter | Value |
|---|---|
| Connection name | |
| Warehouse type | Snowflake / BigQuery / Redshift / other |
| Account / project | |
| Database / dataset | |
| Schema | |
| Authentication method | |
| Named credential reference | |

## Notes

Record any deviations from the standard pattern and why.
