# Well-Architected Notes — Custom Index Requests

## Relevant Pillars

- **Reliability** — Custom indexes prevent queries from degrading to TableScans as data volume grows. Reliability at scale requires anticipating which queries will become non-selective as the org grows from thousands to millions of records and proactively requesting indexing before performance degrades.
- **Operational Excellence** — Index requests require Salesforce Support engagement, selectivity validation, and post-creation monitoring. The operational process — Query Plan analysis, Support case with complete information, and post-index validation — should be documented and repeatable.

## Architectural Tradeoffs

**External ID, Unique, or a Support index:** External ID and Unique both make Salesforce index a custom Auto Number, Email, Number, or Text field; only Unique enforces uniqueness. External ID also makes the field an upsert key, so duplicated values make upserts on it fail. For filter fields of other types, or standard fields, a Support-built index is the path.

**Custom index vs query refactoring:** Requesting a custom index is the right choice when the access pattern is correct and selectivity is achievable. But indexes are not always the answer — a query that will always return 40% of records cannot be made selective by an index. In those cases, refactor the query to add more selective filters or consider a different data model. Do not request an index as a substitute for fixing a non-selective query.

## Anti-Patterns

1. **Requesting an index on a non-selective field** — The optimizer skips a custom index whose filter matches 10% or more of the first million rows (5% beyond). Attach counts and threshold arithmetic to every request.
2. **Testing a skinny table in the wrong sandbox** — Skinny tables are copied to Full sandboxes only, while Support-built custom indexes are copied to all sandboxes created from production. Test each in a sandbox that actually has it.
3. **Using External ID on a field that should not be an upsert key** — External ID marks the field as a record identifier from another system. Using it only to obtain an index on a descriptive field invites accidental upserts on non-unique values; prefer a Support-built index when the field is not a key.

## Official Sources Used

Read for this revision (2026-10-19):

- Best Practices for Deployments with Large Data Volumes (`salesforce_large_data_volumes_bp.txt`): custom indexes via Support or a custom index XML file via Metadata API (L395); copied to all sandboxes (L398); default indexed fields and unindexable types (L399-409); External IDs create an index, allowed types, Support for others (L418-424); null rows excluded and rebuild needed (L436-438); thresholds and worked examples (L463-471); non-deterministic formula cases (L485-505); two-column indexes, column roles, nulls in the second column (L524-538); skinny tables: join avoidance, objects, warning, 200 columns, no cross-object fields, Full sandboxes only (L329-385); nightly statistics (L315-319); NA placeholder for null filters on picklists and foreign keys (L960).
- Apex Developer Guide (`salesforce_apex_developer_guide.txt`): fields indexed by default including External ID or Unique custom fields; unindexable types; TEXT() on picklists; when a custom index isn't used (L9641-9663); upsert key matched multiple times returns an error (L7868).
- Metadata API Developer Guide (`api_meta.txt`): CustomIndex type, `.indx-meta`, API 50.0+, special access rule to contact Customer Support, `allowNullValues`, `booleanIndexedValue` (L41099-41138); CustomField `externalId` and `unique` as separate booleans, `caseSensitive` (L43328, L43402-43404, L43702).
- REST API Developer Guide (`api_rest.txt`): external ID matched multiple times returns a 300 error on upsert (L2977); `explain` plan fields and `relativeCost` above 1.0 meaning not selective (L17784-17867).
- Bulk API 2.0 Developer Guide (`api_asynch.txt`): the same 300 error for duplicated external IDs in ingest (L2500).

Listed in the original version and not re-read (help.salesforce.com cannot be fetched); the per-type caps they were cited for were replaced with the LDV guide's worked examples:

- Salesforce Help 000386864: Developer Console Query Plan Tool FAQ — https://help.salesforce.com/s/articleView?id=000386864&language=en_US&type=1
- Salesforce Help 000383981: Make a SOQL query selective by marking a field as External ID or Unique — https://help.salesforce.com/s/articleView?id=000383981&language=en_US&type=1
- Custom Indexes Overview — https://help.salesforce.com/s/articleView?id=sf.custom_indexes_overview.htm&type=5
- Query and Search Optimization (SOQL and SOSL Reference) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_optimization.htm
