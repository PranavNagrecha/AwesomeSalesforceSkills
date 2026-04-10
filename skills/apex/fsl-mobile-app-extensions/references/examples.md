# Examples — FSL Mobile App Extensions

## Example 1: LWC Quick Action for Offline Work Order Completion

**Context:** A field technician needs a custom "Complete Work" screen inside FSL Mobile that lets them record completion notes and set a status on the WorkOrder. The screen must work offline because technicians often work in areas without connectivity.

**Problem:** Without this guidance, a developer might build the LWC component correctly but place it only in an App Builder Lightning page. The action disappears when the technician goes offline, and they have no way to complete the work in the app.

**Solution:**

`lwc/workOrderComplete/workOrderComplete.js`
```javascript
import { LightningElement, api, wire } from 'lwc';
import { getRecord, updateRecord } from 'lightning/uiRecordApi';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import STATUS_FIELD from '@salesforce/schema/WorkOrder.Status';
import COMPLETION_NOTES_FIELD from '@salesforce/schema/WorkOrder.Description';

const FIELDS = [STATUS_FIELD, COMPLETION_NOTES_FIELD];

export default class WorkOrderComplete extends LightningElement {
    @api recordId;
    notes = '';

    @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
    workOrder;

    handleNotesChange(event) {
        this.notes = event.target.value;
    }

    handleComplete() {
        const fields = {};
        fields['Id'] = this.recordId;
        fields[STATUS_FIELD.fieldApiName] = 'Completed';
        fields[COMPLETION_NOTES_FIELD.fieldApiName] = this.notes;

        updateRecord({ fields })
            .then(() => {
                this.dispatchEvent(new ShowToastEvent({
                    title: 'Success',
                    message: 'Work order marked complete',
                    variant: 'success'
                }));
            })
            .catch(error => {
                this.dispatchEvent(new ShowToastEvent({
                    title: 'Error',
                    message: error.body.message,
                    variant: 'error'
                }));
            });
    }
}
```

`lwc/workOrderComplete/workOrderComplete.js-meta.xml`
```xml
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

Quick Action metadata (`quickActions/WorkOrder.Work_Order_Complete.quickAction-meta.xml`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<QuickAction xmlns="http://soap.sforce.com/2006/04/metadata">
    <actionSubtype>ScreenAction</actionSubtype>
    <label>Complete Work Order</label>
    <lightningWebComponent>workOrderComplete</lightningWebComponent>
    <optionsCreateFeedItem>false</optionsCreateFeedItem>
    <type>LightningWebComponent</type>
</QuickAction>
```

**Critical layout step:** Open the WorkOrder page layout in Setup. In the "Salesforce Mobile and Lightning Experience Actions" section, add the "Complete Work Order" quick action. This step — NOT the App Builder configuration — is what makes the action available offline.

**Why it works:** `updateRecord` from `lightning/uiRecordApi` leverages the Lightning Data Service (LDS) offline write queue. Writes made while offline are queued locally and automatically synced to the server when connectivity resumes.

---

## Example 2: Custom Metadata Type Values Available Offline via Wire + Custom Object Cache

**Context:** A field technician's completion form needs to show a picklist of "Failure Codes" that are stored in a Custom Metadata Type (`Failure_Code__mdt`) managed by the operations team. The form must work offline.

**Problem:** Custom Metadata Types are not supported as a Briefcase Builder priming target. A wire call to an Apex method that queries the CMT will fail silently when the device is offline, leaving the picklist empty and blocking the technician.

**Solution:**

Apex controller (cacheable for LDS caching benefit when online):
```apex
public with sharing class FailureCodeController {
    @AuraEnabled(cacheable=true)
    public static List<Map<String, String>> getFailureCodes() {
        List<Map<String, String>> results = new List<Map<String, String>>();
        for (Failure_Code__mdt fc : [
            SELECT MasterLabel, Code__c, Category__c
            FROM Failure_Code__mdt
            WHERE IsActive__c = true
            ORDER BY MasterLabel
        ]) {
            results.add(new Map<String, String>{
                'label' => fc.MasterLabel,
                'value' => fc.Code__c,
                'category' => fc.Category__c
            });
        }
        return results;
    }
}
```

LWC using the wire adapter (online path) with a fallback to a cached Custom Object (offline path):
```javascript
import { LightningElement, api, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';
import getFailureCodes from '@salesforce/apex/FailureCodeController.getFailureCodes';

export default class FailureCodePicker extends LightningElement {
    @api recordId;
    failureCodes = [];
    error;

    @wire(getFailureCodes)
    wiredCodes({ data, error }) {
        if (data) {
            this.failureCodes = data.map(fc => ({ label: fc.label, value: fc.value }));
            // Persist to local custom object when online for offline fallback
            this.cacheCodesLocally(data);
        } else if (error) {
            // Wire failed — likely offline; read from cached custom object
            this.loadCachedCodes();
        }
    }

    // Implementation of cacheCodesLocally and loadCachedCodes uses
    // createRecord / getRecord on a FailureCodeCache__c custom object
    // tied to the ServiceAppointment's ServiceResource, which IS
    // primed via Briefcase Builder.
}
```

**Why it works:** The `@AuraEnabled(cacheable=true)` annotation enables LDS to cache the response, so on a warm cache (recently online) the wire adapter returns cached data. For truly cold offline scenarios, the Custom Object cache primed through Briefcase Builder provides a reliable fallback. Never rely solely on the wire adapter for CMT data in offline scenarios.

---

## Anti-Pattern: Imperative Apex Call in an Offline Action

**What practitioners do:** They write a button handler that calls an Apex method imperatively (`import getWorkDetails from '@salesforce/apex/WorkController.getWorkDetails'` called in a click handler), expecting it to fetch data when the button is pressed.

**What goes wrong:** Imperative Apex calls go directly to the server. When the device is offline, the call fails immediately with a network error. The component does not display any data. The technician sees an error toast or blank screen.

**Correct approach:** Use `@wire(getWorkDetails, { recordId: '$recordId' })` instead. Wire adapters backed by LDS populate from the local cache when offline. For data that must absolutely be current (not cached), document the online-only requirement explicitly and do not add the action to the page layout's offline action section.
