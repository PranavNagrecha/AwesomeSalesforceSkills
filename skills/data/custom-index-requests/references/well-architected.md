# Well-Architected Notes — Custom Index Requests

## Relevant Pillars

- **Reliability** — Custom indexes prevent queries from degrading to TableScans as data volume grows. Reliability at scale requires anticipating which queries will become non-selective as the org grows from thousands to millions of records and proactively requesting indexing before performance degrades.
- **Operational Excellence** — Index requests require Salesforce Support engagement, selectivity validation, and post-creation monitoring. The operational process — Query Plan analysis, Support case with complete information, and post-index validation — should be documented and repeatable.

## Architectural Tradeoffs

**External ID vs non-unique custom index:** Marking a field as External ID creates a unique index and enforces uniqueness at the database level. If the field does not need uniqueness, External ID is not semantically correct. A non-unique custom index (via Support case) is the right choice for fields that filter records but contain duplicates. Do not misuse External ID designation just to get an index.

**Custom index vs query refactoring:** Requesting a custom index is the right choice when the access pattern is correct and selectivity is achievable. But indexes are not always the answer — a query that will always return 40% of records cannot be made selective by an index. In those cases, refactor the query to add more selective filters or consider a different data model. Do not request an index as a substitute for fixing a non-selective query.

## Anti-Patterns

1. **Requesting an index on a non-selective field** — Salesforce will create the index, but the query optimizer will not use it if the field returns >10% of records. The Support case will have been filed and processed, the index will exist, but query performance will not improve. Always validate selectivity before requesting.
2. **Testing index performance in a Developer sandbox** — custom indexes and skinny tables are not copied to Partial or Developer sandboxes. Performance testing in a Developer sandbox will show no improvement even if the index exists in production. Always validate in a Full sandbox.
3. **Using External ID on a non-integration-key field just to get an index** — External ID implies "this field is a key used to identify records from an external system and is used for upsert operations." Misusing it for non-integration fields creates semantic confusion and enforces a uniqueness constraint that may not be desired.

## Official Sources Used

- Salesforce Large Data Volumes Best Practices — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_introduction.htm
- Query and Search Optimization Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_optimization.htm
- Custom Indexes Overview — https://help.salesforce.com/s/articleView?id=sf.custom_indexes_overview.htm&type=5
