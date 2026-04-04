# Well-Architected Notes — Data Model Design Patterns

## Relevant Pillars

- **Trusted** — Data model design directly affects data integrity. Master-detail enforces referential integrity at the platform level. External ID fields with uniqueness constraints prevent duplicate records. Choosing the wrong field type (e.g., Text for Email) eliminates platform-enforced validation, allowing corrupt data to enter the system.

- **Scalable** — Relationship type and indexing strategy determine how the data model performs at large volumes. Lookup-based junction objects that accumulate orphan records, non-indexed filter fields on large objects, and missing external IDs that cause duplicate proliferation are all scalability failures rooted in the data model. Skinny tables and custom indexes are architectural responses to scale that must be planned early.

- **Adaptable** — Field type selection affects long-term flexibility. Using Text(255) for structured data (phone, email, percentage) creates technical debt when those fields need to participate in deduplication rules, formula logic, or API contracts. MDR chain depth limits future schema changes — adding a third level of master-detail introduces irreversible cascade delete risk.

- **Operational Excellence** — A well-documented data model (relationship types, field type rationale, indexing decisions) reduces the onboarding cost for future administrators and developers. The `data-model-design-patterns-template.md` artifact captures these decisions durably.

---

## Architectural Tradeoffs

### Referential Integrity vs. Flexibility

Master-detail provides strong referential integrity: a child cannot exist without a parent. This is the right choice when the child's existence is semantically dependent on the parent. The tradeoff is that cascade delete is permanent and irreversible, and the conversion from lookup to MDR is a data migration if records already exist.

Lookup is more flexible — the parent is optional, and the child survives parent deletion. The tradeoff is that lookups do not support rollup summaries, and orphan records can accumulate after parent deletes.

**Decision rule:** Choose master-detail when the business explicitly accepts cascade delete and needs rollup summaries. Default to lookup until those requirements are confirmed.

### MDR Junction vs. Lookup Junction

For many-to-many relationships, the junction object pattern with two MDR fields is architecturally superior when rollup summaries or tight referential integrity are needed on either parent. The tradeoff is the cascade delete risk on both sides — a deleted course deletes all its enrollments, which may also cascade into a third level if enrollments are themselves masters of something.

Lookup-based junctions trade away rollup capability and referential integrity for looser coupling. Orphan junction records can accumulate, creating data quality problems over time.

### Early Indexing Planning vs. Retrofit

Identifying filter field candidates early and requesting custom indexes before data volumes grow is significantly cheaper than retroactively requesting an index on an object with 5 million records after production queries are timing out. Custom index creation on large objects can require Salesforce to schedule the build during off-peak hours.

---

## Anti-Patterns

1. **Lookup-based junction objects** — Building a many-to-many junction with two lookup fields instead of two master-detail fields loses rollup summary capability on both parent objects and allows orphan junction records to accumulate after parent deletion. This is the most common many-to-many modeling mistake. Fix: rebuild the junction with MDR fields from the start, or migrate field values and convert after the fact.

2. **Text fields for structured data** — Using Text(255) for phone numbers, email addresses, percentages, or currency amounts strips platform-enforced validation, formatting, and UI affordances. At scale, this creates data quality debt that requires a field migration to remediate. Fix: use the most semantically specific field type the platform offers for each data category.

3. **Deep MDR chains without cascade delete awareness** — Building a three-level master-detail chain (A → B → C) means deleting an A record silently and permanently deletes all B and all C records. This pattern is not always an anti-pattern, but it becomes one when the business is unaware of the cascade behavior and discovers it during a data correction exercise. Fix: document the cascade behavior explicitly, add Apex guard triggers on master objects, and evaluate whether the third level should be a lookup instead.

4. **Missing external IDs on integration objects** — Objects written by external systems without an External ID field force integrations to rely on Salesforce-generated Ids, which are not portable across orgs (sandbox vs. production) and cannot be used for upsert-based idempotent loads. The result is duplicate records on every re-sync. Fix: add an External ID field (Unique) to every object that receives data from an external system.

---

## Official Sources Used

- Salesforce Object Reference — Relationship Considerations — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/relationships_considerations.htm
- Salesforce Help — Relationship Considerations — https://help.salesforce.com/s/articleView?id=sf.relationships_considerations.htm
- Apex Developer Guide — SOQL Indexes — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL_indexes.htm
- Salesforce Help — Custom Field Types — https://help.salesforce.com/s/articleView?id=sf.custom_field_types.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Large Data Volumes Best Practices — knowledge/imports/salesforce-large-data-volumes-best-practices.md (local import)
