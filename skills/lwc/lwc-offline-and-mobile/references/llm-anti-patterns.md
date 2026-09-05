# LLM Anti-Patterns — LWC Offline and Mobile

Common mistakes AI coding assistants make when generating or advising on LWC for the Salesforce
mobile app and offline scenarios. These patterns help the consuming agent self-check its own output.
Cites of the form `lwc_guide <page-slug> L<n>` refer to the crawled Lightning Web Components
Developer Guide (`https://developer.salesforce.com/docs/platform/lwc/guide/<page-slug>.html`).

## Anti-Pattern 1: Using device APIs without checking capability availability — or checking and then not handling errors

**What the LLM generates:**

```javascript
import { getBarcodeScanner } from 'lightning/mobileCapabilities';

connectedCallback() {
    const scanner = getBarcodeScanner();
    scanner.beginCapture({ barcodeTypes: ['qr'] }); // legacy API, no guard, no teardown
}
```

**Why it happens:** LLMs generate the direct API call because training examples focus on the happy
path, and `beginCapture` dominates older samples. Three things are wrong at once: no availability
check, the legacy API, and no `dismiss()`/`endCapture()` to release the scanner.

**Correct pattern:**

```javascript
import { getBarcodeScanner } from 'lightning/mobileCapabilities';

connectedCallback() {
    this.scanner = getBarcodeScanner();
    this.scannerAvailable = Boolean(this.scanner) && this.scanner.isAvailable();
}

handleScan() {
    if (!this.scannerAvailable) {
        return; // render manual entry instead
    }
    this.scanner
        .scan({ barcodeTypes: [this.scanner.barcodeTypes.QR] })
        .then((results) => {
            this.scannedValues = results.map((r) => r.value); // scan() resolves an ARRAY
        })
        .catch((error) => {
            this.message =
                String(error?.code ?? '').toLowerCase() === 'userdismissedscanner'
                    ? 'Scan cancelled.'
                    : `Scan failed: ${error?.message}`;
        })
        .finally(() => this.scanner.dismiss());
}
```

Three grounded corrections to the generated version: `scan()`/`dismiss()` are the modern APIs and
`beginCapture()`/`resumeCapture()`/`endCapture()` will be retired in a future release
(`lwc_guide reference-lightning-barcodescanner-begincapture L17394`); `scan()` resolves an array of
`Barcode` objects rather than one (`lwc_guide reference-lightning-barcodescanner-scan L17345`); and
the OS scanner interface stays on screen after success *or* error until `dismiss()` is called
(`same page L17366`). The guard alone is also not enough — the guide says `isAvailable()` isn't
required before a scan and that your code should handle errors either way
(`lwc_guide reference-lightning-barcodescanner-isavailable L17337`).

**Detection hint:** `scan(`, `beginCapture(`, or `getCurrentPosition(` with no `isAvailable()`
anywhere in the file, or with no `.catch()`, or with no `dismiss()`/`endCapture()` in the chain.

---

## Anti-Pattern 2: Assuming base components behave the same on mobile

**What the LLM generates:**

```html
<lightning-datatable data={data} columns={columns} key-field="Id"
    enable-infinite-loading onloadmore={loadMore}>
</lightning-datatable>
```

**Why it happens:** LLMs design for desktop first and describe the mobile problem as a UX
complaint — small touch targets, horizontal scrolling. The guide is stronger than that:
`lightning-datatable` and `lightning-tree-grid` aren't supported on mobile devices
(`lwc_guide data-table-vs-tree-grid L5600`). "Poor mobile UX" understates a support boundary.

**Correct pattern:**

For mobile, use an iterated card or list layout:

```html
<template for:each={records} for:item="record">
    <div key={record.Id} class="slds-card slds-m-bottom_small">
        <p class="slds-text-heading_small">{record.Name}</p>
        <p>{record.Status}</p>
    </div>
</template>
```

Branch on `@salesforce/client/formFactor` to render the table only where it is supported.

**Detection hint:** `lightning-datatable` or `lightning-tree-grid` in a bundle whose `-meta.xml`
declares `<supportedFormFactor type="Small"/>`, or that omits `supportedFormFactors` on a
record/app page target (the default is every form factor the page type supports —
`lwc_guide use-config-form-factors L9794`).

---

## Anti-Pattern 3: Using `window.location` or direct URL manipulation for navigation

**What the LLM generates:**

```javascript
handleNavigate() {
    window.location.href = `/lightning/r/Account/${this.recordId}/view`;
}
```

**Why it happens:** LLMs fall back to browser-standard navigation.

<!-- UNVERIFIED (2026-09-05): the specific claim that window.location "bypasses the app shell and
     breaks the navigation stack" in the Salesforce mobile app. The LWC Developer Guide states only
     which navigation service is supported where; it does not describe what window.location does
     inside the mobile app container. Keeping the guidance, marking the mechanism. -->

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

What *is* grounded: `lightning/navigation` is supported in Lightning Experience, Experience Builder
sites, and the Salesforce mobile app, and is not supported in other containers such as Lightning
Components for Visualforce or Lightning Out (`lwc_guide use-navigate L10078`). One
mobile-specific consequence to design around: navigating to `filePreview` opens a modal preview in
Lightning Experience but triggers a file **download** in the Salesforce app on mobile devices
(`lwc_guide use-open-files L10341`, detail at `L10350`).

**Detection hint:** `window.location` or `window.open` in a bundle whose `-meta.xml` allows the
`Small` form factor.

---

## Anti-Pattern 4: Reaching for `lightning/graphql` (v2) in a component that must work offline

**What the LLM generates:**

```javascript
import { gql, graphql } from 'lightning/graphql'; // "the newer module"
```

**Why it happens:** The guide recommends v2 where possible and marks v1 deprecated
(`lwc_guide reference-refreshgraphql L13651`), so recency heuristics pick v2 every time. The one
sentence that overrides this for mobile sits on a different page: `lightning/uiGraphQLApi` supports
Mobile Offline use cases, but `lightning/graphql` doesn't
(`lwc_guide reference-graphql-intro L13437`).

**Correct pattern:**

```javascript
// Offline requirement -> v1, deliberately. See references/gotchas.md Gotcha 1.
import { gql, graphql, refreshGraphQL } from 'lightning/uiGraphQLApi';
```

If the component needs v2-only features — optional fields, dynamic query construction, mutations
(`lwc_guide reference-graphql L13634–13638`) — *and* offline, that is a requirements conflict to
raise, not a module to guess at.

**Detection hint:** an import from `lightning/graphql` in a bundle whose SKILL/README/comments claim
offline or mobile-offline support.

---

## Anti-Pattern 5: Making imperative Apex calls the primary data path on a mobile component

**What the LLM generates:**

```javascript
async connectedCallback() {
    this.records = await getRecords();
    // Component shows nothing if the device is offline
}
```

**Why it happens:** LLMs do not model connectivity state, and imperative Apex is the shortest path
to data in a training sample.

**Correct pattern:** Prefer an LDS-backed wire adapter for anything that has to survive a lost
connection, and keep one data path per record.

```javascript
import { getRecord } from 'lightning/uiRecordApi';

@wire(getRecord, { recordId: '$recordId', fields: FIELDS })
record;
```

Grounded reasons: Apex doesn't share a data cache or data store with LDS, so Apex-fetched data can
be inconsistent with wire-adapter data in both online and offline conditions
(`lwc_guide data-guidelines L5364`); and LDS returns an error when the record isn't in the cache and
the server is offline (`lwc_guide data-error L6511`), which at least gives you a state to render,
where an imperative Apex call gives you nothing.

<!-- UNVERIFIED (2026-09-05): that LDS wire adapters "participate in the mobile offline cache when
     the object and fields are primed". Priming is a Briefcase Builder / Mobile Offline mechanism
     documented in the Mobile and Offline Developer Guide, which is not in the crawled corpus. The
     LWC guide confirms the cache exists and that offline reads come from it, not the priming rules
     that populate it. See lwc/lwc-mobile-offline-and-briefcase. -->

**Detection hint:** an `import ... from '@salesforce/apex/...'` in a bundle documented as
mobile/offline-capable with no wire adapter and no cached fallback.

---

## Anti-Pattern 6: Treating "mobile" as a single form factor

**What the LLM generates:**

```javascript
// Component assumes Lightning Experience desktop context throughout
// No form factor detection, no mobile-specific layout branch
```

...or, one step better but still wrong:

```javascript
get isMobile() {
    return FORM_FACTOR === 'Small'; // tablets fall through to the desktop layout
}
```

**Why it happens:** LLMs generate for the default desktop context, and when they do branch, they
collapse three documented values into a boolean.

**Correct pattern:**

```javascript
import FORM_FACTOR from '@salesforce/client/formFactor';

get isPhone() {
    return FORM_FACTOR === 'Small';
}
get isTablet() {
    return FORM_FACTOR === 'Medium';
}
```

```html
<template lwc:if={isPhone}>
    <!-- Phone layout -->
</template>
<template lwc:else>
    <!-- Desktop / tablet layout -->
</template>
```

`@salesforce/client/formFactor` returns `Large`, `Medium`, or `Small`
(`lwc_guide create-client-form-factor L3960–3962`), but `<supportedFormFactor type="…">` accepts
only `Large` and `Small` (`lwc_guide targets-lightning-record-action L19311–19313`) — so a tablet
enters through the `Large` declaration and reports `Medium` at runtime.

**Detection hint:** a component declared for `lightning__AppPage` or `lightning__RecordPage` with no
`@salesforce/client/formFactor` import at all, or one whose only branch tests `=== 'Small'`.

---

## Anti-Pattern 7: Using `localStorage` or `sessionStorage` as the offline data store

**What the LLM generates:**

```javascript
connectedCallback() {
    const cached = localStorage.getItem('myData');
    if (cached) {
        this.data = JSON.parse(cached);
    }
}
```

**Why it happens:** LLMs reach for familiar web-storage APIs when asked to "make it work offline".

<!-- UNVERIFIED (2026-09-05): the specific claims that localStorage in the Salesforce mobile app
     "can be cleared by the OS" and "is not integrated with the Salesforce offline sync framework".
     Neither statement appears in the crawled LWC Developer Guide; the offline sync framework is
     documented in the Mobile and Offline Developer Guide, which is not in the corpus. The guidance
     to prefer LDS is grounded independently (see below); the storage-lifetime mechanism is not. -->

**Correct pattern:** Use an LDS-backed wire adapter for record data that must survive offline —
records loaded in Lightning Data Service are cached and shared across components, so components
reading the same record see the same version and load it once
(`lwc_guide data-ui-api L5374`). Hand-rolled storage sits outside that cache entirely, which
reproduces the Apex/LDS inconsistency problem the guide warns about
(`lwc_guide data-guidelines L5364`). Draft *UI* state — an unsent note, a half-filled form — is a
different and legitimate case; keep it in component state and show the user it is unsaved, as in
`references/code-examples.md` §2.

**Detection hint:** `localStorage` or `sessionStorage` in a bundle that allows the `Small` form
factor or is documented as offline-capable.
