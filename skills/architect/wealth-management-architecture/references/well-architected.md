# Well-Architected Notes — Wealth Management Architecture

## Relevant Pillars

- **Security** — Compliant Data Sharing is the primary security mechanism for regulatory data segmentation. Each object type must be individually enrolled; relying on role hierarchy or manual sharing rules instead of CDS is an architectural violation. Advisor access must be verified to confirm advisors cannot read records assigned to other advisors' books of business.
- **Scalability** — Custodian data volume drives integration pattern selection. Bulk API 2.0 is the scalable path for large nightly feeds; the REST Composite API does not scale beyond tens of thousands of records without hitting governor limits. Portfolio rollup recalculation after bulk loads must be explicitly triggered — it does not fire automatically.
- **Reliability** — Custodian integration runbooks must include dead-letter handling for Bulk API 2.0 failed rows and retry logic for Remote Call-In timeouts. A feed failure that silently drops records corrupts portfolio totals without any advisor notification. Scheduled monitoring of ingest job states is required.
- **Performance** — Real-time custodian updates via Remote Call-In must be scoped to low-volume, high-priority events only. Routing high-volume feeds through the synchronous Remote Call-In path degrades org performance for concurrent advisor sessions. Separate real-time and batch paths explicitly in the integration design.
- **Operational Excellence** — FSC feature flags deployed via IndustriesSettings must be tracked in source control alongside the application code. Manual Setup UI changes to feature flags are not tracked in version control and will be lost on environment refreshes or deployments. All IndustriesSettings flags must be in the project's `settings/` directory.

## Architectural Tradeoffs

**CDS vs Standard Sharing for Data Segmentation**

CDS adds per-record access control overhead but is the only approach that satisfies FSC's regulatory segmentation model for wealth management. Standard Salesforce role hierarchy sharing gives managers visibility into subordinate records, which violates the "advisor sees only their book of business" model common in registered investment advisory (RIA) environments. The operational cost of CDS (recalculation batches, enrollment maintenance) is justified by the compliance requirement.

**Batch vs Real-Time Custodian Integration**

Nightly batch integration is simpler to operate, easier to monitor, and handles arbitrarily large custodian exports. Real-time integration satisfies premium client service requirements but introduces synchronous latency risk and requires the custodian to support outbound webhook-style calls. Most implementations use both: batch for the full nightly reconciliation and real-time for same-day trade confirmations on a subset of high-net-worth accounts. The two paths must be designed to avoid conflicting updates on the same records.

**AI Features Behind Explicit Feature Flags**

The `enableWealthManagementAIPref` flag is a deliberate product gate, not an oversight. It separates general FSC licensing from AI add-on capability licensing. This means architects must plan AI features as a separate deployment artifact rather than assuming they are available in any FSC org. The flag should be deployed in a dedicated metadata component and tracked separately from core FSC configuration.

## Anti-Patterns

1. **Using REST Composite API for high-volume custodian feeds** — The REST path consumes per-transaction governor limits and the daily API call allocation. For feeds exceeding 10K records, this creates limit exhaustion and silent data loss. Use Bulk API 2.0 ingest for all high-volume custodian data.

2. **Activating Compliant Data Sharing without a sharing recalculation plan** — Enabling CDS on an object with existing data immediately removes record visibility for all advisors. Teams that activate CDS without a tested recalculation runbook cause a production outage-equivalent event where advisors see zero client data. Always pair CDS activation with a scheduled and tested recalculation batch.

3. **Assuming FSC base license includes Scoring Framework** — Scoping advisor analytics features that depend on the Scoring Framework without verifying CRM Plus license presence leads to deployments that succeed but produce blank UI components at runtime. License verification must be the first step in any analytics architecture engagement.

4. **Relying on Setup UI toggles for IndustriesSettings flags** — Features enabled via Setup UI are not captured in source control and are lost on scratch org recreation or metadata deployments that overwrite the settings file. All `IndustriesSettings` flags must be managed as source-controlled metadata.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Integration Patterns Guide — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- FSC Industries Developer Guide (IndustriesSettings metadata, Wealth Management AI pref, Financial Deal Management, Compliant Data Sharing) — https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/industries_intro.htm
- Salesforce Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
