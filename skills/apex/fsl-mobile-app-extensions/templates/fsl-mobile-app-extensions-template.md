# FSL Mobile App Extensions — Work Template

Use this template when working on tasks that involve building or troubleshooting
custom extensions for the Salesforce Field Service (FSL) native mobile app.

## Scope

**Skill:** `fsl-mobile-app-extensions`

**Request summary:** (fill in what the user asked for)

**Extension type:** [ ] LWC Quick/Global Action  [ ] HTML5 Mobile Extension Toolkit (legacy)

**Offline requirement:** [ ] Yes — must work offline  [ ] No — online only

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Target object(s):** (e.g., ServiceAppointment, WorkOrder, WorkOrderLineItem)
- **Extension model confirmed:** (LWC Action or HTML5 Toolkit — justify if HTML5)
- **Offline availability required:** (yes/no — drives page layout and priming config)
- **Custom Metadata Types needed:** (yes/no — if yes, use CMT cache pattern)
- **Estimated records per technician per sync window:** (to assess 1,000 page-reference risk)

## Pre-Flight Checks

- [ ] "Enable Lightning SDK for FSL Mobile" permission set exists in org
- [ ] Permission set is assigned to all target users
- [ ] Briefcase Builder is configured (or will be configured) for target objects

## Approach

Record which pattern(s) from SKILL.md apply:

- [ ] Pattern 1: LWC Quick Action with Offline Support
- [ ] Pattern 2: Custom Metadata Types via Apex Wire + Custom Object Cache
- [ ] Pattern 3: Deep Link for Cross-Record Navigation

**Justification:** (fill in — why this pattern fits the request)

## Extension Inventory

| Extension Name | Type (LWC / HTML5) | Target Object | Action Name | Offline? | Status |
|---|---|---|---|---|---|
| | | | | | |

## LWC Quick Action Checklist

(Complete if building a LWC Quick/Global Action)

- [ ] LWC accepts `@api recordId`
- [ ] Data reads use `@wire` / `uiRecordApi` (not imperative Apex)
- [ ] Data writes use `createRecord` / `updateRecord` (benefits from LDS offline queue)
- [ ] `js-meta.xml` targets `lightning__RecordAction` or `lightning__GlobalAction`
- [ ] Quick Action metadata (`.quickAction-meta.xml`) created and points to LWC
- [ ] Quick Action added to **main page layout** (not only App Builder)

## Briefcase Builder Priming Checklist

(Complete if offline data is required)

- [ ] ServiceResource is the root priming object
- [ ] ServiceAppointments primed under ServiceResource
- [ ] WorkOrders primed under ServiceAppointments
- [ ] WorkOrderLineItems primed under WorkOrders (if needed)
- [ ] Date range filter applied (e.g., next 7 days)
- [ ] Status filter applied (e.g., Scheduled, Dispatched)
- [ ] Estimated page reference count < 750 per technician

## Custom Metadata Type Offline Cache Checklist

(Complete only if CMTs must be available offline)

- [ ] Custom Object created (e.g., `ConfigCache__c`) linked to ServiceResource
- [ ] Apex controller (`@AuraEnabled(cacheable=true)`) queries CMT and returns list
- [ ] LWC wires the Apex method and writes to Custom Object when online
- [ ] LWC reads from Custom Object via `getRecord` when offline
- [ ] Custom Object added to Briefcase Builder priming

## Deep Link Checklist

(Complete if deep links are used)

- [ ] URI constructed using FSL-specific schema
- [ ] Payload passes record IDs, not full field values
- [ ] Total encoded payload size confirmed < 1 MB (target < 900 KB)
- [ ] Navigation tested on device

## Final Review Checklist

- [ ] "Enable Lightning SDK for FSL Mobile" assigned to all target users
- [ ] LWC action on main page layout (if offline required)
- [ ] Briefcase Builder priming tested — records appear when device is offline
- [ ] Extension tested on device in airplane mode
- [ ] No imperative Apex calls for data that must be available offline
- [ ] Custom Metadata Type values available offline (cache pattern) if needed

## Notes

Record any deviations from the standard pattern and the reason:

(fill in)
