---
name: sis-integration-patterns
description: "Use this skill when designing or implementing an integration between a Student Information System (SIS) — such as Ellucian Banner, Ellucian Colleague, Anthology Student, Oracle PeopleSoft Campus Solutions, or Workday Student — and Salesforce Education Cloud. Covers the canonical Education Cloud data model objects (AcademicTermEnrollment, CourseOfferingParticipant, CourseOfferingPtcpResult, LearnerProfile, PersonAcademicCredential), external ID / upsert keying strategies using SIS-native identifiers (Banner PIDM, PeopleSoft EMPLID), batch nightly upsert patterns, Change Data Capture (CDC) for enrollment status writeback, and MuleSoft/middleware watermark patterns. Trigger keywords: SIS integration, Banner integration, PeopleSoft integration, Education Cloud data model, enrollment sync, grade writeback, AcademicTermEnrollment, LearnerProfile upsert. NOT for Salesforce Admissions Connect application processing, Financial Aid integration, Learning Management System (LMS) integrations, or general ETL tooling not involving Education Cloud objects."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
  - Operational Excellence
triggers:
  - "how do I sync enrollment records from Banner into Education Cloud AcademicTermEnrollment"
  - "what external ID field should I use to upsert LearnerProfile records keyed on PeopleSoft EMPLID"
  - "nightly SIS batch job is creating duplicate Contact records — how do I prevent that"
  - "enrollment status changed in Colleague — how do I write that back to Salesforce in near real-time"
  - "how do I map Banner PIDM to a Salesforce external ID field on Contact or LearnerProfile"
  - "grade sync from SIS to CourseOfferingPtcpResult is failing with DUPLICATE_VALUE errors"
  - "what Education Cloud objects does a SIS integration need to populate and in what order"
  - "MuleSoft watermark pattern for incremental SIS sync — which timestamp field to use"
tags:
  - sis-integration
  - education-cloud
  - academic-term-enrollment
  - learner-profile
  - banner
  - peoplesoft
  - upsert
  - change-data-capture
  - mulesoft
  - external-id
inputs:
  - "Which SIS platform is in use (Banner, Colleague, Anthology, PeopleSoft, Workday Student)"
  - "SIS-native student identifier field name and format (e.g., Banner PIDM as integer, PeopleSoft EMPLID as string)"
  - "Education Cloud API version deployed in the org (must be v57.0+ for AcademicTermEnrollment; v63.0+ for LearnerProfile; v64.0+ for DroppedDateTime on CourseOfferingParticipant)"
  - "Integration middleware or tooling in use (MuleSoft, Informatica, Boomi, custom Apex)"
  - "Sync frequency requirements (nightly batch vs. near-real-time CDC)"
  - "Whether a Person Account model or Contact/Account model is in use for student records"
outputs:
  - "External ID field design for Contact and LearnerProfile keyed on SIS identifier"
  - "Ordered upsert sequence for Education Cloud objects (Contact → AcademicTermEnrollment → CourseOfferingParticipant → CourseOfferingPtcpResult → PersonAcademicCredential)"
  - "Batch upsert Apex or middleware flow pattern with error handling and idempotency"
  - "CDC / Platform Event design for enrollment status writeback to SIS"
  - "Watermark strategy for incremental loads from SIS"
  - "Review checklist for SIS integration go-live"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# SIS Integration Patterns

Use this skill when a practitioner needs to design or implement a bidirectional data integration between a Student Information System (SIS) and Salesforce Education Cloud. This skill covers the canonical Education Cloud data model objects, SIS-to-Salesforce upsert keying strategies, batch and near-real-time sync patterns, and enrollment status writeback flows.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Education Cloud API version deployed in the org. `AcademicTermEnrollment` and `CourseOfferingParticipant` are available from API v57.0; `LearnerProfile` from v63.0; `CourseOfferingParticipant.DroppedDateTime` from v64.0. Integration code targeting older API versions will silently omit fields or fail.
- Identify the SIS-native student identifier. Banner uses PIDM (a numeric surrogate key), PeopleSoft uses EMPLID (a string), Colleague uses student ID. This identifier must be mapped to a custom External ID field on Contact (and optionally on LearnerProfile) before any upsert pattern can work reliably.
- Determine whether the org uses a Person Account model or a Contact-only model. Education Cloud's `AcademicTermEnrollment.LearnerContactId` and `LearnerProfile.ContactId` are Contact lookups. Person Account implementations populate `Contact` records via the Person Account trigger infrastructure — upserts targeting `Contact` directly are affected by Person Account sharing rules and record type constraints.
- Confirm integration middleware and its error-handling capabilities. Bulk API 2.0 is the correct API surface for nightly batch loads; REST Composite API is appropriate for transactional writes of 25 records or fewer; MuleSoft Salesforce Connector handles Bulk API natively and provides Object Store for watermark persistence.

---

## Core Concepts

### Education Cloud Data Model Hierarchy for SIS Integration

The core SIS-relevant Education Cloud objects form a strict parent-child hierarchy:

```
Contact (student)
 └── AcademicTermEnrollment  (one per student per term; API v57.0+)
      └── CourseOfferingParticipant  (one per student per course section; API v57.0+)
           └── CourseOfferingPtcpResult  (grade result; API v57.0+)
LearnerProfile  (master-detail to Contact; one per student; API v63.0+)
PersonAcademicCredential  (earned degree or credential; API v59.0+)
```

Key field relationships from the Education Cloud Developer Guide (v66.0):
- `AcademicTermEnrollment.LearnerContactId` — required lookup to Contact.
- `AcademicTermEnrollment.EnrollmentStatus` — restricted picklist: Active, Dropout, Expelled, Graduated, No show, Other, Transferred, Withdrawn.
- `CourseOfferingParticipant.AcademicTermEnrollmentId` — lookup to AcademicTermEnrollment.
- `CourseOfferingParticipant.CourseOfferingId` — required lookup to CourseOffering.
- `CourseOfferingPtcpResult.CourseOfferingParticipantId` — required lookup to CourseOfferingParticipant.
- `CourseOfferingPtcpResult.LetterGrade` — string; `NumericGrade` — double; `ParticipantResultStatus` — restricted picklist: Fail, Incomplete, Pass, Withdraw.
- `LearnerProfile.ContactId` — master-detail to Contact; this is a create-only field.
- `LearnerProfile.StudentIdNumber` — string field for the institution-issued student identifier.
- `PersonAcademicCredential.LearnerContactId` — lookup to Contact; `AchievedDate` — date.

Parent records must exist before child records are upserted. Attempting to upsert a `CourseOfferingParticipant` before its parent `AcademicTermEnrollment` is committed produces a REQUIRED_FIELD_MISSING or INVALID_CROSS_REFERENCE_KEY error in Bulk API 2.0.

### External ID Keying Strategy

Upsert operations require an External ID field to identify whether to insert or update a record. The SIS native identifier (PIDM, EMPLID, or equivalent) must be surfaced as a custom External ID field in Salesforce.

Recommended pattern:
- On `Contact`: create a custom field `SIS_Student_ID__c` (Text, External ID, Unique). Populate this field during the initial student load. All downstream upserts reference Contact via this field, not by Salesforce record ID.
- On `LearnerProfile`: the `StudentIdNumber` standard field is a plain string and is **not** an External ID — it cannot be used as an upsert key. Create a separate custom field `SIS_LearnerProfile_ID__c` (Text, External ID, Unique) if you need to upsert LearnerProfiles without first querying for the Salesforce record ID.
- On `AcademicTermEnrollment`, `CourseOfferingParticipant`, and `CourseOfferingPtcpResult`: create composite external IDs that encode SIS identifiers plus term/section codes (e.g., `SIS_Enrollment_Key__c` = `PIDM|TermCode`).

Without External ID fields, every batch job must first query Salesforce IDs, dramatically increasing API call volume and introducing race conditions.

### Change Data Capture for Enrollment Status Writeback

Many SIS platforms require Salesforce to push enrollment status changes back (e.g., a student self-service drop in Salesforce must update the SIS). The supported patterns are:

1. **Change Data Capture (CDC)**: Enable CDC on `AcademicTermEnrollment`. Subscribing middleware receives a change event payload including old and new `EnrollmentStatus` values. This is the lowest-latency, lowest-overhead pattern for writeback. Available for custom and standard objects; Education Cloud objects support CDC from API v47.0+.
2. **Platform Events**: If the SIS cannot consume CDC directly, use an Apex trigger or Flow on `AcademicTermEnrollment` to publish a custom Platform Event. The middleware subscribes to the Platform Event topic.
3. **Outbound Messaging** (legacy): Workflow-driven SOAP callback. Suitable only if the SIS already exposes a SOAP endpoint and the latency requirement is loose (up to 24 hours with retries).

CDC is preferred because it requires no custom Apex, supports replay from a durable event bus (72-hour retention), and includes field-level change detection.

---

## Common Patterns

### Pattern 1: Nightly Batch Upsert from SIS to Education Cloud

**When to use:** The SIS runs a nightly export of changed enrollment, grade, and student demographic data. Latency of up to 12–24 hours is acceptable.

**How it works:**

1. SIS exports a set of CSV or JSON files partitioned by object type (students, term enrollments, course participants, grades).
2. Middleware (MuleSoft, Boomi, or custom) reads each file and invokes Salesforce Bulk API 2.0 upsert jobs in dependency order:
   - Job 1: Upsert `Contact` on `SIS_Student_ID__c`
   - Job 2: Upsert `LearnerProfile` on `SIS_LearnerProfile_ID__c` (after Job 1 completes)
   - Job 3: Upsert `AcademicTermEnrollment` on `SIS_Enrollment_Key__c`
   - Job 4: Upsert `CourseOfferingParticipant` on `SIS_CourseParticipant_Key__c`
   - Job 5: Upsert `CourseOfferingPtcpResult` on `SIS_GradeResult_Key__c`
3. Failed records are written to an error log; a retry job processes them after a configurable delay.
4. A watermark timestamp (e.g., `LastModifiedDate` from the SIS extract) is stored in middleware persistent state (MuleSoft Object Store, database table) to support incremental loads on the next run.

**Why not a simple insert:** Without upsert on External ID, re-running the job on duplicate data creates duplicate records. Without the ordered job sequence, child upserts fail because parent IDs do not yet exist.

```apex
// Apex example — bulk upsert of AcademicTermEnrollment records using External ID
List<AcademicTermEnrollment__c> enrollments = buildEnrollmentList(sisExportRows);
Database.UpsertResult[] results = Database.upsert(enrollments,
    AcademicTermEnrollment__c.SIS_Enrollment_Key__c, false);
for (Database.UpsertResult r : results) {
    if (!r.isSuccess()) {
        logError(r.getErrors());
    }
}
```

### Pattern 2: Near-Real-Time Enrollment Status Writeback via CDC

**When to use:** The institution requires the SIS to reflect enrollment status changes (adds, drops, withdrawals) made in Salesforce within minutes, not overnight.

**How it works:**

1. Enable Change Data Capture for `AcademicTermEnrollment` in Setup > Integrations > Change Data Capture.
2. MuleSoft (or another EDA-compatible middleware) subscribes to the `/data/AcademicTermEnrollmentChangeEvent` topic using the CometD protocol.
3. On each change event, check the `changedFields` payload for `EnrollmentStatus`.
4. If `EnrollmentStatus` changed, extract `SIS_Enrollment_Key__c` from the event payload and call the SIS update API to write the new status.
5. Acknowledge the event. Failed SIS calls are retried with exponential backoff; the CDC bus retains events for 72 hours, allowing catch-up after middleware downtime.

**Why not polling:** Polling SOQL queries consume API call quota and introduce latency proportional to poll interval. CDC delivers changes within seconds and has no per-event API cost against the REST/SOAP call limits.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Nightly full-file SIS export, < 1M records | Bulk API 2.0 upsert with External IDs, ordered by object hierarchy | Bulk API handles large volumes without hitting per-transaction limits; External ID prevents duplicates |
| < 500 records per transaction, near-real-time | REST Composite API (sObject Collections upsert) | Lower overhead than Bulk API for small payloads; synchronous response enables immediate error handling |
| Salesforce enrollment change must reach SIS within 5 minutes | Change Data Capture on AcademicTermEnrollment + middleware subscriber | CDC is lowest-latency option with durable replay; no custom Apex trigger needed |
| SIS does not expose real-time API for writeback | Scheduled Apex or Flow batch that queries changed records and calls SIS via callout | Provides controlled retry and rate-limiting; less real-time than CDC |
| Grades sync (CourseOfferingPtcpResult) | Bulk API 2.0 upsert after CourseOfferingParticipant job completes | Grade records are child of participant; parent must exist first |
| Initial historical load (years of data) | Bulk API 2.0 with parallel jobs per object type, sequential per dependency layer | Parallelism within a layer is safe; cross-layer parallelism causes INVALID_CROSS_REFERENCE_KEY |
| SIS uses composite key (PIDM + TermCode) as natural key | Custom External ID field encoding both values (e.g., `12345|FA2025`) | Salesforce External ID must be unique per object; composite encoding avoids multi-field lookup |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify SIS identifier and API version.** Confirm which SIS platform is in use, the format of its student identifier (PIDM, EMPLID, etc.), and the Education Cloud API version in the target Salesforce org. API version determines field availability — verify `LearnerProfile` (v63.0+) and `CourseOfferingParticipant.DroppedDateTime` (v64.0+) are present if needed.

2. **Design and deploy External ID fields.** Create custom External ID fields on `Contact` (`SIS_Student_ID__c`), and composite-key External ID fields on `AcademicTermEnrollment`, `CourseOfferingParticipant`, and `CourseOfferingPtcpResult`. Confirm each field is marked Unique and External ID in the field definition. Do not use `LearnerProfile.StudentIdNumber` as an upsert key — it is not indexed as an External ID.

3. **Scaffold the integration flow in dependency order.** Implement upsert jobs that execute in the mandatory sequence: Contact → LearnerProfile → AcademicTermEnrollment → CourseOfferingParticipant → CourseOfferingPtcpResult → PersonAcademicCredential. Each layer must fully complete (and errors resolved) before the next layer runs.

4. **Implement watermark-based incremental loads.** Store the `LastModifiedDate` (or SIS-equivalent timestamp) of the last successfully processed batch run in durable middleware state (MuleSoft Object Store, a custom Salesforce object, or an external database). On subsequent runs, filter the SIS export to records modified after the watermark.

5. **Enable CDC and build the writeback subscriber.** If near-real-time writeback from Salesforce to SIS is required, enable Change Data Capture on `AcademicTermEnrollment` via Setup. Implement a middleware subscriber to the `/data/AcademicTermEnrollmentChangeEvent` topic. Filter on `EnrollmentStatus` field changes and invoke the SIS update API, with retry and dead-letter handling.

6. **Test with production-scale data volumes.** Run bulk upsert jobs against a full scratch org dataset. Verify that Bulk API 2.0 job completion rates and failed-record counts are within acceptable thresholds. Confirm CDC event throughput matches expected enrollment change rates using the Event Monitoring logs.

7. **Review checklist before go-live.** Run through every item in the Review Checklist below; do not mark the integration complete until all items pass.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Custom External ID fields exist on Contact, AcademicTermEnrollment, CourseOfferingParticipant, CourseOfferingPtcpResult, and LearnerProfile (where upsert is needed); all are marked Unique and External ID
- [ ] Upsert job sequence enforces parent-before-child ordering: Contact → AcademicTermEnrollment → CourseOfferingParticipant → CourseOfferingPtcpResult
- [ ] Watermark timestamp is persisted in durable state after each successful batch run; incremental loads use the watermark
- [ ] Bulk API 2.0 is used for loads of more than 500 records per object per run (not REST single-record operations)
- [ ] Failed-record error logs are captured and surfaced to the integration operations team; a retry mechanism exists
- [ ] CDC is enabled on AcademicTermEnrollment (if writeback is required) and the middleware subscriber handles the 72-hour replay window
- [ ] `LearnerProfile.ContactId` is set only on insert (master-detail); update operations do not attempt to reassign this field
- [ ] Integration user has the minimum required object and field permissions; FLS blocks are tested, not assumed
- [ ] FERPA-sensitive fields (e.g., grades in CourseOfferingPtcpResult) are not written to non-Education-Cloud objects or exposed in integration logs

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **LearnerProfile.ContactId is a create-only master-detail field.** Once a LearnerProfile is created, its `ContactId` cannot be updated via API. Attempting to upsert a LearnerProfile and change `ContactId` throws `FIELD_INTEGRITY_EXCEPTION`. If a student's Contact is merged or the SIS identifier changes, the old LearnerProfile must be deleted and re-created, not updated.

2. **LearnerProfile.StudentIdNumber is not an External ID.** Despite being the obvious field for storing a SIS identifier, `StudentIdNumber` is a plain Text field without External ID or Unique attributes. Upserting LearnerProfile by this field throws `INVALID_FIELD` in the Bulk API. A custom External ID field is required.

3. **AcademicTermEnrollment.EnrollmentStatus uses a restricted picklist.** Values not in the allowed set (Active, Dropout, Expelled, Graduated, No show, Other, Transferred, Withdrawn) cause `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST` errors in bulk loads. SIS enrollment status codes must be mapped to these canonical values before the upsert — a pass-through mapping of the SIS raw status string will fail.

4. **Bulk API 2.0 processes records within a job in arbitrary order.** If a single Bulk API 2.0 job contains both a parent AcademicTermEnrollment record and its child CourseOfferingParticipant records, the parent is not guaranteed to be processed before the child. Split parents and children into separate sequential jobs; never mix parent and child records in the same upsert job.

5. **CDC events do not include field values for unchanged fields.** When consuming a `AcademicTermEnrollmentChangeEvent`, only fields present in `changedFields` have updated values. Reading `EnrollmentStatus` from the payload when it is not in `changedFields` returns null, not the current value. Middleware must either store prior state or make a follow-up SOQL query to get the full current record state.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| External ID field design document | Field names, types, and encoding logic for SIS identifiers on each Education Cloud object |
| Upsert job sequence diagram | Ordered list of Bulk API 2.0 jobs with dependencies, error handling, and retry logic |
| Watermark persistence design | Middleware storage location and field used for incremental load watermark |
| CDC subscriber design | CometD topic subscription configuration, change event filter, SIS writeback API call pattern |
| Go-live review checklist | Completed checklist from the Review Checklist section above |

---

## Related Skills

- ferpa-compliance-in-salesforce — when the SIS integration involves student academic records, FERPA compliance controls on LearnerProfile and ContactPointTypeConsent must be reviewed alongside the integration design
- data/sharing-recalculation-performance — large-volume SIS loads often trigger sharing recalculation; review performance implications when record ownership or sharing rules are modified as part of the sync
