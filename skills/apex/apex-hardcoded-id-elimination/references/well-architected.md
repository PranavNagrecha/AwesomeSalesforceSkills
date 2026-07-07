# Well-Architected Notes — Apex Hardcoded ID Elimination

## Relevant Pillars

- **Reliability** — Hardcoded IDs are the single largest source of "works in prod, breaks in sandbox" defects. The same code path is triggered, but the ID literal points to nothing in the destination org. Eliminating literals eliminates an entire failure mode that is invisible in static analysis and only surfaces at runtime, often in the wrong environment.
- **Operational Excellence** — Name-based and CMDT-driven lookups make Apex portable across sandbox refreshes, scratch-org CI, and managed-package subscriber orgs. Admins can re-target a Queue or default Owner without a code release. Refresh cycles, sandbox seeding, and scratch-org definition files become repeatable.

## Architectural Tradeoffs

| Tradeoff | Discussion |
|---|---|
| Describe-API call vs SOQL | Describe is free of SOQL cost but takes some CPU. For RecordType, describe is unambiguously better. For Profile/Group/Queue, describe is unavailable; SOQL with caching is the pattern. |
| Cached static map vs Platform Cache | Static map is per-transaction, simple, no setup. Platform Cache survives transactions but adds operational complexity. Use Platform Cache only when measured SOQL cost across transactions justifies it. |
| Custom Metadata vs Custom Setting | CMDT is deployable and visible in source control; ideal for ID mappings. Custom Settings (Hierarchy) suit per-user/per-profile overrides. ID-mapping config almost always belongs in CMDT. |
| Metadata Relationship field vs raw `Text__c` ID | For references to *metadata* (another CMDT record, an object, a field), a Metadata Relationship field gives referential integrity and portability that a raw ID string cannot. Reserve `Text__c` for references to *data* records that metadata relationships can't target — custom metadata types have no Lookup field type, so a Text field is the only place to store a data-record Id. |
| `getInstance()` cache read vs SOQL on `__mdt` | `getInstance()`/`getAll()` are free of SOQL and query-row limits but truncate every field to 255 chars. When a config value can exceed 255 chars, the SOQL query on the `__mdt` type is the correct read even though it costs a query. |
| Lookup at every call vs static-init | Static initializers (`static final Id X = describe(...)`) are concise but throw at class-load time if metadata is missing. Lazy lookup via helper method gives clearer errors. |

## Anti-Patterns

1. **Literal Salesforce IDs in production Apex** — guaranteed to break on sandbox refresh, scratch-org spin-up, or managed-package install. There is no scenario in which a literal ID is the right answer in non-test code.
2. **Looking up by translatable label (`getRecordTypeInfosByName`)** — labels are not API-stable. Use `getRecordTypeInfosByDeveloperName()`.
3. **`String` typed variables holding IDs** — opens the 15/18-char comparison failure mode. Always use the `Id` type.
4. **Per-iteration SOQL for ID lookup** — single query per transaction, cached in a static map, is the only acceptable shape.
5. **Test classes that hardcode test data IDs** — non-portable, fail in scratch orgs and across CI environments. Insert seed data, capture `.Id` at runtime.
6. **Parking a raw record ID in a CMDT `Text__c` field when a Metadata Relationship fits** — for references to metadata (another CMDT record, an object, a field), the Metadata Relationship field type carries a stable reference with referential integrity. Dropping a raw 15/18-char ID into a text field re-imports the very portability problem CMDT is meant to solve.

## Official Sources Used

- Apex Developer Guide — DescribeSObjectResult — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_sobject_describe.htm
- Apex Developer Guide — Schema Methods — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_schema.htm
- Apex Developer Guide — Working with Schema Information — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dynamic_schema.htm
- Salesforce Architects — Avoid Hardcoding IDs — https://architect.salesforce.com/well-architected/operational-excellence/operable
- Apex Developer Guide — Custom Metadata Types — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_metadata_intro.htm
- Metadata API Developer Guide — Custom Metadata Types (deploy/DML model) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_custommetadatatypes.htm
- Salesforce Help — Custom Metadata Type Fields (supported field-type list; no Lookup type) — https://help.salesforce.com/s/articleView?id=platform.custommetadatatypes_fields.htm&language=en_US&type=5
- Salesforce Help — Custom Metadata Relationship Fields — https://help.salesforce.com/s/articleView?id=sf.custommetadatatypes_relationships.htm&language=en_US&type=5
- Apex Reference Guide — Custom Metadata Type Methods (getAll/getInstance, cache, 255-char limit) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_custom_metadata_types.htm
- Salesforce Help — Custom Metadata Type Visibility (Public/Protected/PackageProtected) — https://help.salesforce.com/s/articleView?id=platform.custommetadatatypes_protection.htm&language=en_US&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
