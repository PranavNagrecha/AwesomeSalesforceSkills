# Examples — SIS Integration Patterns

## Example 1: Nightly Banner PIDM Upsert into AcademicTermEnrollment via Bulk API 2.0

**Context:** A mid-size university runs Ellucian Banner as its SIS. Banner exports a nightly CSV of all enrollment changes since the previous night, keyed on the Banner PIDM (a numeric surrogate key). The Salesforce org runs Education Cloud v64.0. The integration middleware is MuleSoft Anypoint Platform.

**Problem:** Without a stable SIS-sourced External ID, each nightly run risks inserting duplicate `AcademicTermEnrollment` records for students who already exist in Salesforce. A plain SOQL query-then-upsert approach makes two round-trips per record and exhausts the 24-hour API call limit for a 30,000-student institution.

**Solution:**

Step 1 — Field setup (one-time, done in Setup):
- `Contact.Banner_PIDM__c` — Text(18), External ID, Unique
- `AcademicTermEnrollment__c.SIS_Enrollment_Key__c` — Text(50), External ID, Unique. Value format: `{PIDM}|{TermCode}`, e.g., `1234567|FA2025`

Step 2 — MuleSoft flow (simplified):

```xml
<!-- MuleSoft DataWeave mapping — Banner export row to AcademicTermEnrollment upsert payload -->
%dw 2.0
output application/json
---
{
  attributes: { type: "AcademicTermEnrollment__c" },
  "SIS_Enrollment_Key__c": payload.pidm ++ "|" ++ payload.term_code,
  "LearnerContact": { "Banner_PIDM__c": payload.pidm },
  "AcademicTermId": payload.sf_term_id,          // pre-resolved in prior step
  "EnrollmentStatus": mapStatus(payload.banner_status), // see status mapping below
  "EnrollmentDate": payload.enroll_date as Date,
  "StudentAcademicLevel": mapAcademicLevel(payload.level_code)
}
```

Step 3 — Bulk API 2.0 upsert job (MuleSoft Salesforce Connector):
```
operation: upsert
sObjectType: AcademicTermEnrollment__c
externalIdFieldName: SIS_Enrollment_Key__c
```

Step 4 — Banner-to-Salesforce status mapping (applied in DataWeave `mapStatus` function):

| Banner Status | Salesforce EnrollmentStatus |
|---|---|
| EW (Enrolled/Web) | Active |
| WD (Withdrawn) | Withdrawn |
| GR (Graduated) | Graduated |
| XF (Expelled) | Expelled |
| NS (No Show) | No show |
| TR (Transfer Out) | Transferred |

**Why it works:** Upsert on `SIS_Enrollment_Key__c` makes each run idempotent — re-running the same extract never creates duplicates. Using a relationship reference (`LearnerContact.Banner_PIDM__c`) in the upsert payload avoids a pre-query for the Salesforce Contact ID. Bulk API 2.0 processes the full nightly file as a single asynchronous job, well within governor limits.

---

## Example 2: PeopleSoft EMPLID Grade Writeback to CourseOfferingPtcpResult

**Context:** A large research university uses PeopleSoft Campus Solutions. Final grades are entered by faculty in Salesforce Education Cloud after the grading period ends and must be written back to PeopleSoft as the system of record for official transcripts. The integration runs at end-of-term grade submission.

**Problem:** `CourseOfferingPtcpResult` records have a parent `CourseOfferingParticipant` that was created earlier in the term. The grades upsert job must resolve the correct `CourseOfferingParticipantId` for each student-section combination, or it will fail with `INVALID_CROSS_REFERENCE_KEY`. Additionally, attempting to upsert `CourseOfferingPtcpResult` with a `ParticipantResultStatus` value not in the restricted picklist causes silent row-level failures in Bulk API 2.0.

**Solution:**

Step 1 — External ID field setup:
- `CourseOfferingParticipant.SIS_CourseParticipant_Key__c` — Text(80), External ID, Unique. Value: `{EMPLID}|{TermCode}|{ClassNbr}`
- `CourseOfferingPtcpResult.SIS_GradeResult_Key__c` — Text(80), External ID, Unique. Value: `{EMPLID}|{TermCode}|{ClassNbr}|FINAL`

Step 2 — Upsert payload for CourseOfferingPtcpResult:

```json
{
  "SIS_GradeResult_Key__c": "98765|SP2026|12345|FINAL",
  "CourseOfferingParticipant": {
    "SIS_CourseParticipant_Key__c": "98765|SP2026|12345"
  },
  "LetterGrade": "A-",
  "NumericGrade": 3.7,
  "ParticipantResultStatus": "Pass",
  "UnitsEarned": 3.0,
  "DurationUnit": "CreditHours"
}
```

Step 3 — Bulk API 2.0 upsert job on `CourseOfferingPtcpResult` with `externalIdFieldName: SIS_GradeResult_Key__c`. Run **after** the CourseOfferingParticipant upsert job has completed successfully.

Step 4 — Result status mapping from PeopleSoft grade values:

| PeopleSoft Grade | ParticipantResultStatus |
|---|---|
| A, B, C, D | Pass |
| F | Fail |
| W, WF | Withdraw |
| I | Incomplete |

**Why it works:** Using a relationship reference (`CourseOfferingParticipant.SIS_CourseParticipant_Key__c`) in the payload eliminates the need to pre-query `CourseOfferingParticipantId`. The composite External ID on `CourseOfferingPtcpResult` prevents duplicate grade records when the job is re-run (e.g., for grade corrections). Explicit status mapping prevents INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST errors.

---

## Anti-Pattern: Running Parent and Child Upserts in the Same Bulk API 2.0 Job

**What practitioners do:** To reduce middleware complexity, some teams load both `AcademicTermEnrollment` (parent) and `CourseOfferingParticipant` (child) records in a single Bulk API 2.0 job, relying on the assumption that records are processed top-to-bottom as submitted.

**What goes wrong:** Bulk API 2.0 does not guarantee processing order within a job. Salesforce processes records in batches of up to 10,000 rows, and the processing order within and across batches is nondeterministic. Child `CourseOfferingParticipant` records may be processed before their parent `AcademicTermEnrollment` records exist, causing `INVALID_CROSS_REFERENCE_KEY` errors for the children. These errors appear in the job result file but do not fail the job overall, so they are easy to miss if error logs are not monitored.

**Correct approach:** Always run parent object upserts as a separate Bulk API 2.0 job that must reach `JobComplete` state before the child job is submitted. MuleSoft's Salesforce Connector provides a `waitForResult` operation; other middleware should poll the job status endpoint (`GET /services/data/vXX.0/jobs/ingest/{jobId}`) until `state: JobComplete` before proceeding.
