# Well-Architected Notes — Field Audit Trail

## Relevant Pillars

- **Security** — Field Audit Trail is a Shield security feature. Its primary purpose is enabling tamper-evident, long-term audit records of field-level changes across sensitive objects. Proper FAT configuration directly satisfies the Well-Architected Security pillar's requirement that "data access and changes are logged at the appropriate granularity for compliance and incident response." FAT provides the field-level audit log needed to answer: who changed what, when, and from what value.

- **Operational Excellence** — FAT retention policies and querying patterns must be documented, validated, and maintained as the org evolves. Adding new sensitive fields to an object without updating the FAT policy creates silent compliance gaps. Operational Excellence requires that FAT coverage is treated as a living configuration — tracked in metadata, validated by automated checkers, and reviewed when new regulated fields are added or compliance requirements change.

## Architectural Tradeoffs

**Standard Field History Tracking vs. Shield FAT:**
Standard Field History Tracking is included with all Salesforce editions and is reportable — it is the correct default for short-term operational audit needs (< 18 months, < 20 fields per object). Shield FAT is the right choice only when retention requirements exceed 18 months or field counts exceed 20. Introducing Shield FAT without a genuine compliance requirement adds complexity (async archival, SOQL-only querying, separate retention policy management) with no operational benefit over standard history.

**60-Field Ceiling vs. Unlimited External Archival:**
FAT caps at 60 fields per object. For orgs with requirements that exceed this ceiling, or where field change data must be stored outside Salesforce entirely (data residency, air-gap requirements), an external archival pattern using Platform Events and a trigger-based change capture to an external data store is an architectural alternative. This pattern is more complex but removes the Salesforce platform ceiling. Evaluate against the compliance requirement before choosing.

**SOQL-Only Querying vs. Reporting Needs:**
`FieldHistoryArchive` data is not surfaced in Salesforce Reports. If compliance stakeholders require self-service reporting, the architectural options are: (a) a custom Lightning component querying Apex, (b) ETL export to an external analytics platform, or (c) scheduled Apex Batch jobs that export to a Big Object or external storage. Plan the reporting delivery mechanism before committing to FAT as the sole audit store.

## Anti-Patterns

1. **FAT Without Field History Tracking Enabled** — Configuring FAT retention policies without verifying Field History Tracking is active on the same fields produces a configuration that passes a Setup review but captures no data. FAT is a retention extension, not a capture mechanism. This is the most common and highest-impact FAT misconfiguration in production.

2. **Relying on FAT Default Retention Policies** — Not setting an explicit retention policy and relying on Salesforce's platform defaults creates ambiguity for compliance evidence. Salesforce may change default policies, and the default may not match the governing regulation's requirement. Every regulated object must have an explicit, documented FAT retention policy set by the org's admin — not left to platform defaults.

3. **Using FAT as a Data Audit Replacement for All Compliance Needs** — FAT tracks field value changes, not record views, report exports, or API data access. Auditors requiring evidence of who viewed or exported data need Event Monitoring (the other Shield feature), not FAT. Combining both is the complete Shield audit posture, but they address different requirements. Positioning FAT as a universal compliance solution leads to audit gaps when access log evidence is required.

## Official Sources Used

- Field Audit Trail Help (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.field_audit_trail.htm
- FieldHistoryArchive Object (SOAP API Developer Reference) — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_objects_fieldhistoryarchive.htm
- Salesforce Shield Overview (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.shield.htm
- Shield Platform Encryption Implementation Guide — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm&type=5
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
