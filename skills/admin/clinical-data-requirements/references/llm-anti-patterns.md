# LLM Anti-Patterns — Clinical Data Requirements

Common mistakes AI coding assistants make when generating or advising on clinical data model requirements.

## Anti-Pattern 1: Treating Salesforce as a 1:1 FHIR R4 Implementation

**What the LLM generates:** FHIR integration designs that assume FHIR bundles can be sent directly to Salesforce and stored without transformation, or that Salesforce's FHIR R4 implementation exactly mirrors the HL7 FHIR R4 specification for all resources.

**Why it happens:** Salesforce markets FHIR R4 alignment prominently. LLMs interpret this as full spec conformance. The deliberate deviations (complex type flattening, cardinality caps, mandatory field differences) are implementation details not inferrable from product marketing.

**Correct pattern:**
A middleware layer is always required between the source FHIR system and Salesforce. The middleware must handle: complex type flattening, CodeableConcept truncation at 15 codings, field cardinality normalization, and identifier mapping. Do not design FHIR integrations that bypass middleware.

**Detection hint:** If the integration design shows FHIR bundles flowing directly from EHR to Salesforce without a transformation layer, the middleware requirement is missing.

---

## Anti-Pattern 2: Writing FHIR Patient Demographics to Account Fields

**What the LLM generates:** FHIR Patient resource mapping that writes Patient.name to Account.Name, Patient.telecom to Account.Phone, and Patient.address to Account.BillingAddress.

**Why it happens:** Account.Name and Account.Phone are the obvious field mappings for Patient.name and Patient.telecom in a standard Salesforce CRM model. LLMs apply this direct mapping without knowing the Health Cloud child-object model.

**Correct pattern:**
FHIR Patient demographics map to child objects: PersonName (name), ContactPointPhone/Email (telecom), ContactPointAddress (address). These must be created as child records linked to the Person Account. Writing directly to Account fields bypasses the Health Cloud data model and breaks clinical UI components.

**Detection hint:** If the FHIR Patient mapping writes name/telecom/address fields directly to Account/Contact fields without creating child objects, the Health Cloud data model is being bypassed.

---

## Anti-Pattern 3: Using Legacy HC24__ EHR Objects for New Integrations

**What the LLM generates:** Integration code targeting HC24__EhrCondition__c, HC24__EhrMedication__c, HC24__EhrProcedure__c, or HC24__EhrLabResult__c for new Health Cloud clinical data integrations.

**Why it happens:** Legacy managed-package EHR objects appear in pre-Spring '23 documentation and tutorials. LLMs trained on historical content recommend these objects without knowing about the write-lock applied in new orgs.

**Correct pattern:**
Target FHIR R4-aligned standard objects: HealthCondition (not HC24__EhrCondition__c), PatientMedication, MedicalProcedure, CareObservation. For new orgs (Spring '23+), HC24__ objects are read-only where standard counterparts exist. All new integrations must target standard objects.

**Detection hint:** If the integration code references objects with `HC24__` prefix for data that has a corresponding FHIR R4-aligned standard object, legacy objects are being targeted incorrectly.

---

## Anti-Pattern 4: Designing HL7 v2 Direct Integration Without Middleware

**What the LLM generates:** Integration architectures where HL7 v2 messages from an EHR are sent directly to Salesforce via REST or SOAP APIs, without a middleware translation layer.

**Why it happens:** LLMs know Salesforce supports REST and SOAP APIs and know that EHRs send HL7 v2 messages. The logical inference is that HL7 v2 can be sent to Salesforce directly. Salesforce's inability to natively parse HL7 v2 is not a general API knowledge fact.

**Correct pattern:**
HL7 v2 messages must be translated to FHIR R4 JSON by a middleware layer before storage in Salesforce clinical objects. Salesforce's FHIR Healthcare API accepts FHIR R4 JSON only — not HL7 v2. Middleware options include MuleSoft HL7 connector, Mirth Connect, Rhapsody, or custom FHIR translators.

**Detection hint:** If the HL7 integration design shows ADT or ORU messages going directly to Salesforce APIs without a translator, the middleware layer is missing.

---

## Anti-Pattern 5: Omitting FHIR R4 Support Settings Activation as a Prerequisite

**What the LLM generates:** Clinical data configuration instructions that begin with creating HealthCondition or CareObservation records without first noting that FHIR R4 Support Settings must be enabled.

**Why it happens:** Org preferences are administrative setup steps that LLMs often omit because they are not visible in object schemas or API documentation. FHIR R4 Support Settings is a critical prerequisite that must be completed before any FHIR-aligned clinical object is accessible.

**Correct pattern:**
The first step in any clinical data model configuration is to enable the FHIR-Aligned Clinical Data Model in Setup > FHIR R4 Support Settings. Without this, all FHIR R4-aligned clinical objects are inaccessible. This activation is irreversible once enabled — document the decision before proceeding.

**Detection hint:** If clinical data model configuration steps begin without mentioning FHIR R4 Support Settings activation, the activation prerequisite is missing.
