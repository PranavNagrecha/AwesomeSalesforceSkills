# Well-Architected Notes — Automotive Cloud Setup

## Relevant Pillars

- **Reliability** — VIN ingestion is the trust spine of the dealer org. A broken upsert (VIN duplication, definition explosion) corrupts every downstream process: recall routing, warranty lookup, financial linkage. Build idempotent loads with external IDs from day one and monitor delta-feed lag.
- **Scalability** — At fleet scale (millions of VINs across an OEM dealer network), `VehicleDefinition` deduplication is the difference between a 50,000-row reference table and a 5-million-row table that breaks model-level reporting. The dedup pass is non-negotiable, not an optimization.
- **Operational Excellence** — Recall and service-campaign orchestration runs continuously across an OEM's lifetime. Versioned `ActionableEventTypeDef` records preserve audit trails when remedies update; without TypeDef versioning, completion-rate reporting becomes a manual reconciliation exercise.

## Architectural Tradeoffs

**Standard Vehicle vs. Custom Vehicle__c:** Some teams arrive at Automotive Cloud with a Sales-Cloud-era custom Vehicle object already in production. Migration to the standard `Vehicle` carries cost (data backfill, integration rewrites, sharing-rule rebuild) but is the right long-term call — standard `Vehicle` ships with ActionableEvent integration, prebuilt FinancialAccount lookups, and Industries-platform alignment that custom objects do not get.

**`AccountAccountRelation` vs. Custom Junction:** A custom `Dealer_OEM__c` junction is faster to build but disconnects from Industries-standard sharing patterns and from prebuilt features (LightningContactRoleProvider, partner-portal templates) that key off `AccountAccountRelation`. Use the standard relation object even when the immediate use case feels too simple to warrant it.

**Real-time VIN Sync vs. Nightly Bulk:** Streaming inventory updates via Platform Events keeps the dealer UX accurate but introduces backpressure and replay complexity at fleet scale. Nightly Bulk API 2.0 ingest is simpler and sufficient for most retail dealer workflows; reserve streaming for the subset of attributes (location, sold/available status) that genuinely need real-time accuracy.

## Anti-Patterns

1. **Building Custom `Vehicle__c` While the Standard Object Is Available** — Adds 4–8 weeks of rework when migrated to the standard object, breaks integration with ActionableEvent and FinancialAccount.

2. **Definition Explosion (One VehicleDefinition Per VIN)** — Inflates reference data 30–50x, makes inventory search unusable, breaks model-level reporting. Always dedup definitions before loading vehicles.

3. **Using `ParentId` for Multi-Franchise Dealer Hierarchy** — Single-valued field cannot model dealers selling multiple OEM brands. Migrate to `AccountAccountRelation` before scaling beyond single-franchise pilots.

4. **Direct DML on `ActionableEventOrchestration.Status`** — Bypasses orchestration side-effects and leaves the engine in an inconsistent state. Drive state through invocable actions only.

## Official Sources Used

- Automotive Cloud Developer Guide (Spring '26) — https://developer.salesforce.com/docs/atlas.en-us.automotive_cloud_dev.meta/automotive_cloud_dev/automotive_cloud_dev_intro.htm
- Set Up Automotive Cloud (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.auto_set_up_automotive_cloud.htm&type=5
- ActionableEventOrchestration Standard Object — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_actionableeventorchestration.htm
- AccountAccountRelation Standard Object — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_accountaccountrelation.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
