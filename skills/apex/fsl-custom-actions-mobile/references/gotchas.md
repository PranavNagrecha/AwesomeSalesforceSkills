# Gotchas — FSL Custom Actions Mobile

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: lightning__GlobalAction LWCs Are Invisible Outside FSL Mobile

**What happens:** A component with `lightning__GlobalAction` target compiles and deploys successfully, appears in the App Manager configuration, and shows no errors — but does not appear to end users in the standard Salesforce Mobile App or Lightning Experience desktop.

**When it occurs:** Developers test on desktop or in the standard Salesforce Mobile App instead of FSL Mobile. The component is available in the action bar configuration in both setups, making it look correct when it isn't.

**How to avoid:** Document explicitly that `lightning__GlobalAction` components for FSL are FSL Mobile-only. Test exclusively on a device with the FSL Mobile app installed. Do not accept desktop behavior as confirmation of correct deployment.

---

## Gotcha 2: Missing Permission Set Causes Silent Failure

**What happens:** Custom LWC actions do not appear in FSL Mobile for technicians who lack the `Enable Lightning SDK for FSL Mobile` permission set. No error message is shown — the action simply doesn't appear in the action bar.

**When it occurs:** Permission set assignment is missed during user provisioning, or the permission set is present on some profiles but not assigned to contractors who use FSL Mobile.

**How to avoid:** Include the permission set in the FSL Mobile permission set group assigned during onboarding. Validate by querying `PermissionSetAssignment` for the target user before troubleshooting component code.

---

## Gotcha 3: Nimbus Plugin Returns Null — Not a Disabled State

**What happens:** `getBarcodeScanner()`, `getLocationService()`, and `getCameraCapture()` return `null` (not a disabled plugin object) when called outside FSL Mobile or without the correct permission set. Calling any method on null immediately throws `TypeError`.

**When it occurs:** Desktop testing, staging org validation, or missing permission set on the test device.

**How to avoid:** Always check both: `if (plugin == null || !plugin.isAvailable())`. A check only for `isAvailable()` will throw on null.

---

## Gotcha 4: Legacy HTML5 Toolkit Actions Are Not Migrated Automatically

**What happens:** An org with legacy Mobile Extension Toolkit HTML5 actions does not gain LWC-based Nimbus capabilities for those actions. The two SDK models are architecturally separate; you cannot "upgrade" an HTML5 toolkit action to use Nimbus plugins.

**When it occurs:** Any FSL implementation that was built before the Lightning SDK for FSL Mobile was available (pre-Spring '21).

**How to avoid:** Identify all legacy toolkit actions before a mobile modernization project. Budget for full rewrites, not incremental migrations.

---

## Gotcha 5: endCapture() Must Always Be Called After beginCapture()

**What happens:** If `scanner.beginCapture()` is called and the promise is neither resolved nor rejected (e.g., the user cancels, or an exception is thrown in the `.then()` handler), the scanner session remains open. Subsequent calls to `beginCapture()` fail because only one capture session can be active at a time.

**When it occurs:** Error paths that don't call `endCapture()`, or component disconnection during an active scan session.

**How to avoid:** Call `endCapture()` in both the `.then()` and `.catch()` handlers. Add a `disconnectedCallback()` that calls `endCapture()` if a scan is in progress.
