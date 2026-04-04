# Well-Architected Notes — External ID Strategy

## Relevant Pillars

- **Reliability** — External ID-based upsert is the primary mechanism for making data loads idempotent. A well-designed external ID strategy ensures that any load can be safely re-run after a failure without creating duplicate records or orphaned children. The upsert insert-or-update semantic eliminates the need for pre-load deduplication logic, reducing failure surface area in long-running migration pipelines.

- **Performance** — External ID fields are automatically indexed at field creation, without requiring a Salesforce Support case for a custom index. This means upsert match lookups scale to millions of records without query optimizer degradation. Choosing the correct field type (Number vs Text) avoids index inefficiencies introduced by case-folding in text comparisons.

- **Operational Excellence** — Decoupling Salesforce records from Salesforce record IDs (by using source system natural keys as external IDs) makes the integration portable across org copies: sandboxes, scratch orgs, and production all hold the same source system keys. This means integration tooling and load files do not need to be regenerated per environment, reducing the cost of new org provisioning and integration testing cycles. A documented composite key formula and per-object field inventory also makes future maintainers able to reproduce any load or troubleshoot matching failures without tribal knowledge.

- **Operational Excellence** — A documented composite key formula and per-object external ID field inventory enables any future maintainer to understand how records were loaded, reproduce a load, and troubleshoot matching failures. Integrations that rely on Salesforce record IDs instead of external IDs create undocumented dependencies that break silently when sandbox refreshes or record deletions occur.

## Architectural Tradeoffs

**External ID field type: Text vs Number**
Text fields can carry alphanumeric keys from any source system but introduce case-sensitivity decisions and require ETL normalization. Number fields are unambiguous for integer keys but cannot carry alphanumeric source IDs. The correct choice depends entirely on what the source system generates — there is no universal default. Defaulting to Text for all external IDs without considering case sensitivity is the most common architectural mistake in this domain.

**Single-field vs composite key strategy**
Using a single source-system field as the external ID is simpler and requires fewer ETL transformations. A composite key is required when no single field is globally unique. The tradeoff: composite keys add ETL complexity and a formula that must be maintained across all future loads. The risk of choosing wrong is high — migrating from a single-field to a composite key after records are loaded requires a full re-key of all existing records, which is a costly rework.

**Two-pass parent-child load vs relationship column resolution**
A two-pass load (query parent IDs, embed in child file) is conceptually simple but creates org-specific artifacts (load files that contain Salesforce IDs). Relationship column resolution (using `ParentObject.ExternalIdField__c` syntax) is idempotent and portable but requires the integration author to understand the relationship syntax and enforce parent-before-child load ordering. The relationship column approach is architecturally superior for any integration that must run across multiple org copies.

## Anti-Patterns

1. **Using Salesforce record IDs as the integration's cross-system identifier** — Embedding Salesforce `Id` values in source systems or load files creates a hard dependency on a specific org. Sandbox refreshes, record deletions, and org migrations all invalidate these IDs. External IDs should always be the cross-system reference; Salesforce `Id` values are internal platform artifacts that integrations should never store or transmit beyond a single transaction boundary.

2. **Omitting the Unique constraint on an external ID field used for upsert** — A non-unique external ID field appears to work until the first upsert encounters duplicate values in the org. At that point every upsert row for the affected value errors, and data can only be corrected by manually deduplicating records and re-running the load. Setting both External ID and Unique at field creation is a quality gate, not an optional setting.

3. **Designing a composite key without documenting the formula** — A composite key that is assembled differently across integration runs (different separator, different field ordering, different null handling) produces values that do not match existing records, causing incorrect inserts instead of updates. The composite key formula must be treated as an immutable integration contract and documented before the first load.

## Official Sources Used

- Salesforce Help: External ID Custom Fields — https://help.salesforce.com/s/articleView?id=sf.customfields_external_id.htm
- REST API Developer Guide: Upsert a Record Using an External ID — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_upsert.htm
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference: sObject Concepts — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
