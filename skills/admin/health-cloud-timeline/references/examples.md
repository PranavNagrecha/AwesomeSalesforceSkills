# Examples — Health Cloud Timeline

## Example 1: Surfacing a Custom Care Gap Object on the Patient Timeline

**Context:** A Health Cloud org tracks care gaps in a custom object `Care_Gap__c`. The object has a `Patient__c` lookup to Account (the patient's Account record) and a `Gap_Identified_Date__c` date field. The care coordination team wants care gaps to appear chronologically on the patient timeline so clinicians can see them alongside other clinical events.

**Problem:** Without a `TimelineObjectDefinition`, the Industries Timeline component has no knowledge of `Care_Gap__c`. Records exist in the database but nothing appears on the timeline. Adding a related list to the page layout shows the records in table form but not in the unified chronological view clinical staff need.

**Solution:**

Step 1: Confirm in Setup > Timeline > Categories that a "Care Gaps" category exists. Create it if not.

Step 2: Create the metadata file at `force-app/main/default/timelineObjectDefinitions/Care_Gap__c.timelineObjectDefinition-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TimelineObjectDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <baseObject>Care_Gap__c</baseObject>
    <dateField>Gap_Identified_Date__c</dateField>
    <descriptionField>Gap_Description__c</descriptionField>
    <icon>warning</icon>
    <label>Care Gap</label>
    <labelPlural>Care Gaps</labelPlural>
    <nameField>Name</nameField>
    <timelineCategory>Care Gaps</timelineCategory>
</TimelineObjectDefinition>
```

Step 3: Deploy:

```bash
sf project deploy start --source-dir force-app/main/default/timelineObjectDefinitions
```

Step 4: Open App Builder for the patient record page and confirm the Industries Timeline component is present (not the legacy HealthCloud.Timeline). Save and activate.

Step 5: Navigate to a patient record with existing `Care_Gap__c` records. Confirm entries appear under the "Care Gaps" filter category with the warning icon and correct date placement.

**Why it works:** The `Patient__c` field on `Care_Gap__c` is a lookup to Account. The Enhanced Timeline engine traverses this relationship when querying records for a given patient Account. The category assignment connects the definition to the filter picklist so clinicians can isolate care gaps without scrolling through medications or encounter entries.

---

## Example 2: Migrating from Legacy HealthCloud.Timeline to Industries Timeline

**Context:** An org was provisioned with Health Cloud in 2021 and uses the legacy `HealthCloud.Timeline` managed-package component. The timeline currently displays `EhrPatientMedication`, `PatientHealthCondition`, and `ClinicalEncounter` records. The implementation team has been notified the legacy component is deprecated and needs to migrate to the Industries Enhanced Timeline.

**Problem:** The legacy component reads its configuration from Health Cloud Custom Settings. The Industries Timeline component reads `TimelineObjectDefinition` metadata. Simply swapping the component on the page layout without creating the metadata records results in an empty timeline — all clinical data disappears from view.

**Solution:**

Step 1: Audit the legacy timeline configuration. In Setup, search for Custom Settings related to Timeline or check `HealthCloud__Timeline_Config__c` to identify which objects were configured.

Step 2: Create `TimelineObjectDefinition` records for each legacy object. For the three standard Health Cloud clinical objects:

```xml
<!-- EhrPatientMedication -->
<?xml version="1.0" encoding="UTF-8"?>
<TimelineObjectDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <baseObject>EhrPatientMedication</baseObject>
    <dateField>MedicationStartDate</dateField>
    <descriptionField>MedicationName</descriptionField>
    <icon>pill</icon>
    <label>Medication</label>
    <labelPlural>Medications</labelPlural>
    <nameField>MedicationName</nameField>
    <timelineCategory>Medications</timelineCategory>
</TimelineObjectDefinition>
```

```xml
<!-- PatientHealthCondition -->
<?xml version="1.0" encoding="UTF-8"?>
<TimelineObjectDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <baseObject>PatientHealthCondition</baseObject>
    <dateField>OnsetDate</dateField>
    <descriptionField>ConditionName</descriptionField>
    <icon>heart</icon>
    <label>Health Condition</label>
    <labelPlural>Health Conditions</labelPlural>
    <nameField>ConditionName</nameField>
    <timelineCategory>Conditions</timelineCategory>
</TimelineObjectDefinition>
```

Step 3: Create the corresponding category values in Setup > Timeline > Categories: "Medications", "Conditions", "Encounters".

Step 4: In App Builder, open the patient record page. Add the Industries Timeline component. Remove the legacy `HealthCloud.Timeline` component from the same page. Activate the updated page.

Step 5: Validate in sandbox on 3+ patient records with data in all three objects. Confirm each category filter shows the correct records.

**Why it works:** The Industries Timeline component reads exclusively from `TimelineObjectDefinition` metadata records. Each standard Health Cloud clinical object already has the required Account relationship in its data model, so no schema changes are needed. Removing the legacy component immediately prevents duplicate rendering that occurs when both components are present simultaneously.

---

## Anti-Pattern: Placing Both Legacy and Industries Timeline Components on the Same Page

**What practitioners do:** When migrating, teams add the Industries Timeline component to the page layout without removing the legacy `HealthCloud.Timeline` component, intending to run a parallel validation period.

**What goes wrong:** Both components query independently. Clinical records that appear in both configurations display twice on the page. Each component has its own filter state. Page load performance degrades because two separate timeline queries execute on every record open. Clinical staff report "duplicate entries" and raise data quality tickets before the issue is diagnosed as a configuration problem.

**Correct approach:** Never run both components simultaneously on the same page layout. If parallel validation is needed, create a separate sandbox or use a separate user profile pointing to a different page assignment. In production, the migration should be a single deployment that adds the Industries Timeline and removes the legacy component atomically.
