# Examples — Health Cloud LWC Components

## Example 1: Adding Custom Clinical Fields to the Patient Card

**Context:** A care coordinator needs to see the patient's primary care physician name and most recent A1c result directly on the patient card header — without scrolling to another section.

**Problem:** The developer attempts to add these fields by dragging a custom LWC child component into the Patient Card Lightning component area in App Builder, or by adding fields directly to the Lightning record page in the Patient Card slot. Neither approach works — the Patient Card does not support standard LWC slot injection.

**Solution:**
1. Navigate to Setup > Health Cloud Setup > Patient Card Configuration.
2. Click "Edit" on the patient card configuration for the appropriate record type.
3. Find the section where the primary care physician name can be added — this field is on the CareTeamMember object (linked to the patient Account).
4. For the A1c result: verify that the most recent CareObservation record with the correct LOINC code is accessible. Add the CareObservation field to the appropriate patient card section.
5. Save the configuration and test on a patient record with care team and observation data.

**Why it works:** The Patient Card component reads its field configuration from Health Cloud Setup, not from Lightning App Builder. Field additions must go through this Setup path. The component supports fields from any object with an Account lookup to the patient.

---

## Example 2: Creating a TimelineObjectDefinition for Custom Referral Entries

**Context:** A health system has ClinicalServiceRequest (referral) records that should appear in the patient timeline alongside encounters, care plans, and medications.

**Problem:** The developer adds a standard LWC list component to the patient page to show referrals, but it appears below the timeline rather than integrated within it. The timeline chronological view does not include the referrals.

**Solution:**
1. Create a TimelineObjectDefinition metadata record in the org.
2. Set the configuration fields:
   - `baseObject`: `ClinicalServiceRequest`
   - `dateField`: `ReferralDate`
   - `referenceObjectField`: `PatientId` (the Account lookup on ClinicalServiceRequest)
   - `label`: `Referrals`
   - `active`: `true`
   - `iconType`: `standard:clinical_service_request`
3. Deploy the metadata to the org.
4. Navigate to a patient record with referrals — referrals now appear in the Industries Timeline sorted chronologically by ReferralDate alongside other clinical events.

**Why it works:** TimelineObjectDefinition (API v55.0+) is the declarative way to add any object to the Industries Timeline, as long as the object has an Account lookup. No custom LWC is needed — the platform handles rendering from the JSON definition.

---

## Anti-Pattern: Storing Clinical Summary Data in Custom Account Fields

**What practitioners do:** Create custom fields on the Account object (e.g., `MostRecentDiagnosis__c`, `ActiveMedicationCount__c`) and populate them from triggers or Flows to display clinical summaries in the patient card or timeline.

**What goes wrong:** Health Cloud clinical UI components (PatientCard, Timeline, MedTimeline) query standard clinical objects (HealthCondition, PatientMedication, etc.) via their Account lookup relationships. Custom Account fields are invisible to these components — the fields appear on standard record page layouts but are never consumed by clinical UI. The care coordinator sees the clinical summary correctly in the standard record page layout but blank or missing in the clinical console.

**Correct approach:** All clinical data should be stored on the appropriate clinical standard objects with Account lookups. Custom LWCs that need to display summaries should query clinical objects via Account lookup, not read from denormalized Account fields. The timeline and patient card read from clinical objects, not from Account summary fields.
