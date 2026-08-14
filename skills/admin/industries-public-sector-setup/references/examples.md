# Examples — Industries Public Sector Setup

## Example 1: Choosing the Right Intake Object for a Permit Programme

**Scenario:** A municipal food-service permit. Applicants are a mix of sole traders and incorporated restaurant groups. The permit is granted for two years and is inspectable.

**Problem:** The obvious model is one application object with an "applicant type" picklist. PSS does not work that way, and there is no `LicenseApplication` object to hold the shared case.

**Solution:** Route by applicant type at intake, into two different shipped objects, converging on a single granted artefact:

```
Sole trader path
  IndividualApplication          "an application form submitted by an individual or
                                  organization" (API 50.0+)

Incorporated path
  BusinessProfile                the applying entity
    └── BusinessLicenseApplication

Both converge on
  BusinessLicense                the granted permit
    ├── RegulatoryAuthorizationType   what kind of authorisation this is
    ├── RegulatoryAuthority           who issues it
    └── BusinessLicenseCodeSet        which regulatory codes it is subject to
```

Reference data has to exist before either path can run:

```
1. RegulatoryAuthority          the issuing body
2. RegulatoryAuthorizationType  permit / licence / registration types
3. RegulatoryCode               "the regulation code enforced by the regulatory
                                 body" (API 49.0+)
4. BusinessType                 classification of the applying entity
5. InspectionType               how this permit gets inspected
6. ViolationType                what findings are possible
```

**Why it works:** Splitting intake and converging on `BusinessLicense` means the approval, renewal, and inspection processes are written once against the granted artefact, while the two intake experiences can differ as much as the statute requires. Confirm the exact field API names and the lookup relationships against the PSS object reference before building — the structure above is the part that is easy to get wrong.

---

## Example 2: An Inspection That Produces Structured, Reportable Findings

**Scenario:** A routine food-safety inspection against the permit above. Twelve criteria. The agency needs a compliance rate by regulatory code, by inspector, and by ward.

**Problem:** Built as a `Case` with an "Inspection" record type and a long-text findings field, none of those three reports is possible without re-reading free text. The shipped model structures every one of them.

**Solution:** Use the visit-and-assessment family, the same objects Consumer Goods Cloud uses for retail execution:

```
InspectionType                     classifies this kind of inspection
  └── Visit                        the site call
        ├── Visitor                the inspector
        ├── VisitedParty           who was present at the premises
        └── AssessmentTask         the checklist instance
              ├── AssessmentTaskDefinition      reusable checklist template
              ├── AssessmentTaskIndDefinition   template -> criterion
              ├── AssessmentIndicatorDefinition each criterion
              ├── AssessmentIndDefinedValue     its permitted answers
              └── AssessmentIndValue            what the inspector recorded

Findings
  RegulatoryCodeViolation          a failed criterion, tied to its RegulatoryCode
    ├── ViolationType              classification
    ├── RegCodeAssessmentInd       criterion <-> regulatory code
    └── ViolationEnforcementAction the follow-up (notice, fine, closure)
```

The compliance report the agency asked for then exists as an ordinary rollup:

```sql
SELECT RegulatoryCodeId, COUNT(Id) violations
FROM RegulatoryCodeViolation
WHERE CreatedDate = LAST_N_MONTHS:12
GROUP BY RegulatoryCodeId
```

**Why it works:** Each criterion is a record, so failure rates aggregate without parsing anything. `RegCodeAssessmentInd` is what ties a checklist item to the statute it enforces — that link is what makes a finding defensible on appeal. Note that `Visit`, `Visitor`, `VisitedParty`, and the `AssessmentTask` family are shared with Consumer Goods Cloud; in an org running both, changes to their layouts, record types, or validation rules affect both programmes.

---

## Anti-Pattern: Inferring PSS Object Names from Their Labels

**What practitioners do:** Write the data model from the capability names used in the requirements workshop:

```apex
// WRONG. None of these compile -- every one is a plausible name that
// does not exist in the shipped model.
LicenseApplication  app       = new LicenseApplication();
Authorization       auth      = new Authorization();
Party               applicant = new Party();
PartyRelationship   rel       = new PartyRelationship();
```

**What goes wrong:** The real names are `BusinessLicenseApplication` or `IndividualApplication`, `RegulatoryAuthorizationType` or `BusRegAuthorizationType`, and `BusinessProfile`. Several are truncated to fit the API-name ceiling — `BusRegAuthTypeDependency`, `BenefitDisbursementAdj`, `BnftAsgntBnftItemCode`, `ViolationTypeAssessmentInd`, `FundingAwardRqmtSection` — so the readable spelling a model or a person would "correct" to resolves to nothing.

**Correct approach:** Copy names from the object reference and let the compiler enforce them:

```apex
// Compile-time tokens. A wrong name fails the deploy rather than the
// integration test three weeks later.
Schema.SObjectType bizApp    = BusinessLicenseApplication.SObjectType;
Schema.SObjectType indApp    = IndividualApplication.SObjectType;
Schema.SObjectType violation = RegulatoryCodeViolation.SObjectType;

System.debug(bizApp.getDescribe().getName());
```

The PSS data models "provide objects and fields to support licensing and permitting, inspections and assessments, case and program management, benefit management, grantmaking, and other features" — all standard, all provisioned with the licence. Nothing in this model should be rebuilt as a custom object, and any design that proposes to is a signal the shipped model was never read.
