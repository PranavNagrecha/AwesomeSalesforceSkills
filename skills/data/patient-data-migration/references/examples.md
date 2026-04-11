# Examples — Patient Data Migration

## Example 1: Migrating EMR Patient Records as Person Accounts

**Context:** A health system is migrating 250,000 patient records from an Epic EMR to Salesforce Health Cloud. Each source record has a stable MRN (Medical Record Number). The target org has Person Accounts enabled and the `Patient` record type deployed.

**Problem:** Without a stable External ID, re-running the migration (due to partial failures) inserts duplicate Person Accounts. Without the correct record type assignment, Health Cloud's patient card and clinical summary components do not render.

**Solution:**

```csv
# patients.csv — Bulk API 2.0 Upsert, ExternalIdFieldName = EMR_Patient_ID__c
EMR_Patient_ID__c,FirstName,LastName,PersonBirthdate,RecordTypeId
MRN-001234,Jane,Doe,1975-03-22,0124x000000XXXXX
MRN-001235,John,Smith,1982-11-09,0124x000000XXXXX
```

Bulk API 2.0 job configuration:
```json
{
  "object": "Account",
  "operation": "upsert",
  "externalIdFieldName": "EMR_Patient_ID__c",
  "contentType": "CSV",
  "lineEnding": "CRLF"
}
```

Post-load verification SOQL:
```soql
SELECT COUNT()
FROM Account
WHERE RecordType.DeveloperName = 'Patient'
  AND EMR_Patient_ID__c != null
```

**Why it works:** Upsert with External ID makes the operation idempotent — re-running the same CSV updates existing records rather than inserting duplicates. `RecordTypeId` must be the 18-character ID for the `Patient` record type in the target org; query `RecordType` beforehand to get the correct ID per environment.

---

## Example 2: Migrating Clinical Medication History

**Context:** After Person Accounts are loaded, the team needs to migrate 1.4 million `EhrPatientMedication` records that reference each patient by MRN.

**Problem:** The source export has the EMR patient ID, not the Salesforce Account ID. Building a mapping table of 250,000 ID pairs and joining them into the CSV is brittle and environment-specific (IDs differ between sandbox and production).

**Solution:**

Use Bulk API 2.0's relationship-by-external-ID to avoid the ID mapping entirely:

```csv
# medications.csv — Bulk API 2.0 Insert
Account.EMR_Patient_ID__c,Name,MedicationName__c,StartDate__c,Status__c
MRN-001234,Metformin 500mg,Metformin,2023-01-15,Active
MRN-001234,Lisinopril 10mg,Lisinopril,2022-06-01,Active
MRN-001235,Atorvastatin 20mg,Atorvastatin,2021-09-10,Discontinued
```

The column header `Account.EMR_Patient_ID__c` tells Bulk API 2.0 to resolve `AccountId` by looking up `Account` where `EMR_Patient_ID__c` matches the supplied value. No Salesforce ID mapping table needed.

Post-load orphan check:
```soql
SELECT COUNT()
FROM EhrPatientMedication
WHERE AccountId = null
```

**Why it works:** Bulk API 2.0 supports polymorphic relationship-by-external-ID lookups natively. This pattern works identically in sandbox and production because it resolves via the external ID, not environment-specific record IDs. Any record whose MRN does not match a loaded Person Account will land in the failed results file — surfacing the gap explicitly rather than silently nulling the lookup.

---

## Example 3: Migrating Care Plans with Historical Dates

**Context:** The source system has active and closed care plans going back several years. The team needs to migrate both open plans and historical (closed) plans to preserve the patient's longitudinal record.

**Problem:** Teams sometimes assume that importing a CarePlan with a `StartDate` in the past will fail validation or trigger platform re-computation. They may also attempt to import platform-generated engagement events alongside the care plan record, which fails silently.

**Solution:**

```csv
# careplans.csv — Bulk API 2.0 Insert
CarePlan_Ext_ID__c,Account.EMR_Patient_ID__c,Name,StartDate,Status
CP-001,MRN-001234,Diabetes Management Plan,2022-03-01,Active
CP-002,MRN-001234,Post-Op Recovery Plan,2021-06-15,Completed
CP-003,MRN-001235,Hypertension Management,2023-09-01,Active
```

After CarePlan is loaded:
```csv
# careplan_goals.csv — Bulk API 2.0 Insert after careplans.csv job is JobComplete
Goal_Ext_ID__c,CarePlan.CarePlan_Ext_ID__c,Name,StartDate,TargetDate,Status
GOAL-001,CP-001,HbA1c below 7.0,2022-03-01,2022-09-01,Completed
GOAL-002,CP-001,Weight reduction 10 lbs,2022-03-01,2022-12-01,Active
```

**Why it works:** CarePlan accepts past `StartDate` and `EndDate` values. Historical plans migrate cleanly as data records. Platform-generated engagement logs (e.g., Care Plan Engagement History created by the engagement engine) are system-owned and cannot be replicated — they are expected to be absent for migrated historical plans, and this gap should be documented in the migration runbook, not treated as a defect.

---

## Anti-Pattern: Loading Clinical Objects Before Person Accounts

**What practitioners do:** Run all object loads in parallel to save time, submitting Bulk API 2.0 jobs for EhrPatientMedication and PatientHealthCondition simultaneously with the Account (Person Account) job.

**What goes wrong:** The `AccountId` lookup on each clinical record is required and non-nullable. If the Person Account records are not yet committed when the clinical job executes, every clinical record fails with a lookup resolution error. Bulk API 2.0 places them in the failed results file. There is no automatic retry — the practitioner must re-submit the entire clinical batch after confirming Account insertion is complete.

**Correct approach:** Gate Phase 2 (clinical objects) on Phase 1 (Person Accounts) reaching `JobComplete` status with zero failed records. Use a polling loop on the Bulk API 2.0 job status endpoint before submitting Phase 2 batches.
