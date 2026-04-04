# Well-Architected Notes — Field History Tracking

## Relevant Pillars

- **Security** — Field History Tracking is a primary mechanism for meeting audit and data governance requirements. Tracking who changed sensitive fields (e.g., financial values, PII, status fields), when, and from what value to what value provides an immutable platform-generated audit log. This directly supports access accountability and principle of least privilege verification — if a user changed a field they should not have, the history record surfaces it. Well-Architected guidance emphasizes implementing audit controls proportionate to data sensitivity.

- **Reliability** — The 18-month rolling retention window and automatic deletion of history for hard-deleted records are reliability risks for audit-dependent processes. A reliable configuration documents these limits explicitly, communicates them to stakeholders, and establishes an escalation path (Shield Field Audit Trail or custom logging) before data loss occurs. Treating retention as an assumed-infinite behavior is a known failure mode.

## Architectural Tradeoffs

**Standard Field History Tracking vs. Custom Logging:**
Standard FHT is zero-maintenance, platform-generated, and queryable via standard SOQL and Report Builder. Custom logging via Apex triggers or Flow is more flexible (no field-type restrictions, configurable retention, initial values at creation) but requires ongoing maintenance and does not benefit from platform optimization. For most audit requirements within the 18-month window, standard FHT is the correct choice. Custom logging should be additive, not a replacement.

**Field Selection Tradeoffs:**
The 20-field-per-object limit forces deliberate triage. Tracking more fields than necessary adds storage overhead and makes history queries noisier. Tracking too few fields creates compliance gaps. The correct approach is to align tracked fields directly to documented compliance requirements and remove fields from tracking when the requirement lapses.

**Reporting vs. SOQL:**
History sObjects are available in Salesforce Report Builder, making them accessible to non-technical stakeholders. For large-scale extractions or cross-object joins, SOQL via Data Loader or Workbench is more appropriate. Design the audit workflow to match the consumer — reports for operational users, SOQL exports for compliance teams delivering to external auditors.

## Anti-Patterns

1. **Enabling history on all available fields "just in case"** — Selecting the maximum 20 fields indiscriminately without tying each to a documented compliance or operational need wastes the field limit, complicates the audit record with irrelevant changes, and makes it harder to identify genuinely important change events. Instead, map each tracked field to a specific requirement and review selections annually.

2. **Treating the 18-month retention as permanent storage** — Organizations that design multi-year compliance programs on top of standard Field History Tracking will discover the data no longer exists when auditors request historical records. This anti-pattern typically surfaces during external audits. The correct architectural decision is to assess retention requirements at design time and select Shield Field Audit Trail proactively if the window exceeds 18 months.

3. **Building audit trails on formula fields** — Attempting to audit formula-field values via FHT silently fails because formula fields are ineligible. Practitioners who don't realize this build a false sense of coverage. The architecture must distinguish between stored field values (trackable) and computed values (not trackable), and substitute a stored field pattern when audit coverage of a derived value is genuinely required.

## Official Sources Used

- Salesforce Help — Track Field History: https://help.salesforce.com/s/articleView?id=sf.tracking_field_history.htm
- Salesforce Object Reference — AccountHistory Object: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_accounthistory.htm
- Salesforce Object Reference — OpportunityHistory Object: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunityhistory.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/well-architected/overview
