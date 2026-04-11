# Gotchas — Patient Data Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Shield Platform Encryption Must Be Configured Before First Data Load

**What happens:** PHI loaded before Shield Platform Encryption is enabled on a field is stored in the platform's unencrypted column. Enabling encryption after the fact triggers a background re-index job that encrypts values in the primary object table, but field history tracking entries, Chatter feed items, and audit log snapshots created during the pre-encryption window retain the plaintext value. Salesforce does not retroactively redact or re-encrypt these secondary stores.

**When it occurs:** Any org where the migration team activates Shield encryption partway through the project (e.g., enables it after a successful pilot load of a subset of patients).

**How to avoid:** Add Shield Platform Encryption configuration to the pre-flight checklist and treat it as a hard gate: no PHI data load until encryption is confirmed active on all relevant fields (BirthDate, SSN, diagnosis codes, medication names, and any custom PHI fields). Verify with `EncryptionScheme` metadata queries before submitting the first Bulk API 2.0 job.

---

## Gotcha 2: Platform-Generated Engagement History Cannot Be Bulk-Imported

**What happens:** Health Cloud's engagement engine auto-generates engagement history records when care plan actions are executed, care gaps are closed, or outreach tasks are completed through the platform. These are system-managed records with no writable DML surface. Attempting to import them via Bulk API 2.0 or Data Loader returns a permission error or produces a no-op. The absence of pre-migration engagement history in the imported data is expected behavior, not a migration defect.

**When it occurs:** When the migration scope document includes "engagement history" or "patient outreach history" from the source EMR without distinguishing between data records (importable) and platform audit records (system-generated, not importable).

**How to avoid:** During scoping, explicitly classify each source object as "data record" (can import) vs. "system-generated event" (cannot import). Document the gap in the migration runbook. Set stakeholder expectations that Health Cloud engagement history will start from the go-live date, not the historical EMR date.

---

## Gotcha 3: CarePlanTask References CarePlanGoal, Not CarePlan

**What happens:** The `CarePlanTask` object has a required lookup to `CarePlanGoal`, not a direct lookup to `CarePlan`. Practitioners who build their data model from the care plan hierarchy often assume Task → Plan, but the correct relationship is Task → Goal → Plan. Loading `CarePlanTask` records before `CarePlanGoal` records are committed, or providing a `CarePlan` ID where a `CarePlanGoal` ID is required, produces unresolvable lookup failures. In Bulk API 2.0 these appear as failed records in the results file with a cryptic field validation error, not an obvious schema message.

**When it occurs:** During Phase 3 care object loads when the team runs Goal and Task in the same batch job, or when the field mapping document incorrectly maps the parent reference to CarePlan.

**How to avoid:** Load in strict sub-phase order within Phase 3: CarePlan → CarePlanProblem + CarePlanGoal (parallel) → CarePlanTask. Verify the `CarePlanGoal` lookup field name in the CarePlanTask schema before building the CSV. Use `CarePlanGoal.Goal_Ext_ID__c` as the relationship resolver in the CarePlanTask CSV.

---

## Gotcha 4: Duplicate Person Accounts Are Not Reliably Caught on Bulk Loads

**What happens:** Standard Duplicate Rules (Match Rules configured in Setup) are evaluated during standard DML operations but can be bypassed by Bulk API 2.0 when the duplicate rule's "Action on Insert" is set to "Allow" (warn only) or when the rule does not target the `Patient` record type specifically. This means that running the migration twice (e.g., after a partial failure) without deduplication logic can create duplicate Person Accounts with identical EMR_Patient_ID__c values — unless Upsert is used.

**When it occurs:** When a team switches from Upsert to Insert mid-migration (e.g., after clearing the table and restarting), or when the External ID field is not populated on all records.

**How to avoid:** Always use Bulk API 2.0 Upsert for Person Accounts with `EMR_Patient_ID__c` as the external ID. After every load phase, run a SOQL aggregate query to detect duplicates: `SELECT EMR_Patient_ID__c, COUNT(Id) cnt FROM Account WHERE RecordType.DeveloperName = 'Patient' GROUP BY EMR_Patient_ID__c HAVING COUNT(Id) > 1`.

---

## Gotcha 5: Sandbox Data Mask Must Be Applied Before Loading PHI for Testing

**What happens:** Development and QA sandboxes are frequently shared among team members who are not covered under the HIPAA BAA. Loading production PHI (even a small "representative" patient set) into an unmasked sandbox exposes real patient data to unauthorized personnel. This is a HIPAA violation regardless of the organization's internal access controls, because the sandbox environment itself may be outside the BAA scope.

**When it occurs:** When the migration team wants to test the load pipeline with "real data" to verify field mappings, and applies Salesforce Data Mask only to production — not to every sandbox in the pipeline.

**How to avoid:** Apply Salesforce Data Mask (or an equivalent masking tool) to every sandbox before any PHI is introduced. Use synthetic patient data (generated fixtures that match the schema but contain no real patient identifiers) for all early-stage pipeline testing. Reserve PHI loads for the final production migration window only.
