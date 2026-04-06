# Well-Architected Notes — Product Catalog Data Model

## Relevant Pillars

- **Reliability** — The hard platform constraint (Standard PBE required before custom PBE) means a load sequence error causes a partial catalog with some products missing from custom pricebooks. Reliability requires the load pipeline to verify Standard PBE completion before proceeding, and to use upsert (not insert) so re-runs do not create duplicate records.

- **Operational Excellence** — Product catalog data is referenced by Opportunities, Quotes, and Contracts. Stale or inconsistent pricebook data (e.g., products active in the Standard Pricebook but missing from custom pricebooks, or retired products still active) causes operational failures in downstream sales processes. Operational excellence requires a systematic load sequence, a validation step after each load phase, and explicit product retirement procedures.

- **Performance** — For catalogs with tens of thousands of products across multiple pricebooks, Bulk API 2.0 is required for load performance. SOQL queries against PricebookEntry without selective filters on `Product2Id` or `Pricebook2Id` can become slow on large catalogs. Opportunity product search performance depends on correct PricebookEntry indexing.

- **Security** — PricebookEntry records are visible to all Salesforce users who can access Opportunities; there is no record-level security on PricebookEntry. Pricing confidentiality must be managed at the Pricebook2 level (assigning pricebooks to user profiles) and at the Opportunity level, not through field-level security on PricebookEntry.

- **Scalability** — The three-object model scales to large catalogs without architectural changes. The primary scalability concern is SOQL performance on the Opportunity Line Item product selector when a pricebook contains thousands of active PricebookEntry records. Deactivate unused PricebookEntries to keep the active set lean.

## Architectural Tradeoffs

**Standard Products vs CPQ:** The standard Product2/Pricebook2/PricebookEntry model is appropriate for catalogs with relatively static pricing and no complex configuration rules (no bundles with forced includes, option constraints, or attribute-driven pricing). When the catalog grows beyond simple pricing structures with complex bundling, discount schedules, or subscription pricing, the tradeoff shifts toward Salesforce CPQ or Industries CPQ. See `cpq-vs-standard-products-decision` for the decision criteria.

**UseStandardPrice inheritance vs explicit pricing:** Inheriting from the standard price (`UseStandardPrice = true`) reduces the number of price records to maintain but creates a tight coupling between all custom pricebooks and the standard price. A price change in the Standard Pricebook immediately propagates to all inheriting custom pricebook entries. If different pricebooks need independent price change workflows, all custom PBEs should use explicit `UnitPrice` (`UseStandardPrice = false`).

**Single Standard Pricebook constraint:** The singleton Standard Pricebook cannot be archived or bypassed. It is a hard platform primitive. Architectures that attempt to treat the Standard Pricebook as optional — loading products and bypassing the Standard PBE step — are not supported.

## Anti-Patterns

1. **Loading all PricebookEntry types in a single bulk job** — Mixing Standard PBE rows and custom PBE rows in a single Bulk API job does not guarantee Standard PBEs are committed first. The correct architecture is two sequential jobs with a verification step between them. A single-job approach produces unpredictable partial failures.

2. **Hardcoding the Standard Pricebook ID across orgs** — Any architecture that embeds the Pricebook2 ID with `IsStandard = true` as a constant (in CSVs, Apex, configuration, or metadata) creates an org-specific dependency. The architecture breaks on sandbox refresh, production deployment, or org migration. Always query the ID at runtime.

3. **Using insert instead of upsert for PricebookEntry loads** — A load architecture that inserts rather than upserts PricebookEntries cannot be safely re-run after a partial failure. Retry attempts create duplicate entries (blocked by the uniqueness constraint) and require manual cleanup. All production load pipelines for PricebookEntry should use upsert-equivalent logic.

## Official Sources Used

- PricebookEntry Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_pricebookentry.htm
- Pricebook2 Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_pricebook2.htm
- Product and Price Book Data Model (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.products_pricebooks_def.htm&type=5
- Insert Products via Data Loader (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.data_loader_insert_products.htm&type=5
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Data Loader Guide — https://help.salesforce.com/s/articleView?id=sf.data_loader.htm&type=5
