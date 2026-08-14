# Examples — Field Dependency and Controlling

## Example 1: Complete `valueSettings` Matrix for a Two-Level Dependency

**Scenario:** `Product_Family__c` (controlling) filters `Product_Line__c` (dependent) on a custom object. Two families, four lines.

**Problem:** Hand-authored `valueSettings` almost always ships partial, and the collection is an allow-list — anything not listed is disabled. The failure is silent: the field deploys, and users simply stop seeing options.

**Solution:** One `valueSettings` block per dependent value, each listing every controlling value that enables it. `controllingFieldValue` is a repeated element because the Metadata API types it as a string array:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Product_Line__c</fullName>
    <label>Product Line</label>
    <type>Picklist</type>
    <valueSet>
        <controllingField>Product_Family__c</controllingField>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value><fullName>Laptops</fullName><label>Laptops</label><default>false</default></value>
            <value><fullName>Desktops</fullName><label>Desktops</label><default>false</default></value>
            <value><fullName>Handsets</fullName><label>Handsets</label><default>false</default></value>
            <value><fullName>Accessories</fullName><label>Accessories</label><default>false</default></value>
        </valueSetDefinition>
        <!-- One block per dependent value. Accessories is enabled for BOTH
             families, so it lists two controllingFieldValue elements. -->
        <valueSettings>
            <controllingFieldValue>Computers</controllingFieldValue>
            <valueName>Laptops</valueName>
        </valueSettings>
        <valueSettings>
            <controllingFieldValue>Computers</controllingFieldValue>
            <valueName>Desktops</valueName>
        </valueSettings>
        <valueSettings>
            <controllingFieldValue>Mobile</controllingFieldValue>
            <valueName>Handsets</valueName>
        </valueSettings>
        <valueSettings>
            <controllingFieldValue>Computers</controllingFieldValue>
            <controllingFieldValue>Mobile</controllingFieldValue>
            <valueName>Accessories</valueName>
        </valueSettings>
    </valueSet>
</CustomField>
```

**Why it works:** Every enabled pair is present, so nothing is disabled by omission. `restricted` is set alongside the matrix but does a different job — it limits which values may exist at all, not which controlling value they may accompany.

---

## Example 2: Reading the Dependency in an LWC Without Hardcoding It

**Scenario:** A custom form needs the same filtering the standard record form gives for free, because the two picklists sit inside a larger custom UI.

**Problem:** `validFor` holds integer indexes into `controllerValues`, not controlling-field strings, and the map is absent whenever the controlling field is hidden by FLS. Components that ignore either fact render an empty dropdown.

**Solution:**

```javascript
import { LightningElement, api, wire } from 'lwc';
import { getPicklistValues } from 'lightning/uiObjectInfoApi';
import PRODUCT_LINE_FIELD from '@salesforce/schema/Order_Item__c.Product_Line__c';

export default class DependentProductLine extends LightningElement {
    @api recordTypeId;
    @api controllingValue;          // current Product_Family__c value

    allValues = [];
    controllerIndexByValue = {};    // { Computers: 0, Mobile: 1 }
    isDependent = false;

    @wire(getPicklistValues, { recordTypeId: '$recordTypeId', fieldApiName: PRODUCT_LINE_FIELD })
    handlePicklist({ data, error }) {
        if (!data) {
            if (error) this.allValues = [];
            return;
        }
        this.allValues = data.values;
        this.controllerIndexByValue = data.controllerValues ?? {};
        // An independent picklist -- or a dependent one whose controlling
        // field is hidden by FLS -- yields an empty controllerValues map.
        this.isDependent = Object.keys(this.controllerIndexByValue).length > 0;
    }

    get options() {
        if (!this.isDependent) {
            return this.allValues.map(v => ({ label: v.label, value: v.value }));
        }
        const idx = this.controllerIndexByValue[this.controllingValue];
        if (idx === undefined) {
            return [];                       // controller not chosen yet
        }
        return this.allValues
            .filter(v => v.validFor.includes(idx))
            .map(v => ({ label: v.label, value: v.value }));
    }
}
```

**Why it works:** The map is built from `controllerValues` at runtime, so adding a controlling value in Setup needs no code change. The `isDependent` guard is what makes the component reusable: on an independent picklist `validFor` is an empty list, and filtering on it would hide every option.

---

## Anti-Pattern: Assuming One Wire Call Describes a Three-Level Cascade

**What practitioners do:** Build Region → Country → City with a single `getPicklistValues` call for City, then resolve the user's Region selection against the returned index map.

**What goes wrong:** `controllerValues` is "a map of its immediate controlling field's picklist values to their indexes" — for City, the immediate controller is Country. Looking up a Region name in that map returns `undefined`, so either nothing renders or, worse, the lookup accidentally matches a Country whose name collides and the component shows cities from the wrong country. Two-level tests never expose it, because there the immediate controller is the entire chain.

**Correct approach:** One wire per level, each resolving against its own controller, and an explicit downstream clear:

```javascript
handleRegionChange(event) {
    this.region = event.detail.value;
    this.country = null;   // level 2 must be cleared by you
    this.city = null;      // level 3 too -- the platform will not do it
}
```

Salesforce filters the *options* at each level; it does not invalidate a stored selection further down the chain. A record saved through a custom cascade can end up holding a City that is no longer reachable from its Region, which then appears blank in the standard UI while still holding a value in the API.
