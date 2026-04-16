# Data Cloud Integration Strategy — Work Template

Use this template when designing or troubleshooting how a source system connects to Data Cloud.

## Scope

**Skill:** `data-cloud-integration-strategy`

**Request summary:** (fill in: source system type, data volume, latency requirements)

## Source System Assessment

- **Source system type:** [ ] CRM Connector  [ ] Cloud Storage  [ ] Ingestion API  [ ] MuleSoft Direct
- **Data volume:** (daily rows / payload size per event)
- **Latency requirement:** [ ] Near-real-time (~3 min acceptable)  [ ] Batch (nightly/weekly)
- **MuleSoft licensed?** [ ] Yes  [ ] No (affects MuleSoft Direct eligibility)

## Connector Decision

- **Selected connector type:**
- **Rationale:**
- **Streaming or Bulk (for Ingestion API)?** [ ] Streaming (≤200KB/request)  [ ] Bulk (CSV, ≤150MB/file)

## Schema Design (for Ingestion API)

- **Schema format:** OpenAPI 3.0.x YAML
- **Engagement-category object?** [ ] Yes — include DateTime field  [ ] No
- **Schema reviewed before deployment:** [ ] Yes — irreversible after deploy

## Pipeline Lag Estimate

- Ingestion batch window (streaming): ~3 min
- DSO → DLO processing: ~X min (estimate)
- DLO → DMO mapping: ~X min (estimate)
- Identity resolution run: ~15 min
- **Estimated total for segment availability:** (sum above)

## Checklist

- [ ] Connector type matches source system and licensing
- [ ] Streaming vs. bulk decision documented
- [ ] Schema designed before deployment — irreversible after
- [ ] 200 KB streaming limit / 150 MB bulk limit verified against data volume
- [ ] DateTime field included for engagement-category DSOs
- [ ] Multi-hop pipeline lag communicated to stakeholders
- [ ] Datasets > 50 GB: Data Federation considered as alternative

## Notes

(Record any deviations from the standard pattern and why)
