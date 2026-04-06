# LLM Anti-Patterns — SIS Integration Patterns

Common mistakes AI coding assistants make when generating or advising on SIS integration patterns with Salesforce Education Cloud. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using LearnerProfile.StudentIdNumber as the Upsert External ID Key

**What the LLM generates:**
```
// Bulk API 2.0 job config
externalIdFieldName: StudentIdNumber
```
Or in REST: `PATCH /services/data/v64.0/sobjects/LearnerProfile/StudentIdNumber/{sisId}`

**Why it happens:** LLMs pattern-match on field name semantics. `StudentIdNumber` is semantically the "ID from the SIS" and is the field explicitly described in documentation as "The identifier issued to the learner by the institution." LLMs infer it is suitable as an upsert key without checking whether it carries the External ID attribute.

**Correct pattern:**
```
// Correct: custom External ID field required
externalIdFieldName: SIS_LearnerProfile_ID__c
// This custom field must be created with External ID + Unique attributes in Setup
```

**Detection hint:** Any generated code or configuration that references `StudentIdNumber` as an `externalIdFieldName` parameter or in a REST upsert URL is wrong.

---

## Anti-Pattern 2: Mixing Parent and Child Objects in the Same Bulk API 2.0 Job

**What the LLM generates:**
```python
# "Efficient" single-job load of AcademicTermEnrollment and CourseOfferingParticipant
records = enrollment_records + participant_records
bulk_job.upload(records)
```
Or advice like: "You can load both objects in one job to reduce job overhead."

**Why it happens:** LLMs optimize for reducing code complexity and API call count. The constraint that Bulk API 2.0 does not guarantee intra-job ordering is a non-obvious platform behavior not present in general ETL training data. LLMs default to single-job patterns familiar from relational database bulk loaders.

**Correct pattern:**
```python
# Correct: separate sequential jobs with status check between them
job1 = submit_bulk_upsert(enrollment_records, "AcademicTermEnrollment__c", "SIS_Enrollment_Key__c")
wait_for_job_complete(job1)  # poll GET /jobs/ingest/{jobId} until state == JobComplete
assert_zero_failures(job1)
job2 = submit_bulk_upsert(participant_records, "CourseOfferingParticipant", "SIS_CourseParticipant_Key__c")
wait_for_job_complete(job2)
```

**Detection hint:** Generated code that submits multiple Education Cloud objects in one Bulk API 2.0 job or submits parent and child jobs without a `wait_for_completion` barrier between them.

---

## Anti-Pattern 3: Reading All Fields from a CDC Change Event Without Checking changedFields

**What the LLM generates:**
```java
// Middleware subscriber — reads EnrollmentStatus from every event
EnrollmentStatus status = event.getEnrollmentStatus(); // null if not changed
sisClient.updateEnrollmentStatus(studentId, status);   // writes null to SIS
```

**Why it happens:** LLMs model CDC events as full-record snapshots because most event-driven training examples (Kafka, SQS, Pub/Sub) include the full object state in the payload. The Salesforce CDC partial-payload behavior is a platform-specific constraint that LLMs do not reliably reproduce.

**Correct pattern:**
```java
// Correct: check changedFields before reading EnrollmentStatus
List<String> changed = event.getChangedFields();
if (changed.contains("EnrollmentStatus")) {
    String status = event.getEnrollmentStatus();
    sisClient.updateEnrollmentStatus(studentId, status);
} else {
    // EnrollmentStatus did not change in this event; no SIS writeback needed
}
```

**Detection hint:** Generated CDC subscriber code that reads Education Cloud field values without first checking the `changedFields` list.

---

## Anti-Pattern 4: Using REST Single-Record DML for Large Nightly Batch Loads

**What the LLM generates:**
```apex
// Loop over all 50,000 enrollment records and upsert one at a time
for (EnrollmentRow row : sisExport) {
    Http http = new Http();
    HttpRequest req = new HttpRequest();
    req.setEndpoint('/services/data/v64.0/sobjects/AcademicTermEnrollment__c/SIS_Enrollment_Key__c/' + row.key);
    req.setMethod('PATCH');
    req.setBody(JSON.serialize(row.toSObject()));
    http.send(req);
}
```
Or equivalently: advice to use REST Composite for a 50,000-record nightly load.

**Why it happens:** LLMs are heavily trained on REST API examples and tend to generate REST-based solutions by default. The Bulk API 2.0 is less frequently illustrated in training data. LLMs do not reliably surface the 24-hour per-org REST API call limit (150,000 calls/day for standard editions) or the 10,000 Apex DML rows-per-transaction limit.

**Correct pattern:**
```
Use Bulk API 2.0 for any nightly batch load exceeding ~500 records per object.
Bulk API 2.0 endpoint: POST /services/data/v64.0/jobs/ingest/
Each job supports up to 150 MB of CSV data (~15 million fields).
No per-record API call count impact; only contributes to the daily Bulk API
characters-processed limit (10 GB/day by default).
```

**Detection hint:** Generated code that calls a REST or Apex DML endpoint in a loop over more than 200 records for a SIS object.

---

## Anti-Pattern 5: Setting LearnerProfile.ContactId in Update Payloads

**What the LLM generates:**
```json
// PATCH /sobjects/LearnerProfile__c/SIS_LearnerProfile_ID__c/LP-12345
{
  "ContactId": "003XXXXXXXXXXXXXXX",
  "Major": "Computer Science",
  "EnrollmentStatus": "Active"
}
```

**Why it happens:** LLMs treat master-detail relationship fields as updatable lookup fields, which is the default behavior for lookup fields in Salesforce. The immutability of master-detail fields after record creation is an exception to the general pattern. LLMs often include all fields from the source object in update payloads without distinguishing create-only fields.

**Correct pattern:**
```json
// Correct: omit ContactId from update payloads; include only on initial insert
// For upserts where the record may already exist, either:
// Option A: always omit ContactId (Salesforce ignores null on update if not provided)
{
  "Major": "Computer Science",
  "EnrollmentStatus": "Active"
}
// Option B: split insert and update into separate operations using a pre-check query
```

**Detection hint:** Any generated upsert payload for `LearnerProfile` that includes `ContactId` as a field. On the initial insert this is required; on updates it must be absent.

---

## Anti-Pattern 6: Generating SIS Status Mappings That Pass Raw Codes to EnrollmentStatus

**What the LLM generates:**
```python
# "Simple" mapping — pass SIS code directly
enrollment.EnrollmentStatus = sis_row["STST_CODE"]  # e.g., "EW", "WD", "GRD"
```

**Why it happens:** LLMs do not reliably know which Salesforce picklist fields are restricted vs. unrestricted. They generate pass-through mappings that work in unrestricted picklist fields. `EnrollmentStatus` on `AcademicTermEnrollment` is a restricted picklist, meaning only the eight canonical values are allowed. Raw SIS status codes that do not match exactly cause `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST` row-level failures in Bulk API 2.0.

**Correct pattern:**
```python
STATUS_MAP = {
    "EW": "Active", "EN": "Active", "ENR": "Active",
    "WD": "Withdrawn", "WIT": "Withdrawn",
    "GR": "Graduated", "GRD": "Graduated",
    "XF": "Expelled",
    "NS": "No show",
    "TR": "Transferred", "TRO": "Transferred",
    "DP": "Dropout",
}
enrollment.EnrollmentStatus = STATUS_MAP.get(sis_row["STST_CODE"], "Other")
```

**Detection hint:** Generated transformation code that directly assigns SIS status codes to `EnrollmentStatus` without a lookup or mapping step.
