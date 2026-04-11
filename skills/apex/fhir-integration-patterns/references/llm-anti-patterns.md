# LLM Anti-Patterns — FHIR Integration Patterns

Common mistakes AI coding assistants make when generating or advising on FHIR integration patterns.

## Anti-Pattern 1: Designing Salesforce as a Native CDS Hooks Service

**What the LLM generates:** Integration architecture where Salesforce's FHIR Healthcare API endpoint is registered directly as a CDS Hooks service in the EHR, without MuleSoft middleware.

**Why it happens:** LLMs know Salesforce supports FHIR R4 and know that CDS Hooks is a FHIR-related standard. The logical (but incorrect) inference is that Salesforce can natively serve CDS Hook responses.

**Correct pattern:**
CDS Hooks requires MuleSoft (or equivalent middleware) as the HTTP service endpoint. MuleSoft receives the CDS Hook POST from the EHR, queries Salesforce for relevant clinical alerts or care gaps, and assembles the CDS card JSON response. Salesforce has no native CDS Hook handler.

**Detection hint:** If the CDS Hooks architecture shows the EHR calling Salesforce's FHIR Healthcare API directly as the CDS service endpoint without a middleware layer, the architecture is incorrect.

---

## Anti-Pattern 2: Assuming 1:1 FHIR Spec Compliance for All Fields

**What the LLM generates:** FHIR-to-Salesforce field mapping code that assumes every FHIR field has a direct Salesforce equivalent with the same cardinality and format, without consulting the official Salesforce FHIR R4 mapping guide.

**Why it happens:** FHIR R4 field names and Salesforce object field names are often similar or identical in naming conventions. LLMs map them 1:1 without knowing the deliberate deviations (complex type flattening, CodeableConcept cardinality caps, mandatory field differences).

**Correct pattern:**
Every field mapping must be verified against the Salesforce FHIR R4 to Salesforce Standard Objects mapping guide. Key deviations: FHIR Period → multiple Salesforce date fields; FHIR CodeableConcept 0:many → Salesforce single CodeSet lookup (max 15 on CodeSetBundle); FHIR Patient.name → PersonName child object.

**Detection hint:** If the mapping code maps FHIR Period type fields to a single Salesforce DateTime field, or maps FHIR Patient.name directly to Account.Name, the deviations from spec are not being handled.

---

## Anti-Pattern 3: Targeting HC24__ EHR Objects for FHIR Integration

**What the LLM generates:** Integration code that creates HC24__EhrCondition__c, HC24__EhrMedication__c, or other legacy managed-package EHR objects as the target for inbound FHIR clinical data.

**Why it happens:** Legacy HC24__ EHR objects appear prominently in pre-Spring '23 Health Cloud documentation and community content. LLMs trained on this content recommend them as the target for clinical data storage.

**Correct pattern:**
Spring '23+ orgs cannot write to HC24__ EHR objects where standard FHIR R4-aligned objects exist. Target: HealthCondition (conditions), PatientMedication (medications), MedicalProcedure (procedures), CareObservation (lab results/observations). Always check the target org's provisioning date and use current FHIR R4 mapping documentation.

**Detection hint:** If integration code targets objects with the `HC24__` namespace prefix for clinical data that has a FHIR R4-aligned counterpart, legacy objects are being used incorrectly.

---

## Anti-Pattern 4: Skipping Middleware for Raw FHIR Bundle Ingest

**What the LLM generates:** Integration designs that send raw FHIR R4 bundle JSON directly from the EHR to Salesforce's FHIR Healthcare API, assuming Salesforce can store the bundle as-is.

**Why it happens:** Salesforce has a FHIR Healthcare API that accepts FHIR R4 format. LLMs infer that the API can store raw FHIR bundles without transformation. The platform's non-conformant deviations (complex type flattening, cardinality differences) are not visible in the API endpoint URL.

**Correct pattern:**
Middleware is always required for inbound FHIR bundles. The middleware must: flatten FHIR complex types (Period, Quantity, Range), normalize CodeableConcept codings (max 15 per CodeSetBundle), map FHIR identifiers to Salesforce record IDs, and handle FHIR fields that are optional in the spec but required in Salesforce.

**Detection hint:** If the integration design shows FHIR bundles going directly from EHR to Salesforce FHIR Healthcare API without a transformation middleware step, the normalization gap exists.

---

## Anti-Pattern 5: Omitting Experience Cloud FHIR Permission Set for Portal Users

**What the LLM generates:** Patient portal permission configurations that assign standard Health Cloud permission sets but omit the "FHIR R4 for Experience Cloud" permission set required for portal users to access FHIR-aligned clinical objects.

**Why it happens:** The FHIR R4 for Experience Cloud permission set is an Experience Cloud-specific permission requirement that is additional to the base FHIR R4 permission. LLMs assign the base FHIR R4 permission without knowing the Experience Cloud-specific variant is also required.

**Correct pattern:**
Experience Cloud portal users need both the Experience Cloud for Health Cloud permission set AND the FHIR R4 for Experience Cloud permission set to view FHIR-aligned clinical data in the patient portal. The standard FHIR R4 permission set used by internal users is not sufficient for portal users.

**Detection hint:** If portal user permission configuration includes FHIR permissions but does not include "FHIR R4 for Experience Cloud" specifically, portal users will not be able to view FHIR clinical data.
