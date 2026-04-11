# Examples — Care Coordination Requirements

## Example 1: Mapping SDOH Barrier Tracking Requirements for a Community Health Worker Program

**Context:** A federally qualified health center is implementing Health Cloud for community health workers (CHWs) who conduct social needs screenings and connect patients to community resources.

**Problem:** The implementation team designed a custom SocialBarrier__c object for tracking SDOH findings, not knowing that Health Cloud ICM has a native CareBarrier/CareBarrierType object family for exactly this purpose.

**Solution:**
1. Enable Integrated Care Management in Setup (both checkboxes).
2. Map each social barrier category (food insecurity, housing instability, transportation, social isolation, utilities) to a CareBarrierType picklist value.
3. Create a CareDeterminant record for each category (e.g., Food Security, Housing Stability) to anchor the barrier types.
4. Design the screening Assessment form (using Discovery Framework/OmniStudio) to create CareBarrier records automatically when a patient screens positive for a social need.
5. Configure Task creation automation: when a CareBarrier is created, auto-create a Task assigned to the CHW with action steps for that barrier type.
6. Build CareBarrier resolution reports grouped by CareDeterminant for population health dashboards.

**Why it works:** Native CareBarrier objects integrate with Health Cloud's patient timeline and care coordination views without custom development. The platform-standard approach enables reporting and population health management features that custom objects do not provide.

---

## Example 2: Designing Care Gap Display for a Quality Improvement Program

**Context:** A health plan needs to display care gaps (overdue preventive screenings, quality measures) to care coordinators in Health Cloud so they can prioritize outreach.

**Problem:** The care coordinator team assumed they could create care gaps manually when reviewing patient charts. The requirements document included a "Create Care Gap" button on the patient page. The implementation team built this before discovering that CareGap records cannot be created manually.

**Solution:**
1. Revise the requirements: care gaps will NOT be manually created. Instead, the plan's quality analytics system generates quality measure gaps nightly.
2. Configure an integration (using MuleSoft or the FHIR R4 Healthcare API) to ingest CareGap records from the quality analytics system into Salesforce via the FHIR CareGap resource.
3. Design the care coordinator UI to display incoming CareGap records on the patient timeline and in a filtered list view for prioritization.
4. Create a care coordinator workflow for "acknowledging" a care gap (updating status to indicate the care coordinator has reviewed it and is taking action) — this uses a status update, not record creation.
5. Build outreach tracking by linking CareGap records to Tasks and Cases created by care coordinators.

**Why it works:** CareGap records are system-generated quality measure artifacts. Requiring an external system to populate them is not a limitation to work around — it is the correct architectural separation of the clinical rules engine from the care management platform.

---

## Anti-Pattern: Treating CareBarrier and CarePlanProblem as Interchangeable

**What practitioners do:** Use CarePlanProblem records for SDOH barriers (e.g., "Transportation Barrier") and CareBarrier records for clinical problems (e.g., "Uncontrolled Hypertension") because both represent "problems the care team is addressing."

**What goes wrong:** CarePlanProblem is part of the ICM care plan hierarchy (linked to GoalDefinitions and ActionPlanTemplates). Using it for SDOH barriers pollutes the clinical care plan with social needs records that have different workflows, different resolution criteria, and different reporting requirements. CareBarrier is designed specifically for SDOH social factors and links to Cases and Tasks for community resource intervention — a completely different workflow from clinical care plan management.

**Correct approach:** CareBarrier = SDOH social factors and community resource interventions. CarePlanProblem = clinical diagnoses and health conditions within a care plan. Keep them separate and design the care coordinator workflows to use each object for its intended purpose.
