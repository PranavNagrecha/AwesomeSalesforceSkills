# Well-Architected Notes — Data Model Design Patterns

## Relevant Pillars

- **Trusted** — Data model design directly affects data integrity. Master-detail enforces referential integrity at the platform level. External ID fields marked Unique prevent duplicate keys; External ID alone does not. Choosing the wrong field type (e.g., Text for Email) eliminates platform-enforced validation, allowing corrupt data to enter the system.

- **Scalable** — Relationship type and indexing strategy determine how the data model performs at large volumes. Lookup-based junction objects that accumulate orphan records, non-indexed filter fields on large objects, and missing external IDs that cause duplicate proliferation are all scalability failures rooted in the data model. Skinny tables and custom indexes are architectural responses to scale that must be planned early.

- **Adaptable** — Field type selection affects long-term flexibility. Using Text(255) for structured data (phone, email, percentage) creates technical debt when those fields need to participate in deduplication rules, formula logic, or API contracts. MDR chain depth limits future schema changes — adding a third level of master-detail introduces irreversible cascade delete risk.

- **Operational Excellence** — A well-documented data model (relationship types, field type rationale, indexing decisions) reduces the onboarding cost for future administrators and developers. The `data-model-design-patterns-template.md` artifact captures these decisions durably.

---

## Architectural Tradeoffs

### Referential Integrity vs. Flexibility

Master-detail provides strong referential integrity: a child cannot exist without a parent. This is the right choice when the child's existence is semantically dependent on the parent. The tradeoff is cascade delete (and a parent delete that fails if any child can't be deleted), and converting a lookup to MDR needs a parent on every existing child.

Lookup is more flexible — the parent is optional, and the child survives parent deletion. The tradeoff is that lookups do not support rollup summaries, and orphan records can accumulate after parent deletes.

**Decision rule:** Choose master-detail when the business explicitly accepts cascade delete and needs rollup summaries. Default to lookup until those requirements are confirmed.

### MDR Junction vs. Lookup Junction

For many-to-many relationships, the junction object pattern with two MDR fields is architecturally superior when rollup summaries or tight referential integrity are needed on either parent. The tradeoff is the cascade delete risk on both sides — a deleted course deletes all its enrollments, which may also cascade into a third level if enrollments are themselves masters of something.

Lookup-based junctions trade away rollup capability and referential integrity for looser coupling. Orphan junction records can accumulate, creating data quality problems over time.

### Early Indexing Planning vs. Retrofit

Identifying filter field candidates early, and checking them against the custom-index threshold for the expected row count, is cheaper than discovering a table scan after the object reaches millions of rows. External ID covers key fields of the allowed types; everything else needs a Support request.

---

## Anti-Patterns

1. **Lookup-based junction objects** — Building a many-to-many junction with two lookup fields instead of two master-detail fields loses rollup summary capability on both parent objects and allows orphan junction records to accumulate after parent deletion. This is the most common many-to-many modeling mistake. Fix: rebuild the junction with MDR fields from the start, or migrate field values and convert after the fact.

2. **Text fields for structured data** — Using Text(255) for phone numbers, email addresses, percentages, or currency amounts strips platform-enforced validation, formatting, and UI affordances. At scale, this creates data quality debt that requires a field migration to remediate. Fix: use the most semantically specific field type the platform offers for each data category.

3. **Deep MDR chains without cascade delete awareness** — Building a three-level master-detail chain (A → B → C) means deleting an A record deletes all its B and C records. This pattern is not always an anti-pattern, but it becomes one when the business is unaware of the cascade behavior and discovers it during a data correction exercise. Fix: document the cascade behavior explicitly, add Apex guard triggers on master objects, and evaluate whether the third level should be a lookup instead.

4. **Missing external IDs on integration objects** — Objects written by external systems without an External ID field force integrations to rely on Salesforce-generated Ids, which are not portable across orgs (sandbox vs. production) and cannot be used for upsert-based idempotent loads. The result is duplicate records on every re-sync. Fix: add an External ID field (Unique) to every object that receives data from an external system.

---

## Official Sources Used

Read for this revision (2026-10-19):

- Object Reference (`object_reference.txt`), "Relationships Among Objects": master-detail cascade delete, owner from master, sharing inherited, required on the detail page layout, reparenting off by default, standard objects can't be the detail of a custom object, the eight objects that can't be the master, junction objects with two master-detail fields, lookups not automatically required (L3254-3302).
- Metadata API Developer Guide (`api_meta.txt`), CustomField: `deleteConstraint` values Cascade, Restrict, SetNull (default) (L43348-43356); `relationshipOrder` primary/secondary for junctions (L43582-43591); `reparentableMasterDetail` default false (L43593-43596); `summaryForeignKey` is the master-detail field (L43648-43649); `writeRequiresMasterRead` (L43725-43732); `externalId` types, `unique`, `caseSensitive` (L43328, L43402-43404, L43702).
- Apex Developer Guide (`salesforce_apex_developer_guide.txt`): cascade deletes succeed only if each child can be deleted (L8236-8240); Recycle Bin for 15 days and undelete (L8259-8262); default indexes and when a custom index isn't used (L9641-9663).
- Apex Reference Guide (`salesforce_apex_reference_guide.txt`): `emptyRecycleBin` takes the top-level Id for cascade-deleted records (L206927-206931).
- Best Practices for Deployments with Large Data Volumes (`salesforce_large_data_volumes_bp.txt`): custom index thresholds (L463-471); unindexable types and deterministic formulas (L409, L483-484); skinny tables (L329-385).
- Salesforce Developer Limits and Allocations Quick Reference (`salesforce_app_limits_cheatsheet.txt`): a custom object allows up to 40 relationships (L1131-1134); a query operation has 2 minutes to execute (L1101-1104).
- REST API Developer Guide (`api_rest.txt`): upsert key matched multiple times returns a 300 error (L2977); `explain` plans (L17784-17867).

Listed in the original version and not re-read (help.salesforce.com cannot be fetched); claims that rested only on them (lookup Cascade enablement and its sharing behaviour, the 25 External ID limit, field-history behaviour on lookup deletes) were removed or turned into questions:

- Salesforce Help — Enable 'cascade delete on custom lookup relationships' feature — https://help.salesforce.com/s/articleView?id=000382017&language=en_US&type=1
- Salesforce Help — Relationship Considerations — https://help.salesforce.com/s/articleView?id=sf.relationships_considerations.htm
- Salesforce Help — Custom Field Types — https://help.salesforce.com/s/articleView?id=sf.custom_field_types.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
