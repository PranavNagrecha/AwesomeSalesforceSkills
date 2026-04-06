# SIS Integration Patterns — Work Template

Use this template when designing or reviewing a SIS-to-Education-Cloud integration task.

## Scope

**Skill:** `sis-integration-patterns`

**Request summary:** (fill in what the practitioner asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- SIS platform in use: (Banner / Colleague / Anthology / PeopleSoft / Workday Student / Other)
- SIS-native student identifier field name and format: (e.g., PIDM as 7-digit integer, EMPLID as 10-char string)
- Education Cloud API version deployed in org: (confirm v57.0+ for ATE/COP; v63.0+ for LearnerProfile)
- Integration middleware: (MuleSoft / Boomi / Informatica / Custom Apex / Other)
- Sync frequency requirement: (nightly batch / near-real-time CDC / both)
- Person Account model or Contact-only model:
- Known volume: (approximate student count, enrollment records per term)

## External ID Field Design

| Object | Field API Name | Type | Encoding | Notes |
|---|---|---|---|---|
| Contact | SIS_Student_ID__c | Text(18), External ID, Unique | Raw SIS ID | Set on initial load; never changes |
| LearnerProfile | SIS_LearnerProfile_ID__c | Text(18), External ID, Unique | Same as Contact SIS ID | Required because StudentIdNumber is NOT an External ID |
| AcademicTermEnrollment | SIS_Enrollment_Key__c | Text(50), External ID, Unique | `{SIS_ID}|{TermCode}` | |
| CourseOfferingParticipant | SIS_CourseParticipant_Key__c | Text(80), External ID, Unique | `{SIS_ID}|{TermCode}|{SectionCode}` | |
| CourseOfferingPtcpResult | SIS_GradeResult_Key__c | Text(80), External ID, Unique | `{SIS_ID}|{TermCode}|{SectionCode}|FINAL` | |

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1: Nightly Batch Upsert (Bulk API 2.0, ordered jobs)
- [ ] Pattern 2: Near-Real-Time Writeback via CDC
- [ ] Both

Justification: (why this pattern is appropriate given the stated sync frequency and volume)

## Upsert Job Sequence

List each Bulk API 2.0 job in the required execution order:

1. Job 1 — Upsert `Contact` on `SIS_Student_ID__c` — must reach `JobComplete` before Job 2
2. Job 2 — Upsert `LearnerProfile` on `SIS_LearnerProfile_ID__c`
3. Job 3 — Upsert `AcademicTermEnrollment` on `SIS_Enrollment_Key__c`
4. Job 4 — Upsert `CourseOfferingParticipant` on `SIS_CourseParticipant_Key__c`
5. Job 5 — Upsert `CourseOfferingPtcpResult` on `SIS_GradeResult_Key__c`
6. Job 6 — Upsert `PersonAcademicCredential` (end-of-term only)

## Enrollment Status Mapping

| SIS Status Code | Salesforce EnrollmentStatus |
|---|---|
| (fill in SIS codes) | Active / Withdrawn / Graduated / Expelled / No show / Dropout / Transferred / Other |

## Watermark Design

- Watermark field: (which SIS timestamp or sequence number)
- Watermark storage location: (MuleSoft Object Store / custom Salesforce object / external DB table)
- Watermark update trigger: (after Job 1 completes successfully / after all jobs complete)

## CDC Writeback Design (if applicable)

- CDC object: AcademicTermEnrollment
- CometD topic: `/data/AcademicTermEnrollmentChangeEvent`
- Fields triggering writeback: EnrollmentStatus
- SIS update API endpoint: (fill in)
- Retry strategy: (exponential backoff, max N retries, dead-letter queue)

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Custom External ID fields deployed on Contact, AcademicTermEnrollment, CourseOfferingParticipant, CourseOfferingPtcpResult, LearnerProfile
- [ ] Upsert job sequence enforces parent-before-child ordering
- [ ] Watermark timestamp persisted after each successful batch run
- [ ] Bulk API 2.0 used for loads > 500 records per object
- [ ] Failed-record error logs captured and monitored
- [ ] CDC enabled on AcademicTermEnrollment if writeback required; subscriber handles 72-hour replay
- [ ] LearnerProfile.ContactId excluded from update payloads
- [ ] Integration user has minimum required object/field permissions
- [ ] FERPA-sensitive fields not exposed in integration logs

## Notes

Record any deviations from the standard pattern and why.
