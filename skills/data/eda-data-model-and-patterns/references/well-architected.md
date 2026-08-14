# Well-Architected Notes — EDA Data Model and Patterns

## Relevant Pillars

- **Scalability** — EDA is contact-centric on purpose: one Contact per person,
  with role expressed through `hed__Affiliation__c` rows rather than
  role-specific objects. That keeps the schema flat as the institution adds
  roles (applicant, student, alum, guardian, adjunct, donor) but pushes the cost
  onto row volume: a 40,000-student university with a decade of history carries
  millions of Affiliation and Course Connection rows. Design for that shape —
  selective filters on `hed__Status__c` and date fields, skinny/custom indexes
  on the SIS external ID, and archival of terminated terms — rather than for the
  10-student demo dataset.

- **Reliability** — EDA's automation is table-driven (`hed__Trigger_Handler__c`)
  and its behaviour is configured through List custom settings whose *rows* are
  data, not metadata. Reliability here is mostly about the configuration
  surviving environment moves: an Affiliation Mapping table that is empty after
  a deploy produces no exception at load time, just quietly null Primary
  Affiliation fields. Post-deployment verification of configuration rows belongs
  in the release checklist, not in someone's memory.

## Architectural Tradeoffs

**Contact-centric vs role objects.** Making every person a Contact means every
person inherits Contact's sharing, its field limit, and its page-layout
politics. The alternative — `Student__c`, `Faculty__c`, `Alum__c` — gives each
role a clean schema and immediately breaks the thing EDA exists to provide: one
record for a person who is simultaneously an alum, a parent, and an adjunct.
Take the contact-centric cost. It is real, and it is smaller.

**`Attribute__c` key-value vs fields on Contact.** Key-value survives schema
churn (each new survey, each new test type is a row, not a deployment) and costs
you reportability, validation, and required-field enforcement. Fields on Contact
give you all three and accumulate: a Contact with 200 sparsely populated custom
fields slows every query that touches it and is unusable in Object Manager.
Split on volatility, not on convenience — stable, universally-populated
attributes are fields; institution-specific, versioned, or optional attributes
are rows.

**Primary Affiliation lookups as denormalisation.** EDA maintains up to six
Account lookups on Contact so reports and Flows can filter without a join. They
are a cache. Writing to them directly, or treating them as the system of record,
produces exactly the drift the Affiliation object was meant to prevent.

**Extending EDA vs shadowing it.** Adding a field to `hed__Affiliation__c` keeps
EDA's handlers, rollups, and packaged reports working. Building a parallel
`Enrollment__c` alongside `hed__Course_Enrollment__c` breaks all three, and the
duplication is permanent because nothing reconciles the two.

## Anti-Patterns

1. **A `Student__c` object alongside Contact.** It duplicates identity, splits
   sharing, and orphans every EDA rollup and packaged report. Model role as an
   Affiliation.
2. **Treating custom-setting rows as deployable metadata.** Affiliation Mappings
   and Reciprocal Relationships are configuration *data*. A release plan that
   omits them ships a silently degraded org.
3. **Disabling all TDTM handlers for a load and reactivating "later".** The
   failure is invisible: no error, just Households and Primary Affiliations that
   stop being maintained. Scope the bypass to the load user and assert the
   restore.
4. **Hard-coding `hed__Term__c` Ids in Apex or Flow.** Terms roll over every
   academic period; query by date range or a maintained current-term flag.

## Official Sources Used

- Education Data Architecture (Managed Package) — Data Model Gallery — https://developer.salesforce.com/docs/platform/data-models/guide/education-data-architecture-managed-package.html — confirms the object roster of the EDA managed package (Affiliation, Affiliation Mappings, Attribute, Course, Course Connection, Course Offering, Term, Relationship, Trigger Handler and the rest) and that the package spans the K-20 journey (verified 2026-08-14)
- EDA package source, `SalesforceFoundation/EDA` (BSD-3-Clause), `sfdx-project.json` and `cumulusci.yml` — confirms the package namespace is `hed` (verified 2026-08-14)
- EDA package source, `force-app/main/default/objects/Course_Enrollment__c/Course_Enrollment__c.object-meta.xml` — confirms the object with label "Course Connection" has API name `Course_Enrollment__c` (verified 2026-08-14)
- EDA package source, `force-app/main/default/objects/Affl_Mappings__c/` — confirms `Affl_Mappings__c` is `<customSettingsType>List</customSettingsType>` with fields `Account_Record_Type__c` and `Primary_Affl_Field__c` (verified 2026-08-14)
- EDA package source, `force-app/main/tdtm/objects/Trigger_Handler__c/` — confirms the TDTM object and its `Active__c`, `Class__c`, `Object__c`, `Trigger_Action__c`, `Load_Order__c`, `Asynchronous__c` and `Usernames_to_Exclude__c` fields (verified 2026-08-14)
- EDA package source, `force-app/main/default/classes/STG_InstallScript.cls` (`insertMappings`) — confirms the six default Affiliation Mappings, their record type developer names (`Academic_Program`, `Business_Organization`, `HH_Account`, `Educational_Institution`, `University_Department`, `Sports_Organization`) and that only `Primary_Organization__c` and `Primary_Household__c` are namespace-prefixed (verified 2026-08-14)
- EDA package source, `force-app/main/default/labels/CustomLabels.labels-meta.xml` — source of every verbatim error string quoted in `gotchas.md` (`afflAccountNoRecordType`, `afflAccoutMappingError`, `invalidRecordTypeInAffiliationMapping`, `affiliationWithSameAccExists`, `stgAfflNotInserted`, `defaultAccountRecordTypeMissingError`, `stgCourseConnBackFillSuccess`, `afflTypeEnforcedDescription`, `stgHelpCourseConnectionBackfill`) (verified 2026-08-14)
- Salesforce Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm — standard-object semantics underlying Contact and Account in the EDA model (verified 2026-08-14)
