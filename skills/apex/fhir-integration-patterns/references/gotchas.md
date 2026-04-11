# Gotchas — FHIR Integration Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: No Native CDS Hooks Service Endpoint in Salesforce

**What happens:** The integration team registers Salesforce's FHIR Healthcare API endpoint as a CDS Hooks service. The EHR sends CDS Hook POST requests to Salesforce, which returns a 404 or 405 error because there is no native CDS Hook handler.

**When it occurs:** When architects assume Salesforce can natively act as a CDS Hooks service because it supports FHIR R4. CDS Hooks is a separate HL7 standard that requires a specific HTTP service format not provided by Salesforce's FHIR Healthcare API.

**How to avoid:** Always route CDS Hooks through MuleSoft as middleware. MuleSoft serves as the CDS Hook service endpoint, queries Salesforce for clinical alert/gap data, and assembles the CDS card JSON response. Document this architecture pattern explicitly in the integration design.

---

## Gotcha 2: FHIR CodeableConcept Maps to Single Lookup (Not Zero-to-Many) in Most Objects

**What happens:** Inbound FHIR resources with multi-coding CodeableConcepts lose all but the primary coding when stored in Salesforce. The FHIR spec allows zero-to-many Coding elements per CodeableConcept, but most Salesforce FHIR R4-aligned objects accept only a single CodeSet lookup per field.

**When it occurs:** Any time a source EHR sends conditions, observations, or medications with multiple coding systems (SNOMED + ICD-10 + LOINC on the same concept). The middleware must explicitly map the primary coding to the Salesforce CodeSet field — additional codings are dropped unless the CodeSetBundle junction approach is used.

**How to avoid:** Review the Salesforce FHIR R4 mapping guide for each resource to confirm whether the Salesforce implementation supports multi-coding via CodeSetBundle. For fields that do not support multi-coding, implement a coding priority policy in middleware and document the truncation decision.

---

## Gotcha 3: Legacy HC24__ EHR Objects Are Write-Locked in Spring '23+ Orgs

**What happens:** Integration code targeting HC24__EhrCondition__c, HC24__EhrMedication__c, or other legacy packaged EHR objects fails with "insufficient privileges" or "entity is read-only" errors in orgs provisioned on or after Spring '23.

**When it occurs:** When integration code is written using pre-Spring '23 documentation that shows HC24__ objects as the target for clinical data, and then deployed to a new org.

**How to avoid:** Target FHIR R4-aligned standard objects for all new integrations: HealthCondition, PatientMedication, MedicalProcedure, CareObservation. Check the org's Health Cloud version and provisioning date. For legacy orgs with existing HC24__ data, plan migration to standard objects.

---

## Gotcha 4: Experience Cloud Users Need a Separate FHIR R4 Permission Set

**What happens:** Patient portal users (Experience Cloud users) cannot access FHIR R4-aligned clinical data via the portal because they lack the FHIR R4 for Experience Cloud permission set.

**When it occurs:** When patient portal configuration assigns the standard Health Cloud permission sets but omits the "FHIR R4 for Experience Cloud" permission set required for portal users to view FHIR-aligned clinical objects through the portal.

**How to avoid:** Assign the "FHIR R4 for Experience Cloud" permission set to all Experience Cloud users who need to view FHIR-aligned clinical data (HealthCondition, CareObservation, etc.) in patient portal pages. Internal org users with the standard FHIR R4 permission set do NOT need this additional permission set — it is specific to Experience Cloud portal users.
