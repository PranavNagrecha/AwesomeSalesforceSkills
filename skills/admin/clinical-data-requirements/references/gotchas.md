# Gotchas — Clinical Data Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: FHIR R4 Support Settings Must Be Manually Enabled

**What happens:** All FHIR R4-aligned clinical objects (HealthCondition, CareObservation, PatientImmunization, AllergyIntolerance, etc.) are unavailable in the org. SOQL queries return "Object not found" errors. Integration tests fail immediately.

**When it occurs:** In any new or existing Health Cloud org where the FHIR-Aligned Clinical Data Model org preference was never enabled. This is opt-in, not default-on.

**How to avoid:** Make FHIR R4 Support Settings activation the first step in any clinical data implementation checklist. Navigate to Setup > FHIR R4 Support Settings and enable both "FHIR-Aligned Clinical Data Model" and (if applicable) "FHIR R4 for Experience Cloud." Document the activation in the implementation runbook.

---

## Gotcha 2: CodeableConcept Is Capped at 15 CodeSet References

**What happens:** Source system FHIR payloads with CodeableConcept elements containing more than 15 Coding elements are silently truncated. Coding entries 16 and beyond are dropped during storage. Clinical data appears complete in Salesforce but is missing coding variants that may be required for downstream analytics or clinical decision support.

**When it occurs:** With any source system (EHR, payer, HIE) that uses richly coded clinical concepts — particularly SNOMED CT, which has deep hierarchical coding. Terminology-rich FHIR implementations commonly exceed 15 codings per concept.

**How to avoid:** Audit source system coding practices before implementation. If codings regularly exceed 15, implement a middleware truncation policy that prioritizes the most clinically important coding systems (ICD-10-CM, SNOMED CT, LOINC) before the Salesforce hard limit.

---

## Gotcha 3: Legacy HC24__ EHR Objects Are Write-Locked in New Orgs

**What happens:** Attempts to write data to HC24__EhrCondition__c, HC24__EhrMedication__c, HC24__EhrProcedure__c, or HC24__EhrLabResult__c fail with insufficient privileges or read-only errors in orgs provisioned as of Spring '23.

**When it occurs:** When integration code or data migration scripts targeting legacy managed-package EHR objects are run in a new Health Cloud org. Also common when documentation from before Spring '23 is followed without checking the org's edition and provisioning date.

**How to avoid:** Always check whether the org uses legacy managed-package EHR objects or FHIR R4-aligned standard objects. For new orgs: use HealthCondition, PatientMedication, MedicalProcedure, CareObservation. For legacy orgs with HC24__ data: plan a migration to standard objects and target standard objects for all new integrations.

---

## Gotcha 4: HL7 v2 Messages Cannot Be Directly Stored in Salesforce Clinical Objects

**What happens:** Teams attempt to build a direct HL7 v2 to Salesforce integration, only to find there is no native HL7 v2 parser in Salesforce. The integration must be redesigned with a middleware layer.

**When it occurs:** When the integration architecture is designed assuming Salesforce can natively receive and parse HL7 v2 messages (ADT, ORU, ORM) the same way it can receive FHIR R4 REST payloads via the Healthcare API.

**How to avoid:** Explicitly document in the integration architecture that HL7 v2 sources require a middleware layer (MuleSoft HL7 Connector, Mirth Connect, custom FHIR translator) to convert HL7 v2 to FHIR R4 before storage in Salesforce. Salesforce's FHIR Healthcare API receives FHIR R4 JSON; it does not support HL7 v2 message formats.
