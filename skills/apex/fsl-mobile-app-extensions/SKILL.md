---
name: fsl-mobile-app-extensions
description: "Use when building custom LWC Quick Actions, Global Actions, deep links, or offline data extensions for the Salesforce Field Service (FSL) native mobile app. Trigger keywords: FSL mobile extension, LWC action FSL, field service deep link, offline custom action, FSL mobile toolkit. NOT for LWC in standard Salesforce mobile app or Lightning Experience."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
triggers:
  - "how do I add a custom button or LWC action inside the FSL mobile app for technicians"
  - "field service mobile custom screen not available offline even though it is deployed"
  - "how to pass record context or navigate between records using deep links in FSL mobile"
tags:
  - fsl-mobile-app-extensions
  - field-service
  - lwc-actions
  - offline-data
  - deep-linking
  - mobile-extensions
inputs:
  - target object for the extension (ServiceAppointment, WorkOrder, WorkOrderLineItem, etc.)
  - extension type required (LWC Quick/Global Action vs legacy HTML5 Mobile Extension Toolkit)
  - offline availability requirement (yes/no)
  - list of records or related objects that must be primed offline
  - whether Custom Metadata Types need to be available offline
outputs:
  - LWC component and metadata (js-meta.xml) for the Quick/Global Action
  - permission set assignment guidance for "Enable Lightning SDK for FSL Mobile"
  - page layout configuration steps to enable offline availability
  - Briefcase Builder priming hierarchy and object configuration
  - deep link URI construction and payload sizing guidance
  - Apex wire adapter pattern for offline-unavailable data (e.g., Custom Metadata Types)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Mobile App Extensions

This skill activates when a practitioner needs to build, configure, or troubleshoot custom extensions inside the Salesforce Field Service (FSL) native mobile app — including LWC Quick/Global Actions, deep links, offline data priming, and the legacy HTML5 Mobile Extension Toolkit. It does NOT cover LWC components running in the standard Salesforce Mobile app or Lightning Experience.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the target app is the FSL native mobile app (not standard Salesforce Mobile). The two apps have different extension models and different permission requirements.
- Determine whether the extension must work offline. If yes, both the permission set assignment AND the page layout placement are mandatory — neither alone is sufficient.
- Identify all objects that need to be available offline, including whether Custom Metadata Types are involved (they cannot be primed via Briefcase Builder and require a different approach).

---

## Core Concepts

### Two Extension Models: LWC Actions vs HTML5 Mobile Extension Toolkit

The FSL mobile app supports two distinct extension models.

**LWC Quick/Global Actions (modern, recommended):** Standard Salesforce LWC components deployed as Quick Actions (on an object) or Global Actions. The component receives `@api recordId` and uses standard LDS wire adapters (`uiRecordApi`). These are the default choice for all new extensions. They render natively inside FSL Mobile but do NOT render inside standard Lightning Experience or standard Salesforce Mobile — a `lightning__GlobalAction` LWC target is FSL-specific.

**HTML5 Mobile Extension Toolkit (legacy):** A separate extension framework predating LWC. Extensions are written as plain HTML/JavaScript pages. They cannot use native LWC elements or import LWC modules (`lwc`, `lightning/uiRecordApi`, `@salesforce/`). Apex is accessible only via REST API calls, not via `@wire` or Apex method imports. Use this model only when maintaining existing legacy extensions or when a native capability (e.g., device camera API via a specific SDK method) is not yet available in the LWC path.

### Permission Set Requirement: "Enable Lightning SDK for FSL Mobile"

LWC Quick/Global Actions in FSL Mobile require the **"Enable Lightning SDK for FSL Mobile"** permission set to be assigned to every user who will use the extension. Without it, the action button either does not appear or throws an error at runtime. This permission set is not included in standard FSL license assignments — it must be explicitly assigned.

### Offline Availability: Page Layout Placement Is Mandatory

For an LWC action to be available when the device is offline, two conditions must both be true:

1. The user has the "Enable Lightning SDK for FSL Mobile" permission set assigned.
2. The LWC action is added to the **main page layout** of the target object — not just to an App Builder page or a related list button.

If the action is added only through App Builder and not to the page layout, it will work when online but will be missing when the device is offline. This is the most common misconfiguration.

### Deep Links: FSL URI Schema and the 1 MB Limit

FSL Mobile supports a custom deep link URI schema for encoding record context and navigation targets. Deep links can open specific records, trigger actions, or pre-populate fields. The encoded payload has a hard limit of **1 MB**. Attempting to pass a payload larger than 1 MB will silently truncate or fail — no runtime error is surfaced to the user. Always calculate payload size before encoding, and pass record IDs rather than full record data wherever possible.

### Briefcase Builder Priming: Hierarchy and the 1,000 Page-Reference Limit

Briefcase Builder controls which records are downloaded to the device when the technician primes (syncs) their data. The priming hierarchy is hierarchical and must be configured in order:

```
ServiceResource → ServiceAppointments → WorkOrders → WorkOrderLineItems
```

Each level depends on the level above it. Configuring a child object without the parent will result in no data being primed for that child.

The Briefcase Builder configuration has a hard limit of **1,000 page references** per priming run. Exceeding this limit causes records beyond the limit to be silently dropped — no error is shown and the technician sees no warning. Monitor record counts per technician and use filters (e.g., date ranges, status values) to stay well below 1,000.

**Custom Metadata Types cannot be primed via Briefcase Builder.** They are not supported as a priming target. To make Custom Metadata Type data available offline, use an Apex wire adapter that reads the values at load time when online and stores them in a local Custom Object record or in the LWC component's local cache. Alternatively, hard-code non-sensitive configuration values directly in the LWC component.

---

## Common Patterns

### Pattern 1: LWC Quick Action with Offline Support

**When to use:** When a technician needs a custom screen (form, checklist, guided step) on a ServiceAppointment or WorkOrder that must work without connectivity.

**How it works:**
1. Create an LWC component that accepts `@api recordId`.
2. Use `@wire(getRecord, ...)` from `lightning/uiRecordApi` to read record data — wire adapters use the LDS offline cache automatically.
3. Use `updateRecord` or `createRecord` for writes — these queue offline and sync when connectivity resumes.
4. Set `targets` in `lwc.js-meta.xml` to `lightning__RecordAction` (Quick Action) or `lightning__GlobalAction`.
5. Create a Quick Action on the object pointing to the LWC.
6. Add the Quick Action to the **main page layout** of the object (not just App Builder).
7. Assign the "Enable Lightning SDK for FSL Mobile" permission set to all users.

**Why not the alternative:** Using imperative Apex calls (`@wire(apexMethod)` with `wire` is fine; `import { callApex }` imperatively at button click is not) bypasses the LDS cache, so data is not available offline.

### Pattern 2: Custom Metadata Types Available Offline via Apex Wire + Custom Object Cache

**When to use:** When extension logic depends on configuration stored in Custom Metadata Types (e.g., picklist mappings, threshold values, routing rules).

**How it works:**
1. Create an Apex method annotated `@AuraEnabled(cacheable=true)` that queries the Custom Metadata Type and returns a serialized list.
2. Wire the method in the LWC: `@wire(getConfigValues) configValues`.
3. On first load (online), write the values into a Custom Object record linked to the ServiceResource or a well-known singleton record.
4. On subsequent offline loads, read the Custom Object record via standard `getRecord` wire adapter.

**Why not the alternative:** Briefcase Builder does not support Custom Metadata Types as a priming target. If you rely solely on the CMT wire call, the extension will fail offline with a network error.

### Pattern 3: Deep Link for Cross-Record Navigation

**When to use:** When the technician needs to navigate from a ServiceAppointment to a related WorkOrder, or launch an action pre-populated with context from the current record.

**How it works:**
1. Construct the FSL deep link URI using the FSL-specific schema documented in the Field Service Developer Guide.
2. Pass record IDs and action targets — avoid embedding full record field values in the payload.
3. Validate that the total encoded payload is under 1 MB.
4. Render the link in the LWC as a button using `NavigationMixin` or a plain anchor with the `href` set to the deep link URI.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New custom screen or action for technician | LWC Quick Action (RecordAction target) | Modern, supported, offline-capable via LDS, maintainable |
| Existing HTML5 extension that must be updated | Stay in HTML5 Toolkit, update in place | Migration to LWC requires full re-test of offline behavior |
| Data from Custom Metadata Types needed offline | Apex wire + Custom Object cache | Briefcase Builder cannot prime CMTs |
| Cross-record navigation in mobile | FSL deep link URI | NavigationMixin alone does not support FSL-specific targets |
| Configuration that is not sensitive, changes rarely | Hard-code in LWC component | Simpler than CMT cache pattern, zero offline risk |
| Extension that only runs when online | LWC Quick Action without layout placement (but document this clearly) | Reduces layout clutter; acceptable if truly online-only |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Determine extension model.** Confirm whether a new LWC Quick/Global Action or the legacy HTML5 Toolkit is required. Default to LWC for all new work. Document the justification if choosing HTML5 Toolkit.
2. **Audit permissions.** Verify the "Enable Lightning SDK for FSL Mobile" permission set exists in the org and is assigned to all target users. This is a prerequisite for any LWC extension.
3. **Build the LWC component.** Use `@api recordId`, `@wire(getRecord)` for reads, and `createRecord`/`updateRecord` for writes. Avoid imperative Apex calls for data that must be offline-accessible.
4. **Configure the Action and page layout.** Create the Quick Action or Global Action pointing to the LWC. Add it to the **main page layout** (not just App Builder) if offline availability is required.
5. **Configure Briefcase Builder priming.** Set up the priming hierarchy (Resource → ServiceAppointments → WorkOrders → WorkOrderLineItems). Apply filters to keep record counts below 1,000 page references. Handle Custom Metadata Types via the Apex wire + Custom Object cache pattern separately.
6. **Test offline behavior.** Put the test device in airplane mode, open the FSL mobile app, and confirm the action appears and executes. Check that any CMT-dependent data is readable.
7. **Validate deep links (if applicable).** Construct and test deep link URIs, confirm payloads are under 1 MB, and verify navigation lands on the correct record and action.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] "Enable Lightning SDK for FSL Mobile" permission set assigned to all target users
- [ ] LWC Quick Action added to the main page layout (not only App Builder) if offline is required
- [ ] All record reads use `@wire(getRecord)` or other LDS-backed adapters, not imperative Apex
- [ ] Briefcase Builder priming hierarchy configured (Resource → SA → WO → WOLI); record count filters applied
- [ ] Custom Metadata Types that must be offline-accessible are cached in a Custom Object via Apex wire pattern
- [ ] Deep link payloads tested and confirmed under 1 MB
- [ ] Extension tested on device in airplane mode

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Offline layout requirement silently disables actions** — Adding a LWC Quick Action to an App Builder page but not to the main page layout causes it to be fully invisible when the device is offline. There is no error message. Technicians simply do not see the button. Always add to the page layout.
2. **"Enable Lightning SDK for FSL Mobile" is not part of FSL license** — Assigning a Field Service Mobile license does not automatically grant this permission set. It must be assigned separately. Forgetting it causes the action to fail or not appear for specific users.
3. **Briefcase Builder silently drops records past 1,000 page references** — There is no warning when the priming run exceeds the limit. Technicians arrive on-site without critical records. Use status and date filters in Briefcase Builder to control volume.
4. **Custom Metadata Types cannot be primed** — Briefcase Builder does not list CMTs as a priming target. Extensions that wire CMT data directly will return empty results offline. Must use the Custom Object cache workaround.
5. **`lightning__GlobalAction` LWC does not render in Lightning Experience** — An LWC component targeted at `lightning__GlobalAction` for FSL Mobile renders only inside the FSL native app. It will not appear in standard Lightning Experience or standard Salesforce Mobile. This is by design, not a bug, but it means the component cannot be tested in the desktop browser's record page.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| LWC component (`js`, `html`, `js-meta.xml`) | The custom action component wired for offline-compatible data access |
| Quick Action metadata | QuickAction XML pointing to the LWC, targeting the correct object |
| Permission set assignment instructions | Steps to assign "Enable Lightning SDK for FSL Mobile" |
| Page layout configuration steps | Which layout to edit and where to add the Quick Action |
| Briefcase Builder priming configuration | Object hierarchy, filter criteria, and page reference budget |
| Apex wire adapter + Custom Object cache (if CMTs needed) | Apex class and Custom Object schema for offline CMT workaround |
| Deep link URI template (if navigation needed) | URI construction pattern with payload size guidance |

---

## Related Skills

- admin/fsl-mobile-app-setup — admin-side configuration of FSL mobile (app settings, connected app, initial priming setup); use alongside this skill for end-to-end FSL mobile work
- lwc/lwc-offline-and-mobile — LWC-specific offline patterns (LDS cache, conflict resolution, sync queue) for components running in FSL or standard mobile

## Official Sources Used

- Customize FSL Mobile with LWC — https://help.salesforce.com/s/articleView?id=sf.fs_mobile_extension_lwc.htm
- Deep Linking Schema — Field Service Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_mobile_deep_linking.htm
- FSL Mobile Extension Overview — https://help.salesforce.com/s/articleView?id=sf.fs_mobile_extensions.htm
- Offline Priming and Briefcase Builder — https://help.salesforce.com/s/articleView?id=sf.fs_mobile_priming.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
