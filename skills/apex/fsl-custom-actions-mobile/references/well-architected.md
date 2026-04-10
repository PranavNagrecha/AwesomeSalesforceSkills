# Well-Architected Notes — FSL Custom Actions Mobile

## Relevant Pillars

- **Performance** — Nimbus plugin calls (barcode, GPS, camera) are native device API calls. They are fast but depend on hardware state (GPS signal, camera permissions, lighting). Always implement async patterns with timeout handling and graceful degradation for poor signal conditions.
- **Reliability** — FSL Mobile operates in offline conditions. Custom LWC actions must handle the case where the device is offline and record writes must queue for sync. The `isAvailable()` guard prevents crashes when device capabilities are absent.
- **Security** — Device capability permissions (camera, location) require explicit user consent on both iOS and Android. The `Enable Lightning SDK for FSL Mobile` permission set controls which Salesforce users can access these capabilities. Audit permission set assignment as part of FSL user provisioning.

## Architectural Tradeoffs

**GlobalAction vs. RecordAction:** `lightning__GlobalAction` provides a persistent entry point from any screen in FSL Mobile — best for general-purpose field utilities (barcode lookup, GPS check-in). `lightning__RecordAction` scopes the action to a specific record type — best for context-sensitive workflows (photo documentation on a work order, parts consumption confirmation on a WOLI). Choose based on whether the context of the action matters.

**Native Nimbus vs. HTML5 fallback:** The Nimbus plugin provides better fidelity, especially for barcode scanning in poor lighting. However, if the action also needs to work on desktop (for supervisor review or admin testing), implement a dual path: Nimbus in FSL Mobile, HTML5/manual input elsewhere, gated by `isAvailable()`.

## Anti-Patterns

1. **Calling Nimbus methods without isAvailable() guard** — Nimbus plugins return null outside FSL Mobile. Any method call on null throws immediately and crashes the component. The guard is not optional defensive coding — it is required for any deployment that touches non-FSL-Mobile contexts.
2. **Testing custom actions only in the desktop browser** — Desktop validation produces false confidence. `lightning__GlobalAction` components may appear in App Manager configuration but only render in FSL Mobile. Always test on a physical device.
3. **Mixing legacy HTML5 Mobile Extension Toolkit and LWC SDK** — These are separate frameworks with different configuration paths. LWC components with Nimbus plugins cannot be configured through the legacy toolkit's extension points.

## Official Sources Used

- Scan Barcodes in FSL Mobile (developer.salesforce.com) — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_mobile_barcode.htm
- lightning/mobileCapabilities Module (LWC Developer Guide) — https://developer.salesforce.com/docs/component-library/bundle/lightning-mobile-capabilities/documentation
- FieldServiceMobileSettings Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_fieldservicemobilesettings.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
