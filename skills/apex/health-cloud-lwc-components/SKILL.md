---
name: health-cloud-lwc-components
description: "Use this skill when building custom LWC components for Health Cloud: extending patient card configurations, building custom timeline components using TimelineObjectDefinition metadata, creating care plan visualizations, and surfacing clinical data via LWC. NOT for standard LWC development unrelated to Health Cloud clinical components, or OmniStudio FlexCard development."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "How do I add custom fields to the Health Cloud patient card component?"
  - "TimelineObjectDefinition metadata for adding custom objects to the Health Cloud timeline"
  - "Custom LWC is not showing clinical data from Health Cloud objects like HealthCondition or EhrPatientMedication"
  - "How to configure the Industries Timeline component vs. the legacy HC package timeline"
  - "Health Cloud patient card cannot be extended via Lightning App Builder slot injection"
tags:
  - health-cloud
  - lwc
  - patient-card
  - timeline
  - timeline-object-definition
  - clinical-components
inputs:
  - Health Cloud org with appropriate clinical objects enabled
  - Existing Health Cloud patient page layout with patient card or timeline component
  - Clinical data objects to surface (HealthCondition, ClinicalEncounter, etc.)
outputs:
  - Custom patient card field configuration via Health Cloud Setup
  - TimelineObjectDefinition metadata for custom timeline entries
  - Custom LWC that queries Health Cloud clinical objects via Account lookups
  - Care plan visualization component
dependencies:
  - admin/health-cloud-patient-setup
  - admin/health-cloud-timeline
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Health Cloud LWC Components

Use this skill when building custom LWC components for Health Cloud: adding clinical fields to the patient card via Health Cloud Setup, configuring the Industries Timeline with custom object entries via TimelineObjectDefinition metadata, and building custom LWCs that query Health Cloud clinical data objects. This skill covers Health Cloud-specific component extension patterns. It does NOT cover standard LWC development for non-Health Cloud use cases, OmniStudio FlexCard development, or general Lightning App Builder component placement.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org uses the **legacy Health Cloud managed-package timeline** or the **Industries Timeline** (backed by TimelineObjectDefinition). These are different components with different configuration mechanisms. The legacy managed-package timeline is deprecated in favor of the Industries Timeline.
- Understand that the Patient Card component (`healthCloudUtility:patientCard`) is NOT extensible via Lightning App Builder slot injection or standard child component override. Clinical field additions to the patient card must go through Health Cloud Setup > Patient Card Configuration, not standard App Builder drag-and-drop.
- Know that custom LWCs surfacing clinical data must query Health Cloud clinical objects (HealthCondition, ClinicalEncounter, EhrPatientMedication, etc.) using the Account lookup relationship. Clinical data is stored on clinical objects linked to the patient Account — NOT in custom fields on Account or Contact. Custom Account/Contact fields are invisible to all Health Cloud clinical UI components.

---

## Core Concepts

### Patient Card Extension via Health Cloud Setup (Not App Builder)

The Health Cloud Patient Card component cannot be extended via Lightning App Builder slot injection, child component override, or standard Lightning component composition. Adding new clinical fields to the patient card requires:
1. Navigate to Health Cloud Setup > Patient Card Configuration.
2. Add the clinical field from the appropriate object (must be an object with a lookup to the patient Account).
3. Save the configuration.

Attempting to extend the patient card by placing a child LWC inside it via App Builder will not work — the component does not support child slots in the Lightning App Builder.

### Industries Timeline vs. Legacy HC Package Timeline

Health Cloud ships two timeline components with different configuration mechanisms:

**Industries Timeline (recommended):**
- Configured via `TimelineObjectDefinition` metadata type (API v55.0+)
- Configured in Setup as a declarative JSON definition on the `TimelineObjectDefinition` metadata
- Supports any object related to the patient Account
- Receives ongoing Salesforce investment
- Category-based filtering in the timeline UI

**Legacy HC Package Timeline:**
- Deprecated — no new Salesforce investment
- Configured via custom metadata in the HC managed package
- Orgs still using the legacy component must plan migration to the Industries Timeline
- Different configuration mechanism from Industries Timeline; changes to one do not apply to the other

Use the Industries Timeline for all new development. Document the migration plan from legacy timeline to Industries Timeline if the org currently uses the legacy component.

### Clinical Data via Account Lookups (Not Account/Contact Fields)

Custom LWCs that need to display clinical data must query Health Cloud clinical objects using their Account lookup:
- `HealthCondition` where `PatientId = :accountId`
- `ClinicalEncounter` where `PatientId = :accountId`
- `PatientMedication` where `PatientId = :accountId`
- `CareObservation` where `PatientId = :accountId` (via parent records)

**Critical rule:** Data stored in custom fields on Account or Contact is NOT accessible to Health Cloud clinical UI components. The PatientCard, Timeline, and other Health Cloud components query clinical objects via their standard Account lookup fields. A custom `RecentCondition__c` text field on Account will never appear in clinical components regardless of how it is placed on the page layout.

---

## Common Patterns

### Adding Custom Objects to the Industries Timeline

**When to use:** A custom clinical workflow creates records on a custom sObject (or standard object) that needs to appear on the patient timeline.

**How it works:**
1. Ensure the custom object has an Account lookup field (required for timeline inclusion).
2. Create a `TimelineObjectDefinition` metadata record in Setup.
3. Define the JSON configuration: object API name, date field, title field, subtitle field, icon name, and filter criteria.
4. Save and deploy the metadata.
5. The custom object entries now appear in the Industries Timeline filtered by the configured date field.

```xml
<!-- TimelineObjectDefinition metadata example -->
<TimelineObjectDefinition>
    <active>true</active>
    <baseObject>ClinicalServiceRequest</baseObject>
    <dateField>ReferralDate</dateField>
    <iconType>standard:clinical_service_request</iconType>
    <label>Referrals</label>
    <objectColor>#1589EE</objectColor>
    <referenceObjectField>PatientId</referenceObjectField>
</TimelineObjectDefinition>
```

**Why not the alternative:** Manually wiring a custom LWC into the timeline area via page layout defeats the purpose of the Industries Timeline's configurable approach and does not benefit from timeline filtering and categorization.

### Custom LWC for Clinical Data Display

**When to use:** A care coordinator needs to see a summary of recent conditions and encounters on the patient page, beyond what the standard clinical components show.

**How it works:**
1. Define an Apex controller that queries clinical objects with Account lookup:
   ```apex
   @AuraEnabled(cacheable=true)
   public static List<HealthCondition> getConditions(Id accountId) {
       return [SELECT Id, Name, ConditionSeverity, OnsetDate 
               FROM HealthCondition 
               WHERE PatientId = :accountId 
               ORDER BY OnsetDate DESC LIMIT 10];
   }
   ```
2. In the LWC, retrieve the Account ID from the record context and call the Apex controller.
3. Render the clinical data in the component.
4. Apply appropriate FLS checks in Apex — clinical data is PHI and requires field-level security enforcement.

**Why not the alternative:** Using custom Account fields for clinical summaries means the data is not in the Health Cloud clinical data model and cannot be used by clinical components, reports, or FHIR APIs.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Add fields to patient card | Health Cloud Setup > Patient Card Configuration | App Builder slot injection does not work for this component |
| Add custom object to timeline | TimelineObjectDefinition metadata | Declarative; receives platform investment |
| Display clinical data in custom LWC | Query clinical objects via Account lookup | Clinical data is on clinical objects, not Account fields |
| Legacy timeline in org | Plan migration to Industries Timeline | Legacy component is deprecated |
| New timeline entry needed | Industries Timeline + TimelineObjectDefinition | Not legacy HC package timeline configuration |

---

## Recommended Workflow

1. **Identify component type** — determine whether the requirement is: patient card field addition, timeline entry addition, or a net-new custom clinical LWC component. Each follows a different implementation path.
2. **Verify timeline component version** — check which timeline component is active on the patient page (Industries Timeline backed by TimelineObjectDefinition vs. legacy HC package timeline). Confirm the implementation approach for the correct component type.
3. **For patient card additions** — navigate to Health Cloud Setup > Patient Card Configuration. Add the clinical field from the appropriate source object. Test that the field appears on the patient card.
4. **For timeline additions** — create a TimelineObjectDefinition metadata record with the correct object API name, date field, Account lookup field reference, and display configuration. Deploy and test in sandbox.
5. **For custom LWC** — write the Apex controller using Account lookup queries on clinical objects. Implement FLS checks. Build the LWC HTML/JS to display results. Add to page layout and test with a patient record.
6. **Security review** — verify the LWC and Apex enforce FLS for all clinical fields. Clinical data is PHI; HIPAA compliance requires proper field-level security enforcement in all custom code.

---

## Review Checklist

- [ ] Patient card field additions done via Health Cloud Setup (not App Builder)
- [ ] Industries Timeline vs. legacy timeline component confirmed
- [ ] TimelineObjectDefinition metadata created for custom timeline entries
- [ ] Custom LWC queries clinical objects via Account lookup (not Account fields)
- [ ] Apex controller enforces FLS for PHI fields
- [ ] Custom components tested with a real patient record in sandbox

---

## Salesforce-Specific Gotchas

1. **Patient Card cannot be extended via App Builder** — Lightning App Builder slot injection and child component override do not work for the Health Cloud Patient Card component. All patient card field additions must go through Health Cloud Setup > Patient Card Configuration.

2. **Industries Timeline and legacy timeline require different configuration** — changing TimelineObjectDefinition metadata does not affect the legacy HC package timeline. If the org has both components on different pages, they must be configured separately and through different mechanisms.

3. **Clinical data in Account fields is invisible to HC components** — only data stored on clinical objects (HealthCondition, ClinicalEncounter, PatientMedication) with proper Account lookups is accessible to Health Cloud clinical UI components. Custom denormalized summary fields on Account will not be consumed by the PatientCard, Timeline, or related components.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| TimelineObjectDefinition metadata | XML definition for custom object timeline entries |
| Patient card field configuration | Documented fields added via HC Setup > Patient Card Configuration |
| Custom clinical LWC | Component with Apex controller querying clinical objects via Account lookup |
| FLS enforcement pattern | Apex security review checklist for clinical data access in custom components |

---

## Related Skills

- admin/health-cloud-patient-setup — Patient account configuration and patient card baseline setup
- admin/health-cloud-timeline — Timeline configuration and TimelineObjectDefinition overview
- apex/health-cloud-apex-extensions — Apex extension points for Health Cloud managed package callbacks
