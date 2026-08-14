# Well-Architected Notes — Industries Public Sector Setup

## Relevant Pillars

### Security

Public-sector data is protected by statute rather than by policy, and the org's most exposed surface is the one the programme exists to provide: a citizen-facing portal whose guest user sits in front of `IndividualApplication`, `BusinessLicenseApplication`, and the benefit model. Guest access has to be scoped to what intake needs to create and nothing it needs to read back, and the sharing model for guest-created records designed separately from the intake flow. Field history on the application, disbursement, and violation objects has to be enabled before go-live — history is not retroactive, so a disclosure question about month one cannot be answered by a setting turned on in month three.

### Reliability

Jurisdiction is the load-bearing structure. Role hierarchy and agency account hierarchy determine who may see which record, and they are statutory rather than negotiable. Getting them right before the first transactional record lands is the whole of reliability here: reparenting afterwards triggers a sharing recalculation that runs for hours on government-scale volumes and leaves the org in a partially-recalculated state while it does. Reference data has the same property — `RegulatoryAuthority`, `RegulatoryAuthorizationType`, `RegulatoryCode`, `BusinessType`, `InspectionType`, `ViolationType`, `BenefitType` all have to exist before anything points at them.

### Operational Excellence

The shipped model already expresses what most agencies are about to rebuild: licensing and permitting, inspections and assessments, case and programme management, benefit management, and grantmaking. Operational excellence starts with reading it, because every custom object built alongside it is a permanent divergence from what upgrades and shipped OmniScripts assume. It continues with structure over free text — a finding recorded as a `RegulatoryCodeViolation` tied to its `RegulatoryCode` is reportable and defensible on appeal; the same finding in a notes field is neither.

## Architectural Tradeoffs

**Two intake objects vs. one with a type field.** PSS splits business and individual intake into `BusinessLicenseApplication` and `IndividualApplication`. That is more objects to maintain and lets the two experiences diverge exactly as far as the statute requires, converging on a single `BusinessLicense` so approval, renewal, and inspection are written once. Forcing them into one custom object collapses the divergence and loses the shipped intake components.

**Shipped OmniScripts vs. Flow.** PSS intake and decisioning ship as OmniScripts, Integration Procedures, and DataRaptors. Rebuilding an intake journey in Flow is more familiar to most admins and inherits none of the shipped upgrades. Clone and version rather than customise in place, and where Flow genuinely is the better fit, record why — it is a divergence with a maintenance cost, not a preference.

**Eligibility in BRE vs. in code.** A Business Rules Engine expression set is auditable, versioned, and what the shipped OmniScripts expect. Apex or Flow eligibility is faster to write for a developer already fluent in it, and cannot be shown to an auditor as a rule. For statutory eligibility the auditability is the requirement, not a nice-to-have — confirm the org's BRE entitlement before designing around it.

## Anti-Patterns

1. **Inventing `LicenseApplication`, `Party`, or `Authorization`.** All three are plausible names that do not exist. The real ones are `BusinessLicenseApplication` / `IndividualApplication`, `BusinessProfile`, and `RegulatoryAuthorizationType`. Several PSS names are truncated to fit the API-name ceiling, so the spelling a person or a model would "correct" to resolves to nothing.

2. **Modelling inspections as `Case` record types with free-text findings.** The shipped `Visit` / `AssessmentTask` / `AssessmentIndValue` family structures every criterion as a record, and `RegulatoryCodeViolation` ties a failure to the statute it breaches. Free text cannot produce a compliance rate by code and cannot be defended on appeal.

3. **Collapsing `BenefitAssignment` into `BenefitDisbursement`.** Entitlement and payment are different facts. Inferring entitlement from payment history breaks the first time a payment is adjusted or missed, which is precisely the case an audit or an appeal will ask about.

## Official Sources Used

- Public Sector Solutions Developer Guide — Public Sector Solutions Standard Objects — the data-model scope statement and the full object list by capability: licensing and permitting (`BusinessLicense`, `BusinessLicenseApplication`, `BusinessLicenseCodeSet`, `BusinessProfile`, `BusinessType`, `BusRegAuthorizationType`, `BusRegAuthTypeDependency`, `RegulatoryAuthority`, `RegulatoryAuthorizationType`, `RegulatoryCode`, `RegAuthorizationTypeProduct`, `Examination`, `TrnCourse`, `InspectionType`), inspections (`Visit`, `Visitor`, `VisitedParty`, `AssessmentTask`, `AssessmentTaskDefinition`, `AssessmentTaskIndDefinition`, `AssessmentIndicatorDefinition`, `AssessmentIndDefinedValue`, `AssessmentIndValue`, `RegulatoryCodeViolation`, `ViolationType`, `ViolationEnforcementAction`, `RegCodeAssessmentInd`, `ViolationTypeAssessmentInd`), benefits (`Benefit`, `BenefitType`, `BenefitAssignment`, `BenefitAssignmentAdjustment`, `BenefitDisbursement`, `BenefitDisbursementAdj`, `BenefitSchedule`, `BenefitScheduleAssignment`), grantmaking (`FundingOpportunity`, `FundingAward`, `FundingAwardRequirement`, `FundingAwardRqmtSection`, `FundingDisbursement`), and case/programme management (`Program`, `ProgramEnrollment`, `CarePlan`, `CaseParticipant`, `CaseProceeding`) (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.psc_api.meta/psc_api/api_psc_overview.htm
- Public Sector Solutions Developer Guide — `IndividualApplication` — "an application form submitted by an individual or organization", API 50.0 and later (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.psc_api.meta/psc_api/sforce_api_objects_individualapplication.htm
- Public Sector Solutions Developer Guide — `RegulatoryCode` — "the regulation code enforced by the regulatory body", API 49.0 and later (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.psc_api.meta/psc_api/sforce_api_objects_regulatorycode.htm
- Public Sector Solutions Developer Guide — `BusinessLicenseApplication` (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.psc_api.meta/psc_api/sforce_api_objects_businesslicenseapplication.htm
- Object Reference for the Salesforce Platform — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
