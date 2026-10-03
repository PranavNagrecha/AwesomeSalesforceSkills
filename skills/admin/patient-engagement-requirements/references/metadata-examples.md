# Metadata and API Examples: Patient Engagement Requirements

Deployable and runnable artifacts for this skill. Each block names the file path it lives at. Narrative examples are in `references/examples.md`.

## Example 1: Prerequisite Checks and an Appointment Payload for the Requirements Pack

**Context:** The requirements pack for a primary care self-scheduling and pre-visit assessment rollout must prove each prerequisite with evidence from the target org, not with assumptions.

**Artifact 1: configuration inventory queries** (run in the target org; save the results with the requirements).

```sql
-- Which patient-facing reasons and channels exist (Agentforce Health Developer Guide, IAM objects)
SELECT Id, Name, AppointmentReasonId, AppointmentReason.AppointmentReason,
       EngagementChannelTypeId, DefaultWorkTypeId, EstablishedWorkTypeId
FROM ApptReasonEngmtChannelType
ORDER BY AppointmentReasonId
```

```sql
-- Assessment delivery status per patient (Health Assessments objects, API 58.0+)
SELECT Id, Name, AccountId, ContactId, Status, NotificationStatus, ExpirationDateTime,
       (SELECT Id, AssessmentId, OmniProcessId, Status FROM AssessmentEnvelopeItems)
FROM AssessmentEnvelope
WHERE Status != 'Completed'
ORDER BY ExpirationDateTime
```

UNVERIFIED (2026-10-03): the child relationship name `AssessmentEnvelopeItems` is assumed from the standard naming pattern; the object reference read for this revision lists `AssessmentEnvelopeItem.AssessmentEnvelopeId` but not the relationship name. If the subquery fails, query `AssessmentEnvelopeItem` with a filter on `AssessmentEnvelopeId`.

**Artifact 2: the booking call the portal will make into Salesforce** (Appointment Management Connect API, `POST /services/data/v66.0/connect/health/appointment-management/appointment`, request body for an EHR-backed slot as documented in the REST Reference).

```json
{
  "startDate": "2026-11-03T09:00:00Z",
  "endDate": "2026-11-03T09:30:00Z",
  "workTypeId": "<workTypeId for the reason and channel>",
  "channelId": "<engagement channel id>",
  "sourceSystem": "cerner",
  "comment": "New patient annual physical booked from the patient portal.",
  "slots": [
    { "id": "<slot id returned by the EHR>", "reference": "<healthcarePractitionerId>" }
  ],
  "participants": [
    { "reference": "Patient/<patientId>" },
    { "reference": "Facility/<facilityId>" },
    { "reference": "Practitioner/<healthcarePractitionerId>", "isReferenceRequired": true }
  ]
}
```

**Artifact 3: retrieve manifest for the IAM integration components** a reviewer should inspect before sign-off (the custom `AppointmentBookingInterop` class and the Named Credential the developer guide says to use for callouts).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/iam-integration-review.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>ClinicAppointmentBookingInterop</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>EHR_Scheduling</members>
        <name>NamedCredential</name>
    </types>
    <version>66.0</version>
</Package>
```

`ClinicAppointmentBookingInterop` and `EHR_Scheduling` are placeholder names for the org's own class and credential. Leave the class out when the org uses the default `AppointmentBookingInteropFhirAdapter`.

**Why it works:** Each artifact turns a requirement into a checkable fact: the reasons and channels patients will see, the assessments in flight, the exact payload the portal sends, and the integration components that must exist before go-live.
