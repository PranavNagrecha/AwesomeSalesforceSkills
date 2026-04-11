# Well-Architected Notes — FSC Integration Patterns Dev

## Relevant Pillars

- **Reliability** — FSC financial integrations must produce correct, complete position data. The primary reliability threat is partial load failure due to row-lock contention (Rollup-by-Lookup) and CDC event loss beyond the 72-hour replay window. Both require independent batch reconciliation as a backstop, not sole reliance on event-driven feeds.

- **Performance** — Bulk API 2.0 is the correct performance pattern for loads above ~5,000 records. Synchronous Apex upserts at this scale exhaust DML row limits (10,000 per transaction) and CPU governor limits. Batch scope tuning for callout-bearing jobs (50–100 records per chunk) balances throughput against per-transaction callout limits.

- **Security** — Integration users must use dedicated Connected Apps with OAuth 2.0 JWT Bearer authentication, not username/password flows. The integration profile should have the minimum permission set required: CRUD on FinancialAccount and FinancialHolding, no administrative permissions. Named Credentials should store endpoint URLs and auth tokens — no hardcoded credentials in Apex.

- **Scalability** — The integration design must accommodate growth in position volume (daily reconciliation jobs that handle 10× current volume without rearchitecting). Using Bulk API 2.0 with DPE recalculation scales linearly; RBL-based recalculation does not — it degrades quadratically as parent account contention increases.

- **Operational Excellence** — Integration jobs must emit observable state: Bulk API job IDs logged to a custom object, Platform Events published on completion, error rates surfaced via a dashboard. Silent partial failures are the dominant operational risk in FSC financial integrations.

---

## Architectural Tradeoffs

**Batch reconciliation vs. real-time event-driven:** Batch Bulk API reconciliation is reliable and scalable but introduces a processing lag (typically hours after market close). Real-time Remote Call-In via the FSC Integrations API provides near-instant data currency but has throughput limits and requires the upstream custodian to support webhooks. The canonical FSC architecture uses both: nightly batch for authoritative position accuracy, real-time events for intraday UI freshness. Never replace the batch with events-only — CDC reliability guarantees are insufficient for financial record accuracy.

**RBL vs. DPE for rollup recalculation:** Rollup-by-Lookup provides automatic real-time rollup updates but introduces row-lock contention at bulk load scale. Data Processing Engine performs recalculation as a separate, scheduled batch operation after a load. For orgs processing >10,000 holdings per night, DPE is the only viable path; RBL should be disabled for the integration user and treated as a convenience feature for low-volume manual updates only.

**CDC for replication vs. batch for reconciliation:** CDC is appropriate for propagating Salesforce-side changes (advisor profile updates, risk scores) to downstream systems. It is not appropriate as the sole mechanism for inbound custodian data replication — the 72-hour event retention window creates an unacceptable gap risk for financial records.

---

## Anti-Patterns

1. **Synchronous trigger callouts on FSC financial objects** — Placing market data or custodian API calls inside Apex triggers on FinancialHolding or FinancialAccount violates the Apex callout-after-DML restriction, breaks under bulk load, and couples data write latency to external system response time. Move all callouts to Batchable/Queueable classes running in fresh transactions.

2. **Relying solely on CDC for custodian data ingestion** — Treating CDC as a bidirectional sync mechanism for inbound custodian position data couples Salesforce data accuracy to a 72-hour event window. Any consumer outage beyond that window causes permanent data drift. Always maintain a nightly Bulk API reconciliation job as the authoritative position source.

3. **Hardcoded FSC object/field namespace in integration code** — Writing integration Apex or ETL mappings that assume a single FSC deployment type (`FinServ__` or no namespace) without checking at configuration time. This creates fragile integrations that break silently when deployed to orgs with a different FSC variant or after a package upgrade changes field names.

---

## Official Sources Used

- FSC Integrations API — Get Started: https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_full.meta/financial_services_cloud_full/fsc_integrations_api_get_started.htm
- Apex Developer Guide (Batchable, Queueable, callout restrictions): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Salesforce Bulk API 2.0 Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Salesforce Integration Patterns (Architects guide): https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Change Data Capture Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
