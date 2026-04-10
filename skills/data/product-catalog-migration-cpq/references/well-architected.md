# Well-Architected Notes — Product Catalog Migration CPQ

## Relevant Pillars

- **Reliability** — CPQ catalog migration is a high-consequence data operation. A single wave loaded out of order, or CPQ triggers active during bulk DML, can corrupt the pricing configuration in ways that are not visible until a quote is generated in production. Wave sequencing, post-wave validation queries, and pre-go-live quote smoke tests are the primary reliability controls.

- **Operational Excellence** — The migration must be repeatable and auditable. External ID fields on every SBQQ object, post-wave row count comparisons, and the orphan detection SOQL create a documented audit trail. "Triggers Disabled" must be treated as an operational gate — confirmed before every wave, not assumed to persist from session start.

- **Performance** — CPQ managed-package triggers are expensive at bulk scale. Disabling triggers before DML operations and re-enabling after all waves complete is a performance control that prevents CPU governor limit failures and cascading quote recalculations from slowing or blocking the migration.

- **Security** — CPQ product catalog records (PriceRule, DiscountSchedule) control commercial pricing. Access to the migration tooling, the export files, and the target org during migration should be restricted to the migration team. External ID fields that expose internal product codes or pricing logic should not persist after the migration is complete — consider removing or nulling the migration external ID values post-cutover if they expose commercially sensitive data.

- **Scalability** — The wave-based dependency sequence scales linearly with catalog size. Orgs with tens of thousands of ProductOption records should partition Wave 4 into sub-batches by bundle family to stay within Bulk API 2.0 job size limits and to allow partial retry on failure without re-running the entire wave.

## Architectural Tradeoffs

**External ID upsert vs. manual ID mapping table:** External ID upsert with relationship notation is strongly preferred. It delegates FK resolution to the platform, eliminates the manual mapping table, and is idempotent — re-running the upsert with the same external IDs is safe. The tradeoff is that external ID fields must be created on each SBQQ object before the migration starts, which requires a metadata deployment to the target org. For migrations under tight timelines, some practitioners use a manual ID mapping table instead — this is acceptable for small catalogs (under 500 records) but becomes error-prone at scale.

**Single-job multi-object load vs. strict wave isolation:** Wave isolation (one completed Bulk API job per wave before starting the next) is more reliable than multi-object batching. The tradeoff is elapsed time — a fully isolated wave migration may take hours for a large catalog. Multi-object batching with carefully ordered rows is tempting but introduces non-deterministic FK resolution failures (see gotchas). Wave isolation is always the correct architectural choice for CPQ catalog migrations.

**Leaving CPQ triggers disabled vs. partial trigger re-enable between waves:** Some practitioners re-enable triggers between waves to run validation checks. This is an anti-pattern — it introduces the risk of partial cascade runs against an incomplete catalog state. Keep triggers disabled for the full duration of the load. Run post-load validation using SOQL queries (not CPQ UI) while triggers are still disabled. Re-enable only once all waves are confirmed and all validation queries pass.

## Anti-Patterns

1. **Loading SBQQ objects in undefined order** — Inserting ProductOption, PriceAction, ConfigurationAttribute, and OptionConstraint without a documented dependency sequence produces a mix of immediate FK failures and silent orphan records. The failure mode depends on which objects happen to be committed at the time each batch processes — making it non-deterministic and hard to reproduce in a retry. Always use the five-wave sequence defined in SKILL.md.

2. **Assuming Bulk API success = data integrity** — Bulk API 2.0 success responses confirm that records were written to the database. They do not confirm that CPQ-layer FK relationships (e.g., PriceAction → PriceRule) are valid from the pricing engine's perspective. Post-load validation SOQL queries are mandatory; Bulk API success alone is not a sufficient quality gate for CPQ catalog migrations.

3. **Re-enabling CPQ triggers before post-load validation** — Re-enabling triggers while orphaned PriceActions or incomplete ProductOption sets exist in the target causes the CPQ pricing engine to run against an invalid catalog state. Any quote generated in this window may produce incorrect prices or configuration errors. Always complete all validation queries and confirm zero orphans before re-enabling triggers.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Data Loader Guide — https://help.salesforce.com/s/articleView?id=sf.data_loader.htm&type=5
- Salesforce CPQ Price Rules — https://help.salesforce.com/s/articleView?id=sf.cpq_price_rules.htm&type=5
- Salesforce CPQ Discount Schedules — https://help.salesforce.com/s/articleView?id=sf.cpq_discount_schedules.htm&type=5
- Insert Products via Data Loader — https://help.salesforce.com/s/articleView?id=sf.products_insert_data_loader.htm&type=5
- PricebookEntry Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_pricebookentry.htm
