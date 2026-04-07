# Well-Architected Notes — Care Plan Configuration

## Relevant Pillars

- **Security** — Care plan records contain clinical and sensitive health information governed by HIPAA and regional data privacy regulations. The ICM model uses standard Salesforce object permissions, sharing rules, and field-level security — giving architects full control over which users can read, create, or edit care plan records, problems, goals, and activities. The legacy model's reliance on Case records and managed-package objects makes fine-grained security configuration less flexible. Principle of least privilege must be applied to both models: care coordinators should not have access to care plans for patients outside their assigned population.

- **Performance** — Care plan template instantiation in the ICM model creates multiple related records (`CarePlan`, `CarePlanProblem`, `CarePlanGoal`, `CarePlanActivity`) in a single operation. For high-volume scenarios — bulk enrollment, population health programs with thousands of simultaneous instantiations — this multi-object write must be handled asynchronously (via Apex batch or Flow with asynchronous path) to avoid governor limit breaches. The PGI library is read frequently during template picker rendering; ensure ProblemDefinition and GoalDefinition records are indexed on the fields used in list views and searches.

- **Scalability** — The ICM model scales significantly better than the legacy model. ActionPlanTemplate is a standard object with full Metadata API support, enabling DevOps pipelines, change sets, and version-controlled template deployment. The legacy CarePlanTemplate__c object is a managed-package custom object that requires manual recreation or package-level deployment, limiting scalable template management. For organizations managing hundreds of distinct care plan types across specialties, ICM is the only viable architecture.

- **Reliability** — Care plans are clinical-workflow-critical records. Template misconfiguration — particularly missing PGI library links — can result in care coordinators creating clinically incomplete care plans without errors or alerts. Reliability requires validation at template activation time (confirm PGI links exist), testing of instantiation in sandbox before go-live, and monitoring of care plan completion rates post-launch to detect missing task structures.

- **Operational Excellence** — The ICM model supports Metadata API deployment for ActionPlanTemplate records, enabling CI/CD pipelines for care plan template lifecycle management. Teams can version-control templates, peer-review changes, and deploy through change management processes. The legacy model requires manual UI-based configuration that cannot be easily scripted or audited. Operational excellence in care plan management strongly favors ICM.

## Architectural Tradeoffs

**ICM vs. Legacy investment horizon:** The primary tradeoff is between immediate implementation simplicity (legacy, already familiar to teams with older Health Cloud experience) and long-term architectural health (ICM, future investment target, FHIR aligned). New implementations should always choose ICM. Existing legacy implementations face a migration cost that must be weighed against the ongoing cost of maintaining an architecture with no new feature development — for most orgs, migration is the right long-term choice.

**PGI library standardization vs. flexibility:** Standardizing problems and goals through the PGI library improves data quality, reporting consistency, and interoperability. However, it requires upfront curation work and governance to maintain the library over time. Organizations that skip library governance find the PGI library becomes polluted with duplicate or inconsistent records, degrading care coordinator experience. The tradeoff is upfront library design effort in exchange for sustained data quality.

**Template versioning and in-flight care plans:** ICM's point-in-time instantiation model provides auditability (the care plan reflects what was active when it was created) at the cost of requiring manual processes to update live care plans when clinical guidelines change. Organizations with frequent guideline updates must define explicit processes for care plan refresh — there is no automatic cascade.

## Anti-Patterns

1. **Mixed architecture without migration plan** — Configuring both `CarePlanTemplate__c` records (legacy) and `ActionPlanTemplate` records (ICM) in the same org without a clear migration timeline creates two parallel care plan workflows that the standard Health Cloud UI does not reconcile. Care coordinators see different experiences depending on which path they follow, reporting is split across two data models, and permission management becomes inconsistent. Choose one model as the target and execute a complete migration rather than tolerating coexistence indefinitely.

2. **Bypassing PGI library with free-text problems and goals** — Configuring ICM care plans without PGI library records forces care coordinators to type problems and goals as free text on individual care plan records. This defeats the clinical standardization purpose of the ICM model: downstream reporting, population health analytics, and interoperability all require standardized coded entries. The effort saved by skipping PGI setup is vastly outweighed by the data quality debt it creates.

3. **Deploying CarePlanTemplate__c via manual UI in a DevOps pipeline** — Legacy care plan templates cannot be deployed through the Metadata API in the same way as standard objects. Teams that attempt to include legacy managed-package care plan configuration in CI/CD pipelines find that template records must be recreated manually in each environment. This forces a manual-only deployment model for care plan changes, creating change management risk and environment drift. ICM ActionPlanTemplate records support Metadata API deployment and should be used for any org with a DevOps maturity requirement.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Health Cloud Administration Guide — https://help.salesforce.com/s/articleView?id=sf.health_cloud_admin_guide.htm
- Integrated Care Management Data Model — https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/hco_icm_data_model.htm
- Health Cloud Administration: Create a Care Plan Template — https://help.salesforce.com/s/articleView?id=sf.admin_create_care_plan_template.htm
- Explore Integrated Care Management (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/integrated-care-management
