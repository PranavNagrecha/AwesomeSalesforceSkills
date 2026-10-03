# Well-Architected Notes — Care Coordination Requirements

## Relevant Pillars

- **Operational Excellence** — Care coordination workflows must be designed with measurable handoff points. Using standard ICM objects (ClinicalServiceRequest, CareEpisode, CareGap) enables platform-native reporting on care coordination KPIs. Custom objects require custom reporting infrastructure.
- **Security** — Care coordination objects contain PHI. CareBarrier records include SDOH data that can be sensitive. ICM and social determinants objects require the Health Cloud permission set licenses and permission sets named in `gotchas.md` gotcha 3, plus appropriate OWD and sharing rules (UNVERIFIED (2026-10-03): a `HealthCloudICM` permission set is not named in the guide). HIPAA minimum-necessary access applies — care coordinators should only see care barriers and episodes relevant to their patients.
- **Reliability** — Care gap detection depends on external system integration reliability. If the clinical rules engine or import pipeline is down, calculated and imported CareGap records go stale; record `LastEvaluatedDate` and the source system so coordinators can see staleness. Design the care coordinator workflow to handle stale or absent care gap data gracefully.

## Architectural Tradeoffs

**Native ICM objects vs. Custom Objects:** ICM standard objects (CareBarrier, CareGap, CareEpisode) provide native integration with Health Cloud's care coordinator console, patient timeline, and reporting. Custom objects require custom UI, custom reporting, and manual FHIR mapping if interoperability is needed. The tradeoff: ICM objects have fixed schemas that may not match all organizational nuances; custom objects can be shaped exactly to requirements but lose all native platform integration.

**Manual Care Gap Entry vs. Integration-Driven:** Manual entry is supported (`RecordOriginType` = `ManuallyCreated`) and is useful for gaps an engine missed, but it is only as accurate as the coordinator's chart review. CareGap records represent quality measure calculations from clinical rules engines — accuracy requires that these come from authoritative clinical systems. The integration-driven approach is architecturally correct but requires an integration layer that must be scoped and resourced.

## Anti-Patterns

1. **Conflating CareBarrier (SDOH) with care plan problems (clinical)**: CareBarrier is for social determinants resolved through community resources. Care plan problems are `HealthCondition` records instantiated from `ProblemDefinition`. There is no standard `CarePlanProblem` object. Mixing them pollutes both the care plan and the SDOH tracking workflows.
2. **Writing CareGap.Status directly**: Status has no Create or Update property. Closure and exclusion run through `MeasureEvaluationStatus` with a `StatusReason`.
3. **Assuming Care Coordination for Slack is on**: the app is controlled by `IndustriesSettings.enableCareMgmtSlackAccess`. Designing Slack-dependent care team workflows without confirming the setting and licensing creates scope risk (UNVERIFIED (2026-10-03): the separate-add-on licensing claim is not in the guides read).

## Official Sources Used

Read for the 2026-10-03 pass (fetched with plain `curl`; line numbers cite the `pdftotext -layout` extraction):

- Agentforce Health Developer Guide (Health Cloud developer guide), Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/health_cloud_dev_guide.pdf (ICM settings and object list L36184-36300; CareGap fields, calls, origin and status L36860-37150; social determinants prerequisites and CareBarrier L66010-66260; clinical data model org pref table L8345-8368; legacy `HC24__` object names L24860-24895)
- Metadata API Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (IndustriesSettings Health Cloud fields L119538-119645 including `enableCareMgmtSlackAccess` L119550 and `enableClinicalDataModel` L119553; ActionPlanTemplate L15080-15365)
- Object Reference for the Salesforce Platform, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (ActionPlan and ActionPlanTemplateItem, including `ItemEntityType` values L21594-22300)

Listed by the original author and not re-read in this pass (help.salesforce.com and architect.salesforce.com do not serve article content to plain HTTP clients; the atlas object reference pages below were superseded by the PDFs above):

- Health Cloud Admin Guide, Protect Health Data with Salesforce Shield: https://help.salesforce.com/s/articleView?id=ind.hc_protect_health_data.htm
- Integrated Care Management Data Model: https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/hco_intro.htm
- CareGap Object Reference (API v59.0+): https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_caregap.htm
- CareBarrier Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_carebarrier.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
