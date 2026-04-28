---
name: health-cloud-timeline
description: "Configure the Industries Enhanced Timeline in Health Cloud to display clinical events, custom object records, and activity history on a patient or member record. Trigger keywords: Enhanced Timeline, TimelineObjectDefinition, Industries Timeline, timeline categories, clinical event display, timeline configuration. NOT for standard Activity Timeline (task/event list), NOT for Experience Cloud timelines, NOT for legacy Health Cloud managed-package Timeline component unless migrating away from it."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Performance
triggers:
  - "How do I show custom object records on the patient timeline in Health Cloud?"
  - "The Industries Timeline component is not displaying clinical events from a related object"
  - "How do I configure timeline categories and filter picklist values for Health Cloud Enhanced Timeline?"
  - "We need to migrate from the legacy Health Cloud Timeline component to the new Industries Timeline"
  - "TimelineObjectDefinition metadata not working — timeline still empty after deployment"
  - "How do I control which event types appear on the patient care timeline?"
tags:
  - health-cloud
  - enhanced-timeline
  - industries-timeline
  - TimelineObjectDefinition
  - clinical-data
  - patient-record
  - admin
  - metadata
inputs:
  - "Target Salesforce org with Health Cloud or Industries license that includes Timeline permissions"
  - "List of objects to surface on the timeline and their relationship path to Account"
  - "Desired timeline category labels (used as filter picklist values)"
  - "Whether the org is currently using the legacy managed-package Timeline component"
outputs:
  - "TimelineObjectDefinition metadata records configured for each target object"
  - "Timeline category values configured in Setup"
  - "Industries Timeline Lightning component embedded in the patient/member page layout"
  - "Migration checklist if moving from legacy to Enhanced Timeline"
dependencies:
  - health-cloud-patient-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Health Cloud Timeline

This skill activates when a practitioner needs to configure the **Industries Enhanced Timeline** in Health Cloud — adding custom object records, clinical events, or activity history to the patient or member timeline view. It covers `TimelineObjectDefinition` metadata setup, timeline category configuration, component placement, and migration away from the legacy managed-package Timeline component.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has a Health Cloud or Industries license that includes the **Timeline** permission. Without this, `TimelineObjectDefinition` records cannot be created and the Industries Timeline component will not render.
- Identify whether the page currently uses the **legacy Timeline component** (from the `HealthCloud` managed package, typically installed as `HealthCloud.Timeline`) or the **Industries Timeline component** (`industries:timeline` or `forceContent:timeline` in the page layout). These two components use completely different configuration mechanisms.
- Determine the relationship path from each target object back to the **Account** object. Enhanced Timeline requires every displayed object to be related to the patient/member through Account — direct or through a related Account lookup. Objects without an Account relationship path cannot be surfaced.
- Check the API version in use. `TimelineObjectDefinition` metadata is available at **API v55.0 and later**. Orgs deploying via older tooling or scratch org definitions with older API versions will get metadata errors.

---

## Core Concepts

### TimelineObjectDefinition Metadata Type

`TimelineObjectDefinition` is the metadata type that tells the Industries Enhanced Timeline which objects to query and how to display their records. Each definition maps one object to the timeline and configures:

| Field | Purpose |
|---|---|
| Object API name | The Salesforce object whose records appear as timeline entries |
| Date field | Which date/datetime field determines where the record appears on the timeline axis |
| Title field | Field shown as the entry headline |
| Description field | Optional secondary text |
| Timeline category | The filter group label (appears in the filter picklist on the timeline component) |
| Icon | SLDS utility icon name to display alongside entries |

`TimelineObjectDefinition` records are org-wide metadata; they are not record-type-specific. Once deployed, all instances of the Industries Timeline component in the org will include records from that object definition unless filtered by category at the component level.

### Account Relationship Requirement

The Enhanced Timeline queries objects by traversing the relationship graph from the patient's Account record. Every object surfaced on the timeline must have a lookup or master-detail relationship that connects it to Account — either a direct `AccountId` field or a chain of lookups that resolves to Account. Objects related only to Contact, Case, or other non-Account objects cannot be displayed. This is the single most common configuration mistake.

For Health Cloud clinical objects (e.g., `PatientHealthCondition`, `EhrPatientMedication`, `ClinicalEncounter`), the Account relationship is built into the Health Cloud data model and can be referenced directly. For custom objects, verify the relationship chain before writing the `TimelineObjectDefinition`.

### Timeline Categories

Timeline categories are the filter labels that appear in the Industries Timeline component's filter picklist. A practitioner creates category values in Setup and then assigns each `TimelineObjectDefinition` to one category. Well-designed categories group related clinical events (e.g., "Medications", "Encounters", "Labs") so the clinician can filter the timeline to relevant event types without scrolling through unrelated entries.

Categories are configured in **Setup > Timeline > Categories**, not in the metadata file itself. If a `TimelineObjectDefinition` references a category name that does not exist as a configured category value, the timeline will silently omit the filter option — a hard-to-diagnose display gap.

### Legacy vs. Enhanced Timeline Components

The original Health Cloud managed package shipped a `Timeline` component under the `HealthCloud` namespace. This component is **deprecated** as of Health Cloud v236 (Summer '22). Salesforce has directed customers to migrate to the Industries Timeline component, which is backed by `TimelineObjectDefinition` metadata.

Key differences:

| Aspect | Legacy Timeline (HealthCloud.Timeline) | Enhanced Timeline (Industries Timeline) |
|---|---|---|
| Configuration | Custom Settings and list views | TimelineObjectDefinition metadata |
| Object support | Limited to Health Cloud clinical objects | Any object with Account relationship |
| API version | Not metadata-API-configurable | API v55.0+ |
| Filter UI | Hardcoded categories | Configurable timeline categories |
| Future support | Deprecated — no new features | Actively developed |

---

## Common Patterns

### Pattern 1: Adding a Custom Object to the Patient Timeline

**When to use:** An org has a custom object (e.g., `Patient_Visit__c`) with an `Account__c` lookup field, and the care team needs visit records to appear chronologically on the patient record timeline.

**How it works:**

1. Confirm `Patient_Visit__c` has an `Account__c` lookup to Account (or `AccountId` standard field).
2. In Setup > Timeline > Categories, create a category named "Visits" if it does not exist.
3. Create a `TimelineObjectDefinition` metadata record:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TimelineObjectDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <baseObject>Patient_Visit__c</baseObject>
    <dateField>Visit_Date__c</dateField>
    <descriptionField>Visit_Notes__c</descriptionField>
    <icon>event</icon>
    <isActive>true</isActive>
    <label>Patient Visit</label>
    <labelPlural>Patient Visits</labelPlural>
    <nameField>Name</nameField>
    <timelineCategory>Visits</timelineCategory>
</TimelineObjectDefinition>
```

4. Deploy via SFDX or Metadata API. Verify in Setup > Timeline that the definition appears and is active.
5. Open the patient record and confirm the Industries Timeline component shows visits in the expected date range.

**Why not the alternative:** Manually customizing page layouts with related lists is not equivalent — related lists show records in a table, not chronologically alongside other clinical events. The timeline provides the unified chronological view clinical staff need to understand care history at a glance.

### Pattern 2: Migrating from Legacy to Enhanced Timeline

**When to use:** The org was provisioned before Health Cloud v236 and uses the legacy `HealthCloud.Timeline` component. Clinical data appears on the timeline today, but the component is deprecated and no longer receives updates.

**How it works:**

1. Audit which objects currently appear on the legacy timeline using the Health Cloud Custom Settings under `HealthCloud__Timeline__c` or equivalent.
2. For each object, confirm its relationship path to Account.
3. Create `TimelineObjectDefinition` records for each object, matching category labels to the existing filter structure so end users experience minimal change.
4. Add the Industries Timeline Lightning component to the patient page layout (App Builder > drag `Industries Timeline` from component panel).
5. Remove the legacy `HealthCloud.Timeline` component from the same page layout.
6. Validate in a sandbox with representative patient records before deploying to production.

**Why not the alternative:** Leaving both components on the page layout simultaneously causes duplicate entries and performance issues. The two components query independently and do not deduplicate records.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Adding a standard Health Cloud clinical object (EhrPatientMedication, PatientHealthCondition) | Create TimelineObjectDefinition referencing the standard Health Cloud object | These objects already have Account relationships built into the Health Cloud data model |
| Adding a custom object with no Account relationship | Add Account lookup to the custom object first, then create TimelineObjectDefinition | Enhanced Timeline cannot surface the object without Account path |
| Org uses legacy HealthCloud.Timeline | Full migration to Industries Timeline + TimelineObjectDefinition | Legacy component is deprecated; no new features or bug fixes will be delivered |
| Need to filter timeline by event type per user role | Configure timeline categories and use component-level category filtering | Categories are the supported filter mechanism; record type filters on the component are not available |
| Object is related to Contact only, not Account | Evaluate adding an Account lookup or using a junction object | There is no workaround; Account relationship is mandatory for Enhanced Timeline |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify license and permissions** — Confirm the org has Health Cloud or an Industries license that includes Timeline. Check that the running admin user has the "Industries Timeline" permission. Without these, Setup > Timeline will not appear.
2. **Audit object relationships** — For each object to be surfaced, trace the relationship path to Account. Document the lookup field name used. Flag any objects that do not have an Account path before proceeding.
3. **Create timeline categories in Setup** — Navigate to Setup > Timeline > Categories and add any new category values needed (e.g., "Medications", "Encounters", "Labs", "Custom Visits"). Note the exact label spelling — it must match the `timelineCategory` field in the metadata exactly.
4. **Author and deploy TimelineObjectDefinition metadata** — Create one XML file per object in the `timelineObjectDefinitions/` metadata folder. Set `active` to `true`, choose the correct date field, and assign the correct timeline category. Deploy via SFDX (`sf project deploy start`) or Metadata API.
5. **Place the Industries Timeline component on the page layout** — In App Builder, open the patient or member record page and add the `Industries Timeline` component. If the legacy component is present, remove it in the same deployment to avoid duplicate entries.
6. **Validate with representative records** — Open 2–3 patient records that have data in each configured object. Confirm entries appear in the correct date order, under the correct category, with the correct icon and label.
7. **Document the configuration** — Record each TimelineObjectDefinition, its object, date field, and category in the org's admin runbook. Future administrators will need this to diagnose gaps or add new object types.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All target objects have a confirmed Account relationship path (direct lookup or chain)
- [ ] All referenced timeline category values exist in Setup > Timeline > Categories with exact spelling match
- [ ] All TimelineObjectDefinition metadata records are set to `active: true` and deployed successfully
- [ ] Industries Timeline component is on the page layout; legacy HealthCloud.Timeline component is removed if present
- [ ] Timeline renders correctly on at least 2 representative patient records with real data
- [ ] API version in project configuration is v55.0 or later
- [ ] Admin runbook updated with new TimelineObjectDefinition entries and relationship field names

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Legacy component deprecation is silent in production** — The legacy `HealthCloud.Timeline` managed-package component continues to function after deprecation; Salesforce does not force-remove it. Orgs discover the deprecation only when they hit a bug that Salesforce will not fix or when a new Health Cloud release breaks the component. Proactive migration to the Industries Timeline is the only safe path.

2. **Category name mismatch silently drops timeline entries** — If the `timelineCategory` value in a `TimelineObjectDefinition` does not match an active category in Setup > Timeline > Categories (case-sensitive, exact match), the object's records will not appear in the filter picklist and will render uncategorized or not at all depending on component settings. There is no deployment-time validation of this mismatch.

3. **Account relationship is strictly required — Contact-only objects cannot appear** — Practitioners who design custom Health Cloud objects with only a Contact lookup (no Account lookup) cannot surface those objects on the Enhanced Timeline regardless of workarounds. The component's query engine anchors to Account. Retrofitting an Account lookup onto an existing object with data requires a data migration and re-deployment.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `timelineObjectDefinitions/*.timelineObjectDefinition` | Deployable metadata XML files, one per object surfaced on the timeline |
| Timeline category configuration | Category values added in Setup > Timeline > Categories |
| App Builder page layout | Patient/member record page with Industries Timeline component placed and legacy component removed |
| Migration checklist | Tracking sheet for legacy-to-enhanced migration covering each previously configured object |

---

## Related Skills

- `health-cloud-patient-setup` — Person Account and patient record type setup required before timeline configuration makes sense; the timeline anchors to the patient's Account record
