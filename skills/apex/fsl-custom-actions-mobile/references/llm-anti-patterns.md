# LLM Anti-Patterns — FSL Custom Actions Mobile

Common mistakes AI coding assistants make when generating or advising on FSL Custom Actions Mobile.

## Anti-Pattern 1: Using navigator.geolocation Instead of getLocationService()

**What the LLM generates:**
```javascript
// Wrong — uses browser geolocation API
navigator.geolocation.getCurrentPosition(pos => {
    console.log(pos.coords.latitude);
});
```

**Why it happens:** LLMs default to the standard Web Platform geolocation API, which is correct for browser-based apps but is not available in the FSL Mobile native container's LWC runtime.

**Correct pattern:**
```javascript
import { getLocationService } from 'lightning/mobileCapabilities';
const locationService = getLocationService();
if (locationService != null && locationService.isAvailable()) {
    locationService.getCurrentPosition({ enableHighAccuracy: true })
        .then(pos => console.log(pos.coords.latitude));
}
```

**Detection hint:** Any use of `navigator.geolocation` in a component intended for FSL Mobile is wrong.

---

## Anti-Pattern 2: Missing isAvailable() Guard on Nimbus Plugins

**What the LLM generates:**
```javascript
const scanner = getBarcodeScanner();
scanner.beginCapture({ barcodeTypes: ['QR'] }); // throws if scanner is null
```

**Why it happens:** LLMs pattern-match to API usage examples that assume the capability is always present, skipping the guard that the documentation requires.

**Correct pattern:**
```javascript
const scanner = getBarcodeScanner();
if (scanner == null || !scanner.isAvailable()) {
    return; // show fallback UI
}
scanner.beginCapture({ barcodeTypes: ['QR'] }).then(result => { ... });
```

**Detection hint:** Any Nimbus plugin method call without a preceding `isAvailable()` check is wrong.

---

## Anti-Pattern 3: Adding lightning__GlobalAction to a Standard Lightning App

**What the LLM generates:** Instructions to add the custom action to a standard Lightning App's action set (Sales App, Service Console) to make it available to FSL Mobile users.

**Why it happens:** LLMs conflate `lightning__GlobalAction` targets across different Salesforce apps — the same target works in multiple contexts for non-FSL components.

**Correct pattern:** `lightning__GlobalAction` FSL Mobile components must be added to the FSL Mobile app specifically via Setup > App Manager > FSL Mobile App > Action Bar. Adding them to other apps has no effect for FSL Mobile users.

**Detection hint:** Instructions to add the action to any app other than the FSL Mobile app should be questioned.

---

## Anti-Pattern 4: Expecting lightning__GlobalAction to Render on Desktop

**What the LLM generates:** Test instructions like "open the Salesforce app in your browser and verify the action appears in the global action bar."

**Why it happens:** `lightning__GlobalAction` is a shared target across multiple contexts in Salesforce. LLMs don't know it behaves differently for FSL Mobile-specific components.

**Correct pattern:** FSL Mobile custom LWC actions render only in the FSL Mobile iOS/Android app. Desktop testing confirms compilation; only device testing confirms function.

**Detection hint:** Any validation step that describes verifying FSL Mobile actions in a desktop browser is misleading.

---

## Anti-Pattern 5: Not Calling endCapture() in Error Paths

**What the LLM generates:**
```javascript
scanner.beginCapture(options)
    .then(result => {
        scanner.endCapture();
        // process result
    });
    // No .catch() or no endCapture in catch
```

**Why it happens:** LLMs generate happy-path code. The error path that calls `endCapture()` to release the scanner session is commonly omitted.

**Correct pattern:**
```javascript
scanner.beginCapture(options)
    .then(result => {
        scanner.endCapture();
        // process result
    })
    .catch(err => {
        scanner.endCapture(); // required in catch too
        console.error(err);
    });
```

**Detection hint:** Any `beginCapture()` call that doesn't have `endCapture()` in both the `.then()` and `.catch()` handlers is incomplete.

---

## Anti-Pattern 6: Assuming Legacy Mobile Extension Toolkit Actions Can Be Extended with LWC

**What the LLM generates:** Advice to "add LWC components to your existing Mobile Extension Toolkit actions" or to extend existing HTML5 toolkit actions with Nimbus plugins.

**Why it happens:** LLMs conflate the two FSL mobile extension models because both produce "custom actions" in FSL Mobile.

**Correct pattern:** The Legacy HTML5 Mobile Extension Toolkit and the LWC Lightning SDK for FSL Mobile are separate frameworks. Existing toolkit actions must be fully rewritten as LWC components to use Nimbus plugins. There is no incremental migration path.

**Detection hint:** Any reference to modifying `.html` files in a Mobile Extension Toolkit bundle to add Nimbus features is wrong.
