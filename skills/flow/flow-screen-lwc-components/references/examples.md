# Examples — Flow Screen LWC Components

End-to-end LWC bundle examples wired for `lightning__FlowScreen`. Each example
shows the three files that make up a deployable Flow-screen component
(`.html`, `.js`, `.js-meta.xml`) plus a brief explanation of the integration
contract with Flow.

---

## Example 1: Single-input screen LWC with output and synchronous validation

**Context:** A Service Cloud screen flow asks an agent to capture a 10-digit
case reference number from a third-party system. The number must match a
specific format (`CR-` prefix + 10 digits). The flow then uses the captured
value to call an external system. Stock components cannot enforce the
prefix-plus-length rule without a roundtrip to a Flow formula resource and
a separate validation rule, which is awkward — a custom LWC is justified.

**Problem without this skill:** authors commonly forget the
`lightning__FlowScreen` target (component never appears in the palette),
declare an `outputOnly` property without dispatching `FlowAttributeChangeEvent`
(the Flow variable stays empty), or write `async validate()` (the validation
is silently ignored).

**Solution:**

`caseReferenceCapture.js-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>61.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Case Reference Capture</masterLabel>
    <description>Captures a CR-formatted case reference for a screen flow.</description>
    <targets>
        <target>lightning__FlowScreen</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__FlowScreen">
            <property name="placeholder"
                      type="String"
                      label="Placeholder text"
                      default="CR-1234567890"/>
            <property name="caseReference"
                      type="String"
                      label="Case Reference"
                      role="outputOnly"/>
            <supportedFormFactors>
                <supportedFormFactor type="Large"/>
                <supportedFormFactor type="Small"/>
            </supportedFormFactors>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

`caseReferenceCapture.js`:

```js
import { LightningElement, api } from 'lwc';
import { FlowAttributeChangeEvent } from 'lightning/flowSupport';

const PATTERN = /^CR-\d{10}$/;

export default class CaseReferenceCapture extends LightningElement {
    @api placeholder = 'CR-1234567890';
    @api caseReference;

    handleChange(event) {
        const newValue = event.target.value;
        // Push the value back to the Flow variable mapped to {!caseReference}.
        this.dispatchEvent(new FlowAttributeChangeEvent('caseReference', newValue));
    }

    // Synchronous. Flow ignores async returns silently.
    @api
    validate() {
        if (!this.caseReference || !PATTERN.test(this.caseReference)) {
            return {
                isValid: false,
                errorMessage: 'Case Reference must be CR- followed by 10 digits.'
            };
        }
        return { isValid: true };
    }
}
```

`caseReferenceCapture.html`:

```html
<template>
    <lightning-input
        type="text"
        label="Case Reference"
        placeholder={placeholder}
        value={caseReference}
        onchange={handleChange}>
    </lightning-input>
</template>
```

**Why it works:**

- `<target>lightning__FlowScreen</target>` is the single switch that makes the
  component appear in Flow Builder's screen palette. Without it the component
  is invisible.
- `caseReference` is declared `role="outputOnly"` AND has a matching
  `FlowAttributeChangeEvent` dispatch in `handleChange`. Both are required;
  one without the other does nothing.
- `validate()` is synchronous and returns the documented shape. The Flow
  runtime calls it on every Next click and blocks navigation when
  `isValid: false`.
- `placeholder` is a regular `@api` input declared in `<targetConfig>`
  without `role`, so admins can configure it from the property panel.
- `<supportedFormFactors>` includes `Small`, so the component also runs in
  the Salesforce mobile app.

---

## Example 2: Auto-advance scanner with programmatic Next

**Context:** A field-service screen flow asks a technician to scan an
asset barcode. The moment a valid barcode is captured, the flow should
advance — no Next click. If the scan is invalid, the screen stays put with
an inline error.

**Solution highlights:**

`assetBarcodeScanner.js`:

```js
import { LightningElement, api } from 'lwc';
import {
    FlowAttributeChangeEvent,
    FlowNavigationNextEvent
} from 'lightning/flowSupport';

export default class AssetBarcodeScanner extends LightningElement {
    @api scannedAssetTag;
    @api availableActions = [];   // populated by Flow runtime

    handleScanResult(event) {
        const code = event.detail.code;
        if (!this.isValidAssetTag(code)) {
            this.errorMessage = 'Scan an asset tag (AT-XXXX-XXXX).';
            return;
        }
        this.errorMessage = null;
        // 1. Push value to the Flow variable.
        this.dispatchEvent(new FlowAttributeChangeEvent('scannedAssetTag', code));
        // 2. Then advance — only if Next is actually available on this screen.
        if (this.availableActions.find((action) => action === 'NEXT')) {
            this.dispatchEvent(new FlowNavigationNextEvent());
        }
    }

    @api
    validate() {
        if (!this.scannedAssetTag) {
            return { isValid: false, errorMessage: 'Scan an asset tag to continue.' };
        }
        return { isValid: true };
    }

    isValidAssetTag(value) {
        return /^AT-\d{4}-\d{4}$/.test(value);
    }
}
```

The corresponding meta.xml declares `scannedAssetTag` with
`role="outputOnly"` AND a separate `availableActions` input typed `String`
that the Flow runtime auto-populates.

**Why it works:**

- The dispatch order is attribute-change first, then `Next`. Reversed, the
  next screen may render before the variable update propagates.
- The `availableActions` guard prevents firing `Next` on the final screen
  (where it does nothing) or in a paused state.
- `validate()` still implements the same rule for users who manually click
  Next without scanning.

---

## Example 3: Reactive component pair driven by FlowAttributeChangeEvent

**Context:** Two custom LWCs on the same screen. The first lets a user pick
a region; the second renders a region-specific cost summary that should
update the moment the region changes — no Next click.

**Solution highlights:**

The "source" LWC (`regionPicker`) declares an output:

```xml
<property name="selectedRegion" type="String" role="outputOnly"/>
```

…and dispatches:

```js
this.dispatchEvent(new FlowAttributeChangeEvent('selectedRegion', value));
```

The admin in Flow Builder maps `regionPicker.selectedRegion` →
`{!flowVar_Region}` (a screen-level Flow variable) → `regionCostSummary.region`
(the consuming LWC's input). With Flow API version 59.0 +, the second LWC's
`region` setter fires the moment the first LWC dispatches the event, with no
Next click.

```js
// regionCostSummary.js
@api
get region() { return this._region; }
set region(value) {
    this._region = value;
    this.recalculate();
}
```

**Why it works:**

- There is NO direct LWC-to-LWC binding. The Flow variable is the contract.
- The Flow's API version must be 59+; older flows ignore the reactive update.
- The consuming LWC uses a setter so it reacts to the input change.

---

## Anti-Pattern: Async `validate()` masquerading as a check

**What practitioners do:**

```js
@api
async validate() {
    const isUnique = await this.checkUniquenessOnServer();
    return { isValid: isUnique, errorMessage: 'Duplicate value.' };
}
```

**What goes wrong:**

The Flow runtime calls `validate()` synchronously during the Next-click
handler. An `async` function returns a Promise; the runtime sees a truthy
object that is not the documented shape, treats it as `{ isValid: true }`,
and lets navigation proceed. Users sail past the duplicate check.

**Correct approach:**

Pre-fetch the uniqueness check via `@wire` or `connectedCallback`, store the
result on the instance, and validate against the cached value:

```js
@wire(checkUniqueness, { value: '$valueToCheck' })
wiredUniqueness({ data }) {
    this._isUnique = !!data;
}

@api
validate() {
    if (!this._isUnique) {
        return { isValid: false, errorMessage: 'Duplicate value.' };
    }
    return { isValid: true };
}
```

The race window (user clicks Next before the wire returns) is real and
must be designed around — debounce the Next click in the parent screen
or render a "checking…" placeholder until `_isUnique` is defined.

---

## Anti-Pattern: Forgetting `lightning__FlowScreen` target

**What practitioners do:**

```xml
<targets>
    <target>lightning__AppPage</target>
    <target>lightning__RecordPage</target>
</targets>
```

…and then wonder why the component is "missing" from Flow Builder.

**What goes wrong:**

Flow Builder filters the screen-component palette to components that
declare `lightning__FlowScreen`. There is no error, no warning — the
component simply never appears. Admins waste time searching, refreshing
the browser, and re-deploying.

**Correct approach:** add the target. If the component should also be
usable on a Lightning page, list both:

```xml
<targets>
    <target>lightning__FlowScreen</target>
    <target>lightning__AppPage</target>
    <target>lightning__RecordPage</target>
</targets>
```

And add a separate `<targetConfig>` block per target if behaviors diverge.
