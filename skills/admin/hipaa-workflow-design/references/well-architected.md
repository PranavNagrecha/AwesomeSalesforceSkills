# Well-Architected Notes — HIPAA Workflow Design

## Relevant Pillars

- **Security** — All HIPAA workflow design is security-driven. Access control (minimum necessary), encryption (PHI at rest and in transit), and audit controls are non-negotiable HIPAA technical safeguards, not optional enhancements.
- **Operational Excellence** — HIPAA compliance is not a one-time implementation task. Event Monitoring streaming to SIEM is an ongoing operational requirement. Shield Field Audit Trail requires ongoing field coverage maintenance as new PHI fields are added. Compliance posture must be monitored continuously.
- **Reliability** — The Event Log File export pipeline is a reliability concern: Event Log File storage is 1 year by default for Shield and Event Monitoring customers, Event Log Objects keep 30 days, and real-time streams keep 3 days, so a failed export loses evidence once the relevant window passes. Pipeline health monitoring is part of the compliance control.

## Architectural Tradeoffs

**Shield Field Audit Trail vs. Standard Field History Tracking:** Field Audit Trail is a paid Shield feature and needs a retention policy and a deletion procedure, but it keeps archived history until you delete it and tracks up to 200 fields per object. Standard field history keeps 18 months (24 via API) on up to 20 fields. For any agreed retention period longer than 18 months, Field Audit Trail is the platform option (UNVERIFIED (2026-10-03): whether HIPAA itself requires 6 years for field history is a legal interpretation).

**In-Platform Audit vs. External SIEM:** Event Monitoring covers in-platform access evidence for a limited window (1 year of Event Log File storage by default for Shield and Event Monitoring customers; shorter for Event Log Objects and streams). An external store is required for anything longer. The architectural question is which store and how the export pipeline is monitored.

## Anti-Patterns

1. **Using standard Field History Tracking for HIPAA audit compliance**: 18-month retention fails any longer agreed period. Use Field Audit Trail for PHI fields that need longer history, and alternative evidence for untrackable fields such as long text.
2. **Treating BAA as org-wide coverage** — The BAA covers specific products, not all services in the org. PHI in uncovered products creates compliance gaps.
3. **Configuring Event Monitoring without an export pipeline**: Event Log Files leave platform storage after the default one-year window (Event Log Objects after 30 days). Export them and monitor the export.

## Official Sources Used

Read for the 2026-10-03 pass (fetched with plain `curl`; line numbers cite the `pdftotext -layout` extraction):

- Salesforce Security Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf (field history retention 18 and 24 months L4628-4645; Field Audit Trail, 200-field limit, policy objects, default archiving, untrackable fields, record deletion and archive, encryption of archived data L4823-4906; Real-Time Event Monitoring three-day retention L5440-5455; LoginEvent comparison table L6320-6360; Event Log Objects 30-day retention L9830-9840)
- Object Reference for the Salesforce Platform, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (EventLogFile one year of storage for Shield and Event Monitoring customers L112511-112552; FieldSecurityClassification L137834-137840)
- Metadata API Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (CustomObject `enableHistory` and `historyRetentionPolicy` L42040, L42164; CustomField `complianceGroup`, `encryptionScheme`, `securityClassification`, `trackHistory` L43334-43682; HistoryRetentionPolicy L44074-44125; PermissionSet L94772-94840)

Listed by the original author and not re-read in this pass (help.salesforce.com and architect.salesforce.com do not serve article content to plain HTTP clients; hhs.gov returned 403 and the eCFR and govinfo pages for 45 CFR Part 164 did not return regulation text on 2026-10-03):

- Health Cloud Admin Guide, Protect Your Health Data with Salesforce Shield: https://help.salesforce.com/s/articleView?id=ind.hc_protect_health_data.htm
- Salesforce HIPAA BAA Help Article: https://help.salesforce.com/s/articleView?id=000394847
- Salesforce Shield Security Guide (atlas HTML): https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/security_overview.htm
- HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/index.html
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
