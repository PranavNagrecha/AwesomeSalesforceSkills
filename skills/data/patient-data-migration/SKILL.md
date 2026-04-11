---
name: patient-data-migration
description: "Use this skill when migrating patient records into Salesforce Health Cloud, including Person Account (Patient record type) setup, clinical history objects, and care plan data. Trigger keywords: patient migration, EMR import, EHR to Health Cloud, clinical data load, care plan history migration, HIPAA-compliant data import. NOT for generic data migration, non-patient CRM data, or marketing cloud contact imports."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
triggers:
  - "How do I migrate patient records from an EMR into Salesforce Health Cloud?"
  - "What is the correct insert order for Health Cloud clinical objects during a bulk data migration?"
  - "How do I migrate care plan history into Health Cloud while staying HIPAA-compliant?"
  - "We need to import EhrPatientMedication and PatientHealthCondition records from our legacy EHR system — what is the right approach?"
  - "What Shield Platform Encryption and HIPAA controls do I need before loading PHI into Health Cloud?"
tags:
  - health-cloud
  - patient-migration
  - hipaa
  - clinical-data
  - care-plan
  - bulk-api
  - person-accounts
inputs:
  - Source system export (EMR/EHR) with patient demographics, clinical history, and care plan records
  - Salesforce Health Cloud org with Person Accounts and Patient record type enabled
  - HIPAA BAA in place with Salesforce
  - Shield Platform Encryption configuration completed on PHI fields before first data load
  - Field mapping document from source identifiers to Health Cloud object fields
outputs:
  - Ordered data load plan with object sequencing and dependency graph
  - Data mapping templates (CSV/JSON) per Health Cloud clinical and care object
  - HIPAA compliance checklist for the migration pipeline
  - Validation queries (SOQL) to verify load completeness and referential integrity
  - Checker script output flagging common configuration gaps
dependencies:
  - data/health-cloud-data-model
  - data/clinical-data-quality
  - data/consent-data-model-health
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Patient Data Migration

Use this skill when loading patient records, clinical history, and care plan data from an external EMR or EHR system into Salesforce Health Cloud. It covers the mandatory insert order, HIPAA compliance requirements for data-in-transit and at-rest, and the boundary between records that can be bulk-imported and system-generated data that cannot.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Person Accounts are enabled in the org and the `Patient` record type exists on the Account object. Without this, no clinical or care objects will resolve their `AccountId` lookup.
- Confirm Shield Platform Encryption is configured on PHI fields (date of birth, SSN, diagnosis codes, medication names) **before any data is loaded**. Encrypting after the fact requires a full re-index and may leave unencrypted values in audit logs.
- Confirm a signed HIPAA Business Associate Agreement (BAA) is on file with Salesforce. Loading live PHI into an org without a BAA is a HIPAA violation.
- Determine data volumes per object type. Clinical objects (EhrPatientMedication, PatientHealthCondition) can reach millions of rows for a single patient panel — Bulk API 2.0 is required, not REST or SOAP.
- Identify which fields are system-generated (platform engagement history, field audit trail entries). These cannot be imported and must be excluded from scope.

---

## Core Concepts

### Insert Order and AccountId Dependency

Every clinical and care object in Health Cloud carries a required `AccountId` lookup that must resolve to a Person Account with the Patient record type. The insert order is therefore non-negotiable:

1. **Person Accounts (Patient record type)** — must be loaded first. Use an External ID field (e.g., `EMR_Patient_ID__c`) to allow upserts and cross-reference from downstream objects.
2. **Clinical objects** — `EhrPatientMedication`, `PatientHealthCondition`, `PatientImmunization`, `PatientMedicalProcedure`. Each references `AccountId`. Load only after all Person Accounts are confirmed inserted.
3. **Care objects** — `CarePlan`, `CarePlanProblem`, `CarePlanGoal`, `CarePlanTask`. `CarePlan` references `AccountId`; `CarePlanProblem`, `CarePlanGoal`, and `CarePlanTask` reference the parent `CarePlan` record. Load `CarePlan` before loading child care objects.

Violating this order produces foreign-key failures that corrupt the entire batch.

### HIPAA Compliance Checklist for Migration

Four controls must be in place before any PHI enters the org:

| Control | Mechanism |
|---|---|
| Signed BAA | Salesforce contract with covered entity |
| Data at rest | Shield Platform Encryption on all PHI fields |
| Data in transit | TLS 1.2+ for all Bulk API 2.0 connections |
| Sandbox masking | Salesforce Data Mask (or equivalent) on all sandboxes used for testing |

Skipping sandbox masking exposes de-identified PHI to developers who lack HIPAA authorization — a common audit finding.

### What Can and Cannot Be Bulk-Imported

Not all historical data is importable as records:

- **Can import:** CarePlan records (including historical plans with past dates), clinical encounter data stored as sObject records, consent records.
- **Cannot import:** Platform-generated engagement history (automatically created by Health Cloud's engagement engine), field audit trail entries (system-generated, immutable, not writable via API), and process/flow execution logs. These are system-managed and have no writeable DML surface.

Attempting to import these produces permission errors or silent no-ops, and the historical gap is an expected outcome — not a migration defect.

---

## Common Patterns

### Pattern 1: Upsert-Based Patient Load with External ID

**When to use:** When migrating from an EMR that has its own stable patient identifiers (MRN, patient GUID) and you need to run migration incrementally or re-runnable.

**How it works:**
1. Add an External ID field `EMR_Patient_ID__c` (type: Text, External ID, Unique) to the Account object.
2. In the source export, include the EMR patient identifier as a column mapped to `EMR_Patient_ID__c`.
3. Use Bulk API 2.0 Upsert (not Insert) with `EMR_Patient_ID__c` as the external ID. This makes the load idempotent — re-running will update rather than duplicate.
4. In clinical object CSV files, reference `Account.EMR_Patient_ID__c` as the relationship field instead of the Salesforce record ID. Bulk API 2.0 supports relationship-by-external-ID lookups natively.

**Why not INSERT with Salesforce ID:** Source systems have no knowledge of Salesforce IDs before first load. Any mapping table that pre-loads IDs requires a query round-trip per record and breaks at scale.

### Pattern 2: Ordered Batch Pipeline for Full Migration

**When to use:** Initial full migration from an EMR, or when migrating an entire patient panel (e.g., practice acquisition).

**How it works:**
```
Phase 1: Load Person Accounts (Patient record type)
  - Input:  patients.csv  [EMR_Patient_ID__c, FirstName, LastName, BirthDate, ...]
  - Method: Bulk API 2.0 Upsert on EMR_Patient_ID__c
  - Gate:   All jobs = 'JobComplete', 0 failed records

Phase 2: Load Clinical Objects (parallel, all reference AccountId)
  - EhrPatientMedication.csv   → Bulk API 2.0 Insert
  - PatientHealthCondition.csv → Bulk API 2.0 Insert
  - PatientImmunization.csv    → Bulk API 2.0 Insert
  - PatientMedicalProcedure.csv → Bulk API 2.0 Insert
  - Method: relationship field Account.EMR_Patient_ID__c → AccountId

Phase 3: Load Care Objects (ordered within phase)
  - Step 3a: CarePlan.csv           → Bulk API 2.0 Insert (references AccountId)
  - Step 3b: CarePlanProblem.csv    → Insert (references CarePlan.CarePlan_Ext_ID__c)
  - Step 3c: CarePlanGoal.csv       → Insert (references CarePlan.CarePlan_Ext_ID__c)
  - Step 3d: CarePlanTask.csv       → Insert (references CarePlanGoal.Goal_Ext_ID__c)
```

**Why not all parallel:** CarePlanProblem, CarePlanGoal, and CarePlanTask reference their parent CarePlan. Loading them in the same batch as CarePlan produces unresolvable lookups in the same job.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Migrating 1–10M patient records from a single EMR | Bulk API 2.0 Upsert with External ID in ordered phases | Only API that handles volumes above 500K rows; upsert makes pipeline re-runnable |
| Migrating historical care plans with past start/end dates | Import as CarePlan data records with historical dates | CarePlan supports past dates; platform validates field format but not temporal sequence |
| Migrating engagement history (e.g., outreach event logs) | Exclude from scope; document the gap | Platform-generated engagement history is system-owned; no DML surface available |
| Testing migration logic in sandbox | Apply Salesforce Data Mask before loading any PHI | Sandbox environments are often shared; unmasked PHI is a HIPAA audit finding |
| Source has no stable patient identifier | Create a composite key (LastName + DOB + MRN) as External ID | Prevents duplicates on re-load; deterministic key survives system restarts |
| Shield Encryption not yet configured | Stop migration; configure encryption first | Encryption after load requires re-index; values already loaded will be unencrypted in logs |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Pre-flight compliance check** — Verify BAA is signed, Shield Platform Encryption is active on all PHI fields (AccountId-linked objects), TLS is enforced on all integration endpoints, and Data Mask is applied to target sandbox. Do not proceed until all four controls are confirmed.
2. **Inventory source data and map to Health Cloud objects** — Produce a field mapping document for each Health Cloud object in scope. Identify external IDs, required fields, and record type assignments. Flag any source fields that map to system-generated targets (audit trail, engagement history) and remove them from scope.
3. **Add External ID fields and record type configuration** — Create `EMR_Patient_ID__c` on Account, `CarePlan_Ext_ID__c` on CarePlan, and `Goal_Ext_ID__c` on CarePlanGoal (or equivalent per source system). Deploy to the target org before any data load.
4. **Load Person Accounts (Phase 1)** — Execute Bulk API 2.0 Upsert for patient records. Poll job status until `JobComplete`. Query `Account` for `RecordType.DeveloperName = 'Patient'` to confirm count matches source. Resolve all failed records before proceeding.
5. **Load clinical objects (Phase 2)** — Execute Bulk API 2.0 Insert for EhrPatientMedication, PatientHealthCondition, PatientImmunization, PatientMedicalProcedure in parallel (they share only the AccountId dependency, which is now satisfied). Use relationship-by-external-ID for AccountId. Verify row counts per object post-load.
6. **Load care objects (Phase 3, ordered)** — Insert CarePlan first, wait for job completion, then insert CarePlanProblem, CarePlanGoal (in parallel), then CarePlanTask. Verify parent-child counts with SOQL spot checks.
7. **Post-load validation** — Run SOQL queries to detect orphaned records (AccountId = null), duplicate person accounts, and missing required fields. Run `check_patient_data_migration.py` against the target org metadata. Confirm Health Cloud patient card renders records correctly for a sample patient.

---

## Review Checklist

Run through these before marking migration work complete:

- [ ] HIPAA BAA confirmed signed with Salesforce
- [ ] Shield Platform Encryption active on all PHI fields before first data load
- [ ] TLS enforced on all Bulk API 2.0 connections (pipeline configuration confirmed)
- [ ] Sandbox Data Mask applied before any PHI loaded into sandbox
- [ ] Person Accounts loaded and row count verified against source
- [ ] All clinical objects loaded with zero orphaned AccountId lookups
- [ ] CarePlan loaded before CarePlanProblem/Goal/Task
- [ ] Platform-generated engagement history and field audit trail excluded from scope (documented)
- [ ] External ID fields deployed and populated correctly
- [ ] Post-load SOQL validation queries run and passed

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Shield Encryption must precede data load, not follow it** — If PHI is loaded before Shield Platform Encryption is enabled on a field, the already-loaded values exist in the platform's unencrypted storage. Enabling encryption later triggers a re-index job, but historical audit log entries and feed items may retain plaintext values. There is no retroactive redaction of feed or log data.
2. **CarePlanTask references CarePlanGoal, not CarePlan directly** — A common mistake is loading CarePlanTask with a direct CarePlan reference. The correct parent is CarePlanGoal. Loading Task before Goal produces unresolvable lookups and silent failures in Bulk API 2.0 (records go to the failed results file, not an error log).
3. **Duplicate Person Accounts are not caught by standard duplicate rules on bulk loads** — Standard Duplicate Rules are evaluated per-record via the DML layer but can be bypassed with Bulk API 2.0 when "Allow Save" is configured, or when the duplicate rule does not apply to Person Account record types. Run a post-load deduplication query explicitly.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Ordered data load plan | Phase-by-phase sequencing of objects with dependency graph and gate conditions |
| Field mapping CSVs | Per-object column-to-field mapping documents with external ID annotations |
| HIPAA compliance checklist | Four-control checklist (BAA, Shield, TLS, Data Mask) with confirmation evidence |
| Post-load SOQL validation queries | Queries to detect orphaned records, duplicate patients, missing required fields |
| `check_patient_data_migration.py` output | Automated metadata scan for Shield encryption and External ID field presence |

---

## Related Skills

- data/health-cloud-data-model — Full Health Cloud object schema reference; consult before mapping source fields
- data/clinical-data-quality — Duplicate detection and data quality rules for clinical objects post-load
- data/consent-data-model-health — Consent record migration if source system includes patient authorization data
- admin/hipaa-compliance-architecture — Full HIPAA architectural controls for Health Cloud orgs
