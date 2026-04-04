# Well-Architected Notes — Data Storage Management

## Relevant Pillars

- **Reliability** — Storage exhaustion causes record insert failures across the entire org. Any trigger, flow, process, or API call that creates a record will fail with a "storage limit exceeded" error once data storage is full. Proactive monitoring and reclamation are reliability requirements, not just operational preferences.
- **Scalability** — Storage is a fixed shared resource that grows predictably with record volume but can spike unexpectedly with file uploads, history tracking, or bulk data loads. Capacity planning must project storage growth 12–24 months out and include archival triggers before limits are reached.
- **Operational Excellence** — Salesforce's built-in storage alerts (75%, 90%, 100%) are lagging indicators. Operationally excellent orgs monitor storage via the Limits API on a scheduled basis and act at 70% to avoid emergency remediation. Retention policies should be codified and automated rather than manually triggered after an alert.
- **Security** — ContentDocument sharing is governed by ContentDocumentLink `ShareType` and `Visibility` settings. Incorrect visibility settings (e.g., `AllUsers` on sensitive documents) can expose files to all internal users. File storage management actions (bulk delete, migration) should be performed with appropriate record ownership and sharing rules in mind.

## Architectural Tradeoffs

**ContentDocument vs Attachment:** ContentDocument requires more design upfront (ContentVersion insert, then ContentDocumentLink creation) but eliminates binary duplication and supports versioning and sharing. Attachment is simpler to create but creates one binary copy per parent record. At scale, the Attachment model is storage-inefficient. New designs should always use ContentDocument.

**Big Object vs standard object for log/audit data:** Standard custom objects count toward data storage and benefit from full SOQL, reports, and list views. Big Objects do not count toward standard data storage, support billions of records, but have limited query flexibility (indexed fields only, no arbitrary SOQL filters). For append-only audit data with known access patterns, Big Objects are the right choice. For operational data that needs flexible querying, keep in standard objects and manage lifecycle through deletion or archival.

**Proactive reclamation vs reactive emergency cleanup:** Organizations that implement automated retention policies (batch delete of records past retention age) maintain predictable storage levels and avoid emergency situations. Organizations that react only to 90% or 100% alerts face time pressure, incomplete analysis, and risk of accidental deletion of needed records. The Well-Architected principle of proactive risk management applies directly here.

**Limits API monitoring vs Setup UI:** The Setup UI is point-in-time and manual. The Limits API enables automated trend tracking, scheduled alerts, and integration with external monitoring tools (Datadog, PagerDuty). For production orgs, automated Limits API polling should replace Setup UI manual checks as the primary monitoring mechanism.

## Anti-Patterns

1. **Reacting only to Salesforce storage alert emails** — Salesforce's automated alerts at 75%, 90%, and 100% are designed as a safety net, not a monitoring strategy. By 90%, the org may have days or hours before insert failures begin. An org without proactive Limits API monitoring is one large data load away from an outage. Implement automated monitoring that alerts at 70% remaining to allow time for planned reclamation.

2. **Migrating records to Big Objects to "free up data storage" without confirming Big Object allocation** — Big Objects have their own separate storage allocation. Moving data from standard custom objects to Big Objects does reclaim standard data storage. However, Big Objects require a defined composite index and do not support all SOQL features. Migrating data to a Big Object without designing the index and validating query patterns results in data that is inaccessible or requires full-scan workarounds.

3. **Deleting parent records without cleaning up orphaned ContentDocuments** — Bulk record deletions that do not include ContentDocument cleanup leave orphaned files in file storage indefinitely. At scale, these orphans can consume gigabytes of storage with no business value. Any automated record lifecycle or archival job should include a ContentDocument cleanup step for records with known file attachment patterns.

## Official Sources Used

- Salesforce Help: Manage Storage — https://help.salesforce.com/s/articleView?id=sf.admin_monitorresources.htm&type=5
- Salesforce REST API Developer Guide: Limits Resource — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm
- Salesforce Object Reference: ContentDocument — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentdocument.htm
- Salesforce Object Reference: ContentDocumentLink — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contentdocumentlink.htm
- Salesforce Well-Architected Overview — architecture quality framing for reliability and scalability pillars — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Large Data Volumes Best Practices — storage, archival, and query guidance for high-volume orgs — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_introduction.htm
