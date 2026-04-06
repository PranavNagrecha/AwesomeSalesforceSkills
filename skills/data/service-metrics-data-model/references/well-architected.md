# Well-Architected Notes — Service Metrics Data Model

## Relevant Pillars

- **Reliability** — SLA compliance depends on CaseMilestone records being created reliably. Any gap in Entitlement assignment, expired Entitlement records, or misconfigured Business Hours silently breaks milestone creation. Reliable service metric reporting requires data quality checks that catch these gaps before they distort KPIs.
- **Performance** — `CaseMilestone` and `Case` tables grow with case volume. SOQL queries for compliance reports that lack selective filters on `IsCompleted`, `IsViolated`, or date ranges can trigger full-table scans. Custom indexes on `CaseMilestone.CaseId` and `Case.EntitlementId` are platform-provided, but reporting queries must still use date-range filters to stay within governor limits.
- **Scalability** — Orgs with high case volume accumulate `CaseMilestone` records at a rate of (cases per day) × (milestones per entitlement process). A 1,000-case/day org with 2 milestones per process generates ~730,000 CaseMilestone records per year. SOQL and report queries must be designed with this scale in mind. Aggregate reporting via Summary reports is preferable over row-level exports for large datasets.
- **Operational Excellence** — Service metric reports are consumed by support leadership for SLA governance. The `IsViolated = true AND IsCompleted = true` late-completion state must be explicitly documented for report consumers. Undocumented semantics cause misinterpretation and erode trust in the data. Operational runbooks for SLA metric definitions (which milestone types, which Business Hours, which entitlement tiers) must be kept current.

## Architectural Tradeoffs

**Calendar MTTR vs. Business-Hours MTTR:**
Calendar MTTR (formula field) is zero-maintenance and fully declarative. Business-hours MTTR (Apex trigger) requires ongoing maintenance when Business Hours records change, adds Apex trigger complexity, and can fall out of sync if cases are mass-imported via API without triggering the after-update logic. Choose BH-MTTR only when the SLA contract explicitly requires business-hours measurement.

**Native Salesforce Reports vs. External BI for SLA Metrics:**
Native reports are easier to deploy and require no ETL, but they hit the 2,000-row report-run limit for detail exports and cannot perform cross-object aggregations beyond what the report builder supports. External BI tools (Tableau, Power BI) need a reliable data export of `CaseMilestone` with the correct field set — including pre-computed `MTTR_BH_Mins__c` — to avoid re-implementing business-hours logic outside Salesforce.

**Single MTTR Field vs. Per-Milestone Elapsed Time:**
Storing a single MTTR field on Case loses the per-milestone breakdown. Reporting on `CaseMilestone.ElapsedTimeInMins` per milestone type preserves granularity. For most orgs, both are useful: MTTR on Case for executive-level KPIs, per-milestone elapsed time for operational drill-down.

## Anti-Patterns

1. **Using IsViolated as the sole SLA compliance flag** — Treating `IsViolated = false` as "compliant" includes open in-progress milestones in the compliance rate, overstating performance. And treating `IsViolated = true` as "still unresolved" misclassifies late completions. Both errors can be corrected only by using the full four-quadrant state model (IsCompleted × IsViolated).

2. **Hardcoding the default Business Hours ID in MTTR triggers** — Orgs with multiple entitlement tiers using different Business Hours records will compute incorrect MTTR for non-default-hours cases. The Entitlement's `BusinessHoursId` must be used, not the org's default. This becomes a silent data quality issue — MTTR values look plausible but are wrong for premium-tier accounts.

3. **Deriving MTTR entirely in an external BI tool using raw timestamps** — External tools that compute `ClosedDate - CreatedDate` without Business Hours awareness produce calendar-time MTTR, not contract-time MTTR. For SLA reporting in regulated industries, this can misrepresent contract compliance. Pre-compute `MTTR_BH_Mins__c` in Salesforce and export that field.

## Official Sources Used

- Track Service Metrics — https://help.salesforce.com/s/articleView?id=sf.entitlements_manage_milestones.htm&type=5
- CaseMilestone Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_casemilestone.htm
- Entitlement Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_entitlement.htm
- BusinessHours.diff() Apex Reference — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_businesshours.htm
- Set Up Entitlements and Milestones — https://help.salesforce.com/s/articleView?id=sf.entitlements_setting_up.htm&type=5
