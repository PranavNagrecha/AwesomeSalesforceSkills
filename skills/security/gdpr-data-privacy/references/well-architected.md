# Well-Architected Notes — GDPR Data Privacy

## Relevant Pillars

- **Security** — The primary pillar. Data privacy under GDPR is a security and compliance obligation. Consent records, Individual linkage, and erasure workflows are all security controls that protect the personal data of data subjects. Incomplete implementation (e.g., ShouldForget flag without erasure automation) creates legal and regulatory exposure.
- **Reliability** — Erasure batch jobs must reliably process all in-scope records. A batch that silently skips records due to null IndividualId, governor limit failures, or unhandled exceptions produces incomplete erasure — a compliance failure. Batch jobs must be monitored, retried on failure, and audited for completeness.
- **Scalability** — The consent data model must scale to the number of data subjects in the org. A ContactPointTypeConsent record per channel per person at millions of contacts creates significant query volume. Indexes on `PartyId` and `ContactPointType` are critical. Privacy Center policy engines are designed for high-volume erasure; custom Batch Apex must be size-tested.
- **Operational Excellence** — GDPR compliance is an ongoing operational process, not a one-time implementation. Data Subject Requests arrive continuously, consent records expire, and new objects storing PII are created by future development. Operational tooling (intake workflows, audit trails, consent expiry alerts) must be part of the design from the start.
- **Performance** — Large-scale anonymization batch jobs can consume significant CPU and DML limits. Batch size tuning (200 records/batch for complex DML operations), asynchronous execution, and off-peak scheduling are required for orgs with millions of Contact and Lead records.

---

## Architectural Tradeoffs

### Privacy Center vs. Custom Batch Apex

Privacy Center provides a no-code, auditable RTBF policy engine with built-in data portability export. It is the recommended approach for orgs with significant DSR volume, complex data models, or strict audit requirements. The tradeoff is cost: Privacy Center is a separately purchased add-on, and the licensing decision must account for DSR volume and the org's risk tolerance.

Custom Batch Apex gives full control and has no additional licensing cost, but creates ongoing maintenance burden. Every new object or field storing PII must be added to the batch logic manually. There is no built-in data portability, and the audit trail must be custom-built. For orgs with very low DSR volume (<5/month) and simple data models, this is proportionate. For complex orgs, the maintenance risk outweighs the cost savings.

### Anonymization vs. Hard Delete

Hard delete is the most complete form of erasure but breaks referential integrity in almost every production Salesforce org. The Salesforce Well-Architected Framework's Reliability pillar requires that data operations not corrupt related records or produce orphaned data. Anonymization satisfies the GDPR erasure obligation for personal data fields while preserving the record shell for relational integrity. The tradeoff is that anonymized records still occupy storage and appear in reports; post-anonymization record suppression (via record type or a custom filter field) is needed to prevent anonymized shells from polluting operational reports.

### Native Consent Model vs. Custom Fields

The native `ContactPointTypeConsent` and `ContactPointConsent` objects are designed for GDPR-style consent tracking and integrate with Marketing Cloud's consent synchronization. The tradeoff is complexity: the object model is more sophisticated than simple checkboxes on Contact, requiring additional triggers or flows to maintain. Custom checkbox fields are simpler to build but cannot represent consent history, per-purpose consent, or time-bounded consent windows — all of which are necessary for GDPR Article 7 compliance.

---

## Anti-Patterns

1. **Setting ShouldForget Without Erasure Automation** — Treating `Individual.ShouldForget = true` as a complete RTBF response without building the responding automation. This creates the appearance of compliance while personal data remains untouched. The Individual flag is a signal; the automation is the erasure. Both must exist.

2. **Scoping Erasure Only to Contact** — Building an erasure batch that only anonymizes Contact records, ignoring Leads, PersonAccounts, and custom objects that store PII. GDPR erasure applies to all personal data regardless of which object holds it. An incomplete scope is still a compliance failure, even if the Contact is anonymized.

3. **Using HasOptedOutOfEmail as the GDPR Consent System of Record** — The standard Contact opt-out field has no timestamps, no capture source, and no history. It cannot demonstrate that consent was freely given and specific. Regulators requesting proof of consent cannot be satisfied with a boolean field that may have been set by a data import rather than a genuine consent event.

---

## Official Sources Used

- Salesforce Privacy Overview — https://help.salesforce.com/s/articleView?id=sf.privacy_overview.htm
- Individual Object and Privacy Data Model — https://help.salesforce.com/s/articleView?id=sf.data_model_individual.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Privacy Center Implementation Guide — https://help.salesforce.com/s/articleView?id=sf.privacy_center_setup.htm
- ContactPointTypeConsent Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contactpointtypeconsent.htm
- ContactPointConsent Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contactpointconsent.htm
- Salesforce Well-Architected Guide Overview — https://architect.salesforce.com/well-architected/overview
