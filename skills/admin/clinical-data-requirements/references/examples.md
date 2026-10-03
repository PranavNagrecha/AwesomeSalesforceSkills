# Examples — Clinical Data Requirements

## Example 1: Discovering FHIR R4 Support Settings Must Be Explicitly Enabled

**Context:** A health system integration team is beginning to build a FHIR R4 integration between their Epic EHR and Salesforce Health Cloud. They attempt to query the HealthCondition object but receive errors that the object does not exist.

**Problem:** The FHIR-Aligned Clinical Data Model org preference was never enabled. The FHIR R4-aligned standard objects (HealthCondition, CareObservation, PatientImmunization, AllergyIntolerance) are not available in the org until this setting is activated.

**Solution:**
1. Navigate to Setup > FHIR R4 Support Settings in the Health Cloud org, or deploy `IndustriesSettings.enableClinicalDataModel` = `true` (see `metadata-examples.md`).
2. Enable the FHIR-Aligned Clinical Data Model org pref.
3. Verify activation with one query per object in scope. Each should return zero rows, not an error:

```sql
SELECT Id FROM HealthCondition LIMIT 1
```

4. Do not wait for `CareObservation`, `CodeSet`, `CodeSetBundle`, or `PersonName`; the guide lists them as available without the org pref.
5. If a patient portal needs clinical data, assign the FHIR R4 for Experience Cloud Sites permission set to the community users who need it. It is a permission set, not an org setting.
6. Record the activation as a prerequisite for all downstream FHIR integration configuration.

**Why it works:** The FHIR-Aligned Clinical Data Model is an opt-in feature. Enabling it is the first step before any clinical data requirements can be implemented.

---

## Example 2: Handling CodeableConcept with More Than 15 Codings

**Context:** A payer's FHIR R4 integration sends Condition resources where each condition has an ICD-10-CM code, a SNOMED CT code, an NCI Thesaurus code, and multiple regional clinical coding variants — sometimes exceeding 15 codings per concept.

**Problem:** Salesforce's FHIR R4 implementation allows maximum 15 CodeSet references per object (CodeSet1Id through CodeSet15Id on the CodeSetBundle junction). When the FHIR payload is processed by middleware, codings 16+ are silently dropped.

**Solution:**
1. Audit the source system's coding practices to identify the maximum number of codings per CodeableConcept.
2. If the maximum exceeds 15, define a coding priority policy in the middleware:
   - Priority 1: ICD-10-CM (required for US billing)
   - Priority 2: SNOMED CT (required for clinical interoperability)
   - Priority 3: LOINC (for labs/observations)
   - Priority 4+: other coding systems in order of business importance
3. Implement truncation logic in the middleware to include only the top 15 codings in priority order.
4. Document the truncation policy in the data mapping specification.
5. Consider storing the full original FHIR payload as a JSON blob in a custom field for audit/fallback purposes.

**Why it works:** Explicitly handling the 15-coding limit with a documented priority policy ensures the most clinically important coding systems are always included, and the truncation is intentional and auditable rather than silent data loss.

---

## Anti-Pattern: Writing FHIR Patient Demographics Directly to Account Fields

**What practitioners do:** Map FHIR Patient.name, Patient.telecom, and Patient.address directly to the corresponding Account/Contact fields (Name, Phone, MailingAddress) because these seem like the obvious field-level equivalents.

**What goes wrong:** Health Cloud clinical UI components (PatientCard, Timeline) query child objects — PersonName, ContactPointPhone, ContactPointAddress — not Account fields directly. Patients created with demographics in Account fields appear correctly in standard CRM views but with blank data in Health Cloud clinical components. Care coordinators see patients with no name or contact information in the clinical console.

**Correct approach:** FHIR Patient demographics map to child objects in Salesforce. Use PersonName for name data, ContactPointPhone/Email for telecom, and ContactPointAddress for address. Create these as child records linked to the Person Account after the Person Account record itself is created.

---

## Example 3: Mapping One FHIR Condition to `HealthCondition` and `CodeSetBundle`

**Context:** The payer feed in Example 2 sends a Condition with three codings and no free text. The middleware team asks for the target shape.

**Solution:** The mapping specification, expressed as the records the middleware writes in order:

```json
{
  "step1_CodeSet": [
    { "Code": "E11.9", "SourceSystem": "http://hl7.org/fhir/sid/icd-10-cm", "Name": "Type 2 diabetes mellitus without complications" },
    { "Code": "44054006", "SourceSystem": "http://snomed.info/sct", "Name": "Diabetes mellitus type 2" }
  ],
  "step2_CodeSetBundle": {
    "Name": "Type 2 diabetes mellitus",
    "CodeSet1Id": "<Id of the ICD-10-CM CodeSet>",
    "CodeSet2Id": "<Id of the SNOMED CT CodeSet>"
  },
  "step3_HealthCondition": {
    "PatientId": "<Person Account Id>",
    "ConditionCodeId": "<Id of the CodeSetBundle>",
    "ConditionStatus": "Active"
  }
}
```

**Why it works:** `coding.code` maps to `CodeSet.Code` (a string) and `coding.system` maps to `CodeSet.SourceSystem` (a string). The bundle holds up to 15 `CodeSet` references, filled in the priority order from Example 2. `condition.code` maps to `HealthCondition.ConditionCodeId`, which is one-to-one in Salesforce, so the bundle must exist before the condition. `HealthCondition.PatientId` and `ConditionStatus` (values `Active`, `Inactive`, `Recurrence`, `Relapse`, `Remission`, `Resolved`) are documented in the guide's HealthCondition field list (`health_cloud_dev_guide L15199-15215`, `L15313`). UNVERIFIED (2026-10-03): the `CodeSet.Name` values shown are illustrative; confirm which `CodeSet` fields are required with a describe call.

