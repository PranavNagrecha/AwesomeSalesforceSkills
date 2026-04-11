---
name: payer-vs-provider-architecture
description: "Use this skill when designing or evaluating a Health Cloud implementation to determine whether the org serves a payer (health insurer), a provider (care delivery organization), or both — and to derive the correct object model, PSL matrix, and feature activation accordingly. Triggers: 'should we use MemberPlan or ClinicalEncounter', 'payer vs provider Health Cloud', 'which Health Cloud objects does an insurer use', 'setting up a Health Cloud org for a hospital vs a health plan', 'Provider Relationship Management vs clinical provider'. NOT for individual feature implementation within an already-classified payer or provider org, and NOT for Salesforce Health Cloud implementations that are clearly a single deployment type with no cross-sector ambiguity."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Scalability
  - Reliability
triggers:
  - "We are building Health Cloud for a health insurance company — which objects and licenses do we need?"
  - "Our org serves both payers and providers and we need to understand how to separate their data models"
  - "The team is confusing Provider Relationship Management with the clinical provider data model"
tags:
  - health-cloud
  - payer
  - provider
  - data-model
  - architecture
inputs:
  - "Organization type: payer (health insurer/managed care), provider (hospital/clinic/care delivery), or dual"
  - "Use case description: member enrollment, claims, utilization management, clinical care, care management, or a mix"
  - "Existing Health Cloud PSL assignments and any payer-specific or provider-specific add-on PSLs"
outputs:
  - "Architecture decision document: recommended deployment type (payer-only, provider-only, or dual with data separation strategy)"
  - "Object model recommendation: canonical object set for the identified deployment type"
  - "PSL matrix: required base and add-on PSLs for each user persona"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Payer vs Provider Architecture

This skill activates when a Health Cloud implementation must be classified as a payer deployment, a provider deployment, or a dual-sector deployment — and when the distinction determines which Salesforce objects, features, and Permission Set Licenses (PSLs) to use. It provides the decision framework to avoid silent feature gaps, data model mismatches, and the most common LLM mistake in Health Cloud: conflating "provider" in the insurance sense with "provider" in the clinical sense.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org owner is a health plan/insurer (payer) or a hospital/clinic/care delivery organization (provider). A single Salesforce org can serve both, but the object models and PSLs do not overlap — this must be established first.
- Identify which Health Cloud PSLs are currently assigned: base Health Cloud PSL, Health Cloud for Payers PSL, Utilization Management PSL, and/or clinical data model activations. Feature gaps caused by missing PSLs are silent — the objects are present in the schema but the permission sets that expose them to users are absent.
- Clarify what "provider" means in the client's vocabulary before any solution discussion. In payer orgs, "provider" means a practitioner or facility billed on a claim — managed through Provider Relationship Management (a payer-facing credentialing and contracting feature). In provider orgs, "provider" means the care-delivering organization itself. The term is overloaded and causes persistent misalignment between architects and clients.

---

## Core Concepts

### The Payer vs Provider Distinction

A payer is a health insurance company or managed care organization that administers member enrollment, collects premiums, processes claims, and manages benefit coverage. A provider is a hospital, clinic, physician practice, or other care-delivery organization that treats patients and records clinical events.

These two sectors interact in real-world healthcare (a provider submits claims to a payer), but in Salesforce Health Cloud they use architecturally separate object models, separate PSLs, and separate feature sets. Treating them as equivalent or interchangeable causes fundamental design errors.

### The "Provider" Terminology Ambiguity

The word "provider" has two unrelated meanings in Health Cloud:

1. **Clinical provider** (provider-org context): the care-delivering organization or practitioner. Modeled in Health Cloud's clinical data layer using objects like `ClinicalEncounter`, `HealthCondition`, `Medication`, and `CareObservation`.
2. **Network provider** (payer-org context): a practitioner or facility that is credentialed in a payer's network and billed on claims. Managed through **Provider Relationship Management**, which is a payer-facing feature covering credentialing, contracting, and network participation — it is not a clinical data model.

Provider Relationship Management is frequently misidentified as a clinical provider capability. It is exclusively a payer-side feature.

### Object Model Split

The two sectors use non-overlapping canonical object sets:

**Payer objects** (insurance enrollment and claims administration):
- `MemberPlan` — links a member (Account or Contact) to a `PurchaserPlan`
- `PurchaserPlan` — the insurance plan product offered by the payer
- `CoverageBenefit` / `CoverageBenefitItem` — benefit structure and line-item coverage details
- `ClaimHeader` / `ClaimLine` — adjudicated claim records
- `AuthorizationForm` / `AuthorizationFormConsent` — prior authorization workflow objects (Utilization Management)

**Provider objects** (clinical care delivery):
- `ClinicalEncounter` — a documented patient visit or care event
- `HealthCondition` — a diagnosed condition associated with a patient
- `Medication` — a prescribed medication record
- `CareObservation` — a clinical measurement or observation (vitals, lab results)
- FHIR R4-aligned objects activated via FHIR R4 Support Settings

**Shared objects** (used in both, with different functional context):
- `Account` — member account (payer) or patient account (provider)
- `Contact` — member contact or patient contact
- `Case` — member services case (payer) or care coordination case (provider)

### PSL Requirements

Base Health Cloud PSL is required in both sectors. Additional PSLs are required for sector-specific capabilities:

- **Payer**: Health Cloud for Payers PSL unlocks member management, benefits, and claims features. Utilization Management PSL is additionally required for `AuthorizationForm` and prior authorization workflows. Provider Network Management PSL is required for Provider Relationship Management (credentialing and contracting).
- **Provider**: Health Cloud PSL plus clinical data model activation via Setup and FHIR R4 Support Settings enabled in Health > Health Cloud Settings. No separate clinical PSL is required beyond base Health Cloud, but FHIR activation is a prerequisite for FHIR-aligned clinical objects.

Missing payer-specific PSLs cause silent feature gaps: users see the org but the member management tabs, claims views, and prior auth workflows are absent without any error message.

---

## Common Patterns

### Payer-Only Deployment

**When to use:** The org exclusively serves a health plan, managed care organization, or other insurance entity. All users are payer-side: member services representatives, claims processors, utilization management nurses, and provider relations staff.

**How it works:** Activate Health Cloud for Payers PSL for all Health Cloud users. Enable Utilization Management if prior auth workflows are in scope. Enable Provider Network Management if credentialing and contracting are in scope. Build the data model around `MemberPlan`, `PurchaserPlan`, `CoverageBenefit`, `ClaimHeader`, and `ClaimLine`. Clinical objects (`ClinicalEncounter`, `HealthCondition`) should not be surfaced to payer users — they are out of scope for insurance administration and their presence creates HIPAA data minimization concerns.

**Why not a generic Health Cloud setup:** Generic Health Cloud guidance frequently recommends activating clinical data model features by default. In a payer org, this adds unnecessary schema complexity, creates data governance risk (clinical data in an insurance org has different HIPAA handling requirements), and misleads implementation teams about what data the org should store.

### Provider-Only Deployment

**When to use:** The org exclusively serves a hospital system, physician practice, or other care delivery organization. Users are clinicians, care coordinators, care managers, and administrative staff focused on patient care.

**How it works:** Activate base Health Cloud PSL. Enable FHIR R4 Support Settings in Health Cloud Setup. Build the data model around `ClinicalEncounter`, `HealthCondition`, `Medication`, and `CareObservation`. Member enrollment and claims objects (`MemberPlan`, `ClaimHeader`) should not be used — they represent insurance administration concepts foreign to a care delivery data model.

**Why not reuse payer objects for care delivery:** Some teams attempt to use `MemberPlan` to represent a patient's care plan or `ClaimLine` to track clinical services. These objects carry insurance-specific semantics (adjudication status, plan coverage logic) that conflict with clinical use cases and break downstream reporting.

### Dual-Sector Deployment

**When to use:** A single Salesforce org must serve both payer users (insurance administration) and provider users (clinical care) — for example, an integrated delivery network that operates both a health plan and hospital system.

**How it works:** Both PSL tracks must be active. Object-level data separation is enforced through record ownership, sharing rules, and profile/permission set boundaries. Payer users receive Health Cloud for Payers PSL and access only payer objects. Provider users receive base Health Cloud PSL with clinical data model activation and access only clinical objects. Shared objects (`Account`, `Case`) require field-level security and record type strategies to prevent cross-sector data exposure. This pattern is architecturally viable but operationally complex — it is not the default recommendation unless business requirements explicitly demand it.

**Why not two separate orgs by default:** Two-org approaches eliminate cross-sector data isolation risk but introduce integration overhead for shared member/patient identity resolution. The dual-deployment pattern is appropriate when a single source of truth for member/patient identity across the two sectors is a hard requirement.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org serves a health plan or managed care org only | Payer-only deployment with Health Cloud for Payers PSL | Insurance administration objects and workflows require payer PSLs; clinical objects add governance risk |
| Org serves a hospital, clinic, or physician practice only | Provider-only deployment with base Health Cloud + FHIR activation | Clinical data model and FHIR-aligned objects are correct for care delivery; payer objects carry insurance semantics that conflict |
| Client uses "Provider Relationship Management" in requirements | Confirm this is payer-side credentialing/contracting, not clinical provider data | Provider Relationship Management is a payer feature; if the requirement is clinical provider data, use the clinical object model instead |
| Org serves both a health plan and a hospital system | Dual-sector deployment with strict PSL and data separation | Single identity source is valuable but requires deliberate object-level and permission-level separation |
| Member services case management is in scope | Payer deployment with `MemberPlan` and `Case` | Member services is a payer function; use `MemberPlan` to link cases to coverage |
| Clinical care coordination is in scope | Provider deployment with `ClinicalEncounter` and `Case` | Care coordination is a provider function; link cases to encounters, not plan records |
| Utilization Management (prior auth) is in scope | Payer deployment with Utilization Management PSL | `AuthorizationForm` and `AuthorizationFormConsent` require Utilization Management PSL; this is exclusively a payer workflow |
| FHIR R4 interoperability is required | Provider deployment with FHIR R4 Support Settings enabled | FHIR R4 object alignment is a provider-side clinical interoperability feature |

---

## Recommended Workflow

Step-by-step instructions for an architect or AI agent working on this task:

1. **Classify the deployment type.** Ask: does the organization administer insurance coverage (payer), deliver clinical care (provider), or both? Document the answer explicitly. Every subsequent decision depends on this classification. Do not proceed until this is unambiguous.

2. **Audit existing PSL assignments.** Export the current Permission Set License assignments from Setup > Company Information > Permission Set Licenses. Map each PSL to the deployment type it supports. Identify gaps between the deployment type determined in step 1 and the PSLs currently assigned.

3. **Identify the correct canonical object set.** Using the Decision Guidance table above, list the specific Health Cloud objects required for the use case. For payer: `MemberPlan`, `PurchaserPlan`, `CoverageBenefit`, `ClaimHeader`, `ClaimLine`. For provider: `ClinicalEncounter`, `HealthCondition`, `Medication`, `CareObservation`. Flag any objects from the wrong sector's model that appear in existing requirements or designs.

4. **Resolve the "provider" terminology ambiguity in all requirement documents.** Audit project documents, user stories, and Jira tickets for the term "provider." For each occurrence, determine whether it means a network provider in the insurance sense (payer-side, handled by Provider Relationship Management) or a clinical care delivery organization (provider-side, handled by the clinical data model). Document the resolution explicitly.

5. **Design the PSL matrix.** For each user persona, specify: base PSL required, sector-specific PSL required, and any feature-specific PSL (Utilization Management, Provider Network Management). For dual-sector orgs, map payer users and provider users to separate PSL tracks and document the permission set boundary.

6. **Validate data separation for dual-sector orgs.** If the deployment is dual-sector, define the record ownership model, sharing rule strategy, and profile/permission set boundaries that prevent payer users from accessing clinical records and provider users from accessing insurance records. Document this as a data separation architecture decision.

7. **Verify FHIR activation for provider deployments.** For provider orgs requiring FHIR R4 interoperability, confirm that FHIR R4 Support Settings are enabled in Health Cloud Setup and that the correct API version is targeted. This is a prerequisite for FHIR-aligned clinical objects and is not activated by default.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Deployment type (payer, provider, or dual) is documented explicitly and agreed by the client
- [ ] PSL matrix is defined for every user persona, including sector-specific and feature-specific PSLs
- [ ] The "provider" term has been disambiguated in all requirement documents — network provider (payer-side) vs clinical provider (provider-side) are clearly differentiated
- [ ] Canonical object set for the deployment type is listed; no objects from the wrong sector's model appear in the design
- [ ] For dual-sector orgs: data separation architecture (record ownership, sharing rules, permission boundaries) is documented
- [ ] For provider orgs: FHIR R4 Support Settings activation is confirmed if FHIR interoperability is in scope
- [ ] For payer orgs: Utilization Management PSL is assigned if prior authorization workflows are in scope

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Missing payer PSLs cause silent feature gaps, not errors** — If Health Cloud for Payers PSL or Utilization Management PSL is not assigned to a user, the member management tabs, claims views, and authorization workflows simply do not appear. There is no error. Users and testers assume the feature is not configured rather than that the license is missing. This can remain undetected through UAT if test users are assigned the wrong PSL.

2. **Provider Relationship Management is a payer feature, not a clinical provider feature** — The name "Provider Relationship Management" sounds like it belongs to a provider (clinical) deployment. It is a payer-facing feature for credentialing and contracting with network practitioners and facilities. Activating it in a clinical provider org adds payer-side schema noise and misleads the data model. Attempting to use it to manage clinical provider organizations in a hospital deployment is a category error.

3. **FHIR R4 Support Settings must be enabled before FHIR-aligned clinical objects are usable** — Even with Health Cloud PSL assigned, FHIR-aligned clinical objects (`ClinicalEncounter`, clinical observation records) are not fully usable until FHIR R4 Support Settings are explicitly enabled in Setup > Health > Health Cloud Settings. This is not documented prominently in the standard PSL assignment guide and is frequently missed during org setup.

4. **`MemberPlan` and `ClinicalEncounter` can coexist in a dual-sector org but share no semantic relationship** — In a dual-sector org, both object sets are present in the schema. There is no platform-enforced relationship between a member's `MemberPlan` and a patient's `ClinicalEncounter`. Architects who assume the platform automatically links insurance coverage to clinical records must build that linkage explicitly — it is not provided out of the box.

5. **AuthorizationForm is a Utilization Management object, not a general consent form** — `AuthorizationForm` and `AuthorizationFormConsent` belong to the Utilization Management feature set and model prior authorization requests in a payer org. They are not general-purpose consent management objects. Using them for clinical consent workflows in a provider org is semantically incorrect and requires the Utilization Management PSL, which is a payer-specific license that should not be assigned to clinical users.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Architecture decision document | Written record of deployment type classification, rationale, and key tradeoffs |
| Object model recommendation | Canonical list of Health Cloud objects for the deployment type, with objects from the wrong sector explicitly excluded |
| PSL matrix | Table mapping each user persona to required base PSL, sector PSL, and feature PSL |
| Data separation architecture (dual-sector only) | Record ownership model, sharing rule strategy, and permission boundary design |

---

## Related Skills

- `health-cloud-data-model` — detailed object model reference for Health Cloud; use alongside this skill once deployment type is classified
- `hipaa-compliance-architecture` — HIPAA data governance requirements; especially relevant for dual-sector orgs where clinical and insurance data coexist
- `compliant-data-sharing-setup` — sharing rule and permission set design for regulated data; use for dual-sector data separation architecture
