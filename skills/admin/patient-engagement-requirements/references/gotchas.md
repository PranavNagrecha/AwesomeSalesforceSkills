# Gotchas — Patient Engagement Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Primary source: Agentforce Health Developer Guide (the Health Cloud developer guide PDF, `health_cloud_dev_guide.pdf`, Spring '26), read on 2026-10-03. License and contract claims cannot be grounded in a developer guide; they are marked UNVERIFIED where they appear.

## Gotcha 1: Experience Cloud for Health Cloud Is Not Included in Base Health Cloud

**What happens:** An implementation proceeds to the portal configuration phase and discovers that Experience Cloud for Health Cloud requires a separately purchased add-on SKU, including per-user licenses for all patient portal users. UNVERIFIED (2026-10-03): this licensing statement comes from Salesforce Help and contract practice; no developer guide read for this revision describes SKUs.

**When it occurs:** When the project scope assumes patient-facing portal capability is included in Health Cloud, based on product documentation that describes Health Cloud portal features without prominently disclosing the separate licensing requirement.

**How to avoid:** At project inception, explicitly confirm that Experience Cloud for Health Cloud is included in the contract. Request the full license breakdown from the Salesforce account team. Identify the per-user license cost and user count estimate before project budgeting.

**Source:** Carried from earlier revisions (Salesforce Help, Experience Cloud for Health Cloud).

---

## Gotcha 2: No-Show Prediction Is Not the Same Thing as the NoShow Status

**What happens:** The implementation delivers Intelligent Appointment Management for patient self-scheduling, but no-show risk prediction is unavailable because CRM Analytics is not licensed. Separately, teams confuse the prediction feature with the NoShow status that already exists in the data model. The developer guide lists `NoShow` as a value of the `healthcloudext.BookingStatus` enum and of the Service Appointment `StatusReason` field. Recording that a patient did not show up needs no add-on; predicting it in advance is a different feature. UNVERIFIED (2026-10-03): the CRM Analytics dependency for prediction comes from earlier revisions of this skill and Help; the developer guide read for this revision does not describe a prediction feature.

**When it occurs:** When "no-show handling" in requirements means both "mark missed appointments" and "predict missed appointments", and only one is scoped and licensed.

**How to avoid:** Split the requirement in two: recording no-shows (status values that exist) and predicting no-shows (a licensed analytics feature). Confirm the license only for the second.

**Source:** Agentforce Health Developer Guide, HealthCloudExt namespace, `BookingStatus` enum (NoShow); Fields on Service Appointment, `StatusReason` (NoShow).

---

## Gotcha 3: Assessments Need OmniStudio, the Discovery Framework Feature, and Specific Permission Set Licenses

**What happens:** Health assessments cannot be configured, or patients and coordinators cannot see assessment records. Earlier versions of this skill said Discovery Framework is a separate managed package found under Installed Packages. The Salesforce Industries Developer Guide describes it as a feature enabled in the org, and its Metadata API types require "an Omnistudio license and the Discovery Framework feature enabled". OmniStudio itself runs either as Omnistudio for Managed Packages or on the standard runtime. Even when both are in place, the Assessment standard objects are visible only to users with the Health Cloud and Health Cloud Platform permission set licenses and the Health Cloud Permission Set License permission set.

**When it occurs:** When admins assume licensing alone sets up assessments, or when portal or coordinator users lack the permission set licenses.

**How to avoid:** At kickoff, record the OmniStudio runtime, confirm the Discovery Framework feature is enabled, and add the permission set licenses and permission set to the user setup plan for every persona that touches assessments.

**Source:** Agentforce Health Developer Guide, Health Assessments ("Health Cloud Assessments use the power of Discovery Framework and OmniStudio"; visibility statement; API version 57.0); Salesforce Industries Developer Guide, Discovery Framework Metadata API Types (OmniScript special access rules); Trailhead, "Configure a Simple OmniScript" (managed package runtime vs standard runtime note).

---

## Gotcha 4: Secure Patient Messaging Must Use HIPAA-Covered Channels

**What happens:** Clinical communications (appointment reminders containing PHI, care plan instructions, assessment results) are routed through standard Salesforce email (Email-to-Case) or standard Chatter, which may not be covered under the Salesforce BAA for PHI. UNVERIFIED (2026-10-03): BAA coverage is a contractual fact per service; no source read for this revision lists covered services.

**When it occurs:** When the messaging channel is designed for convenience rather than HIPAA compliance, or when the team assumes all Salesforce features are BAA-covered.

**How to avoid:** For any patient communication channel that may carry PHI, explicitly verify BAA coverage for that channel with the account team and legal. Use Salesforce's Messaging for In-App and Web with the Messaging User permission set for secure patient-clinician messaging only after that coverage is confirmed.

**Source:** Carried from earlier revisions.

---

## Gotcha 5: Self-Scheduling Reads Availability From the Source EHR

**What happens:** Patients see no slots, or slots that the clinic cannot honor. To book an appointment, Health Cloud needs the availability of a practitioner at a facility and gets it by querying the source EHR system with the practitioner and facility IDs stored in that system. When the IDs are missing or the EHR integration is not built, there is nothing to show.

**When it occurs:** When requirements treat self-scheduling as a Salesforce-only feature and skip the EHR integration, or when provider records lack their source-system identifiers.

**How to avoid:** Name the scheduling system of record per specialty in the requirements. Plan the integration: the default `AppointmentBookingInteropFhirAdapter` calls an external scheduling system over FHIR R4; a custom Apex class implementing `healthcloudext.AppointmentBookingInterop` is entered in the active Intelligent Appointment Management Configuration; callouts use a Named Credential mapped in the `AppointmentBookingConfig` setup object. Load source-system IDs for practitioners and facilities before testing.

**Source:** Agentforce Health Developer Guide, Intelligent Appointment Management (Practitioner Availability at Facilities); HealthCloudExt Namespace, `AppointmentBookingInterop` Interface usage notes.

---

## Gotcha 6: Appointment Reasons and Channels Are Data You Must Design

**What happens:** The self-scheduling page offers reasons the clinic does not support, or offers video for a visit that must be in person. Self-scheduling uses `AppointmentReason` (API 53.0+, "Not the same as visit type") and `ApptReasonEngmtChannelType` (API 56.0+), which links a reason to an engagement channel and to default and established-patient work types.

**When it occurs:** When the requirements list visit types but never define patient-facing reasons or the channels allowed per reason.

**How to avoid:** Capture a reason-by-channel matrix in requirements, with the work type for new and established patients in each cell. Review it with clinical operations, not only IT.

**Source:** Agentforce Health Developer Guide, Intelligent Appointment Management, `AppointmentReason` and `ApptReasonEngmtChannelType` object references.

---

## Gotcha 7: Portal Users Need a Specific Permission Set for Clinical Data

**What happens:** Portal pages that show conditions, encounters, or service requests fail for community users. The developer guide states that to use the Clinical Data Model objects on an Experience Cloud site, community users need the FHIR R4 for Experience Cloud Sites permission set. Many of those objects (for example `ClinicalEncounter`, `ClinicalServiceRequest`, `HealthCondition`) also require the FHIR-Aligned Clinical Data Model org preference in FHIR R4 Support Settings.

**When it occurs:** When portal requirements include "patients can see their care history" without naming the objects and the access they need.

**How to avoid:** List the clinical objects each portal page reads. Add the org preference and the FHIR R4 for Experience Cloud Sites permission set to the prerequisites. Test with a real portal user, not an internal admin.

**Source:** Agentforce Health Developer Guide, Clinical Data Model (org preference list and the Experience Cloud permission set note).

---

## Gotcha 8: Patient Assessments Travel in Envelopes With Their Own Status

**What happens:** Coordinators cannot tell which assessments a patient has been sent, started, or finished, because the design assigned OmniScripts directly with no tracking record. The health assessments data model creates an `AssessmentEnvelope` (API 58.0+) per user with `AssessmentEnvelopeItem` records, each pointing to an assessment and its OmniScript (`OmniProcessId`). The envelope carries `Status` (NotStarted, InProgress, Completed), `NotificationStatus` (NotSent, Sent), and `ExpirationDateTime`.

**When it occurs:** When requirements describe "send the PHQ-9 before the visit" without saying how sending, reminders, expiry, and completion are recorded.

**How to avoid:** Write requirements in envelope terms: who receives the envelope, which items it holds, when it expires, and who is alerted on completion. Report on envelope Status rather than on OmniScript activity.

**Source:** Agentforce Health Developer Guide, Health Assessments, `AssessmentEnvelope` and `AssessmentEnvelopeItem` object references.

---

## Gotcha 9: Two Appointment APIs Point in Opposite Directions

**What happens:** An integration team builds against the wrong API. The Appointment Management Connect APIs (Book, Cancel, Update under `/connect/health/appointment-management/`) call into Salesforce. The Intelligent Appointment Management Operations APIs call out to an external system to find slots and book.

**When it occurs:** When the requirements say "use the IAM API" without stating which system initiates the call.

**How to avoid:** For each scheduling interaction, record the initiator (patient portal, EHR, call center) and the system that holds the slot. Pick the API family from that.

**Source:** Agentforce Health Developer Guide, REST Reference, Appointment Management ("These APIs are a part of the Intelligent Appointment Management (IAM) and calls into the system, while the Intelligent Appointment Management Operations API calls out to an external system").
