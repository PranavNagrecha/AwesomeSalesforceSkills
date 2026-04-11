# Examples — Clinical Data Requirements

## Example 1: Discovering FHIR R4 Support Settings Must Be Explicitly Enabled

**Context:** A health system integration team is beginning to build a FHIR R4 integration between their Epic EHR and Salesforce Health Cloud. They attempt to query the HealthCondition object but receive errors that the object does not exist.

**Problem:** The FHIR-Aligned Clinical Data Model org preference was never enabled. The FHIR R4-aligned standard objects (HealthCondition, CareObservation, PatientImmunization, AllergyIntolerance) are not available in the org until this setting is activated.

**Solution:**
1. Navigate to Setup > FHIR R4 Support Settings in the Health Cloud org.
2. Enable "FHIR-Aligned Clinical Data Model."
3. If a patient portal will need access to FHIR clinical data: also enable "FHIR R4 for Experience Cloud."
4. Verify activation: query `SELECT Id FROM HealthCondition LIMIT 1` in Developer Console — should return 0 rows (not an error).
5. Assign the FHIR R4 for Experience Cloud permission set to portal users who need to view clinical data.
6. Document the activation as a prerequisite for all downstream FHIR integration configuration.

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
