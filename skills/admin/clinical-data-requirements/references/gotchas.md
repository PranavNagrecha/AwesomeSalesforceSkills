# Gotchas: Clinical Data Requirements

Non-obvious Health Cloud clinical data model behaviors that cause real production problems. Sources are listed in `well-architected.md`. Line references cite the `pdftotext -layout` extraction of the Summer '26 PDFs, written as `<guide> L<n>`; the Health Cloud developer guide is titled "Agentforce Health Developer Guide" in this release. A claim that could not be re-read in an official source carries an inline `UNVERIFIED (2026-10-03):` marker.

## Gotcha 1: Most clinical objects need the org pref, but some exist without it

**What happens:** "To enable these objects in your org, go to FHIR R4 Support Settings in Setup and enable the FHIR-Aligned Clinical Data Model org pref" (`health_cloud_dev_guide L8345-8346`). The guide then splits objects into two lists. `HealthCondition`, `AllergyIntolerance`, `ClinicalEncounter`, `MedicationRequest`, `MedicationStatement`, `PatientImmunization`, `PatientMedicalProcedure`, and others need the pref. `CareObservation`, `CodeSet`, `CodeSetBundle`, `Identifier`, `PersonName`, `Medication`, and others do not, "because they're part of other data models in Health Cloud and Life Sciences Cloud" (`L8347-8380`). Enabling the pref also adds fields to standard objects, such as `Account.SourceSystemIdentifier` and `Contact.Gender` (`L8381-8403`).

**When it occurs:** A query against `HealthCondition` fails with an unknown-object error in a fresh org. In the other direction, earlier versions of this skill said `CareObservation` is unavailable until the pref is on, which sends teams to wait for an object that already exists.

**How to avoid:** Make the org pref the first item on the readiness checklist, or deploy `IndustriesSettings.enableClinicalDataModel` (API 51.0, default false; `api_meta L119553-119555`). Confirm with one SOQL query per object in scope.

---

## Gotcha 2: A CodeableConcept keeps at most 15 coding references

**What happens:** "According to FHIR, CodeableConcept has a zero-to-many coding resource. Because Salesforce doesn't support zero-to-many references, Code Set Bundle flattens this zero-to-many reference to 15 zero-to-one Code Set references. The Code Set references are CodeSet1Id, CodeSet2Id, CodeSet3Id, and so on, until CodeSet15Id" (`health_cloud_dev_guide L75646-75649`).

**When it occurs:** Terminology-rich sources (SNOMED CT hierarchies, regional code systems) send more than 15 codings for one concept.

**How to avoid:** Count codings per concept in source samples. Where the count can exceed 15, define a priority order (for example ICD-10-CM, SNOMED CT, LOINC, then others) and truncate deliberately in the middleware. Keep the original payload in the integration layer's archive if downstream analytics need every coding. UNVERIFIED (2026-10-03): whether an over-limit payload is truncated or rejected by Salesforce is not stated; the middleware should never send more than 15.

---

## Gotcha 3: New customers cannot write packaged EHR objects that have standard counterparts

**What happens:** "Starting with the Spring '23 release, new customers won't be able to create records in the packaged EHR objects that have counterpart standard objects in the FHIR R4-aligned data model," and "all future development will be built on the FHIR R4-aligned data model" (`health_cloud_dev_guide L8406-8409`). The packaged objects include `HC24__EhrCondition__c`, `HC24__EhrMedicationStatement__c`, `HC24__EhrMedicationPrescription__c`, `HC24__EHRProcedure__c`, `HC24__EhrObservation__c`, and `HC24__EhrImmunization__c` (`L24863-24892`).

**When it occurs:** Integration code or tutorials from before Spring '23 target the `HC24__` objects. Earlier versions of this skill also named objects that do not exist (`HC24__EhrMedication__c`, `HC24__EhrLabResult__c`, `PatientMedication`, `MedicalProcedure`).

**How to avoid:** Target the standard objects (`HealthCondition`, `MedicationStatement`, `MedicationRequest`, `PatientMedicalProcedure`, `CareObservation`, `PatientImmunization`). Treat legacy data as a migration workstream.

---

## Gotcha 4: Some fields are required in Salesforce but optional in FHIR

**What happens:** For Condition, "while FHIR defines condition.code as a zero-to-one resource, the Salesforce implementation is a one-to-one field": `condition.code` maps to `HealthCondition.ConditionCodeId`, a lookup to `CodeSetBundle` (`health_cloud_dev_guide L76782-76784`).

**When it occurs:** A source sends problem-list entries with free text and no code, and loads fail.

**How to avoid:** List every 1..1 field in the mapping specification and define the middleware rule for records that arrive without it: map to an "unspecified" code bundle, route to a review queue, or reject with a logged reason.

---

## Gotcha 5: HL7 v2.3 support is a field mapping, not a message listener

**What happens:** The clinical data model "also supports many of the HL7 v2.3 message types" (`health_cloud_dev_guide L8336`). ADT, ORM, ORU, MDM, VXU, and RDE messages "can be stored in Salesforce by mapping their constituent segments to fields in Salesforce standard objects" (`L82441-82450`). The same guide says "a middleware integration solution is required to convert messages from HL7 and FHIR-based systems to the fields and objects in Salesforce" (`L75631-75632`).

**When it occurs:** An architecture sends raw HL7 v2 messages straight at the Salesforce REST API, or assumes HL7 v2 support means no translation layer.

**How to avoid:** Use the guide's segment tables (PID, PV1, PV2, OBX, AL1, ORC, OBR, RXA, RXE, RXR, RXC) as the mapping target, and put a translation layer in front of Salesforce to parse messages and call the APIs. UNVERIFIED (2026-10-03): earlier versions of this skill said the Healthcare API accepts only FHIR R4 JSON; the Healthcare API guide is a separate document not read for this pass.

---

## Gotcha 6: Experience Cloud users need a specific permission set

**What happens:** "To use the Clinical Data Model objects on an Experience Cloud site, community users need the FHIR R4 for Experience Cloud Sites permission set" (`health_cloud_dev_guide L8351-8352`). Earlier versions of this skill described this as an org setting named "FHIR R4 for Experience Cloud"; the guide describes a permission set.

**When it occurs:** A patient portal is built, sharing is configured, and patients still see no clinical records.

**How to avoid:** Add the permission set to the portal user provisioning design, alongside sharing for the clinical records each patient may see.

---

## Gotcha 7: Address lines and names have Salesforce-specific shapes

**What happens:** `address.line` is zero-to-many in FHIR, but "Salesforce supports only one string for each record"; the guide recommends merging multiple lines into a single string. Address `type` and `text` are not supported (`health_cloud_dev_guide L75689-75699`). HumanName maps to `PersonName`, which stores `FirstName`, `LastName`, and `FullName`; `LastName` can hold the family name plus middle names, and `ParentRecordId` relates the name to the person's Account or Contact (`L75633-75637`).

**When it occurs:** Middleware sends address lines as separate fields or drops all but the first, or writes names into the Account record instead of `PersonName` records.

**How to avoid:** Specify the merge rule for address lines (separator, order) and the name rule (which FHIR parts go into `LastName` and `FullName`). Create `PersonName` and contact point records as children of the Person Account.

---

## Gotcha 8: Bundle size limits are unconfirmed

**What happens:** Earlier versions of this skill cited FHIR bundle limits of 30 entries per bundle and 10 read or search operations per bundle. UNVERIFIED (2026-10-03): those figures are not in the Health Cloud developer guide; they belong to the Healthcare API guide, which was not read for this pass.

**When it occurs:** Bulk clinical loads are sized around an unconfirmed limit.

**How to avoid:** Confirm the current limits in the Salesforce Healthcare API guide before sizing batches, and keep batch size configurable in the middleware.
