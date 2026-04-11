# Patient Data Migration — Work Template

Use this template when migrating patient records, clinical history, or care plan data into Salesforce Health Cloud from an external EMR or EHR system.

## Scope

**Skill:** `patient-data-migration`

**Request summary:** (describe the migration request — source system, record types in scope, data volumes, target org)

**In scope:**
- [ ] Person Accounts (Patient record type)
- [ ] Clinical objects (EhrPatientMedication, PatientHealthCondition, PatientImmunization, PatientMedicalProcedure)
- [ ] Care objects (CarePlan, CarePlanProblem, CarePlanGoal, CarePlanTask)
- [ ] Consent records (if applicable — see data/consent-data-model-health)

**Out of scope (always):**
- Platform-generated engagement history (system-generated, not importable)
- Field audit trail entries (system-generated, immutable)
- Process/Flow execution logs

---

## HIPAA Pre-Flight Checklist

Complete all four before loading any data:

- [ ] **BAA signed** — Confirm HIPAA Business Associate Agreement is in place with Salesforce
- [ ] **Shield Platform Encryption active** — Confirm on all PHI fields (BirthDate, SSN, MRN, diagnosis codes, medication names, and custom PHI fields) in target org
- [ ] **TLS enforced** — Confirm Bulk API 2.0 pipeline uses TLS 1.2+ for all connections
- [ ] **Sandbox Data Mask applied** — Confirm Data Mask is active on all sandboxes receiving test data

Do not proceed past this section until all four items are checked.

---

## Context Gathered

- **Target org:** (sandbox name / production)
- **Person Account enabled:** Yes / No
- **Patient record type exists:** Yes / No (RecordTypeId: `_______________`)
- **External ID field on Account:** `EMR_Patient_ID__c` / (other: `_______________`)
- **External ID field on CarePlan:** `CarePlan_Ext_ID__c` / (other: `_______________`)
- **External ID field on CarePlanGoal:** `Goal_Ext_ID__c` / (other: `_______________`)
- **Data volumes:**
  - Person Accounts: _______ records
  - EhrPatientMedication: _______ records
  - PatientHealthCondition: _______ records
  - PatientImmunization: _______ records
  - PatientMedicalProcedure: _______ records
  - CarePlan: _______ records
  - CarePlanProblem: _______ records
  - CarePlanGoal: _______ records
  - CarePlanTask: _______ records

---

## Field Mapping Summary

| Health Cloud Object | Source Object | Key Mapped Fields | External ID Column |
|---|---|---|---|
| Account (Patient) | (e.g. Epic Patient) | FirstName, LastName, PersonBirthdate | EMR_Patient_ID__c |
| EhrPatientMedication | (e.g. Epic Medication) | MedicationName__c, StartDate__c, Status__c | Account.EMR_Patient_ID__c |
| PatientHealthCondition | (e.g. Epic Diagnosis) | ConditionCode__c, OnsetDate__c | Account.EMR_Patient_ID__c |
| PatientImmunization | (e.g. Epic Immunization) | VaccineName__c, AdministeredDate__c | Account.EMR_Patient_ID__c |
| PatientMedicalProcedure | (e.g. Epic Procedure) | ProcedureCode__c, ProcedureDate__c | Account.EMR_Patient_ID__c |
| CarePlan | (e.g. Epic Care Plan) | Name, StartDate, Status | CarePlan_Ext_ID__c, Account.EMR_Patient_ID__c |
| CarePlanGoal | (e.g. Epic Goal) | Name, StartDate, TargetDate, Status | Goal_Ext_ID__c, CarePlan.CarePlan_Ext_ID__c |
| CarePlanTask | (e.g. Epic Task) | Subject, Status, DueDate | CarePlanGoal.Goal_Ext_ID__c |

---

## Load Plan

### Phase 1 — Person Accounts

- **Operation:** Bulk API 2.0 Upsert
- **External ID:** `EMR_Patient_ID__c`
- **File:** `patients.csv`
- **Gate:** Job status = `JobComplete`, failed records = 0
- **Verification SOQL:**
  ```soql
  SELECT COUNT() FROM Account
  WHERE RecordType.DeveloperName = 'Patient'
    AND EMR_Patient_ID__c != null
  ```
- **Expected count:** _______ records

### Phase 2 — Clinical Objects (parallel, after Phase 1 gate passes)

- **Operation:** Bulk API 2.0 Insert (or Upsert if re-runnable load needed)
- **Files:** `medications.csv`, `conditions.csv`, `immunizations.csv`, `procedures.csv`
- **AccountId resolution:** `Account.EMR_Patient_ID__c`
- **Gate per job:** `JobComplete`, failed records = 0
- **Post-load orphan check SOQL:**
  ```soql
  SELECT COUNT() FROM EhrPatientMedication WHERE AccountId = null
  SELECT COUNT() FROM PatientHealthCondition WHERE AccountId = null
  ```

### Phase 3 — Care Objects (ordered)

**Step 3a — CarePlan** (after Phase 1 gate passes):
- **File:** `careplans.csv`
- **External ID:** `CarePlan_Ext_ID__c`
- **AccountId resolution:** `Account.EMR_Patient_ID__c`

**Step 3b — CarePlanProblem and CarePlanGoal** (parallel, after Step 3a gate passes):
- **Files:** `careplan_problems.csv`, `careplan_goals.csv`
- **Parent resolution:** `CarePlan.CarePlan_Ext_ID__c`

**Step 3c — CarePlanTask** (after Step 3b gate passes):
- **File:** `careplan_tasks.csv`
- **Parent resolution:** `CarePlanGoal.Goal_Ext_ID__c` (NOT CarePlan)

---

## Post-Load Validation Checklist

- [ ] Person Account count matches source system patient count
- [ ] No Person Accounts with null `EMR_Patient_ID__c`
- [ ] No duplicate Person Accounts (run dedup SOQL)
- [ ] No clinical records with null `AccountId`
- [ ] No CarePlan records with null `AccountId`
- [ ] No CarePlanTask records with null `CarePlanGoalId`
- [ ] Sample patient record renders correctly in Health Cloud patient card
- [ ] Shield Platform Encryption fields show masked values for unauthorized users
- [ ] `check_patient_data_migration.py` run against target org metadata — no warnings

Dedup check SOQL:
```soql
SELECT EMR_Patient_ID__c, COUNT(Id) cnt
FROM Account
WHERE RecordType.DeveloperName = 'Patient'
GROUP BY EMR_Patient_ID__c
HAVING COUNT(Id) > 1
```

---

## Notes and Deviations

(Record any deviations from the standard pattern and the reason for each.)

- **Engagement history gap:** Platform-generated engagement history prior to [go-live date] is not available in Health Cloud. Historical engagement data remains in source EMR for audit reference. This is expected — not a defect.

- **Other deviations:** (fill in)
