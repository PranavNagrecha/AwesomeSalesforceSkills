---
name: patient-engagement-requirements
description: "Use this skill when defining patient engagement portal requirements for Health Cloud: appointment scheduling, secure in-portal messaging, health assessments, patient education, and self-service features. NOT for care team workflows, SDOH barriers and care gaps — use admin/care-coordination-requirements. NOT for patient portal licensing and cloud topology — use architect/health-cloud-multi-cloud-strategy."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "What are the requirements for patient self-scheduling in Health Cloud Intelligent Appointment Management?"
  - "Does CRM Analytics license required for no-show prediction in patient engagement workflows?"
  - "Health assessment requirements for patient portal in Salesforce Health Cloud"
  - "OmniStudio and Discovery Framework prerequisites for delivering health assessments to patients"
  - "Secure in-portal messaging requirements for HIPAA-compliant patient communication"
  - "scope patient self-scheduling requirements against the EHR we already run"
  - "list the licenses and setup steps a Health Cloud patient portal needs before build"
tags:
  - health-cloud
  - patient-engagement
  - intelligent-appointment-management
  - health-assessment
  - patient-portal
  - omnistudio
inputs:
  - Health Cloud org with patient-facing use case
  - Patient records as Person Accounts
  - Experience Cloud license (required for patient portal)
  - List of patient engagement features in scope
outputs:
  - Patient engagement feature requirements with license prerequisites identified
  - Intelligent Appointment Management (IAM) requirements including CRM Analytics dependency
  - Health assessment requirements with OmniStudio/Discovery Framework prerequisites
  - Secure messaging requirements with HIPAA-compliant channel specification
  - Engagement feature to license dependency matrix
dependencies:
  - admin/health-cloud-patient-setup
  - admin/care-program-management
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Patient Engagement Requirements

Use this skill when defining patient engagement portal requirements for Health Cloud: appointment scheduling, secure in-portal messaging, health assessments, and patient self-service features. This skill covers requirements gathering and license dependency identification for patient-facing features. It does NOT cover Experience Cloud site configuration, OmniStudio component development, or general portal setup unrelated to clinical patient engagement workflows.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm that the Experience Cloud for Health Cloud add-on license is in scope. A base Health Cloud license does NOT include patient-facing portal functionality. Experience Cloud for Health Cloud is a separately purchased add-on SKU.
- Identify which patient engagement features are required: appointment scheduling, health assessments, secure messaging, patient education, self-enrollment. Each may have different license and implementation prerequisites.
- Confirm whether Intelligent Appointment Management (IAM) is in scope. IAM requires CRM Analytics as a separately licensed add-on for no-show prediction functionality. Without CRM Analytics, IAM scheduling works but the predictive analytics features are unavailable.
- Confirm whether health assessments are required. The Agentforce Health Developer Guide says Health Cloud Assessments "use the power of Discovery Framework and OmniStudio". The Salesforce Industries Developer Guide describes Discovery Framework as a feature enabled in the org, and OmniStudio ships either as Omnistudio for Managed Packages or on the standard runtime. Confirm which runtime the org has and that Discovery Framework is enabled.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| Which system owns appointment availability: Salesforce Scheduler, the EHR, or both? | Intelligent Appointment Management queries the source EHR for a practitioner's availability at a facility using the source system's IDs; custom sources need an `AppointmentBookingInterop` implementation and a Named Credential (Agentforce Health Developer Guide). | The source system per specialty and whether its FHIR R4 interface is available. | Self-scheduling shows real slots instead of a copy of the EHR calendar that drifts. |
| Which appointment reasons can a patient pick, and through which channels (video, phone, in person)? | Self-scheduling is driven by `AppointmentReason` records and `ApptReasonEngmtChannelType` rows that link each reason to a channel and default work types. | A reason-by-channel matrix with the work type for each cell. | Patients only see reasons and channels the clinic can actually serve. |
| Which assessments go to patients, and how are they bundled and tracked? | Patient assessments are delivered through `AssessmentEnvelope` and `AssessmentEnvelopeItem` (API 58.0+), with Status and NotificationStatus fields. | The instruments, the envelope grouping, expiry, and who is notified on completion. | Coordinators can see which assessments were sent, started, and finished per patient. |
| Will portal users see clinical records (conditions, encounters, service requests)? | Community users need the FHIR R4 for Experience Cloud Sites permission set for Clinical Data Model objects, and many of those objects need the FHIR-Aligned Clinical Data Model org preference. | The objects in scope and the permission set plan for portal users. | Portal pages show clinical data on day one instead of failing with access errors. |
| Which add-on licenses are in the signed contract (Experience Cloud for Health Cloud, CRM Analytics, Messaging)? | Several features in this skill depend on separately sold licenses; this is contract information no metadata reveals. | A license-to-feature matrix signed off by the account team. | Requirements that the org cannot deliver are cut before build, not after. |
| Which channels may carry PHI, and are they covered by the BAA? | Coverage is a contractual fact per service. | A channel list with BAA status and the PHI each one may carry. | Reminders and messages are designed to stay inside covered channels. |

---

## Core Concepts

### Experience Cloud for Health Cloud Is a Separate License

A Health Cloud license does not automatically include the ability to create patient-facing portals. Experience Cloud for Health Cloud is a distinct add-on SKU that provides:
- Patient-facing community portal with Health Cloud-specific components
- FHIR R4 for Experience Cloud permission set (required for FHIR data in portal)
- Per-user Experience Cloud for Health Cloud permission set licenses

The most common implementation scope gap: teams design a patient portal assuming it is included in Health Cloud, then discover the separate license requirement during contract finalization.

### Intelligent Appointment Management (IAM) and CRM Analytics Dependency

IAM aggregates Salesforce Scheduler and/or external EHR scheduling engines in a single care coordinator or patient-facing console. Key capabilities:
- Patient guest self-scheduling (no Salesforce login required)
- Appointment type configuration by specialty and location
- Provider availability management

**CRM Analytics dependency:** No-show prediction in IAM requires CRM Analytics (formerly Tableau CRM) as a separately licensed add-on. Without this license, the IAM scheduling console works but the AI/ML no-show risk scoring is unavailable. This is a common implementation gap — the feature appears in product marketing but the CRM Analytics dependency is not prominently documented. UNVERIFIED (2026-10-03): the developer guide read for this revision records NoShow as a booking status (`healthcloudext.BookingStatus`) and a Service Appointment Status Reason value, but describes no prediction feature or license dependency.

### OmniStudio and Discovery Framework for Health Assessments

Delivering health assessments (standardized clinical questionnaires, social screening tools, care gap assessments) to patients via a portal requires:
1. **OmniStudio managed package** installed — OmniScript is the form/assessment engine used for health assessments.
2. **Discovery Framework** installed — the clinical assessment library framework used to standardize assessment templates (PHQ-9, GAD-7, SDOH screeners).

Both must be explicitly set up before assessments can be built. OmniStudio is either the managed package runtime or the standard runtime; Discovery Framework is described in the Salesforce Industries Developer Guide as a feature that must be enabled in the org (its Metadata API types require "an Omnistudio license and the Discovery Framework feature enabled"). The Assessment standard objects are visible only to users with the Health Cloud and Health Cloud Platform permission set licenses and the Health Cloud Permission Set License permission set (Agentforce Health Developer Guide, Health Assessments).

### HIPAA-Compliant Secure Messaging

Secure in-portal messaging for patient-clinician communication must route through HIPAA-compliant channels:
- In-app/web messaging via Salesforce Messaging requires the Messaging for In-App and Web add-on with the **Messaging User permission set** explicitly assigned.
- Do not route patient clinical communications through standard Salesforce Email-to-Case or standard Chatter — neither is HIPAA-covered by default.
- All messaging channels used for patient clinical communications must be explicitly covered under the Salesforce BAA.

---

## Common Patterns

### Scoping Patient Self-Scheduling Requirements

**When to use:** A health system wants patients to self-schedule appointments without calling the clinic.

**How it works:**
1. Confirm IAM license is included (separate from base Health Cloud).
2. Confirm whether no-show prediction is needed — if yes, add CRM Analytics to license scope.
3. Identify scheduling data sources: Salesforce Scheduler only, EHR scheduling only, or hybrid aggregation.
4. Define appointment type taxonomy (primary care, specialty, telehealth vs. in-person).
5. Determine patient authentication model: guest (no login), Experience Cloud user (registered patient), or hybrid.
6. Design the appointment confirmation and reminder workflow (email/SMS/push notifications).

**Why not the alternative:** Manual appointment scheduling via phone creates a bottleneck, especially for routine follow-ups. IAM enables patient self-service while maintaining care coordinator oversight.

### Scoping Health Assessment Delivery

**When to use:** A care program requires patients to complete standardized clinical assessments (PHQ-9 depression screening, SDOH social needs screening) via a portal.

**How it works:**
1. Confirm the OmniStudio runtime (managed package or standard) is set up in the org (not just licensed).
2. Confirm the Discovery Framework feature is enabled and assessment templates are available.
3. Identify required assessment instruments (PHQ-9, GAD-7, SDOHCC screening, etc.).
4. Design the assessment trigger (enrollment event, scheduled cadence, or care gap).
5. Define assessment response data model — where responses are stored (standard survey/assessment objects or custom).
6. Design notification workflow to alert care coordinators when high-risk assessments are completed.

---

## Decision Guidance

| Situation | Requirement | License Dependency |
|---|---|---|
| Patient self-scheduling | Intelligent Appointment Management | IAM add-on; CRM Analytics if no-show prediction needed |
| Health assessments via portal | OmniStudio + Discovery Framework | OmniStudio in HC license; Discovery Framework must be installed |
| Patient portal | Experience Cloud for Health Cloud | Separate add-on SKU; per-user license |
| Secure clinical messaging | Messaging for In-App and Web + Messaging User perm set | Separate add-on; must be BAA-covered |
| FHIR data in patient portal | FHIR R4 for Experience Cloud Sites perm set, plus the FHIR-Aligned Clinical Data Model org pref for many clinical objects | Included with Experience Cloud for HC add-on (UNVERIFIED) |

---

## Recommended Workflow

1. **Confirm license scope** — before designing any patient engagement feature, verify which features are covered in the contract: Experience Cloud for Health Cloud, IAM, CRM Analytics, Messaging add-on, OmniStudio activation. Build a license-to-feature mapping as a prerequisite artifact.
2. **Inventory patient engagement requirements** — gather requirements for each engagement category: scheduling, messaging, assessments, education, self-enrollment. For each, note the business requirement, technical prerequisites, and license dependencies.
3. **Identify HIPAA compliance requirements** — for each engagement channel (messaging, assessment responses, appointment data), confirm HIPAA applicability, BAA coverage for the channel, and PHI handling requirements.
4. **Design feature implementation sequence** — sequence features by dependency order. Patient portal (Experience Cloud for HC) must exist before any portal features can be configured. OmniStudio and Discovery Framework must be set up before assessment features are built. Example queries and an appointment booking payload for validating each prerequisite are in `references/metadata-examples.md`.
5. **Document prerequisites for implementation team** — produce a prerequisites document covering: license activation steps, permission set assignments (per-user experience cloud license, FHIR perm set, Messaging User perm set), and package installation sequence.
6. **Validate requirements against licensing contracts** — review the completed requirements against the signed contract to confirm all required license SKUs are included. Flag any gaps before implementation begins.

---

## Review Checklist

- [ ] Experience Cloud for Health Cloud add-on license confirmed (separate from base HC)
- [ ] CRM Analytics license confirmed if IAM no-show prediction is in scope
- [ ] OmniStudio runtime confirmed if health assessments are in scope
- [ ] Discovery Framework feature enabled if standardized assessments are needed
- [ ] Health Cloud and Health Cloud Platform permission set licenses planned for assessment users
- [ ] Messaging add-on confirmed and HIPAA BAA coverage verified for messaging channel
- [ ] Per-user Experience Cloud for Health Cloud permission set assignment planned
- [ ] FHIR R4 for Experience Cloud Sites permission set planned if clinical data is needed in the portal

---

## Salesforce-Specific Gotchas

1. **Experience Cloud for Health Cloud is not included in base Health Cloud** — a Health Cloud license does not include patient portal capability. The Experience Cloud for Health Cloud add-on is a separately purchased SKU with its own per-user license. Discovering this after implementation begins creates significant scope and budget risk.

2. **CRM Analytics required for IAM no-show prediction** — IAM appointment scheduling works without CRM Analytics, but no-show risk prediction (a key feature in product marketing materials) requires CRM Analytics as a separate licensed add-on. Organizations that include no-show prediction in requirements must confirm CRM Analytics is in scope.

3. **OmniStudio and Discovery Framework must be set up, and assessment objects need specific licenses**: Health Cloud orgs without an OmniStudio runtime or with Discovery Framework disabled cannot deliver OmniScript-based assessments. See `references/gotchas.md` for the permission set licenses and the EHR scheduling dependency.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Patient engagement feature inventory | List of all engagement features with license prerequisites |
| License dependency matrix | Feature-to-license mapping for procurement validation |
| HIPAA channel compliance assessment | For each engagement channel: HIPAA applicability, BAA coverage, PHI handling |
| Prerequisites checklist | Ordered list of license activations, package installs, and permission set assignments |

---

## Related Skills

- admin/health-cloud-patient-setup — Patient account configuration that precedes portal setup
- admin/care-program-management — Care program enrollment that patient portal integrates with
- admin/hipaa-workflow-design — HIPAA access control design for patient engagement channels
