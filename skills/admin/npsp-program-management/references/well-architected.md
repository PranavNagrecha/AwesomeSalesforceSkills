# Well-Architected Notes — NPSP Program Management Module (PMM)

## Relevant Pillars

- **Reliability** — PMM's bulk service delivery path is the primary data entry mechanism for program staff. Rowlock errors under concurrent saves represent a reliability risk; orgs must have a recovery process (detect missing records, resubmit) or an architectural mitigation (staggered entry, async processing). Validation rules on ServiceDelivery__c reduce data-quality-driven reporting failures.
- **Operational Excellence** — PMM ships packaged reports and dashboards that are the intended operational view for program managers and grant reporters. Configuring these correctly (correct program/cohort assignments, field set order) determines whether staff can operate independently without admin intervention. Clear runbooks for bulk entry and attendance recording reduce operational burden.
- **Security** — PMM ships its own permission sets (PMM Admin, PMM Program Manager, PMM Staff). These should be used as the baseline and extended with permission set groups rather than modifying org-wide sharing or profiles. ServiceDelivery__c records may contain sensitive client information — ensure OWD defaults and sharing rules are reviewed before going live. Never grant broader access than the narrowest permission set that allows the required workflow.

## Architectural Tradeoffs

**Scheduled delivery (ServiceSchedule__c path) vs. ad hoc delivery (direct ServiceDelivery__c creation):**
The scheduled path provides richer reporting: attendance by session, participant roster by schedule, and no-show tracking. The ad hoc path is simpler for drop-in services with irregular timing. Choosing ad hoc for a program that actually has a schedule creates a reporting gap that is difficult to retrofit — session-level attendance data cannot be reconstructed from aggregate delivery records after the fact. Choose the scheduled path by default unless the service is genuinely unscheduled.

**Bulk Service Delivery quick action vs. custom Flow-based entry:**
The packaged quick action is lower maintenance and receives PMM upgrade improvements automatically. A custom Flow-based entry screen offers more validation control, async processing (reducing rowlock exposure), and custom UX. The tradeoff is upgrade risk — custom Flows may break when PMM updates the ServiceDelivery__c object schema. Use the packaged action unless the rowlock problem is severe enough to require async architecture.

**PMM permission sets vs. custom profiles:**
PMM permission sets are designed to be stacked with org-level profiles. Overriding them with custom profiles that replicate PMM object access creates an upgrade maintenance burden — every PMM package upgrade may add new objects or fields that the custom profile does not include. Use PMM permission sets as the canonical access layer and extend with additional permission sets for org-specific customizations.

## Anti-Patterns

1. **Cross-package rollup fields from ServiceDelivery__c to NPSP Opportunity** — Attempting to build formula fields, Process Builder rollups, or custom triggers that aggregate ServiceDelivery__c data into NPSP Opportunity fields creates unsupported cross-namespace dependencies. These break silently on package upgrades and produce incorrect data when either package changes its object schema. The correct architecture keeps PMM reporting in PMM and NPSP reporting in NPSP, with a dashboard presenting both views side-by-side.

2. **Using Service__c records without a parent Program__c** — Orphaned Service__c records (no Program__c lookup) cannot be selected in the Bulk Service Deliveries cascading filter and cannot be associated with a ProgramEngagement__c. The Salesforce data model does not enforce this parent relationship with a master-detail constraint, so orphaned services are created without error. Prevent this with a validation rule requiring Service__c.pmdm__Program__c to be non-blank on insert.

3. **Modifying PMM packaged fields or removing them from managed field sets** — PMM managed fields are locked for certain edits. Attempting to shorten field labels or change field types on managed fields results in errors. Removing fields from packaged layouts is allowed but removing them from the Bulk_Service_Deliveries_Fields field set breaks the quick action cascade. Treat the first three positions in that field set as read-only from an architectural governance perspective.

## Official Sources Used

- Program Management Module Managed Package (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sfdo.PMM_Manage_the_Package.htm
- Program Management Module Documentation (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sfdo.PMM.htm
- Service Delivery with Program Management Module (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/program-management-module
- Customize Bulk Service Deliveries (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sfdo.PMM_Customize_Bulk_Service_Deliveries.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
