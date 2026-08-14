# Well-Architected Notes — Education Cloud EDA Setup

## Relevant Pillars

### Security

Student records are regulated data, and the model puts the boundary in an unusual place: EDA is Contact-centric, so students, parents, advisors, faculty, and staff are all Contacts differentiated only by their Affiliations. Sharing therefore has to be derived from affiliation and household structure rather than from record type or object. Affiliation status is also the audit trail for enrolment, and field history is not retroactive — enabling it at go-live rather than after the first records request is the difference between answering an audit and reconstructing one. On the standard model, `AcademicTermEnrollment` gives the same timeline as reportable records rather than history entries.

### Reliability

Academic data cannot be reconstructed. The two failure modes that destroy it are both quiet: writing grades onto the offering instead of the enrolment record, which collapses every student in a section to one result, and bulk-loading Contacts through EDA's trigger layer, which completes reporting success while leaving a fraction of records correctly affiliated. EDA logs its own failures to an **Error** object that no standard load tool reads, so reliability here means verifying against that object rather than against the loader's result file.

### Operational Excellence

EDA holds its behaviour in records — **Hierarchy Settings**, **Affiliation Mappings**, **Relationship Auto-Create**, **Relationship Lookup**, **Trigger Handler** — not in Setup screens. Configuration held as data does not travel with a metadata deploy, so a refreshed sandbox can behave differently from production with no metadata difference to point at. Operational excellence means treating these objects as owned, versioned, diffable configuration, and knowing that the Trigger Handler is the switch a bulk load depends on in both directions.

## Architectural Tradeoffs

**EDA vs. the standard Education Cloud model.** EDA is a community-driven managed package with deep K-20 coverage and a large installed base; the standard model ships with the platform, needs no package upgrade cycle, and carries the newer capability areas — admissions (`ApplicationStageDefinition`, `ApplicationReview`, `ApplicationDecision`), learner pathways (`LearnerPathway`, `LearningPathwayTemplate`), and student wellbeing (`PulseCheck`, `WatchlistedLearner`). The choice is made once per org and is not a migration path. Establish which one is installed before any design work.

**Auto-created Households vs. explicit affiliation loads.** Letting EDA create Household accounts and affiliations on Contact insert is less work and behaves unpredictably at load volume. Loading affiliations explicitly is more work and deterministic. For anything past a pilot-sized dataset, explicit wins — an affiliation that silently failed to create is invisible until an advisor cannot see a student.

**Extending the shipped model vs. adding custom objects.** Adding an `Applicant__c` object because applicants "aren't students yet" breaks the Contact-centric assumptions Advisor Link and the shipped reporting rely on. Modelling the same distinction as an affiliation status keeps one person as one Contact through their whole lifecycle, which is what makes prospect-to-alumni reporting possible at all.

## Anti-Patterns

1. **Designing before establishing which model is installed.** EDA and standard Education Cloud share concepts and almost no API names. A design written against the wrong one is discovered at build, after sign-off, and none of it is salvageable by renaming.

2. **Reconstructing EDA API names from labels.** EDA objects are managed-package custom objects carrying the package namespace. `Affiliation__c` and `Course_Connection__c` are plausible reconstructions of the display names and do not resolve. Read the exact API name from the org.

3. **Bulk-loading Contacts without controlling the trigger layer.** EDA automation runs on Contact insert and logs its failures to its own Error object. A load that reports success can still leave orphan affiliations, and nothing in the loader's output says so.

## Official Sources Used

- Education Cloud Developer Guide — Education Cloud Standard Objects — verbatim descriptions for `AcademicTerm`, `AcademicSession`, `AcademicTermEnrollment`, `AcademicYear`, `CourseOfferingParticipant`, `CourseOfferingPtcpResult`, `CourseOfrPtcpActvtyGrd`, `CourseOfferingSchedule`, `CourseOfferingScheduleTmpl`, `Learning`, `LearningCourse`, `LearningProgram`, `LearningProgramPlan`, `LearningProgramPlanRqmt`, `LearnerProgram`, `LearnerPathway`, `LearningPathwayTemplate`, `ApplicationDecision`, `ApplicationReview`, `ApplicationStageDefinition`, `ApplicationSectionDefinition`, `ApplicationTimeline`, `PulseCheck`, `WatchlistedLearner`, `SuccessTeam` (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.edu_cloud_dev_guide.meta/edu_cloud_dev_guide/edu_cloud_standard_objects.htm
- Data Model Gallery — Education Data Architecture (Managed Package) — "a community-driven data architecture that supports the entire K-20 student journey for educational institutions" and the entity list including Affiliation, Affiliation Mappings, Course, Course Connection, Course Offering, Course Offering Schedule, Hierarchy Settings, Plan Requirement, Program Enrollment, Program Plan, Relationship, Relationship Auto-Create, Relationship Lookup, Term, Trigger Handler, Error (verified 2026-08-14) — https://developer.salesforce.com/docs/platform/data-models/guide/education-data-architecture-managed-package.html
- Data Model Gallery — Education — the model list distinguishing Academic Operations, Recruitment and Admissions, Student Success, Appointment Scheduling, Student Financials from the EDA managed-package models (verified 2026-08-14) — https://developer.salesforce.com/docs/platform/data-models/guide/education-cloud-category.html
- Education Cloud Developer Guide — Data Model Overview (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.edu_cloud_dev_guide.meta/edu_cloud_dev_guide/edu_cloud_data_model_overview.htm
- Apex Developer Guide — Namespace Prefix — why managed-package object API names carry a prefix — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_namespace_prefix.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
