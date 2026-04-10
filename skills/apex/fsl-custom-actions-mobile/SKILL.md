---
name: fsl-custom-actions-mobile
description: "Use this skill when building custom LWC actions for the FSL Mobile app: barcode scanning, GPS capture, photo/signature capture, or custom guided workflows on mobile. Trigger keywords: FSL Mobile custom action, lightning__GlobalAction FSL, barcode scanner LWC, mobileCapabilities, Nimbus plugin, FSL lightning SDK. NOT for standard Salesforce Mobile App quick actions, standard Experience Cloud pages, or desktop Lightning Experience LWC components."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Security
  - Reliability
triggers:
  - "Custom LWC action not showing up in FSL Mobile app after adding to page layout"
  - "How to implement barcode scanning in FSL Mobile using LWC and Nimbus plugins"
  - "GPS location capture from a custom action in Field Service Mobile app"
  - "lightning__GlobalAction component works on desktop but not in FSL Mobile"
  - "Enable Lightning SDK for FSL Mobile permission set required for custom actions"
tags:
  - fsl
  - field-service
  - lwc
  - mobile
  - fsl-custom-actions-mobile
  - nimbus
  - barcode
inputs:
  - "Target device capability needed (barcode, GPS, camera/photo, signature)"
  - "Whether the Enable Lightning SDK for FSL Mobile permission set is assigned"
  - "Action target: lightning__GlobalAction (app-level) or lightning__RecordAction (record-level)"
outputs:
  - "LWC component with correct target configuration for FSL Mobile"
  - "Nimbus plugin capability check pattern before using device API"
  - "Page layout or App Manager configuration to surface the action"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Custom Actions Mobile

This skill activates when a developer needs to build custom LWC actions that run inside the FSL Mobile app — including barcode scanning, GPS-based actions, photo capture, and guided work flows. It covers the Lightning SDK for FSL Mobile, the Nimbus plugin device API, and the critical deployment constraints that differ from standard Lightning Experience LWC development.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the `Enable Lightning SDK for FSL Mobile` permission set is assigned to all technician users. Without it, custom LWC actions silently fail to load in FSL Mobile even if page layout configuration is correct.
- Determine the action scope: `lightning__GlobalAction` (available from the app-level action bar — not tied to a specific record) or `lightning__RecordAction` (surfaced on a specific object's record page, e.g., Work Order). The targets have different page layout configuration paths.
- Identify which device capabilities are needed. All Nimbus plugin calls must be gated with `isAvailable()` before invocation — calling without availability check throws on devices or simulators where the capability is absent.
- Check whether the org uses the legacy HTML5 Mobile Extension Toolkit. The LWC-based Lightning SDK model is separate and not interchangeable with the legacy toolkit.

---

## Core Concepts

### Lightning SDK for FSL Mobile

The Lightning SDK is the framework that enables custom LWC components to run natively inside the FSL Mobile app (iOS and Android). Components authored for the Lightning SDK use standard LWC syntax but gain access to device-level capabilities via Nimbus plugins — the bridge between JavaScript and native device APIs.

**Critical constraint:** Components with `lightning__GlobalAction` target render ONLY in FSL Mobile. They do not render in the standard Lightning Experience desktop, the standard Salesforce Mobile App, or Experience Cloud. Developers who test a `lightning__GlobalAction` LWC in the desktop browser will see it in the page layout configuration but it will not function in the mobile app without the permission set and correct app configuration.

### Nimbus Plugins — Device Capability Bridge

Nimbus plugins expose native device APIs to LWC JavaScript:

| Plugin Import | Capability |
|---|---|
| `lightning/mobileCapabilities` | Meta-module — use to get specific plugins |
| `getBarcodeScanner()` | Barcode and QR code scanning |
| `getLocationService()` | GPS coordinates |
| `getCameraCapture()` | Photo capture |

**Availability gate (mandatory):** Every Nimbus plugin must be checked with `isAvailable()` before calling its methods. On desktop or when the permission set is missing, the plugin returns null and calling methods on null throws immediately.

```javascript
import { getBarcodeScanner } from 'lightning/mobileCapabilities';
const scanner = getBarcodeScanner();
if (scanner == null || !scanner.isAvailable()) {
    // Show disabled state or fallback
    return;
}
```

### Action Target Configuration

- `lightning__GlobalAction`: Added to the FSL Mobile app's global action set in Setup > Apps > App Manager > FSL Mobile App. Appears in the mobile app's "+" action bar.
- `lightning__RecordAction`: Added to the page layout of a specific object (e.g., Work Order). Appears in the record's action panel in FSL Mobile.

Both require the component to declare the correct `targets` in its `.js-meta.xml` metadata.

---

## Common Patterns

### Barcode Scan Action

**When to use:** Technician needs to scan a product barcode to look up a part or confirm a serial number during a work order.

**How it works:**

```javascript
// barcodeScanAction.js
import { LightningElement } from 'lwc';
import { getBarcodeScanner } from 'lightning/mobileCapabilities';

export default class BarcodeScanAction extends LightningElement {
    scanner;
    scannedCode = '';

    connectedCallback() {
        this.scanner = getBarcodeScanner();
    }

    get isScanAvailable() {
        return this.scanner != null && this.scanner.isAvailable();
    }

    handleScan() {
        if (!this.isScanAvailable) {
            return; // show error toast in real implementation
        }
        this.scanner.beginCapture({
            barcodeTypes: [this.scanner.BARCODE_TYPE_CODE128, this.scanner.BARCODE_TYPE_QR]
        }).then(result => {
            this.scannedCode = result.value;
            this.scanner.endCapture();
        }).catch(err => {
            this.scanner.endCapture();
        });
    }
}
```

**Why not HTML input:** Camera-based HTML5 input doesn't integrate with the device's native barcode scanning engine and produces unreliable results in field conditions.

### GPS Location Capture

**When to use:** Technician needs to stamp GPS coordinates on arrival at a job site.

**How it works:**

```javascript
import { getLocationService } from 'lightning/mobileCapabilities';

connectedCallback() {
    const locationService = getLocationService();
    if (locationService != null && locationService.isAvailable()) {
        locationService.getCurrentPosition({
            enableHighAccuracy: true,
            timeout: 10000
        }).then(result => {
            const lat = result.coords.latitude;
            const lng = result.coords.longitude;
            // Update record via Apex or wire
        });
    }
}
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Action from main mobile nav | `lightning__GlobalAction` + App Manager | App-level, not tied to a record |
| Action on Work Order record | `lightning__RecordAction` + page layout | Record-scoped |
| Barcode scanning | `getBarcodeScanner()` with `isAvailable()` guard | Native barcode integration |
| GPS stamp | `getLocationService()` with high accuracy | Device GPS vs. browser geolocation |
| Photo documentation | `getCameraCapture()` Nimbus plugin | Native camera via Nimbus |
| Testing on desktop | Guard with `isAvailable()` = false, show fallback UI | Desktop has no Nimbus bridge |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm `Enable Lightning SDK for FSL Mobile` permission set** — Assign to all FSL Mobile users before attempting any deployment or testing. Missing this causes silent failure.
2. **Choose and declare action target** — Set `lightning__GlobalAction` or `lightning__RecordAction` in the LWC's `.js-meta.xml` `<targets>` section.
3. **Import and guard Nimbus plugins** — Import the required plugin from `lightning/mobileCapabilities`. Check `isAvailable()` before any device capability call. Build a visible fallback for desktop/non-supported contexts.
4. **Configure in Setup** — For `lightning__GlobalAction`: App Manager > FSL Mobile App > Action Bar. For `lightning__RecordAction`: page layout editor for the target object.
5. **Test on a physical FSL Mobile device** — Desktop browser testing will not invoke Nimbus plugins. Use a real iOS/Android device with FSL Mobile installed and permission set assigned.
6. **Handle offline behavior** — Verify action behavior when the device is offline; FSL Mobile's briefcase sync controls which records are available offline, not the LWC itself.

---

## Review Checklist

- [ ] `Enable Lightning SDK for FSL Mobile` permission set assigned to target users
- [ ] `targets` in `.js-meta.xml` includes the correct target type
- [ ] All Nimbus plugin calls gated with `isAvailable()` check
- [ ] Fallback UI implemented for non-FSL-Mobile context
- [ ] Action added to correct location in Setup
- [ ] Tested on physical device with FSL Mobile app installed
- [ ] Offline behavior understood

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`lightning__GlobalAction` components do NOT render in Lightning Experience desktop or standard Salesforce Mobile App** — They only appear in FSL Mobile. Testing on desktop appears to work in configuration but produces no visible component for users.
2. **Missing permission set causes silent load failure** — No error is displayed to the technician. The action simply does not appear. Always verify the permission set before troubleshooting component code.
3. **Nimbus plugin returns null on desktop** — `getBarcodeScanner()` returns null in standard Lightning Experience. Calling `.beginCapture()` on null throws immediately. The `isAvailable()` guard is mandatory, not optional.
4. **Legacy HTML5 Mobile Extension Toolkit and LWC are not interchangeable** — Components built with the old toolkit require a full rewrite to use Nimbus plugins. Do not mix configuration from both models in the same org.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| LWC component with Nimbus integration | JavaScript + HTML + XML metadata with correct target and Nimbus availability guard |
| Permission set assignment checklist | Permission sets required for FSL Mobile custom actions |

---

## Related Skills

- apex/fsl-apex-extensions — Broader FSL Apex namespace and SDK patterns
- architect/fsl-offline-architecture — Offline data priming and sync behavior affecting custom action data access
