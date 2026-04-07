# Gotchas — FSL Mobile App Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Silent Truncation at 1,000 Page References

**What happens:** When the total number of page references in an offline priming run for a single resource exceeds 1,000, the sync completes without any error or warning. Records beyond the limit are silently dropped from the device. Technicians go offline missing work orders, line items, or related records — but the app shows no error and the priming sync reports success.

**When it occurs:** High-volume technicians with many appointments per day (e.g., urban territories), wide priming scheduling windows (e.g., 3–7 days), or many enabled related lists per work order. The threshold is easy to exceed on busy accounts.

**How to avoid:** Before rollout, estimate the maximum page reference count for your heaviest-workload resource profile (see examples.md). Keep the count below 1,000 by: (1) narrowing the scheduling window, (2) removing low-priority related lists from the priming config, (3) segmenting large territories to reduce appointment density per resource. Monitor periodically as data volumes grow.

---

## Gotcha 2: HTML5 Mobile Extension Toolkit Cannot Use LWC or Lightning Data Service

**What happens:** Developers familiar with modern Salesforce development attempt to import LWC modules, use `lightning-record-form`, call `@wire` adapters, or use `uiRecordApi` inside an HTML5 Mobile Extension Toolkit extension. The code is silently ignored or throws a JavaScript error in the extension WebView. The extension renders as blank or broken.

**When it occurs:** Any time a developer treats the HTML5 extension container as equivalent to an LWC-capable Lightning container. The HTML5 toolkit predates LWC and runs in a completely separate JavaScript context that has no access to the Lightning component framework or LDS.

**How to avoid:** If you need LDS, `@wire`, or any Lightning component in your extension, use a LWC Quick Action instead. Only use the HTML5 toolkit for legacy extensions that predate LWC support, or for specific non-LWC UI requirements. All data access in the HTML5 toolkit must go through explicit XHR/fetch calls to Apex REST endpoints (`@RestResource`).

---

## Gotcha 3: Branding Configuration Silently Does Nothing Without Mobile App Plus

**What happens:** Admins upload a custom logo, app icon, and color scheme in Field Service Mobile Settings → Branding. The save operation succeeds with no error. However, the app continues showing default Salesforce Field Service branding for all technicians. There is no indication in Setup that the branding license is missing.

**When it occurs:** When the org does not have the Mobile App Plus add-on license, which is a separately purchased entitlement. Branding customization is gated behind this license, but the UI does not surface this restriction.

**How to avoid:** Before starting any branding work, verify with the Salesforce Account Executive or Check My Edition that the Mobile App Plus add-on is active on the org. Look for the add-on in Setup → Company Information → Licenses. Do not attempt to configure branding without confirming the license first.

---

## Gotcha 4: Deep Link Payload Failures Are Silent

**What happens:** A deep link from an external app to FSL Mobile exceeds the 1 MB payload limit. The calling app sends the link successfully. FSL Mobile receives the URI but silently discards the oversized payload. The app either fails to navigate to the target record or opens to the home screen instead. No error is shown to the user.

**When it occurs:** Deep links that carry large serialized record data, base64-encoded content, or multiple concatenated fields. The 1 MB limit applies to the full encoded URI including all query parameters.

**How to avoid:** Design deep links to carry only the minimum required identifiers (typically a record ID and object type). Do not serialize full record payloads into deep link parameters. Test with realistic worst-case data on a physical device before rollout. If more data context is needed, have FSL Mobile fetch it on arrival using the record ID.

---

## Gotcha 5: FSL Mobile Offline Sync Is Not the Same as Briefcase / Einstein for Mobile

**What happens:** Practitioners conflate FSL Mobile's offline priming with Salesforce Briefcase (used in Salesforce Mobile for offline data), Einstein for Mobile, or standard mobile offline settings. Configuration done in those areas has no effect on FSL Mobile's offline behavior. FSL Mobile has its own offline priming pipeline entirely.

**When it occurs:** Orgs that use both standard Salesforce Mobile (with Briefcase) and FSL Mobile simultaneously. Admins configure Briefcase rules to include work orders and assume this covers FSL Mobile technicians. It does not.

**How to avoid:** Treat FSL Mobile offline priming as a completely separate configuration surface. Offline configuration for FSL Mobile lives exclusively in Field Service Mobile Settings → Data Sync and the priming hierarchy settings. Briefcase and standard mobile offline settings are irrelevant to FSL Mobile.
