# Examples — FHIR Integration Patterns

## Example 1: Implementing Inbound FHIR R4 Patient Resource Mapping with Middleware

**Context:** An Epic EHR sends FHIR R4 Patient resources to Salesforce Health Cloud when patients are registered or their demographics are updated.

**Problem:** The initial integration design sends raw FHIR Patient JSON directly to the Salesforce SObject API without transformation. Patient names arrive in Salesforce as Account.Name concatenated strings, but the PatientCard component shows blank names because it reads from PersonName child records, not Account.Name.

**Solution:**
1. Add MuleSoft as middleware between Epic FHIR endpoint and Salesforce.
2. In MuleSoft, build the FHIR Patient to Salesforce mapping:
   - `Patient.name[0].given[0]` + `Patient.name[0].family` → Create PersonName record with `type = official`
   - `Patient.telecom[system=phone]` → Create ContactPointPhone record linked to Account
   - `Patient.telecom[system=email]` → Create ContactPointEmail record linked to Account
   - `Patient.address[0]` → Create ContactPointAddress record linked to Account
   - `Patient.birthDate` → Set `BirthDate` on Person Account
   - `Patient.gender` → Set `PersonGender` on Person Account
3. In MuleSoft: create Person Account first, then create all child contact point records using the new Account ID.
4. Test by viewing the patient in the Health Cloud clinical console — PatientCard should display name, phone, and address correctly.

**Why it works:** Health Cloud clinical UI components (PatientCard, Timeline) query child objects, not Account fields. The middleware correctly creates the child object records that these components expect.

---

## Example 2: CDS Hooks Architecture with MuleSoft

**Context:** A health system wants to display real-time clinical decision support alerts in Epic when a care coordinator opens a patient record that has open care gaps in Salesforce.

**Problem:** The team assumed Salesforce could be registered directly as a CDS Hooks service endpoint. Salesforce has no native CDS Hook service endpoint.

**Solution:**
1. Deploy a MuleSoft API as the CDS Hook service endpoint (e.g., `https://api.healthsystem.com/cds-services/care-gap-alerts`).
2. Register the MuleSoft endpoint in Epic's CDS Hooks registry with hook type `patient-view`.
3. When a clinician opens a patient chart, Epic sends a POST to the MuleSoft endpoint with the CDS Hook context (patient FHIR ID, user context, encounter context).
4. MuleSoft queries Salesforce: map the FHIR patient ID to a Salesforce Account ID, then query CareGap records where PatientId = [Account ID] and Status = 'Open'.
5. MuleSoft assembles CDS Hook card JSON with the care gap summary and a link to the Salesforce patient record.
6. MuleSoft returns the card JSON to Epic; Epic displays the card in the clinical workflow.

**Why it works:** MuleSoft correctly serves as the CDS Hook service. Salesforce provides the clinical data store and business logic. The two systems are decoupled through a well-defined API contract.

---

## Anti-Pattern: Using HC24__ EHR Objects for New FHIR Integration

**What practitioners do:** Build a FHIR R4 integration that creates HC24__EhrCondition__c records because the pre-Spring '23 documentation shows this as the target object for condition data.

**What goes wrong:** Spring '23+ Health Cloud orgs return an "insufficient privileges" or "read-only" error when attempting to write to HC24__EhrCondition__c where HealthCondition (a standard FHIR R4-aligned object) exists. The integration fails on first clinical record write.

**Correct approach:** Target FHIR R4-aligned standard objects for all new integrations: HealthCondition (not HC24__EhrCondition__c), PatientMedication, MedicalProcedure, CareObservation. Verify target objects against the current FHIR R4 mapping guide, not legacy documentation.
