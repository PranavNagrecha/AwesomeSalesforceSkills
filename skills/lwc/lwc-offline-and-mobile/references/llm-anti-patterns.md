# LLM Anti-Patterns — LWC Offline and Mobile

Common mistakes AI coding assistants make when generating or advising on LWC for the Salesforce mobile app and offline scenarios.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using device APIs without checking capability availability

**What the LLM generates:**

```javascript
import { getBarcodeScanner } from 'lightning/mobileCapabilities';

connectedCallback() {
    const scanner = getBarcodeScanner();
    scanner.beginCapture({ barcodeTypes: ['qr'] }); // Crashes on desktop
}
```

**Why it happens:** LLMs generate the direct API call because training examples focus on the happy path. They skip the `isAvailable()` check that guards against running on non-mobile contexts.

**Correct pattern:**

```javascript
import { getBarcodeScanner } from 'lightning/mobileCapabilities';

connectedCallback() {
    this.scanner = getBarcodeScanner();
    this.scannerAvailable = this.scanner.isAvailable();
}

handleScan() {
    if (!this.scannerAvailable) {
        // Show fallback UI or inform user
        return;
    }
    this.scanner.beginCapture({ barcodeTypes: ['qr'] })
        .then(result => { this.scannedValue = result.value; })
        .catch(error => { this.error = error.message; });
}
```

**Detection hint:** `beginCapture`, `getCurrentPosition`, or other mobile API calls without a preceding `isAvailable()` check.

---

## Anti-Pattern 2: Assuming all base components work identically on mobile

**What the LLM generates:**

```html
<lightning-datatable data={data} columns={columns} key-field="Id"
    enable-infinite-loading onloadmore={loadMore}>
</lightning-datatable>
```

**Why it happens:** LLMs design for desktop first. `lightning-datatable` renders but has poor mobile UX — horizontal scrolling, tiny touch targets, and no responsive breakpoints.

**Correct pattern:**

For mobile, prefer card-based or list-based layouts:

```html
<template for:each={records} for:item="record">
    <div key={record.Id} class="slds-card slds-m-bottom_small">
        <p class="slds-text-heading_small">{record.Name}</p>
        <p>{record.Status}</p>
    </div>
</template>
```

Use `@salesforce/client/formFactor` to conditionally render mobile vs. desktop layouts.

**Detection hint:** `lightning-datatable` in a component targeted for mobile without a form-factor check or responsive alternative.

---

## Anti-Pattern 3: Using window.location or direct URL manipulation for navigation

**What the LLM generates:**

```javascript
handleNavigate() {
    window.location.href = `/lightning/r/Account/${this.recordId}/view`;
}
```

**Why it happens:** LLMs fall back to browser-standard navigation. In the Salesforce mobile app, `window.location` bypasses the app shell and causes a full page reload or breaks the navigation stack.

**Correct pattern:**

```javascript
import { NavigationMixin } from 'lightning/navigation';

export default class MyComponent extends NavigationMixin(LightningElement) {
    handleNavigate() {
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: {
                recordId: this.recordId,
                objectApiName: 'Account',
                actionName: 'view'
            }
        });
    }
}
```

**Detection hint:** `window.location` or `window.open` in components that target the Salesforce mobile app.

---

## Anti-Pattern 4: Making imperative Apex calls without offline fallback

**What the LLM generates:**

```javascript
async connectedCallback() {
    this.records = await getRecords();
    // Component shows nothing if the device is offline
}
```

**Why it happens:** LLMs do not consider connectivity state. When offline, Apex calls fail immediately with no cached data fallback.

**Correct pattern:**

```javascript
import { getRecord } from 'lightning/uiRecordApi';

// Use Lightning Data Service wire adapters — they participate in the
// mobile offline cache when the object and fields are primed.
@wire(getRecord, { recordId: '$recordId', fields: FIELDS })
record;
```

For offline-capable components, prefer LDS wire adapters over imperative Apex. LDS has built-in offline caching; Apex does not.

**Detection hint:** Imperative Apex calls in a component documented as mobile/offline-capable with no fallback or cache strategy.

---

## Anti-Pattern 5: Not testing with the Salesforce mobile form factor

**What the LLM generates:**

```javascript
// Component assumes Lightning Experience desktop context throughout
// No form factor detection, no mobile-specific layout branch
```

**Why it happens:** LLMs generate code for the default desktop context. They do not add form factor branching because training examples rarely show it.

**Correct pattern:**

```javascript
import FORM_FACTOR from '@salesforce/client/formFactor';

get isMobile() {
    return FORM_FACTOR === 'Small';
}
```

```html
<template lwc:if={isMobile}>
    <!-- Mobile-optimized layout -->
</template>
<template lwc:else>
    <!-- Desktop layout -->
</template>
```

**Detection hint:** Component declared for `lightning__AppPage` or `lightning__RecordPage` without any `@salesforce/client/formFactor` import or mobile layout consideration.

---

## Anti-Pattern 6: Using localStorage or sessionStorage for offline data persistence

**What the LLM generates:**

```javascript
connectedCallback() {
    const cached = localStorage.getItem('myData');
    if (cached) {
        this.data = JSON.parse(cached);
    }
}
```

**Why it happens:** LLMs use familiar web storage APIs. In the Salesforce mobile app, `localStorage` is available but unreliable — it can be cleared by the OS and is not integrated with the Salesforce offline sync framework.

**Correct pattern:**

Use Lightning Data Service for data that should survive offline. For custom offline needs, leverage the Salesforce Mobile SDK's SmartStore if the project has moved beyond standard LWC in the Salesforce app.

**Detection hint:** `localStorage` or `sessionStorage` in a component targeting mobile offline use.
