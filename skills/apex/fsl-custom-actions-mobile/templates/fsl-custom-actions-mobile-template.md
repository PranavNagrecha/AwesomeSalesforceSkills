# FSL Custom Actions Mobile — Work Template

Use this template when building custom LWC actions for the FSL Mobile app.

## Scope

**Skill:** `fsl-custom-actions-mobile`

**Request summary:** (fill in — e.g. "Barcode scan action for part lookup on Work Order")

## Context Gathered

- **Permission set status:** Enable Lightning SDK for FSL Mobile — assigned / not assigned
- **Action target:** lightning__GlobalAction (app-level) / lightning__RecordAction (record-scoped: _object_)
- **Device capabilities needed:** barcode / GPS / camera / signature / none
- **Offline behavior required:** yes / no

## Component Metadata Checklist

```xml
<!-- Required in .js-meta.xml -->
<targets>
    <target>lightning__GlobalAction</target>
    <!-- OR -->
    <target>lightning__RecordAction</target>
</targets>
```

## Nimbus Plugin Availability Guard

Every capability call must include:

```javascript
import { getBarcodeScanner } from 'lightning/mobileCapabilities';
// or getLocationService, getCameraCapture

const plugin = getBarcodeScanner(); // or appropriate plugin
if (plugin == null || !plugin.isAvailable()) {
    // show fallback UI, do not call device methods
    return;
}
// proceed with plugin.beginCapture() etc.
```

## Implementation Checklist

- [ ] `Enable Lightning SDK for FSL Mobile` permission set assigned to target users
- [ ] `targets` in `.js-meta.xml` set to correct target type
- [ ] All Nimbus plugin calls gated with null check AND `isAvailable()`
- [ ] `endCapture()` called in both `.then()` and `.catch()` for barcode/camera
- [ ] Fallback UI implemented for desktop / non-FSL-Mobile context
- [ ] Action added to correct Setup location (App Manager for Global, page layout for Record)
- [ ] Tested on physical device with FSL Mobile app and permission set

## Notes

(Record deviations from standard pattern and rationale.)
