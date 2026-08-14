# Gotchas — Industries Public Sector Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: There Is No `LicenseApplication` — Business and Individual Intake Are Different Objects

**What happens:** A design document, a data-load spec, or generated Apex references `LicenseApplication`. It does not exist. PSS splits intake by applicant type: `BusinessLicenseApplication` on the business side and `IndividualApplication` — "an application form submitted by an individual or organization," available in API version 50.0 and later — on the individual side. Anything written against the imagined single object has to be rebuilt against whichever of the two the process actually uses, or both.

**When it occurs:** In design, before provisioning makes the model visible. The name is plausible enough that it survives review, and generative tooling reproduces it reliably.

**How to avoid:** Establish applicant type as a first-order design question, not a field on a shared record. A permit programme that serves both sole traders and companies genuinely touches both objects, and the OmniScripts, approval routing, and reporting differ accordingly. Copy every API name from the Public Sector Solutions standard-object list — several are truncated (`BusRegAuthorizationType`, `BusRegAuthTypeDependency`, `BenefitDisbursementAdj`, `BnftAsgntBnftItemCode`, `ViolationTypeAssessmentInd`) and the readable spelling resolves to nothing.

---

## Gotcha 2: Inspections Reuse the Retail Execution Visit Model, Not `Case` Record Types

**What happens:** Inspections are built as `Case` records with an "Inspection" record type, and the shipped inspection features — checklist definitions, captured indicator values, violation classification, enforcement follow-up — have nothing to attach to. The shipped model is the visit-and-assessment family: `InspectionType` classifies, `Visit` records the site call, `AssessmentTask` and `AssessmentTaskDefinition` carry the checklist, `AssessmentIndicatorDefinition` and `AssessmentIndValue` hold the criteria and captured values.

**When it occurs:** Early, because Case is the object every Salesforce practitioner reaches for and "inspection case" is how agencies talk about the work. It surfaces when someone asks for a compliance rate by regulatory code and discovers the findings were never structured.

**How to avoid:** Model findings on the objects built for them. A failed criterion becomes a `RegulatoryCodeViolation`, classified by `ViolationType`, linked to criteria through `RegCodeAssessmentInd` and `ViolationTypeAssessmentInd`, with follow-up as a `ViolationEnforcementAction`. Note that `Visit`, `Visitor`, `VisitedParty`, and the `AssessmentTask` family are shared with Consumer Goods Cloud — an org running both industries shares these objects, so page layouts, record types, and validation rules on them are a cross-programme concern.

---

## Gotcha 3: Benefits Are a Four-Layer Model, and Teams Collapse Assignment into Disbursement

**What happens:** A benefits programme is built with an applicant, a benefit, and a payment, and then cannot answer "what is this person entitled to, and how much of it have they received". The layer that holds entitlement is `BenefitAssignment`; `BenefitDisbursement` holds only the payments made against it. Collapsing them means entitlement is inferred from payment history, which breaks the moment a payment is adjusted or missed.

**When it occurs:** In the first programme, and it does not surface until an audit or an appeal asks for the entitlement as of a past date.

**How to avoid:** Keep all four layers. `Benefit` and `BenefitType` are the catalogue, `BenefitAssignment` is the entitlement, `BenefitSchedule` and `BenefitScheduleAssignment` set the cadence, and `BenefitDisbursement` records what was actually paid. Corrections belong in `BenefitAssignmentAdjustment` and `BenefitDisbursementAdj` rather than as edits to the original records — statutory programmes are audited on who changed what and when, and an edited amount answers neither question.

---

## Gotcha 4: Jurisdictional Ownership Has to Be Right Before the First Record Lands

**What happens:** Cases, licences, and benefit records are loaded, and only afterwards is the role hierarchy or the agency account hierarchy adjusted to match the statutory structure. Reparenting records at that point triggers a sharing recalculation across the whole object, which on a government-scale data volume runs for hours and cannot be paused.

**When it occurs:** When the jurisdiction model is treated as a Setup task that can follow the data load, which is the normal order in a Sales Cloud project. Public-sector deployments invert it, because ownership is statutory rather than commercial and cannot be renegotiated later.

**How to avoid:** Settle role hierarchy and agency account hierarchy before any transactional load, and load reference data first in dependency order — `RegulatoryAuthority`, `RegulatoryAuthorizationType`, `RegulatoryCode`, `BusinessType`, `InspectionType`, `ViolationType`, `BenefitType` — so every transactional record has a valid parent at insert. Where a recalculation is unavoidable, schedule it in a maintenance window and tell the agency it is happening; a half-recalculated org shows officers records they should not see.

---

## Gotcha 5: A Citizen Portal Puts a Guest User in Front of Statutorily Protected Data

**What happens:** An applicant-facing Experience Cloud site is stood up so citizens can submit applications. The guest user profile ends up with more object access than intended, and the objects it reaches — `IndividualApplication`, `BusinessLicenseApplication`, `Benefit` — carry exactly the personal and eligibility data the agency is legally obliged to protect.

**When it occurs:** During portal build, when OmniScripts need object access to create records and the fastest way to make the script work is to widen the guest profile until it does.

**How to avoid:** Grant guest access through a dedicated permission set scoped to the minimum the intake script needs to create, never to read back. Treat the sharing model for guest-created records as a separate design step from the intake flow itself. Enable field history on `BusinessLicenseApplication`, `IndividualApplication`, `BenefitDisbursement`, and `RegulatoryCodeViolation` before go-live rather than after the first disclosure question — history is not retroactive, so a field turned on in month three has nothing to say about month one. And follow the Experience Cloud guest-user hardening guidance as a gate on go-live, not as a post-launch improvement.
