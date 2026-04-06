# Gotchas — SIS Integration Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LearnerProfile.StudentIdNumber Is Not an External ID and Cannot Be an Upsert Key

**What happens:** Practitioners assume `LearnerProfile.StudentIdNumber` — the obvious standard field for storing a SIS-issued student identifier — can be used as the `externalIdFieldName` in a Bulk API 2.0 upsert job. The API returns `INVALID_FIELD: No such column 'StudentIdNumber' on sobject of type LearnerProfile` when this field name is specified as the external ID column.

**When it occurs:** Any time a Bulk API 2.0 or REST API upsert targets `LearnerProfile` and uses `StudentIdNumber` as the upsert key. The field does not have the `External ID` attribute set in the Education Cloud schema; only fields explicitly marked External ID in field metadata are eligible upsert keys.

**How to avoid:** Create a custom Text field on `LearnerProfile` (e.g., `SIS_LearnerProfile_ID__c`) and check both the `Unique` and `External ID` attributes. Populate this field with the same SIS student identifier stored in `StudentIdNumber`. Use the custom field as the upsert key. Keep `StudentIdNumber` populated as well — it is used by Education Cloud UI components and standard reports.

---

## Gotcha 2: LearnerProfile.ContactId Cannot Be Updated After Record Creation

**What happens:** `LearnerProfile.ContactId` is a master-detail relationship field. In Salesforce, master-detail relationship fields are create-only: once the child record is created, the master cannot be reassigned via API. Attempting to upsert a `LearnerProfile` record and include a different `ContactId` than the one used at creation throws `FIELD_INTEGRITY_EXCEPTION: LearnerProfile: Id value of incorrect type`.

**When it occurs:** When student records are merged in the SIS (e.g., two Banner PIDM records are consolidated into one) and the integration tries to update the LearnerProfile's contact linkage to reflect the merge. Also occurs if the integration mistakenly includes `ContactId` in the update payload of an existing record.

**How to avoid:** Treat `ContactId` as immutable after the initial insert. If a student Contact merge happens (either in Salesforce or the SIS), handle it as a delete-and-recreate of the `LearnerProfile`, not an update. Build Contact merge logic in the integration to detect this case and route it to a separate merge reconciliation process. Never include `ContactId` in the update payload of a LearnerProfile upsert — only include it on the initial insert path.

---

## Gotcha 3: AcademicTermEnrollment.EnrollmentStatus Is a Restricted Picklist — SIS Raw Codes Fail Silently in Bulk Jobs

**What happens:** `AcademicTermEnrollment.EnrollmentStatus` is a restricted picklist with exactly eight allowed values as documented in the Education Cloud Developer Guide v66.0: Active, Dropout, Expelled, Graduated, No show, Other, Transferred, Withdrawn. SIS platforms use their own enrollment status codes (Banner: EW, WD, GR; PeopleSoft: ENR, WIT, GRD; etc.). When a Bulk API 2.0 upsert job contains unmapped SIS status codes, those rows fail with `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST`. In a large nightly batch, these row-level errors appear only in the job result CSV and do not cause the overall job to fail — the job completes with a `numberRecordsFailed > 0` count that is easy to overlook if error monitoring is not in place.

**When it occurs:** Any time the SIS export contains a status code value that was not present during initial integration testing, such as a new institutional status added by the registrar. This is particularly common during transitions (e.g., COVID-era "Emergency Remote" status codes, new dual-enrollment statuses).

**How to avoid:** Implement an explicit SIS-to-Salesforce status mapping function in the middleware transformation layer that maps every known SIS code to one of the eight allowed values. Add a catch-all mapping to `Other` for unknown codes. Alert when a new unmapped code is encountered. Monitor `numberRecordsFailed` in every Bulk API 2.0 job completion callback and route any failed records to a dedicated error queue.

---

## Gotcha 4: CDC Change Events Do Not Carry Unchanged Field Values

**What happens:** When consuming `AcademicTermEnrollmentChangeEvent` via Change Data Capture, only fields listed in the event's `changedFields` array contain updated values in the payload. Fields not in `changedFields` are absent from the payload (or null in some SDK implementations). A middleware subscriber that reads `EnrollmentStatus` from every CDC event will receive null for that field when the enrollment record was updated but `EnrollmentStatus` itself did not change. This causes the middleware to either write a null status back to the SIS or throw a null-pointer error.

**When it occurs:** Any update to an `AcademicTermEnrollment` record that does not change `EnrollmentStatus` (e.g., updating `CumulativeGradePointAverage` or `HoursAttempted`) still fires a CDC event. The subscriber must check whether `EnrollmentStatus` is in `changedFields` before acting.

**How to avoid:** In the CDC subscriber, always check the `changedFields` array before reading any field value. Only trigger the SIS writeback when `EnrollmentStatus` is confirmed present in `changedFields`. If the full current record state is needed regardless, make a follow-up REST API call to retrieve the record by ID before calling the SIS update endpoint.

---

## Gotcha 5: Bulk API 2.0 Relationship References Require the Referenced Object's External ID to Already Exist

**What happens:** When using a relationship reference in a Bulk API 2.0 payload (e.g., `LearnerContact.SIS_Student_ID__c` to resolve the Contact ID), the referenced Contact record must already exist in Salesforce with a populated `SIS_Student_ID__c` value. If the Contact upsert job runs in the same nightly window but completes after the AcademicTermEnrollment job starts, the relationship reference resolution fails with `INVALID_CROSS_REFERENCE_KEY` for new students who were just created. The old/existing students succeed because their Contacts are already in Salesforce, masking the issue until the first new-student enrollment of the term.

**When it occurs:** New student cohort loads where Contacts and their AcademicTermEnrollment records are loaded in the same nightly batch window, and the middleware does not enforce strict job completion ordering.

**How to avoid:** Enforce sequential completion of the Contact upsert job (Job 1) before submitting the AcademicTermEnrollment job (Job 2). Poll the Bulk API 2.0 job status endpoint (`GET /services/data/v64.0/jobs/ingest/{jobId}`) until `state` equals `JobComplete` and `numberRecordsFailed` equals 0 before proceeding to the next job. Do not use time-based delays as a substitute for status polling.

---

## Gotcha 6: AcademicTermEnrollment and CourseOfferingParticipant Have IsLocked Fields That Block Updates

**What happens:** Both `AcademicTermEnrollment` and `CourseOfferingParticipant` have an `IsLocked` boolean field (default false). When `IsLocked = true`, the record cannot be modified via API or UI. Bulk API 2.0 upsert operations targeting locked records return `ENTITY_IS_LOCKED` errors. This is commonly encountered after a grading period closes — institutions may lock enrollment records to prevent retroactive changes.

**When it occurs:** When an end-of-term process (manual or automated) sets `IsLocked = true` on historical enrollment records, and a subsequent nightly sync job attempts to update those same records with corrected data from the SIS (e.g., retroactive grade corrections, administrative enrollment adjustments).

**How to avoid:** Filter the SIS export to exclude records whose corresponding Salesforce record has `IsLocked = true`, or implement a pre-check query that identifies locked records before submitting the upsert job. Route locked-record updates to a manual exception queue rather than failing the entire nightly batch.
