# Well-Architected Notes — Data Cloud Ingestion API

## Relevant Pillars

### Reliability

Ingestion API reliability requires: monitoring streaming processing completion (202 does not mean data is available), confirming bulk job status before scheduling the next job, and validating record counts post-ingestion via Data Cloud Query API.

### Security

The `cdp_ingest_api` OAuth scope is explicitly required — not the generic `api` scope. Connected App credentials for server-to-server Ingestion API calls must be stored in a secrets manager, not hardcoded. JWT Bearer Token flow is preferred over user-password OAuth for server-to-server calls.

### Operational Excellence

Schema design is an irreversible deployment decision. Pre-deployment schema review is mandatory. Additive-only change governance must be documented and enforced in the data team's change management process.

---

## WAF Mapping

| WAF Area | Guidance |
|---|---|
| Reliability | Monitor streaming processing lag; validate record counts post-ingestion; poll bulk job status |
| Security | Use cdp_ingest_api scope; store credentials in secrets manager; prefer JWT Bearer Token flow |
| Operational Excellence | Schema is additive-only after deployment — enforce pre-deployment review process |
| Performance | Streaming: micro-batches every ~3 minutes; Bulk: 150 MB/file, 100 files/job |

---

## Cross-Skill References

- `data/data-cloud-data-model-objects` — For DMO design that receives Ingestion API data
- `admin/data-cloud-provisioning` — For Data Cloud org provisioning and Connected App registration
- `integration/api-led-connectivity` — For MuleSoft-based integration patterns that feed the Ingestion API

---

## Official Sources Used

- Ingestion API Overview — Data 360 Integration Guide: https://developer.salesforce.com/docs/data/data-cloud-int/guide/c360-a-ingestion-api.html
- Bulk Ingestion API Reference: https://developer.salesforce.com/docs/data/data-cloud-int/references/data-cloud-ingestionapi-ref/c360-a-api-bulk-ingestion.html
- Streaming Ingestion API Reference: https://developer.salesforce.com/docs/data/data-cloud-int/references/data-cloud-ingestionapi-ref/c360-a-api-streaming-ingestion.html
- Ingestion API Schema Requirements: https://developer.salesforce.com/docs/data/data-cloud-int/guide/c360-a-ingestion-api-schema-req.html
