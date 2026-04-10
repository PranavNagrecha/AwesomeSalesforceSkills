# Well-Architected Notes — Marketing Data Architecture

## Relevant Pillars

- **Performance** — The dominant architectural concern in Marketing Cloud data design. Automation Studio query activities have a hard 30-minute timeout. Normalized DE models with smaller per-DE row counts and custom-indexed filter columns are the primary performance levers. Wide flat DEs with hundreds of columns and millions of rows reliably cause timeout failures that cannot be resolved at runtime — only preventable through upfront schema design.

- **Reliability** — CRM-to-MC data pipelines must be designed for failure resilience. MC Connect Synchronized DEs are near-real-time but can experience sync delays or field exclusions (250-field cap, unsupported field types). SFTP import pipelines are batch and depend on file delivery reliability. Both paths require monitoring, alerting on sync failures, and documented fallback procedures when data does not arrive.

- **Security** — Contact Key / SubscriberKey is a PII-adjacent identifier linking contact identity across all DEs. The data model must ensure that subscriber identity linkage (the Contact Key) is not exposed to unauthorized systems or logs. SDEs contain raw CRM field data including potentially sensitive account and opportunity fields — field selection for sync should be reviewed for data minimization. SFTP pipelines must use encrypted transport and credential rotation.

- **Operational Excellence** — A documented data model (DE schemas, Data Relationship map, Contact Key linkage, integration path) is essential for ongoing operations. Without it, new team members cannot troubleshoot audience count discrepancies or understand why a personalization field returns blank. Automation Studio pipelines should include error notification steps so sync failures and query timeouts generate alerts rather than silent failures.

---

## Architectural Tradeoffs

**Normalized relational DE model vs. wide flat table:**
The normalized model improves query performance, simplifies updates to individual entities, and reduces the risk of hitting the Automation Studio query timeout. The trade-off is query complexity — SQL Query Activities and AMPscript that join across DEs are more complex to author and debug than queries against a single flat table. For teams with limited SQL expertise, the complexity cost may be real. The correct recommendation is normalized model for any implementation expecting more than 500,000 rows per entity or planning to run daily query activities.

**MC Connect Synchronized DEs vs. SFTP import:**
MC Connect provides near-real-time CRM data freshness and reduces manual file management overhead. The trade-off is that SDEs are read-only, require MC Connect to be installed and licensed, and are limited to Salesforce CRM objects. SFTP imports are more flexible (any data source) and produce writable DEs but are batch-only. For CRM-owned contact data, MC Connect is always preferred. For non-CRM data, SFTP is the only option.

**Contact Key vs. Email Address as SubscriberKey:**
Using Contact Key (Salesforce ID) as SubscriberKey is the architecturally correct approach — it is stable, unique, and survives email address changes. The trade-off is that it is not human-readable, making manual subscriber lookups in All Subscribers harder for non-technical users. Email address as SubscriberKey is readable but causes deduplication failures when contacts have multiple email addresses or change addresses. The performance and correctness benefits of Contact Key always outweigh the readability convenience.

---

## Anti-Patterns

1. **Flat Wide DE as the Universal Data Store** — Building a single DE with contact, order, preference, and product data in one table eliminates the need to define Data Relationships and simplifies initial query authoring. This becomes an anti-pattern at scale: the DE grows to millions of rows with hundreds of columns, query activities time out, updating any single entity requires reimporting millions of rows, and the DE becomes a bottleneck for every marketing use case. The Salesforce Well-Architected Performance pillar prescribes designing data structures to remain within platform limits upfront — a wide flat DE violates this by deferring the problem until scale makes it unrecoverable without a full data migration.

2. **Email Address as SubscriberKey** — Using email address as the primary subscriber identifier is a shortcut that creates data integrity failures over time. All Subscribers allows duplicate email addresses under different SubscriberKeys, so email-as-key is not enforced as unique. Subscription status, suppression records, and personalization lookups all depend on SubscriberKey matching correctly. This anti-pattern often appears in orgs that started without CRM integration and becomes expensive to migrate later because changing SubscriberKey values requires re-importing all subscribers and rebuilding suppression lists.

3. **Building Send Audiences Directly Against Synchronized DEs** — SDEs are read-only and have no Send Relationship defined. Using an SDE as a Journey Builder entry source or Email Studio send audience fails at runtime. The correct pattern is to build a writable sendable DE populated by a Query Activity that reads the SDE. This intermediate step is sometimes seen as unnecessary overhead, leading teams to attempt the direct SDE path — which does not work.

---

## Official Sources Used

- Salesforce Help — Manage Data in Data Extensions: https://help.salesforce.com/s/articleView?id=sf.mc_es_data_extension_data.htm&type=5
- Salesforce Help — Data Relationships in Marketing Cloud: https://help.salesforce.com/s/articleView?id=sf.mc_cab_data_relationship.htm&type=5
- Salesforce Help — Create a Data Relationship: https://help.salesforce.com/s/articleView?id=sf.mc_cab_create_data_relationship.htm&type=5
- Salesforce Developer — Standard Data Model Objects: https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/data-extension-object.html
- Salesforce Help — Marketing Cloud Connect Synchronized Data Sources: https://help.salesforce.com/s/articleView?id=sf.mc_co_sync_data_sources.htm&type=5
- Salesforce Well-Architected Overview: https://architect.salesforce.com/well-architected/overview
- Salesforce Well-Architected Performance: https://architect.salesforce.com/well-architected/perform/overview
