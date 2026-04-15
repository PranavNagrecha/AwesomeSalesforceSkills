# Real-Time vs Batch Integration — Decision Template

Use this template to document an integration pattern decision. Fill every section before implementing.

## Scope

**Skill:** `real-time-vs-batch-integration`

**Integration name:** _______________________________________________

**Systems involved:** Salesforce ←→ _______________________________________________

**Request summary:** (describe what the stakeholder asked for)

---

## Requirements

| Dimension | Value |
|---|---|
| Peak record volume (per hour) | _______________ |
| Average record volume (per day) | _______________ |
| Maximum acceptable latency (source change → destination visible) | _______________ |
| Transactionality required? (rollback on failure) | Yes / No |
| Direction | Salesforce → External / External → Salesforce / Bidirectional |
| External system availability SLA | _______________ |
| External system can accept webhooks / events | Yes / No |

---

## Pattern Selected

**Pattern:** (check one)

- [ ] Synchronous callout (Apex HTTP/SOAP, inline transaction)
- [ ] Asynchronous callout (@future / Queueable with callout)
- [ ] Platform Events (Salesforce publishes, external subscribes via CometD or Pub/Sub API)
- [ ] Change Data Capture + Pub/Sub API (platform-generated, external subscribes)
- [ ] Bulk API 2.0 scheduled ingest job (external loads to Salesforce)
- [ ] Bulk API 2.0 scheduled query job (Salesforce exports to external)
- [ ] Hybrid: _______________________________________________

**Rationale:** (explain why this pattern was chosen over alternatives, referencing volume/latency/transactionality)

---

## Governor Limit Validation

Fill in the applicable section for the chosen pattern.

### Synchronous Callout

| Check | Limit | Projected Peak | Status |
|---|---|---|---|
| Callouts per transaction | 100 | ___ | PASS / FAIL |
| Callout timeout | 120 seconds | ___ ms avg | PASS / FAIL |
| API daily request limit | ___ (edition-specific) | ___ | PASS / FAIL |

### Platform Events

| Check | Limit | Projected Peak | Status |
|---|---|---|---|
| Events published per day | 250,000 (standard) | ___ | PASS / FAIL |
| Subscriber replay window needed | 72 hours | ___ hours max outage | PASS / FAIL |

### Bulk API 2.0

| Check | Limit | Projected Volume | Status |
|---|---|---|---|
| Records per 24-hour period | 150 million | ___ | PASS / FAIL |
| Job scheduled outside business hours | Required | ___ (scheduled time) | PASS / FAIL |
| External ID field defined for idempotent upsert | Required | Present: Yes / No | PASS / FAIL |

---

## Error Handling Design

| Failure scenario | Detection mechanism | Recovery action |
|---|---|---|
| External system timeout / unavailable | _______________ | _______________ |
| Partial batch failure (Bulk API) | /failedResults/ polling | Re-queue failed rows next cycle |
| Subscriber offline beyond replay window | Monitor last-poll timestamp | Full reconciliation via Bulk API query job |
| Platform Event phantom publish (rollback) | _______________ | _______________ |

**Dead-letter / error notification:** _______________________________________________

**On-call alert threshold:** _______________________________________________

---

## Security Checklist

- [ ] Named Credential created for all outbound callout endpoints (no hardcoded URLs or credentials)
- [ ] Connected App for Bulk API / Pub/Sub API uses least-privilege OAuth scopes
- [ ] Integration user profile has only the object/field permissions needed for this integration
- [ ] Field-level security reviewed on CDC tracked fields (only fields visible to integration user appear in events)
- [ ] TLS 1.2+ enforced on all external endpoints

---

## Monitoring Plan

| Metric | Alert threshold | Owner |
|---|---|---|
| Callout error rate | > 5% in 15 min | _______________ |
| Platform Event / CDC subscriber last poll | > 48 hours ago | _______________ |
| Bulk API job duration | > 2× baseline | _______________ |
| Bulk API failed records per cycle | > 1% of total | _______________ |

---

## Notes and Deviations

(Record any deviations from the standard pattern recommended in SKILL.md and why)
