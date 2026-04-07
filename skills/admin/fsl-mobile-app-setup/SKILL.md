---
name: fsl-mobile-app-setup
description: "Use this skill when configuring, extending, or troubleshooting the Salesforce Field Service (FSL) Mobile app for field technicians — including offline priming strategy, app extensions, deep linking, and custom branding. Trigger keywords: FSL mobile, Field Service mobile app, offline priming, mobile extension toolkit, app extensions for field service. NOT for standard Salesforce Mobile app configuration, Lightning App Builder layouts for desktop, or Field Service Lightning dispatcher console setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
  - Operational Excellence
triggers:
  - "field service mobile app not syncing data when technician goes offline"
  - "how do i add a custom screen or action inside the FSL mobile app"
  - "field technician cannot see work orders or appointments on their phone"
  - "how to configure offline priming for field service mobile"
  - "deep linking into field service mobile app from another app"
  - "custom branding logo and colors not showing in FSL mobile app"
  - "difference between LWC quick action and HTML5 mobile extension in field service"
tags:
  - field-service
  - fsl-mobile
  - offline
  - app-extensions
  - deep-linking
  - mobile
  - offline-priming
inputs:
  - "Field Service Mobile license and Field Service license assigned to technician users"
  - "FSL Mobile app version in use (iOS/Android)"
  - "List of objects and related lists technicians need offline"
  - "Whether custom branding or Mobile App Plus add-on is available"
  - "Any existing LWC quick actions or custom buttons to surface in the app"
outputs:
  - "Configured offline priming strategy with hierarchy and record limits documented"
  - "App extension type recommendation (LWC vs HTML5 Mobile Extension Toolkit)"
  - "Deep link URI scheme configuration with payload size guidance"
  - "Review checklist for FSL Mobile rollout"
  - "Validation of offline priming page reference count against the 1,000-record limit"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# FSL Mobile App Setup

This skill activates when a practitioner needs to configure, extend, or troubleshoot the Salesforce Field Service (FSL) Mobile native app — including offline data priming, LWC or HTML5 app extensions, deep linking, and custom branding. It does not cover the standard Salesforce Mobile app or the FSL dispatcher console.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has Field Service and Field Service Mobile licenses provisioned. The FSL Mobile app is a distinct native iOS/Android application — it is NOT the standard Salesforce Mobile app and does not share the same configuration surface.
- The most common wrong assumption is that FSL Mobile renders the same Lightning pages as desktop or standard mobile. It does not. It has its own offline-first data model, its own extension framework, and its own priming pipeline.
- Key platform constraints: offline priming is limited to 50 records per related list and 1,000 total page references per resource. Exceeding 1,000 page references causes a silent failure — no error is surfaced to the user or admin.

---

## Core Concepts

### FSL Mobile Is a Separate Native App

The Salesforce Field Service Mobile app (FSL Mobile) is a distinct native application for iOS and Android, separate from the standard Salesforce Mobile app. It is built for offline-first operation: technicians download their data during a priming sync, then work without a network connection. When connectivity is restored, changes sync back to the org. Configuration is done through the Field Service Mobile Settings in Setup, not through Mobile App Builder or standard app configuration.

### Offline Priming Hierarchy

Offline priming determines which records are downloaded to the technician's device. The priming hierarchy is structured as:

1. **Resource** (the technician's ServiceResource record)
2. **Service Appointments** assigned to the resource
3. **Work Orders** linked to those appointments
4. **Work Order Line Items** under those work orders

Each level follows the one above. You cannot prime work order line items unless work orders are primed. The platform enforces a limit of **50 records per related list** and **1,000 total page references per resource** across the priming run. Exceeding 1,000 page references results in silent truncation — no error is raised, and technicians silently lose access to some records without knowing why.

### App Extension Models

There are two extension models for adding custom screens and actions to FSL Mobile:

1. **LWC Quick Actions and Global Actions (recommended):** Lightning Web Components surfaced as quick actions on supported objects (Work Order, Service Appointment, etc.) or as global actions. These use Lightning Data Service (LDS) for data access and are the preferred modern approach. LWC components run inside the app's WebView container and support standard `@wire` adapters and `uiRecordApi` calls.

2. **HTML5 Mobile Extension Toolkit (legacy):** A proprietary toolkit for building HTML5-based extensions embedded in the app. It does NOT support LWC, Lightning Data Service, or Aura. Data access must go through Apex REST endpoints explicitly. Use only when LWC quick actions cannot meet the requirement (e.g., complex multi-step wizards introduced before LWC support landed).

### Deep Linking

FSL Mobile supports a custom URI scheme that allows external apps (e.g., mapping apps, barcode scanners, third-party scheduling tools) to deep link into specific records or actions inside the FSL Mobile app. The deep link carries a data payload encoded in the URI. The maximum supported payload size is **1 MB per link**. Payloads exceeding 1 MB will be silently dropped or cause link failure. Deep link configuration is managed through the Field Service Mobile Settings connected app and the URI scheme registered with the mobile OS.

### Custom Branding

Custom branding (splash screen, app icon, logo, color scheme) for FSL Mobile requires the **Mobile App Plus add-on license**. Without this add-on, the app uses the default Salesforce Field Service branding. Configuring branding without the add-on will appear to succeed in Setup but the changes will not be reflected in the app.

---

## Common Patterns

### Pattern: Offline-First Data Coverage for Technicians

**When to use:** Technicians report missing work orders, line items, or related records when they go offline.

**How it works:**
1. Map all objects technicians need offline against the priming hierarchy (resource → appointments → work orders → line items).
2. For each related list added to the priming config, count the expected maximum records in that list per resource per day. Keep each related list at or below 50 records.
3. Sum all page references across all related lists for a typical resource. Keep the total under 1,000.
4. Enable offline sync for each required object in Field Service Mobile Settings → Data Sync.
5. Test by simulating a full offline priming sync on a test device and verifying all records appear before disabling the network.

**Why not the alternative:** Simply enabling "offline" for an object is not enough. Without configuring the priming hierarchy explicitly, the platform does not know which records belong to which resource, and the technician's device will either be empty or over limit.

### Pattern: LWC Quick Action as App Extension

**When to use:** Adding a custom data-capture screen (e.g., capture a reading, scan a barcode result, log a safety checklist) directly on a Work Order or Service Appointment in FSL Mobile.

**How it works:**
1. Build a standard LWC component with `@api recordId` to accept context.
2. Use `@wire(getRecord)` or `uiRecordApi` for reads; use `updateRecord` or an Apex method for writes.
3. Create a Quick Action on the Work Order (or target object) of type "Lightning Web Component" pointing to the LWC.
4. In Field Service Mobile Settings, add the quick action to the relevant action list for the object.
5. Test in the FSL Mobile app — quick actions appear in the action bar at the bottom of the record detail page.

**Why not the alternative:** The HTML5 Mobile Extension Toolkit requires Apex REST endpoints, cannot use LDS, and adds significant boilerplate. Use LWC quick actions unless you have a legacy toolkit already in place or a specific UI requirement LWC cannot meet.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New custom screen on Work Order in FSL Mobile | LWC Quick Action | Uses LDS, less boilerplate, supported path forward |
| Legacy HTML5 extension already exists and needs minor updates | Keep HTML5 Extension Toolkit, don't rewrite unless scope permits | Rewriting carries risk; toolkit is still supported |
| Technicians missing records offline | Audit priming hierarchy and page reference count | Silent truncation at 1,000 refs; 50 records per related list max |
| Need custom app icon/branding for FSL Mobile | Confirm Mobile App Plus add-on before configuring | Without add-on, branding changes do not apply |
| External app needs to launch FSL Mobile on a specific record | Deep link via custom URI scheme | Built-in mechanism; keep payload under 1 MB |
| Technician needs to access a Visualforce page inside FSL Mobile | Not directly supported; use LWC quick action or HTML5 extension instead | VF is not rendered in FSL Mobile container |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm prerequisites:** Verify the org has Field Service and Field Service Mobile licenses. Confirm the target users have the Field Service Mobile permission set and the `FieldServiceMobileUser` permission. Establish the FSL Mobile app version currently deployed.
2. **Map offline data requirements:** List every object and related list technicians need while offline. For each related list, estimate maximum records per resource per day. Confirm all lists are within the 50-record per related list limit and the total page references per resource remain below 1,000.
3. **Configure offline priming:** In Setup → Field Service Mobile Settings, enable Data Sync for each required object. Map the priming configuration to the resource → appointment → work order → line item hierarchy. Add related lists only for objects within the hierarchy.
4. **Design and build app extensions:** For custom actions or screens, choose LWC Quick Actions (preferred) or HTML5 Mobile Extension Toolkit (legacy). Scaffold the LWC with `@api recordId`, use `uiRecordApi` for data access, and register the quick action on the target object. Add the action to the FSL Mobile action list in Field Service Mobile Settings.
5. **Configure deep links if needed:** Register the custom URI scheme in the connected app settings for FSL Mobile. Define target record types and action identifiers. Keep all payloads below 1 MB. Test deep links from the source app on a physical device.
6. **Configure branding if licensed:** Confirm the Mobile App Plus add-on is provisioned before attempting branding changes. Upload assets in Field Service Mobile Settings → Branding. Branding changes require a republish of the connected app and a reinstall or cache clear on the device.
7. **Validate and test end-to-end on device:** Perform a full priming sync on a test device. Disable the network and verify all expected records are accessible. Test each quick action. Test deep links from external apps. Confirm no silent priming failures by cross-referencing record counts on device against expected counts in the org.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Field Service and Field Service Mobile licenses confirmed on affected user profiles
- [ ] Offline priming hierarchy configured (resource → appointments → work orders → line items)
- [ ] Each related list in priming config has 50 or fewer records in production data range
- [ ] Total page references per resource confirmed below 1,000
- [ ] App extensions use LWC Quick Actions (or HTML5 toolkit with documented justification)
- [ ] Deep link payloads verified below 1 MB if deep linking is in scope
- [ ] Custom branding only configured if Mobile App Plus add-on is licensed
- [ ] End-to-end offline test completed on physical iOS and/or Android device
- [ ] Technician user profiles have correct permission sets and app access

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Silent page reference truncation at 1,000** — If a resource's total page references across all priming objects and related lists exceeds 1,000, the priming sync completes without error but silently drops records. Technicians arrive on-site without the data they need. There is no warning in Setup or in the app. Monitor page reference counts proactively by auditing object counts before rollout.

2. **FSL Mobile is not the standard Salesforce Mobile app** — Configuration done in Mobile App Builder, App Manager (for the Salesforce app), or standard Lightning App pages has no effect on FSL Mobile. FSL Mobile has its own settings under Field Service Mobile Settings. Practitioners who configure the wrong surface waste significant time and wonder why changes don't appear in the app.

3. **HTML5 Mobile Extension Toolkit has no LWC or LDS support** — LLMs and practitioners familiar with modern LWC development may attempt to use `@wire`, `lightning-record-form`, or other LDS-backed components inside an HTML5 extension. These simply do not work. Data must be fetched via explicit REST calls to Apex endpoints exposed as REST resources.

4. **Custom branding silently does nothing without Mobile App Plus** — The branding configuration UI in Field Service Mobile Settings is always visible regardless of license. Saving branding assets without Mobile App Plus appears to succeed, but the changes are never applied to the app. Always verify the add-on is provisioned before doing branding work.

5. **Deep links are silently dropped above 1 MB** — There is no error surfaced to the user or the calling app when a deep link payload exceeds 1 MB. The link simply fails to open the target. Always test deep links with realistic worst-case payloads.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Offline priming configuration plan | Table mapping each required object to the priming hierarchy, with record count estimates and page reference totals |
| App extension type decision | Documented choice between LWC Quick Action and HTML5 toolkit, with rationale |
| Deep link specification | URI scheme, target record types, payload structure, and size budget |
| FSL Mobile rollout checklist | Completed review checklist with license confirmation, priming test results, and device test sign-off |

---

## Related Skills

- lwc/lwc-offline-and-mobile — LWC-specific offline and mobile patterns for components running inside the FSL or standard Salesforce Mobile app
- admin/field-service-dispatcher-console — Dispatcher console configuration, scheduling optimization, and territory management (distinct from mobile app setup)
