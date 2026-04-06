# CTI Adapter Development — Work Template

Use this template when building or reviewing a CTI adapter for Salesforce Open CTI.

## Scope

**Skill:** `cti-adapter-development`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Lightning App hosting the softphone:** (e.g., Service Console App)
- **Adapter page URL (HTTPS):** (e.g., https://cti.mycompany.com/adapter/softphone.html)
- **Telephony vendor / SDK:** (e.g., Twilio, Genesys, custom WebRTC)
- **CSP Trusted Site added:** [ ] Yes  [ ] No  [ ] Unknown
- **CORS Allowed Origin added:** [ ] Yes  [ ] No  [ ] Unknown
- **Call Center definition imported:** [ ] Yes  [ ] No
- **CTIVersion in callcenter.xml:** (must be 4.0 for Lightning)
- **Users assigned to Call Center:** [ ] Yes  [ ] No
- **Objects to screen-pop on inbound calls:** (e.g., Contact, Case, Lead)

## Checklist

- [ ] `callcenter.xml` uses `CTIVersion` 4.0
- [ ] `AdapterUrl` is HTTPS and the domain is in CSP Trusted Sites
- [ ] Adapter domain is in CORS Allowed Origins List
- [ ] `enableClickToDial` is called on adapter load; `onClickToDial` is nested inside its success callback
- [ ] `disableClickToDial` is called when a call connects to prevent double-dials
- [ ] `saveLog` passes `Subject`, `Status: 'Completed'`, `CallType`, `CallDurationInSeconds`, and `WhoId` or `WhatId`
- [ ] `saveLog` callback checks `response.success` and surfaces errors to the agent
- [ ] `screenPop` falls back to `type: 'SEARCH'` when no record ID is available
- [ ] No telephony credentials are hardcoded in the adapter JS
- [ ] `setSoftphonePanelHeight` is called on adapter load to ensure correct panel sizing

## callcenter.xml Skeleton

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<CallCenter>
  <InternalName><!-- unique identifier, no spaces --></InternalName>
  <DisplayName><!-- label in Setup UI --></DisplayName>
  <AdapterUrl><!-- HTTPS URL of adapter page --></AdapterUrl>
  <CTIVersion>4.0</CTIVersion>
  <RequiresCallCenter>true</RequiresCallCenter>
  <CustomSettings>
    <CustomSetting>
      <Label><!-- Setting label --></Label>
      <Name><!-- Setting API name --></Name>
      <Value><!-- Setting value --></Value>
    </CustomSetting>
  </CustomSettings>
</CallCenter>
```

## Adapter Page Initialization Skeleton

```javascript
window.addEventListener('DOMContentLoaded', () => {
  sforce.opencti.enableClickToDial({
    callback: (res) => {
      if (!res.success) {
        // surface error to agent UI
        return;
      }
      sforce.opencti.onClickToDial({
        listener: (payload) => {
          // handle click-to-dial: payload.number, payload.recordId, payload.objectType
        }
      });
    }
  });

  // Set the softphone panel height on load
  sforce.opencti.setSoftphonePanelHeight({
    heightPX: 500,
    callback: () => {}
  });
});
```

## saveLog Call Skeleton

```javascript
sforce.opencti.saveLog({
  value: {
    Subject:               '<!-- Call with [name/number] -->',
    Status:                'Completed',
    CallType:              '<!-- Inbound or Outbound -->',
    CallDurationInSeconds: 0, // replace with actual duration
    WhoId:                 '<!-- Contact or Lead Id, if applicable -->',
    WhatId:                '<!-- Account, Case, or Opportunity Id, if applicable -->',
  },
  callback: (response) => {
    if (!response.success) {
      console.error('saveLog failed:', response.errors);
      // surface error to agent
    }
  }
});
```

## Notes

(Record any deviations from the standard pattern and why.)
