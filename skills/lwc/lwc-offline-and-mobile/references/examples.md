# Examples — LWC Offline And Mobile

## Example 1: Capability-Gated Barcode Scanner

**Context:** A warehouse component should scan barcodes in the Salesforce mobile app but still render safely elsewhere.

**Problem:** The original code assumes the scanner exists in every container and throws errors on desktop.

**Solution:**

```js
import { getBarcodeScanner } from 'lightning/mobileCapabilities';

connectedCallback() {
    this.scanner = getBarcodeScanner();
    this.canScan = this.scanner && this.scanner.isAvailable();
}
```

**Why it works:** The component enables the scanner only where the supported mobile capability exists and can provide a fallback message or manual input elsewhere.

---

## Example 2: Resume-Safe Mobile Task Form

**Context:** A field-service user fills out a short task form on a phone and may lose connectivity or background the app.

**Problem:** The form assumes a continuous session and discards progress when the app resumes.

**Solution:**

```text
Local component state stores the in-progress form values.
On reconnect or resume, the component refreshes current record context and reconciles pending edits before submission.
```

**Why it works:** The design assumes interruption and reconnect, which is normal in mobile workflows.

---

## Anti-Pattern: Treating Mobile As Desktop On A Smaller Screen

**What practitioners do:** They reuse a dense desktop component with large tables, hover interactions, and no capability checks.

**What goes wrong:** The UI becomes hard to use on touch devices and fails in unsupported containers.

**Correct approach:** Start from the mobile interaction model, gate device APIs, and simplify the task flow for touch-first usage.
