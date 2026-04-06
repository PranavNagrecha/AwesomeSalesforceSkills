# Well-Architected Notes — Opportunity Pipeline Migration

## Relevant Pillars

- **Reliability** — The strict load sequence (Product2 → Standard PBE → Custom PBE → Opportunity → OpportunityLineItem → OpportunityTeamMember → OpportunitySplit) must be followed exactly to avoid partial loads and broken referential integrity. Each step must be verified before the next begins. Rollback must be planned before the first record is inserted, using `Migration_Batch_Id__c` on each object for targeted deletes.

- **Operational Excellence** — External ID fields on Opportunity (e.g., `Legacy_Opportunity_Id__c`) and Product2 (e.g., `Legacy_Product_Id__c`) make the migration re-runnable via upsert. Post-migration validation queries (record count reconciliation, Amount total spot-checks, OLI count per opportunity) must be defined before cutover and run immediately after each load step. Migration batch IDs enable surgical rollback without touching records from other batches.

- **Performance** — Bulk API 2.0 is the required tool for large Opportunity migrations. Batch size should target 10,000 records per batch for maximum throughput. Sequential update waves for stage history (Option B) multiply API job count by the number of stage transitions — estimate total API row volume before choosing this approach to avoid hitting the 150M rows/24h Bulk API limit.

- **Security** — The migration user must have a validation rule bypass in place before loading if validation rules are active on Opportunity or its children. Use a Custom Permission bypass (`NOT($Permission.Bypass_Migration_Validation)`) in each rule formula rather than deactivating rules in production. Clear the bypass immediately after the migration completes. Avoid loading sensitive commercial data (pricing, revenue splits) without confirming the migration user's field-level security is scoped appropriately.

## Architectural Tradeoffs

**Task records vs. sequential updates for stage history:**
Task records are lightweight, fast, and do not multiply API job count. They appear in the Activity Timeline but do not populate the native Stage History related list. Sequential updates produce native history that appears in Stage History and is correctly reportable via standard reports, but multiply API job volume by the number of stage transitions per opportunity. For migrating over 20,000 opportunities with more than 3 average stage transitions, sequential updates may exceed daily Bulk API limits and should be spread across multiple days or replaced with Task records.

**Standard vs. Custom Price Book:**
If the org's standard Price Book is the only Price Book, the `Pricebook2Id` on Opportunity can be set to the Standard Price Book Id, eliminating the custom PBE creation step. If multiple custom Price Books exist, the migration CSV must map each source opportunity to the correct Salesforce Price Book before loading — a many-to-one mapping error here locks incorrect Price Books onto Opportunities permanently (post-line-item-load).

**OpportunitySplits enablement timing:**
If the business is unsure whether Splits are needed long-term, enabling them should be deferred until after the core Opportunity and OLI migration is complete, since enabling Splits adds a mandatory SplitType configuration dependency. Enabling Splits mid-migration does not affect already-loaded Opportunity records.

## Anti-Patterns

1. **Attempting to insert OpportunityHistory directly** — OpportunityHistory is system-generated and read-only. Any migration plan that includes a step to insert OpportunityHistory records will fail at runtime. This wastes migration window time and produces misleading error messages. The correct pattern is Task records or sequential Opportunity updates.

2. **Loading OpportunityLineItems before confirming Pricebook2Id on every Opportunity** — If even one Opportunity has a missing or incorrect `Pricebook2Id`, all its line items will fail to load. Because the error message ("pricebook entry does not exist or is not available") implies a missing PricebookEntry rather than a missing Price Book assignment, root-cause diagnosis is slow. Always run a verification query on Pricebook2Id before proceeding to the OLI load.

3. **Loading OpportunitySplit without validating split percentages sum to 100%** — If the org's split validation rule requires percentages to sum to 100% per SplitType per Opportunity, any split set that does not meet this constraint will fail. Loading splits that fail validation produces a partial split state — some team members have splits, others do not — that is difficult to reconcile without deleting all splits and reloading. Validate split totals in the source CSV before load using a simple aggregation script.

## Official Sources Used

- OpportunityHistory Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunityhistory.htm
- OpportunityFieldHistory Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunityfieldhistory.htm
- Load Opportunity Products — https://help.salesforce.com/s/articleView?id=sf.products_opportunity_load.htm&type=5
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Data Loader Guide — https://help.salesforce.com/s/articleView?id=sf.data_loader.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
