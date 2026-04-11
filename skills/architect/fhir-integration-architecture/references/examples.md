# Examples — FHIR Integration Architecture

## Example 1: Real-Time Medication List Display from Epic via Generic FHIR Client

**Scenario:** A care coordinator at a regional health system opens a patient record in Health Cloud. The patient's current medication list is managed in Epic and must be visible in real time without duplicating it into Salesforce.

**Problem:** Without the Generic FHIR Client pattern, architects default to a nightly batch sync that copies all Epic MedicationRequest resources into Health Cloud. By morning, the list is up to date — but if a medication is changed at 2pm, the care coordinator sees stale data for 18+ hours. Alternatively, some teams attempt to store raw FHIR JSON blobs in a Long Text field, which breaks reporting, search, and any downstream automation.

**Solution:**

```
Architecture topology:

Epic FHIR R4 endpoint (secured via OAuth 2.0)
  ↓
Health Cloud Named Credential → Generic FHIR Client configuration
  ↓
Lightning Web Component on Patient record page
  → On record load: invokes Apex controller that calls Generic FHIR Client
  → GET /MedicationRequest?patient={epicPatientId}&status=active
  → Response parsed in Apex; displayed in LWC data table
  → Critical alerts (high-risk meds) optionally written to a Health Cloud
    MedicationStatement record for audit trail
```

Named Credential setup points to the Epic FHIR base URL with OAuth 2.0 JWT bearer authentication. The Generic FHIR Client is configured in Health Cloud Setup under External EMR Settings, referencing the Named Credential. The LWC calls an Apex controller annotated with `@AuraEnabled` that uses the ExternalEMRClient API class to execute the FHIR query.

**Why it works:** The Generic FHIR Client delegates authentication and request routing to the Named Credential, keeping credentials out of Apex code. Data is always fetched live from the source of truth (Epic), eliminating stale copy problems. Only medically significant outlier data (high-risk medication flags) is selectively persisted to Health Cloud objects, keeping the data model clean.

---

## Example 2: ADT Event-Driven Ingestion via MuleSoft for Admission Notification

**Scenario:** A hospital uses Cerner as the EMR. When a patient is admitted, Health Cloud must create an Episode of Care record and enroll the patient in a high-acuity care program within 5 minutes. Cerner emits admission events as HL7 v2 ADT^A01 messages via HL7 MLLP.

**Problem:** A polling-based architecture (e.g., querying Cerner's FHIR Encounter endpoint every 15 minutes) cannot meet the 5-minute SLA. A custom Apex callout to Cerner is blocked by governor limits and requires a Scheduled Apex job, which can queue for up to 15 minutes under load. Attempting to accept raw HL7 v2 messages directly in Salesforce is not supported — there is no native HL7 parser.

**Solution:**

```
Architecture topology:

Cerner EMR
  → HL7 v2 ADT^A01 message via MLLP
  ↓
MuleSoft Accelerator for Healthcare — HL7 v2 Listener
  → Converts ADT^A01 to FHIR R4 Encounter + Patient resources
  → DataWeave transformation: FHIR Encounter → Health Cloud EpisodeOfCare fields
  → DataWeave transformation: FHIR Patient → Health Cloud Account/Contact fields
  ↓
Salesforce Composite REST API call (upsert by Cerner patient MRN as External ID)
  → Creates/updates Account (Patient), Contact, EpisodeOfCare records
  ↓
Platform Event published: PatientAdmission__e
  ↓
Flow triggered on PatientAdmission__e
  → Enrolls patient in High Acuity Care Program
  → Creates care coordinator Task
```

The MuleSoft Accelerator for Healthcare provides the HL7 v2 listener and the ADT-to-FHIR conversion DataWeave scripts for Cerner. Customization is limited to adding Health Cloud-specific field mappings in the DataWeave transform. The Salesforce Composite API call uses the patient MRN (Medical Record Number) as the external ID to ensure idempotent upserts even if the same ADT event is received twice.

**Why it works:** MuleSoft handles the HL7 v2 parsing (which Salesforce cannot do natively) and produces a clean FHIR R4 payload before the Health Cloud boundary. The Platform Event decouples the admission record creation from the downstream care program enrollment, so a failure in enrollment does not roll back the record creation. Idempotent upsert by MRN prevents duplicate patient records if Cerner resends events.

---

## Anti-Pattern: Persisting Raw FHIR Bundles in Long Text Fields

**What practitioners do:** To avoid building a transformation layer, teams store the full FHIR Bundle JSON response from an EMR as a Long Text Area field value on a Health Cloud record. They plan to parse it "later in Apex when needed."

**What goes wrong:** Long Text Area fields are not searchable, not reportable via standard SOQL field queries without LIKE, and cannot be used in Flows, list views, or analytics. Apex parsing logic ends up duplicated across every consumer of the data (LWC controllers, triggers, batch jobs). When the EMR changes a FHIR resource structure or adds a new profile, every piece of parsing logic breaks simultaneously and is hard to find. Health Cloud's clinical data model — including relationships, rollup fields, and care gap logic — cannot operate on data trapped in blob fields.

**Correct approach:** Design the transformation layer before implementation. Use MuleSoft Accelerator DataWeave scripts (or custom DataWeave/Apex) to map each FHIR resource to its target Health Cloud object and field at ingestion time. Store data in structured Health Cloud objects from the start. If the full FHIR payload must be preserved for audit, store it in a related `ExternalRecord__c` or equivalent archival object, not as the primary data store.
