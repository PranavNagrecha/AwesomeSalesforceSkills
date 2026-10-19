# Well-Architected Notes — Data Archival Strategies

## Relevant Pillars

- **Reliability** — An archive is only reliable if it can be read back. Big object writes can partly fail without an exception, and the index cannot be changed after deployment, so a reliable design proves the read path and gates source deletion on verified writes.
- **Scalability** — Archival is the primary mechanism for designing against long-term data growth. Objects that grow unboundedly become query bottlenecks: the query optimizer struggles to use indexes on tables with tens of millions of rows, and reports slow down. A scalable data architecture uses archival to keep active-record counts within performant bounds, offloading aging data to Big Objects or external storage that scale independently.
- **Performance** — Query performance depends on live row counts and on soft-deleted rows, which still have to be excluded from every query. Archival plus a Recycle Bin purge shrinks both.

## Architectural Tradeoffs

**Big Object vs External Storage**

Big Objects keep archived data on-platform and queryable via SOQL (with index constraints) and the Bulk APIs. External storage (S3, Heroku PostgreSQL, Data Cloud) removes data from Salesforce entirely, minimizing on-platform storage costs, but requires custom integration to surface data back to Salesforce users when needed. The tradeoff is: on-platform queryability vs cost-optimized cold storage.

Choose Big Objects when:
- Audit or compliance teams need to run Salesforce-native queries against archived data
- The query pattern is known and fits the composite index design
- Staying fully within the Salesforce trust boundary is a requirement

Choose external storage when:
- Archived data is accessed rarely (cold archive)
- Cost-per-GB is a driving concern
- Data volume exceeds practical Big Object limits or management overhead

**Soft-Delete Pattern vs True Archival**

The IsArchived__c soft-delete pattern preserves full reporting capability at zero implementation cost but does not reclaim any storage. True archival (to Big Object or external) reclaims storage but may break existing reports and integrations that assume all records are in the standard object. The tradeoff is: reporting compatibility vs storage reclamation.

**Field History Retention**

Field history doesn't count against data storage, so it is a retention question, not a storage one. Without Field Audit Trail it is kept up to 18 months (24 via the API), and deleting a record deletes its history. If auditors need history of archived records, a Field Audit Trail policy or an export has to run before the source delete.

## Anti-Patterns

1. **Archiving without a purge** — Soft-deleting the source after archiving leaves rows in the Recycle Bin for 15 days that every query must still exclude. Pair archival with `Database.emptyRecycleBin()` or Bulk API hard delete for query performance; the storage saving comes from the live delete itself.

2. **Using Big Objects as a general-purpose record store** — Big Objects are optimized for high-volume, append-only archival with fixed query patterns. Using them to store data that needs arbitrary filtering, updates, or complex reporting creates significant query limitations and Apex complexity. Only move data to Big Objects when the query pattern is known and maps to an indexable composite key.

3. **Deleting archived parents before settling field history** — The delete cascades to the record's history rows. If retention rules cover field changes, history is lost the moment the archive job deletes the source.

## Official Sources Used

Read for this revision (2026-10-19):

- Big Objects Implementation Guide (API 67.0, fetched from https://developer.salesforce.com/docs/get_document_content/bigobjects/<page>.htm/en-us/262.0, pages big_object, big_object_considerations, big_object_define, big_object_populate, big_object_populate_apex, big_object_delete): editions and 1 million Developer cap; no triggers, flows, processes; object and field permissions only; idempotent writes; SOQL, Bulk, Chatter, SOAP as the only APIs and REST not supported; 100 big objects per org; no encryption for custom big objects; partial batch failures and retry-the-whole-batch; async Apex for writes; index fixed after deployment, required index fields, no LongTextArea/URL, 100-character text total; insertImmediate returns SaveResult, DML treated as callouts and not counted toward DML statements, .trim() advice, NULL upsert behaviour, tests write real data and mixed DML fails; deleteImmediate/deleteByExample with full index, 50,000 per call, 24-hour capacity note.
- Bulk API 2.0 and Bulk API Developer Guide (`api_asynch.txt`): big objects supported for ingest and query in both APIs (L197-198).
- Salesforce Security Guide (`salesforce_security_impl_guide.txt`): field history kept 18 months, 24 via the API, deletable any time, not counted against data storage (L4553-4556, L4632-4636); Field Audit Trail data not counted against storage (L4756, L4826-4827); HistoryRetentionPolicy via Metadata API, FieldHistoryArchive, 200 versus 20 tracked fields, kept until you delete it (L4828-4838); default archive after 18 months in production and one month in sandboxes (L4880-4883); delete cascades to history but not to FieldHistoryArchive (L4892-4897); previously archived history stays unencrypted (L4899-4904); Bulk API 2.0 query on FieldHistoryArchive (L4919-4941).
- Best Practices for Deployments with Large Data Volumes (`salesforce_large_data_volumes_bp.txt`): big objects for archival via Bulk API or Batch Apex (L81-95); soft deletion still affects performance, Recycle Bin items don't count against storage, no item limit, 15-day retention, hard delete recommendation (L733-742); hard delete for one million or more records (L1019-1023); Recycle Bin kept empty in the report case (L1258).
- Apex Reference Guide (`salesforce_apex_reference_guide.txt`): `Database.deleteImmediate` and the 50,000-record big object batch limit (L206783-206805); `Database.emptyRecycleBin` permanent, 10,000 records, counts as a DML statement (L206900-206935).
- Apex Developer Guide (`salesforce_apex_developer_guide.txt`): callouts aren't allowed after DML operations in the same transaction by default (L35136).
- Metadata API Developer Guide (`api_meta.txt`): Index and IndexField types, required name and sortDirection (L44136-44181); CustomField `trackHistory` (L43675).

Listed in the original version and not re-read (help.salesforce.com cannot be fetched); the storage-allocation figures and the Async SOQL retirement note that rested on them were removed from this package rather than kept unverified:

- Salesforce Help 000394892 (Big Objects Async SOQL retirement) — https://help.salesforce.com/s/articleView?id=000394892&language=en_US&type=1
- Salesforce Help: Data and File Storage Allocations — https://help.salesforce.com/s/articleView?id=xcloud.overview_storage.htm&language=en_US&type=5
- Salesforce Help: Manage the Recycle Bin — https://help.salesforce.com/s/articleView?id=xcloud.recycle_bin_manage.htm&language=en_US&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
