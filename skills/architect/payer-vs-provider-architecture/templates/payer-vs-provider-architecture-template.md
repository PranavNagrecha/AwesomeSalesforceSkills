# Payer vs Provider Architecture Decision Template

Use this template to document the deployment type classification and architecture decisions for a Health Cloud implementation. Complete all sections before beginning object model design or PSL assignment.

---

## 1. Implementation Context

**Organization name:** ______________________

**Salesforce org type:** Production / Developer / Sandbox (circle one)

**Project date:** ______________________

**Architect:** ______________________

---

## 2. Deployment Type Classification

Select one. This is the single most important decision in a Health Cloud architecture.

- [ ] **Payer-only** — The organization is a health plan, insurer, or managed care organization. Primary business functions: member enrollment, benefit coverage administration, claims processing, utilization management, provider network management.
- [ ] **Provider-only** — The organization is a hospital, clinic, physician practice, or other care delivery organization. Primary business functions: patient management, clinical documentation, care coordination, care management.
- [ ] **Dual-sector** — A single org must serve both payer users (insurance administration) and provider users (clinical care delivery). Document the business justification for dual-sector below.

**Business justification (required for dual-sector):**

______________________

**Classification confirmed by:** ______________________ (name and role)

---

## 3. Provider Terminology Disambiguation

If the word "provider" appears in any requirements document, user story, or this template — classify each occurrence here. Do not leave this section blank if "provider" is used.

| Requirement or context | Meaning: network provider (payer-side) or clinical provider (care delivery) | Evidence |
|---|---|---|
| ______________________ | Network provider / Clinical provider | ______________________ |
| ______________________ | Network provider / Clinical provider | ______________________ |
| ______________________ | Network provider / Clinical provider | ______________________ |

> Network provider (payer): a practitioner or facility in the health plan's insurance network — managed by Provider Relationship Management (credentialing, contracting).
>
> Clinical provider (care delivery): the hospital, clinic, or clinician who delivers care to the patient — modeled through Account/Contact and clinical data model objects.

---

## 4. Canonical Object Model

Based on the deployment type above, list the Health Cloud objects in scope. Cross out objects that are explicitly out of scope.

### Payer Objects (use for payer-only or dual-sector payer side)

| Object | In Scope | Notes |
|---|---|---|
| MemberPlan | Yes / No | Links member identity to insurance plan |
| PurchaserPlan | Yes / No | The insurance plan product |
| CoverageBenefit | Yes / No | Benefit structure |
| CoverageBenefitItem | Yes / No | Benefit line-item coverage |
| ClaimHeader | Yes / No | Adjudicated claim |
| ClaimLine | Yes / No | Claim line item |
| AuthorizationForm | Yes / No | Prior authorization (requires Utilization Management PSL) |
| AuthorizationFormConsent | Yes / No | Prior auth consent record (requires Utilization Management PSL) |

### Provider Objects (use for provider-only or dual-sector provider side)

| Object | In Scope | Notes |
|---|---|---|
| ClinicalEncounter | Yes / No | Patient visit or care event |
| HealthCondition | Yes / No | Documented diagnosis |
| Medication | Yes / No | Prescribed medication |
| CareObservation | Yes / No | Clinical measurement or observation |

### Shared Objects (applicable to both sectors — configure per sector)

| Object | Payer Use | Provider Use | Notes |
|---|---|---|---|
| Account | Member account | Patient account | Record type strategy required for dual-sector |
| Contact | Member/subscriber | Patient | Same — record type strategy required |
| Case | Member services case | Care coordination case | Record type and permission boundary required |

---

## 5. PSL Matrix

Complete for every user persona in the implementation.

| Persona | Base PSL | Sector PSL | Feature PSL(s) | Notes |
|---|---|---|---|---|
| ______________________ | Health Cloud | Health Cloud for Payers | — | |
| ______________________ | Health Cloud | Health Cloud for Payers | Utilization Management | For prior auth workflows |
| ______________________ | Health Cloud | Health Cloud for Payers | Provider Network Management | For credentialing/contracting |
| ______________________ | Health Cloud | — (clinical activation) | — | For clinical care users |
| ______________________ | Health Cloud | — | — | Add rows as needed |

> Reminder: Missing payer-specific PSLs cause silent feature gaps — member management, claims, and prior auth UI do not appear without Health Cloud for Payers PSL assigned. Validate PSL assignment with a test user before UAT.

---

## 6. Feature Activation Checklist

Complete the relevant section for your deployment type.

### Payer Deployment

- [ ] Health Cloud for Payers PSL assigned to all payer users
- [ ] Utilization Management PSL assigned to clinical review / UM nurses (if prior auth in scope)
- [ ] Provider Network Management PSL assigned to provider relations staff (if credentialing in scope)
- [ ] PSL assignment validated end-to-end with a test user (member management tabs visible)
- [ ] Clinical objects (ClinicalEncounter, HealthCondition) excluded from payer user permission sets

### Provider Deployment

- [ ] Base Health Cloud PSL assigned to all provider users
- [ ] FHIR R4 Support Settings enabled in Setup > Health > Health Cloud Settings (if FHIR in scope)
- [ ] FHIR API endpoint validated: `GET /services/data/vXX.0/health/fhir/r4/metadata` returns CapabilityStatement
- [ ] Payer objects (MemberPlan, ClaimHeader) excluded from provider user permission sets

### Dual-Sector Deployment (complete both sections above, plus:)

- [ ] Separate profiles or permission set groups for payer users and provider users
- [ ] Object-level permissions verified: payer users cannot access clinical objects; provider users cannot access payer objects
- [ ] Sharing rules reviewed for cross-sector exposure risk
- [ ] Field-level security on sensitive clinical fields (diagnosis, medication) restricted to clinical permission set holders
- [ ] Data separation architecture documented and reviewed for HIPAA minimum necessary compliance

---

## 7. Known Risks and Mitigations

Document any risks identified during the architecture decision process.

| Risk | Likelihood (H/M/L) | Impact (H/M/L) | Mitigation |
|---|---|---|---|
| PSL gaps discovered post go-live | M | H | PSL validation checklist in go-live runbook |
| Provider term ambiguity in future requirements | H | M | Disambiguation glossary in project documentation |
| ______________________ | | | |
| ______________________ | | | |

---

## 8. Decision Record

**Decision:** ______________________

**Rationale:** ______________________

**Alternatives considered:** ______________________

**Review date (for dual-sector — annual HIPAA data separation review):** ______________________

**Sign-off:** ______________________ (architect) / ______________________ (client lead)
