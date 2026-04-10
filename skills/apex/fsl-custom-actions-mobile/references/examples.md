# Examples — FSL Custom Actions Mobile

## Example 1: Barcode Scan to Look Up ProductItem (Van Stock)

**Context:** A field technician scans a barcode on a part from their van stock to auto-populate the part number on a Work Order Line Item's ProductConsumed record.

**Problem:** A developer implements an HTML `<input type="file" accept="image/*">` element to capture a photo of the barcode and tries to parse it client-side. This approach fails in field conditions (low light, motion blur) and does not integrate with the device's native barcode scanning engine.

**Solution:**

```javascript
// barcodePartLookup.js
import { LightningElement, api } from 'lwc';
import { getBarcodeScanner } from 'lightning/mobileCapabilities';
import getProductByBarcode from '@salesforce/apex/ProductLookupController.getProductByBarcode';

export default class BarcodePartLookup extends LightningElement {
    @api recordId; // WorkOrderLineItem Id
    scanner;
    product;

    connectedCallback() {
        this.scanner = getBarcodeScanner();
    }

    get scanAvailable() {
        return this.scanner != null && this.scanner.isAvailable();
    }

    handleScan() {
        if (!this.scanAvailable) {
            this.dispatchEvent(
                new ShowToastEvent({ title: 'Not available', message: 'Use FSL Mobile app.', variant: 'error' })
            );
            return;
        }
        this.scanner.beginCapture({ barcodeTypes: ['CODE128', 'QR'] })
            .then(async result => {
                this.scanner.endCapture();
                this.product = await getProductByBarcode({ barcode: result.value });
            })
            .catch(() => this.scanner.endCapture());
    }
}
```

```xml
<!-- barcodePartLookup.js-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>60.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordAction</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordAction">
            <actionType>Action</actionType>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**Why it works:** `getBarcodeScanner().beginCapture()` invokes the device's native barcode scanning API, which handles optics, decoding, and camera control. The `isAvailable()` guard ensures graceful degradation on desktop.

---

## Example 2: GPS Arrival Stamp on Service Appointment

**Context:** A field technician taps "Arrived" on a Service Appointment in FSL Mobile. A custom action captures the device GPS coordinates and stamps them on custom geolocation fields on the SA record.

**Problem:** A developer uses the browser `navigator.geolocation.getCurrentPosition()` Web API directly. This works in a mobile browser but is not available in the FSL Mobile app's LWC runtime, which uses the Nimbus plugin bridge instead of the browser geolocation API.

**Solution:**

```javascript
// arrivalStamp.js
import { LightningElement, api } from 'lwc';
import { getLocationService } from 'lightning/mobileCapabilities';
import stampArrivalLocation from '@salesforce/apex/ArrivalController.stampLocation';

export default class ArrivalStamp extends LightningElement {
    @api recordId; // ServiceAppointment Id

    handleArrival() {
        const locationService = getLocationService();
        if (locationService == null || !locationService.isAvailable()) {
            // Fallback: prompt manual address entry
            this.template.querySelector('.manual-entry').classList.remove('slds-hide');
            return;
        }
        locationService.getCurrentPosition({ enableHighAccuracy: true, timeout: 15000 })
            .then(pos => {
                return stampArrivalLocation({
                    saId: this.recordId,
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude
                });
            })
            .catch(err => console.error('GPS failed:', err));
    }
}
```

**Why it works:** `getLocationService()` uses the Nimbus plugin bridge to call the device's native location API, which is available inside the FSL Mobile native container and provides higher accuracy than browser geolocation.

---

## Anti-Pattern: Missing isAvailable() Guard

**What practitioners do:** Import `getBarcodeScanner` and call `scanner.beginCapture()` directly in a button click handler without checking `isAvailable()` first.

**What goes wrong:** On desktop or when the `Enable Lightning SDK for FSL Mobile` permission set is missing, `getBarcodeScanner()` returns null. Calling `.beginCapture()` on null throws `TypeError: Cannot read properties of null`, crashing the component.

**Correct approach:** Always gate on both null and `isAvailable()`:
```javascript
const scanner = getBarcodeScanner();
if (scanner == null || !scanner.isAvailable()) {
    // show fallback UI, do not call beginCapture
    return;
}
scanner.beginCapture(options).then(...);
```
