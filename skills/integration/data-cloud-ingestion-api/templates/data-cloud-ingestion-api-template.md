# Data Cloud Ingestion API — Work Template

Use this template when designing or implementing a Data Cloud Ingestion API integration.

## Scope

- Data source: ___________
- Ingestion mode: [ ] Streaming  [ ] Bulk  [ ] Both
- Data volume: ___________
- Update frequency: ___________

---

## Pre-Implementation Checklist

- [ ] OpenAPI 3.0.x schema designed and reviewed with all stakeholders
- [ ] Engagement-category objects include a date-time formatted field
- [ ] Schema is designed as additive-only (no planned field removals)
- [ ] Connected App created with cdp_ingest_api OAuth scope
- [ ] OAuth token acquisition tested before schema registration

---

## Schema Design

| Object Name | Category | Key Fields | DateTime Field | Notes |
|---|---|---|---|---|
| | Engagement / Profile / Other | | Required for Engagement | |
| | | | | |

**Schema Governance:** All changes post-deployment must be additive only. No field removal or type changes.

---

## Authentication Configuration

- Connected App Name: ___________
- OAuth Flow: [ ] JWT Bearer Token  [ ] Client Credentials
- Required Scopes: `cdp_ingest_api`, `api`
- Token endpoint: `https://{instanceUrl}/services/oauth2/token`

---

## Ingestion Mode Design

### Streaming (Near-Real-Time Events)

- Endpoint: `POST /services/data/v{version}/ssot/ingest/connectors/{connectorId}/streaming/{objectName}`
- Payload format: JSON array of records
- Processing lag: ~3 minutes after 202 Accepted
- Validate endpoint for development: `.../streaming/{objectName}/validate`

### Bulk (Nightly Snapshot)

- Endpoint: `POST .../jobs` (create job) → upload files → close job
- File format: CSV, UTF-8, comma-delimited, gzip-compressed for > 150 MB
- Max per file: 150 MB
- Max files per job: 100
- Semantics: **FULL REPLACE** — must include complete current dataset, not just delta

---

## Post-Ingestion Validation

```sql
-- Data Cloud Query API (ANSI SQL) — confirm record counts
SELECT COUNT(*) FROM {ObjectApiName}__dlm

-- Confirm latest records arrived
SELECT eventTimestamp FROM {ObjectApiName}__dlm 
ORDER BY eventTimestamp DESC LIMIT 10
```

---

## Error Handling Runbook

- Streaming: check Data Cloud error logs in Setup > Data Cloud > Ingestion API Sources
- Bulk: poll job status `GET .../jobs/{jobId}` until state = `complete` or `failed`
- On failure: inspect `errorRows` in bulk job status response; re-upload corrected files

---

## Notes

_Capture schema decisions, authentication configuration details, and open questions._
