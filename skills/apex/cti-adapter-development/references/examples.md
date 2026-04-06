# Examples — CTI Adapter Development

## Example 1: Minimal Open CTI Adapter Page with Click-to-Dial and Call Logging

**Context:** A telephony vendor provides a WebRTC-based softphone. The Salesforce admin has imported `callcenter.xml` and configured the utility bar. The adapter page needs to activate click-to-dial, listen for phone field clicks, and log calls as Task records on call end.

**Problem:** Without proper sequencing of `enableClickToDial` → `onClickToDial` registration, phone field clicks silently do nothing. Without a `saveLog` call on call end, no activity history is created on the related record.

**Solution:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>My CTI Softphone</title>
  <!--
    Do NOT add a <script src="...opencti_min.js"> tag here.
    Salesforce injects the sforce.opencti namespace automatically
    when this page is loaded inside the Lightning utility panel iframe.
  -->
</head>
<body>
  <div id="softphone-panel">
    <p id="status">Initializing…</p>
    <button id="btn-end-call" disabled>End Call</button>
  </div>

  <script>
    // Track active call state
    let activeCall = null;
    let callStartTime = null;

    // Step 1: Wait for the Open CTI API to be ready.
    // sforce.opencti is injected by Salesforce — it is available
    // as soon as the page loads inside the utility panel iframe.
    window.addEventListener('DOMContentLoaded', () => {
      // Step 2: Enable click-to-dial for this session.
      sforce.opencti.enableClickToDial({
        callback: (response) => {
          if (!response.success) {
            console.error('enableClickToDial failed', response.errors);
            document.getElementById('status').textContent =
              'CTI init failed. Check Call Center assignment.';
            return;
          }

          document.getElementById('status').textContent = 'Ready';

          // Step 3: Register the click-to-dial listener only AFTER
          // enableClickToDial succeeds.
          sforce.opencti.onClickToDial({
            listener: (payload) => {
              // payload: { number, objectType, recordId, recordName }
              handleOutboundCallStart(payload);
            }
          });
        }
      });
    });

    function handleOutboundCallStart(payload) {
      activeCall = payload;
      callStartTime = Date.now();

      document.getElementById('status').textContent =
        `Dialing ${payload.number}…`;
      document.getElementById('btn-end-call').disabled = false;

      // Disable click-to-dial while call is active to prevent double-dials.
      sforce.opencti.disableClickToDial({ callback: () => {} });

      // Screen pop to the record the user clicked from.
      if (payload.recordId) {
        sforce.opencti.screenPop({
          type: sforce.opencti.SCREENPOP_TYPE.SOBJECT,
          params: { recordId: payload.recordId },
          callback: (res) => {
            if (!res.success) {
              console.warn('screenPop failed', res.errors);
            }
          }
        });
      }
    }

    document.getElementById('btn-end-call').addEventListener('click', () => {
      if (!activeCall) return;

      const durationSeconds = Math.round((Date.now() - callStartTime) / 1000);

      // Log the call as a completed Task activity.
      sforce.opencti.saveLog({
        value: {
          Subject:               `Call with ${activeCall.recordName || activeCall.number}`,
          Status:                'Completed',
          CallType:              'Outbound',
          CallDurationInSeconds: durationSeconds,
          // Relate to the Contact/Lead (WhoId) or Account/Case/Opportunity (WhatId)
          WhoId:  activeCall.objectType === 'Contact' || activeCall.objectType === 'Lead'
                    ? activeCall.recordId
                    : undefined,
          WhatId: activeCall.objectType !== 'Contact' && activeCall.objectType !== 'Lead'
                    ? activeCall.recordId
                    : undefined,
        },
        callback: (response) => {
          if (!response.success) {
            console.error('saveLog failed', response.errors);
            alert('Call log failed to save. Please log manually.');
          } else {
            document.getElementById('status').textContent = 'Call ended. Log saved.';
          }
        }
      });

      // Re-enable click-to-dial for the next call.
      sforce.opencti.enableClickToDial({
        callback: (res) => {
          if (res.success) {
            sforce.opencti.onClickToDial({
              listener: handleOutboundCallStart
            });
          }
        }
      });

      activeCall = null;
      callStartTime = null;
      document.getElementById('btn-end-call').disabled = true;
    });
  </script>
</body>
</html>
```

**Why it works:** `enableClickToDial` activates the Open CTI click-to-dial system for the session. The `onClickToDial` listener is nested inside its success callback to guarantee registration order. `disableClickToDial` prevents accidental re-dials while a call is active. `saveLog` maps to standard Task fields and creates a closed activity on the related record.

---

## Example 2: Minimal callcenter.xml for Lightning Open CTI

**Context:** A new CTI integration is being set up. The admin needs a valid Call Center definition file to import into Setup > Call Centers before the utility bar item can be configured.

**Problem:** Using `CTIVersion` 3.0 loads the Classic API; the `sforce.opencti` Lightning namespace is undefined and all API calls fail silently. Omitting required fields causes the import to reject the file.

**Solution:**

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<CallCenter>
  <!--
    InternalName: unique identifier, no spaces, used in API references.
    Do not change after initial import — it is used as the primary key.
  -->
  <InternalName>MyCompanyCTI</InternalName>

  <!--
    DisplayName: label shown in Setup > Call Centers UI.
  -->
  <DisplayName>My Company CTI Softphone</DisplayName>

  <!--
    AdapterUrl: HTTPS URL of the hosted adapter HTML page.
    This domain MUST be added to CSP Trusted Sites and CORS Allowed Origins.
  -->
  <AdapterUrl>https://cti.mycompany.com/adapter/softphone.html</AdapterUrl>

  <!--
    CTIVersion: MUST be "4.0" for Lightning / Open CTI for Lightning.
    "3.0" is Classic-only and will cause sforce.opencti to be undefined.
  -->
  <CTIVersion>4.0</CTIVersion>

  <RequiresCallCenter>true</RequiresCallCenter>

  <!--
    CustomSettings: optional key-value pairs passed to the adapter at runtime.
    Access via sforce.opencti.getCallCenterSettings().
  -->
  <CustomSettings>
    <CustomSetting>
      <Label>Telephony Server URL</Label>
      <Name>TelephonyServerUrl</Name>
      <Value>wss://sip.mycompany.com:5061</Value>
    </CustomSetting>
    <CustomSetting>
      <Label>Call Recording Enabled</Label>
      <Name>CallRecordingEnabled</Name>
      <Value>true</Value>
    </CustomSetting>
  </CustomSettings>
</CallCenter>
```

**Why it works:** `CTIVersion` 4.0 targets the Lightning Open CTI API. `AdapterUrl` points to the hosted adapter page. `CustomSettings` lets the adapter retrieve environment-specific configuration at runtime via `sforce.opencti.getCallCenterSettings`, avoiding hardcoded values in the adapter JavaScript.

---

## Example 3: lightning-click-to-dial LWC Component Usage

**Context:** A service agent record page needs to display a phone number that, when clicked, triggers the CTI adapter's `onClickToDial` listener.

**Problem:** Using a plain `<a href="tel:...">` tag bypasses the Open CTI event system entirely. The telephony adapter never receives the click event, and call tracking does not work.

**Solution:**

```html
<!-- contactPhoneField.html -->
<template>
  <lightning-card title="Contact Phone">
    <div class="slds-p-around_medium">
      <p>Primary Phone:</p>
      <!-- lightning-click-to-dial participates in the Open CTI enable/disable state.
           When the CTI adapter calls disableClickToDial, this component automatically
           renders the number as plain text rather than a clickable link. -->
      <lightning-click-to-dial
        value={phoneNumber}
        record-id={recordId}>
      </lightning-click-to-dial>
    </div>
  </lightning-card>
</template>
```

```javascript
// contactPhoneField.js
import { LightningElement, api, wire } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import PHONE_FIELD from '@salesforce/schema/Contact.Phone';

export default class ContactPhoneField extends LightningElement {
  @api recordId;

  @wire(getRecord, { recordId: '$recordId', fields: [PHONE_FIELD] })
  contact;

  get phoneNumber() {
    return getFieldValue(this.contact.data, PHONE_FIELD) || '';
  }
}
```

**Why it works:** `lightning-click-to-dial` is a Salesforce base component that integrates natively with the Open CTI event system. When clicked, it dispatches the event that the adapter's `onClickToDial` listener receives — with `number`, `recordId`, and `objectType` populated automatically.
