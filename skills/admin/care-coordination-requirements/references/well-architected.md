# Well-Architected Notes — Care Coordination Requirements

## Relevant Pillars

- **Operational Excellence** — Care coordination workflows must be designed with measurable handoff points. Using standard ICM objects (ClinicalServiceRequest, CareEpisode, CareGap) enables platform-native reporting on care coordination KPIs. Custom objects require custom reporting infrastructure.
- **Security** — Care coordination objects contain PHI. CareBarrier records include SDOH data that can be sensitive. All ICM objects require the HealthCloudICM permission set and appropriate OWD/sharing rules. HIPAA minimum-necessary access applies — care coordinators should only see care barriers and episodes relevant to their patients.
- **Reliability** — Care gap detection depends on external system integration reliability. If the clinical rules engine or FHIR ingestion pipeline is down, CareGap records will not be updated. Design the care coordinator workflow to handle stale or absent care gap data gracefully.

## Architectural Tradeoffs

**Native ICM objects vs. Custom Objects:** ICM standard objects (CareBarrier, CareGap, CareEpisode) provide native integration with Health Cloud's care coordinator console, patient timeline, and reporting. Custom objects require custom UI, custom reporting, and manual FHIR mapping if interoperability is needed. The tradeoff: ICM objects have fixed schemas that may not match all organizational nuances; custom objects can be shaped exactly to requirements but lose all native platform integration.

**Manual Care Gap Entry vs. Integration-Driven:** Manual care gap entry (if it were possible) would be simpler to implement but clinically inaccurate. CareGap records represent quality measure calculations from clinical rules engines — accuracy requires that these come from authoritative clinical systems. The integration-driven approach is architecturally correct but requires an integration layer that must be scoped and resourced.

## Anti-Patterns

1. **Conflating CareBarrier (SDOH) with CarePlanProblem (clinical)** — These objects serve different workflow stages. CareBarrier is for social determinants resolved via community resources. CarePlanProblem is for clinical diagnoses within a care plan. Mixing them pollutes both the care plan and the SDOH tracking workflows.
2. **Designing manual CareGap creation workflows** — CareGap records must be system-generated. Designing workflows that require manual entry by care coordinators ignores this constraint and will fail at implementation.
3. **Assuming Care Coordination for Slack is included in Health Cloud licensing** — This is a separately purchased add-on. Designing Slack-dependent care team workflows without confirming the license creates scope risk.

## Official Sources Used

- Health Cloud Admin Guide — Protect Health Data with Salesforce Shield: https://help.salesforce.com/s/articleView?id=ind.hc_protect_health_data.htm
- Integrated Care Management Data Model: https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/hco_intro.htm
- CareGap Object Reference (API v59.0+): https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_caregap.htm
- CareBarrier Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_carebarrier.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
