# LLM Anti-Patterns: FHIR Integration Patterns

Common mistakes AI coding assistants make when generating or advising on FHIR integration patterns.

## Anti-Pattern 1: Designing Salesforce as a Native CDS Hooks Service

**What the LLM generates:** Integration architecture where Salesforce's FHIR Healthcare API endpoint is registered directly as a CDS Hooks service in the EHR, without MuleSoft middleware.

**Why it happens:** LLMs know Salesforce supports FHIR R4 and know that CDS Hooks is a FHIR-related standard. The logical (but incorrect) inference is that Salesforce can natively serve CDS Hook responses.

**Correct pattern:**
CDS Hooks requires MuleSoft (or equivalent middleware) as the HTTP service endpoint. MuleSoft receives the CDS Hook POST from the EHR, queries Salesforce for relevant clinical alerts or care gaps, and assembles the CDS card JSON response. Salesforce documents CDS Hooks through a MuleSoft Direct Integration app (Healthcare API guide, "Explore MuleSoft Direct Integration Apps").

**Detection hint:** If the CDS Hooks architecture shows the EHR calling Salesforce's FHIR Healthcare API directly as the CDS service endpoint without a middleware layer, the architecture is incorrect.

---

## Anti-Pattern 2: Assuming 1:1 FHIR Spec Compliance for All Fields

**What the LLM generates:** FHIR-to-Salesforce field mapping code that assumes every FHIR field has a direct Salesforce equivalent with the same cardinality and format, without consulting the official Salesforce FHIR R4 mapping guide.

**Why it happens:** FHIR R4 field names and Salesforce object field names are often similar or identical in naming conventions. LLMs map them 1:1 without knowing the deliberate deviations (complex type flattening, CodeableConcept cardinality caps, mandatory field differences).

**Correct pattern:**
Every field mapping must be verified against "Mapping FHIR v4.0 to Salesforce Standard Objects" in the Health Cloud developer guide. Key deviations: FHIR Period maps to start and end date fields; FHIR CodeableConcept (0..* Coding) maps to CodeSetBundle with up to 15 CodeSet references; HumanName maps to the PersonName object; Condition.code is required (1..1) in Salesforce.

**Detection hint:** If the mapping code maps FHIR Period type fields to a single Salesforce DateTime field, or maps FHIR Patient.name directly to Account.Name, the deviations from spec are not being handled.

---

## Anti-Pattern 3: Targeting HC24__ EHR Objects for FHIR Integration

**What the LLM generates:** Integration code that creates HC24__EhrCondition__c, HC24__EhrMedication__c, or other legacy managed-package EHR objects as the target for inbound FHIR clinical data.

**Why it happens:** Legacy HC24__ EHR objects appear prominently in pre-Spring '23 Health Cloud documentation and community content. LLMs trained on this content recommend them as the target for clinical data storage.

**Correct pattern:**
Starting with Spring '23, new customers can't create records in packaged EHR objects that have counterpart standard objects. Target: HealthCondition (conditions), MedicationStatement or MedicationRequest (medications), PatientMedicalProcedure (procedures), CareObservation (observations), PatientImmunization (immunizations). Version 1.0.0 of this skill named "PatientMedication" and "MedicalProcedure"; those object names do not appear in the 262 Health Cloud developer guide.

**Detection hint:** If integration code targets objects with the `HC24__` namespace prefix for clinical data that has a FHIR R4-aligned counterpart, legacy objects are being used incorrectly.

---

## Anti-Pattern 4: Skipping Middleware for Raw FHIR Bundle Ingest

**What the LLM generates:** Integration designs that send raw FHIR R4 bundle JSON directly from the EHR to Salesforce's FHIR Healthcare API, assuming Salesforce can store the bundle as-is.

**Why it happens:** Salesforce has a FHIR Healthcare API that accepts FHIR R4 format. LLMs infer that the API can store raw FHIR bundles without transformation. The platform's non-conformant deviations (complex type flattening, cardinality differences) are not visible in the API endpoint URL.

**Correct pattern:**
The Health Cloud developer guide says a middleware integration solution is required to convert HL7 and FHIR messages to Salesforce objects. The middleware must flatten complex types (Period, Quantity, Range, Ratio), normalize CodeableConcept codings (max 15 per CodeSetBundle), validate codes (Salesforce doesn't), map FHIR identifiers to Identifier records, and fill fields that are optional in FHIR but required in Salesforce.

**Detection hint:** If the integration design shows FHIR bundles going directly from EHR to Salesforce FHIR Healthcare API without a transformation middleware step, the normalization gap exists.

---

## Anti-Pattern 5: Omitting the Experience Cloud FHIR Permission Set for Portal Users

**What the LLM generates:** Patient portal permission configurations that assign standard Health Cloud permission sets but omit the "FHIR R4 for Experience Cloud Sites" permission set required for portal users to access FHIR-aligned clinical objects.

**Why it happens:** The FHIR R4 for Experience Cloud Sites permission set is an Experience Cloud-specific permission requirement that is additional to the base FHIR R4 permission. LLMs assign the base FHIR R4 permission without knowing the Experience Cloud-specific variant is also required.

**Correct pattern:**
Community users need the FHIR R4 for Experience Cloud Sites permission set to use Clinical Data Model objects on an Experience Cloud site (Health Cloud developer guide 262, "Clinical Data Model" note). UNVERIFIED (2026-10-03): whether an additional "Experience Cloud for Health Cloud" permission set is also required; it is not named in that note.

**Detection hint:** If portal user permission configuration includes FHIR permissions but does not include "FHIR R4 for Experience Cloud Sites" specifically, portal users will not be able to view FHIR clinical data.

---

## Anti-Pattern 6: Inventing the Healthcare API endpoint

**What the LLM generates:** `GET /services/data/v60.0/healthcare/fhir/R4/Patient/{id}/$everything` returning "up to 30 entries" with `_count` and `_page` paging.

**Why it happens:** The model blends the core REST API path style with generic FHIR server conventions. Version 1.0.0 of this skill used that path.

**Correct pattern:** The Salesforce Healthcare API guide gives the URL shape `https://api.healthcloud.salesforce.com/<module>/fhir-r4/v1/<Resource>` (for example `.../clinical-summary/fhir-r4/v1/Condition`), with `/sandBox/` after the host for sandboxes and regional hosts for EU, CA, and AU. The 30-entry figure is the Bundle (batch) limit, with up to 10 reads or searches. UNVERIFIED (2026-10-03): support for `$everything` and for `_count` or `_page` paging; the guide pages fetched do not mention them.

**Detection hint:** `/services/data/` combined with `healthcare/fhir` in a Healthcare API call.

---

## Anti-Pattern 7: Requesting SMART wildcard scopes or a "healthcare" scope

**What the LLM generates:** "Add the `healthcare` and `api` scopes to the connected app" or "request `patient/*.read`."

**Why it happens:** SMART on FHIR conventions from other servers, plus a remembered scope name.

**Correct pattern:** The Healthcare API uses an external client app with OAuth 2.0 and custom scopes per resource and method, such as `user_condition_read`, `user_all_read`, or `system_all_write`. SMART-format scopes aren't supported because Salesforce doesn't allow wildcard characters in OAuth scopes (Healthcare API guide, "Authorization" and "Considerations"). UNVERIFIED (2026-10-03): any OAuth scope literally named `healthcare`; the guide does not list one.

**Detection hint:** `patient/*`, `user/*`, `launch/patient`, or a `healthcare` scope in a client app configuration.
