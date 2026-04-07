# Examples — Care Plan Configuration

## Example 1: Enabling ICM and Building a Diabetes Management Care Plan Template

**Context:** A regional health system is implementing Health Cloud for the first time on a Spring '25 org. They need a reusable care plan template for Type 2 Diabetes patients that includes standardized goals (HbA1c reduction, weight management) and recurring intervention tasks (quarterly lab review, dietary coaching check-in).

**Problem:** The administrator opened Health Cloud Setup and searched for "Care Plan Templates" but only found the legacy managed-package CarePlanTemplate admin UI. The ICM Action Plan Template setup screens were not visible. Creating a template in the legacy UI would lock the org into the no-investment architecture.

**Solution:**

The administrator first enabled the Integrated Care Management feature, which unlocked the ICM setup screens:

1. Navigate to: Setup > Health Cloud Settings > Integrated Care Management > toggle Enable to On.
2. Assign the `HealthCloudICM` permission set to the Health Cloud Admin profile.
3. Create ProblemDefinition records:
   - Name: "Type 2 Diabetes Mellitus" | Code: E11 | Code System: ICD-10-CM
4. Create GoalDefinition records:
   - Name: "Reduce HbA1c below 7%" | Category: Clinical
   - Name: "Achieve BMI below 30" | Category: Clinical
5. Link goals to the problem via ProblemGoalDefinition junction records.
6. Create an ActionPlanTemplate record:
   - Name: "Diabetes Management Plan" | Status: Draft
7. Add ActionPlanTemplateItem records for tasks:
   - "Quarterly HbA1c Lab Review" — due 90 days from plan start, assign to Care Manager role
   - "Monthly Dietary Coaching Check-In" — due 30 days from plan start, assign to Dietitian role
8. Link ProblemDefinition and GoalDefinition records to the template.
9. Set ActionPlanTemplate status to Active.

**Why it works:** Enabling ICM first makes the platform-native ActionPlanTemplate and PGI library objects available. Populating the PGI library before template creation ensures the problem and goal pickers are populated when care coordinators instantiate the template against a patient record. The template is now versioned, FHIR R4-aligned, and eligible for all future Health Cloud care plan feature releases.

---

## Example 2: Diagnosing Empty Problem Pickers in an ICM ActionPlanTemplate

**Context:** A care operations team reported that their newly created "Hypertension Management" ActionPlanTemplate showed no problems or goals when care coordinators tried to apply it to patients. The template itself was in Active status and appeared correctly in the admin UI.

**Problem:** The template was created before the PGI library was populated. Because ActionPlanTemplate saves successfully without PGI records, there was no error during creation. The problem and goal association fields on the template were blank — there was nothing to display in the picker.

**Solution:**

Diagnose by querying PGI library records:

```soql
SELECT Id, Name, Code, CodeSystemName FROM ProblemDefinition WHERE Name LIKE '%Hypertension%'
```

If this returns zero rows, the PGI library has not been populated for this condition. Fix:

1. Create a ProblemDefinition record: Name = "Essential Hypertension" | Code = I10 | CodeSystemName = ICD-10-CM.
2. Create GoalDefinition records: "Systolic BP below 130 mmHg", "Diastolic BP below 80 mmHg".
3. Create ProblemGoalDefinition junction records linking these goals to the Hypertension ProblemDefinition.
4. Navigate to the ActionPlanTemplate record in Setup.
5. Add the ProblemDefinition and GoalDefinition records to the template's problem and goal sections.
6. Re-publish the template (set to Active).

**Why it works:** The ICM model requires PGI library records to exist before they can be referenced in a template. Once created and linked, the care coordinator's picker will display the standardized problems and goals when instantiating the template against a patient. No platform restart or cache clear is needed — the picker queries live PGI records.

---

## Anti-Pattern: Referencing CarePlanTemplate__c Fields in an ICM Org

**What practitioners do:** Copy SOQL queries or configuration guidance from legacy Health Cloud documentation or training materials that reference `CarePlanTemplate__c` fields — for example, `SELECT Id, TemplateName__c, Description__c FROM CarePlanTemplate__c` — and apply them in an org running the ICM model.

**What goes wrong:** In orgs provisioned with ICM as the primary care plan architecture, `CarePlanTemplate__c` may be an empty or inaccessible managed-package object. The SOQL query throws an error: `No such column 'TemplateName__c' on entity 'CarePlanTemplate__c'` or, in some configurations, the entire object is unavailable. Integrations, report formulas, and validation rules built on these fields silently break.

**Correct approach:** Confirm the care plan architecture before using any object references. For ICM orgs, use `ActionPlanTemplate` (standard object, no namespace):

```soql
SELECT Id, Name, Status FROM ActionPlanTemplate WHERE Status = 'Active'
```

For care plan instances, query `CarePlan` (ICM) rather than Case-linked `CarePlanTemplate__c` templates:

```soql
SELECT Id, Name, Status, PatientId FROM CarePlan WHERE Status = 'InProgress'
```
