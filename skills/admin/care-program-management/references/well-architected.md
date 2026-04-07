# Well-Architected Notes — Care Program Management

## Relevant Pillars

- **Security** — Care Program enrollment involves protected health information (PHI). Consent capture via `AuthorizationFormConsent` is a hard prerequisite and must not be bypassed. Access to `PatientProgramOutcome` objects is gated by a separately licensed permission set, which enforces need-to-know access by default. Object-level security on `CareProgramEnrollee` and related objects must be explicitly configured — Health Cloud does not automatically restrict these objects to appropriate profiles.
- **Reliability** — The strict parent-child hierarchy (CareProgram → CareProgramProduct/Provider → CareProgramEnrollee → CareProgramEnrolleeProduct) means that any gap in the hierarchy creation order or a deactivated root `CareProgram` will silently block enrollment. Reliable implementations validate the full hierarchy before enrollment begins and surface actionable errors to users when prerequisites are missing.
- **Operational Excellence** — The locale exact-match requirement on `AuthorizationFormText` is invisible in standard tooling. Operational excellence requires explicit test coverage for each deployed user locale: test enrollment flows by logging in as a user with each active locale, not only as an admin. Change management must include locale validation whenever new user populations or locales are added to the org.
- **Scalability** — Care Programs are designed for population-scale enrollment. A single `CareProgram` may support thousands of `CareProgramEnrollee` records. Bulk data operations (data migration, nightly feeds from EHR systems) must follow hierarchy order and batch appropriately. Triggers on `CareProgramEnrollee` that perform SOQL queries per record will hit governor limits at scale.
- **Performance** — `CareProgramEnrollee` and `CareProgramEnrolleeProduct` records are often queried in aggregate for reporting. Index `CareProgramEnrollee.Status` and `CareProgramEnrollee.CareProgramId` if enrollment reporting queries are slow. Avoid unindexed cross-object joins across the full hierarchy in a single SOQL query.

## Architectural Tradeoffs

**Consent via UI flow vs. programmatic consent record creation:** The standard Health Cloud enrollment UI captures consent interactively. Programmatic enrollment (API or Apex) requires creating `AuthorizationFormConsent` records directly. The programmatic path is faster for bulk operations but bypasses the UI validation that ensures the correct consent document was reviewed. For regulated Life Sciences orgs, the programmatic path requires additional audit logging to demonstrate informed consent.

**Base Health Cloud outcome tracking vs. Patient Program Outcome Management add-on:** Base Health Cloud allows custom fields on `CareProgramEnrollee` for basic outcome data. The licensed Patient Program Outcome Management feature provides a dedicated `PatientProgramOutcome` object with structured outcome tracking, API support, and reporting. Choosing custom fields on `CareProgramEnrollee` avoids the additional license cost but creates a non-standard data model that diverges from Salesforce's roadmap and breaks compatibility with future Health Cloud features.

**Single program per patient vs. multiple concurrent programs:** Salesforce supports multiple `CareProgramEnrollee` records for the same patient (one per program). If the business has patients enrolled in multiple overlapping programs, this is the correct model. Building a single-program constraint into automation or validation rules will block legitimate multi-program enrollments that arise later.

## Anti-Patterns

1. **Skipping consent setup to speed up enrollment** — Bypassing `AuthorizationFormConsent` to manually set `CareProgramEnrollee.Status` to Active creates compliance risk for HIPAA-regulated orgs and breaks the intended consent audit trail. Even in non-regulated environments, this approach makes it impossible to distinguish patients who have and have not provided consent.

2. **Using Care Plans as the enrollment container** — Building population-level enrollment workflows on `CarePlan` records instead of `CareProgram` records produces a non-standard data model with no support for program-level reporting, consent management, or product-level outcome tracking. Care Plans are per-patient task management frameworks — they are not enrollment containers.

3. **Assuming outcome tracking is included in the base Health Cloud license** — Implementing `PatientProgramOutcome` logic and deploying it to production before confirming the add-on license is in place will result in production errors. Always verify license availability in a sandbox that mirrors the production license profile before building outcome tracking functionality.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Health Cloud Object Reference — Care Program Management Data Model — https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/hco_care_prog_overview.htm
- Life Sciences Developer Guide — Patient Program Outcome Management API v61.0+ — https://developer.salesforce.com/docs/atlas.en-us.health_cloud_developer_guide.meta/health_cloud_developer_guide/hls_patient_program_outcome.htm
- Trailhead — Care Programs Setup and Management — https://trailhead.salesforce.com/content/learn/modules/health-cloud-care-programs
