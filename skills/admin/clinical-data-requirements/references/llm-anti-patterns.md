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

## Anti-Pattern 3: Using Legacy or Invented EHR Object Names

**What the LLM generates:** Integration code targeting `HC24__EhrCondition__c` for a new org, or "replacement" objects that do not exist, such as `PatientMedication`, `MedicalProcedure`, `HC24__EhrMedication__c`, or `HC24__EhrLabResult__c`.

**Why it happens:** Pre-Spring '23 tutorials use the packaged objects, and plausible names fill the gaps.

**Correct pattern:** New customers cannot create records in packaged EHR objects that have standard counterparts. Target `HealthCondition`, `MedicationStatement`, `MedicationRequest`, `PatientMedicalProcedure`, `CareObservation`, `PatientImmunization`, and `AllergyIntolerance`. Confirm every object name against the guide or a describe call.

**Detection hint:** Any `HC24__` object in new integration code, or an object name that a describe call does not return.

---

## Anti-Pattern 4: Treating HL7 v2 as Either Unsupported or Native

**What the LLM generates:** Either "Salesforce cannot store HL7 v2 data at all," or "send the ADT message to Salesforce and it will be parsed."

**Why it happens:** The model knows Salesforce speaks REST and JSON, and does not know the clinical data model documents HL7 v2.3 segment mappings.

**Correct pattern:** The guide documents mappings for ADT, ORM, ORU, MDM, VXU, and RDE (HL7 v2.3) segments to standard object fields, and states that a middleware integration solution is required to convert HL7 and FHIR messages. Put a translation layer in front of Salesforce that parses messages and writes the mapped fields.

**Detection hint:** HL7 v2 messages sent straight to the REST API, or a design that discards HL7 v2 sources as unsupported.

---

## Anti-Pattern 5: Overstating What the Org Pref Gates

**What the LLM generates:** "Without FHIR R4 Support Settings, all clinical objects including CareObservation are inaccessible, and the activation is irreversible."

**Why it happens:** The model generalizes from the objects that do need the pref, and adds an irreversibility claim that is not in the guide.

**Correct pattern:** The guide lists objects that need the FHIR-Aligned Clinical Data Model org pref (for example `HealthCondition`, `ClinicalEncounter`, `MedicationRequest`) and objects that do not (for example `CareObservation`, `CodeSet`, `CodeSetBundle`, `PersonName`). Enable the pref first, list what it unlocks, and treat reversibility as a question to confirm, not a fact.

**Detection hint:** `CareObservation` described as gated by the pref, or "irreversible" stated without a source.

---

## Anti-Pattern 6: Mapping `condition.code` as Optional

**What the LLM generates:** A middleware mapping that sends conditions without a code, because `condition.code` is 0..1 in FHIR.

**Why it happens:** The model maps cardinality straight from the FHIR specification.

**Correct pattern:** `HealthCondition.ConditionCodeId` (a lookup to `CodeSetBundle`) is one-to-one in Salesforce. Build the `CodeSet` and `CodeSetBundle` first, and define a rule for code-less source records.

**Detection hint:** A condition mapping with no rule for missing codes.

---

## Anti-Pattern 7: Calling the Portal Requirement an Org Setting

**What the LLM generates:** "Enable FHIR R4 for Experience Cloud in Setup so patients can see their conditions."

**Why it happens:** Many Health Cloud features are org settings, so the model assumes this one is too.

**Correct pattern:** Community users need the FHIR R4 for Experience Cloud Sites permission set to use clinical data model objects on a site. Pair it with sharing for the records each patient may see.

**Detection hint:** Portal designs that name an org setting instead of the permission set.
