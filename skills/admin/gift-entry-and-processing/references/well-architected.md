# Well-Architected Notes — Gift Entry and Processing

## Relevant Pillars

### Operational Excellence

Gift Entry is a data-entry pipeline with a hard two-phase commit model (staging → target). Operational excellence requires that every staging record either successfully promotes to a GiftTransaction or is flagged for manual review — there must be no silent failures. Implement monitoring on `GiftEntry` records in `Imported` status beyond a defined SLA window (e.g., 24 hours). Use the `isDryRun=true` validation pass as a mandatory pre-batch gate to surface errors before any records are committed.

### Reliability

The `processGiftEntries` invocable action is the single point of promotion from staging to target. A failure in this action leaves staging records in a non-terminal state. Reliability patterns include: idempotent retry logic (the action is not inherently idempotent — do not call it twice on the same staging record without checking current status), error logging on every invocation, and batch split strategies to limit the blast radius of a single failed batch (e.g., process in sub-batches of 50 rather than 500 records in one run).

### Security

Gift entry data includes payment method details, donor personally identifiable information (PII), and financial amounts. Apply field-level security on `GiftTransaction` and `GiftEntry` objects to restrict access to payment fields. Payment gateway credentials must never be stored in `GiftEntry` staging records as plain-text fields — use the platform's named credentials or a dedicated payment gateway integration layer.

### Performance

Batch gift entry at scale (500+ records per batch) should use asynchronous processing. The standard Gift Entry UI processes records synchronously; at high volumes this can hit Apex CPU limits. For very large year-end batches, consider splitting into sub-batches processed via a scheduled Apex job or a Platform Event-driven architecture rather than a single synchronous UI submission.

### Scalability

The `GiftEntry` staging object grows with every unprocessed record. Orgs with high gift volumes should implement a retention policy: archive or delete processed staging records on a defined schedule (e.g., 90 days post-processing). Uncontrolled growth of the staging object degrades SOQL query performance on all Gift Entry-related reports.

---

## Architectural Tradeoffs

**Single template vs. multiple custom templates:** Using the Default Gift Entry Template for all entry simplifies administration but forces all gift entry users into one field layout. Multiple custom batch templates enable team-specific or campaign-specific layouts at the cost of increased template maintenance overhead.

**Synchronous vs. asynchronous processing:** Synchronous `processGiftEntries` calls are simpler and provide immediate user feedback but hit platform limits at batch sizes above a few hundred records. Asynchronous processing via Platform Events or Scheduled Apex scales further but introduces a delay between entry and promotion that must be communicated to end users.

**Native TaxReceiptStatus vs. custom receipt field:** The platform-native `TaxReceiptStatus` field (API v62.0+) integrates directly with future Salesforce receipt generation features, but is unavailable on older API versions. A custom receipt status field works everywhere but requires migration when the org upgrades.

---

## Anti-Patterns

1. **Direct DML to GiftTransaction bypassing Gift Entry** — Writing directly to `GiftTransaction`, `GiftDesignation`, or `Opportunity` outside the Gift Entry framework skips Advanced Mapping transformations, breaks the staging audit trail, omits soft credit logic, and produces records that are structurally inconsistent with Gift Entry-managed records. Always write to `GiftEntry` staging and invoke `processGiftEntries`.

2. **Processing entire year-end batch in one synchronous call** — Submitting hundreds of staging records in a single synchronous `processGiftEntries` loop risks Apex CPU and heap limits, and a single record failure can abort the entire batch with no partial recovery. Implement sub-batch processing with per-record error isolation.

3. **Not monitoring unprocessed staging records** — `GiftEntry` staging records that are never promoted represent phantom gifts. Without a monitoring alert on long-lived `Imported` staging records, these can go undetected for weeks, causing reconciliation failures at fiscal period close.

---

## Official Sources Used

- Salesforce Help — Configure Gift Entry (NPSP): https://help.salesforce.com/s/articleView?id=sf.npsp_gift_entry.htm
- Salesforce Fundraising Developer Guide — GiftEntry Object and processGiftEntries Action (API v59.0+): https://developer.salesforce.com/docs/atlas.en-us.fundraising_dev.meta/fundraising_dev/fundraising_gift_entry_api_overview.htm
- Trailhead — Set Up Gift Entry in Nonprofit Success Pack: https://trailhead.salesforce.com/content/learn/projects/set-up-gift-entry-npsp
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
