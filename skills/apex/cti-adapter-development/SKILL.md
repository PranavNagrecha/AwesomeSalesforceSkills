---
name: cti-adapter-development
description: "Use when building or debugging a browser-based CTI softphone adapter using the Salesforce Open CTI JavaScript API — covers callcenter.xml definition, Lightning utility item registration, core API methods (enableClickToDial, onClickToDial, screenPop, setSoftphonePanelHeight, saveLog), call logging as Task, and the lightning-click-to-dial LWC component. NOT for Service Cloud Voice Amazon Connect setup, Omni-Channel routing configuration, or CTI adapter AppExchange package selection."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I build a custom CTI softphone adapter in Salesforce Lightning?"
  - "Open CTI click-to-dial is not firing / onClickToDial callback never runs"
  - "How do I register a softphone in the Lightning utility bar using callcenter.xml?"
  - "CTI adapter not logging calls to Salesforce activities"
  - "How do I use setSoftphonePanelHeight or screenPop in Open CTI?"
tags:
  - open-cti
  - cti-adapter
  - softphone
  - click-to-dial
  - call-logging
  - lightning-utility-bar
  - callcenter-xml
inputs:
  - "Telephony vendor requirements (SIP endpoint, WebRTC or PSTN bridge details)"
  - "Lightning App where the softphone utility item should appear"
  - "Salesforce objects to screen-pop on incoming calls (Contact, Case, Lead)"
  - "Existing callcenter.xml or adapter page URL if already partially built"
outputs:
  - "Compliant callcenter.xml Call Center definition file"
  - "JavaScript Open CTI adapter hosted page with API method implementations"
  - "Lightning utility bar softphone configuration steps"
  - "Call logging Task creation pattern using saveLog"
  - "lightning-click-to-dial LWC integration snippet"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# CTI Adapter Development

Use this skill when building, diagnosing, or extending a browser-based CTI (Computer Telephony Integration) softphone adapter with the Salesforce Open CTI JavaScript API. It covers the full adapter lifecycle: defining the Call Center in `callcenter.xml`, registering it as a Lightning utility bar item, implementing core Open CTI API calls, enabling click-to-dial on phone fields, logging calls as closed Task records, and integrating with the `lightning-click-to-dial` LWC component.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has a Call Center definition registered under **Setup > Call Centers**. Open CTI requires a valid Call Center record tied to the user before any API calls succeed.
- Identify which Lightning App hosts the softphone. The utility bar must be configured for that specific app — Open CTI softphones do NOT appear in the Salesforce mobile app or Classic UI.
- Understand the telephony vendor's hosting requirements: the CTI adapter page (HTML + JS) must be served from a domain added to Salesforce CSP Trusted Sites and CORS allowed-origins. Omitting this causes the `sforce.opencti` namespace to fail silently.

---

## Core Concepts

### Open CTI JavaScript API

Open CTI is a browser-side JavaScript API exposed by Salesforce. The API namespace is `sforce.opencti` and it is injected into the adapter page by the platform — you do not load it via a `<script src>` tag. The adapter page is a hosted HTML file that runs inside the softphone panel iframe rendered in the Lightning utility bar. All API calls are asynchronous; callbacks receive a `response` object with `success`, `returnValue`, and `errors` fields.

Key API methods:

| Method | Purpose |
|---|---|
| `sforce.opencti.enableClickToDial({callback})` | Activates click-to-dial on all phone fields org-wide for the session. Must be called once on adapter load. |
| `sforce.opencti.onClickToDial({listener})` | Registers a callback that fires when the user clicks a phone field link. Callback receives `{number, objectType, recordId, recordName}`. |
| `sforce.opencti.screenPop({type, params, callback})` | Navigates the agent's browser to a Salesforce record or search result. `type` can be `SOBJECT`, `URL`, `FLOW`, or `SEARCH`. |
| `sforce.opencti.setSoftphonePanelHeight({heightPX, callback})` | Resizes the softphone iframe panel at runtime. |
| `sforce.opencti.saveLog({value, callback})` | Creates or updates an Activity (Task) record to log the call. The Task is created in a closed state (`Status: Completed`) by default. |
| `sforce.opencti.getCallObjectReferences({callback})` | Retrieves active call object references for the current session. |
| `sforce.opencti.disableClickToDial({callback})` | Deactivates click-to-dial — use when call is in progress to prevent accidental new calls. |

### callcenter.xml Definition File

Every CTI adapter is defined by a `callcenter.xml` (Call Center Definition File). This XML file describes the adapter to Salesforce and is imported via **Setup > Call Centers > Import**. The root element is `CallCenter` and the key child elements are:

- `InternalName` — unique identifier (no spaces, used in API references)
- `DisplayName` — label shown in Setup UI
- `AdapterUrl` — the fully-qualified HTTPS URL of the adapter HTML page
- `CTIVersion` — must be `"4.0"` for Lightning / Open CTI for Lightning (not `"3.0"` which is Classic-only)
- `RequiresCallCenter` — set to `"true"` for users to be assigned

After import, users must be assigned to the Call Center via **Setup > Call Centers > Manage Call Center Users**.

### Lightning Utility Bar Registration

The softphone panel is added as a utility bar item in a Lightning App. Navigate to **Setup > App Manager**, edit the target Lightning App, go to **Utility Items**, and add **Open CTI Softphone**. The utility item pulls its adapter URL from the assigned Call Center definition — you do not specify a URL directly in the utility item. Width, height, and panel label are configurable here. The utility bar item is desktop-only; the Salesforce mobile app does not render utility bars.

### Call Logging with saveLog

`sforce.opencti.saveLog` creates a Task record. The `value` parameter is an object where keys are Task API field names. At minimum pass `Subject`, `CallDurationInSeconds`, `CallType`, `Status`, and `WhoId` or `WhatId`. The Task `ActivityDate` defaults to today. Logging should occur on call end, not call start, to capture accurate duration. If the adapter calls `saveLog` before `enableClickToDial` resolves, the API may return an error; always gate saveLog on a confirmed active session.

### lightning-click-to-dial LWC Component

Salesforce provides the `lightning-click-to-dial` base component for use in record pages and list views. It renders a phone number as a clickable link that fires the Open CTI `onClickToDial` listener registered in the adapter. The component accepts `value` (phone string) and `record-id` attributes. Using this component is preferred over raw `<a href="tel:...">` links because it participates in the Open CTI event system and respects `enableClickToDial`/`disableClickToDial` state.

---

## Common Patterns

### Pattern: Enabling Click-to-Dial on Adapter Load

**When to use:** The adapter must activate click-to-dial once when the softphone iframe loads so phone fields become clickable across the entire org session.

**How it works:**

1. On `DOMContentLoaded`, call `sforce.opencti.enableClickToDial` with a callback.
2. Inside the callback, check `response.success`. If `true`, register the `onClickToDial` listener.
3. In the `onClickToDial` listener, extract `number` and `recordId` to initiate the telephony call.
4. Call `sforce.opencti.disableClickToDial` immediately after the call connects to prevent double-dials.

**Why not the alternative:** Registering `onClickToDial` before `enableClickToDial` succeeds causes the listener to register against a deactivated state, meaning clicks on phone fields silently do nothing.

### Pattern: Logging a Call as a Closed Task

**When to use:** Every call end should produce a Task record so supervisors and agents have a call history on the related record.

**How it works:**

1. On telephony call-end event (vendor-specific), capture duration and call direction.
2. Call `sforce.opencti.saveLog` with a `value` object containing at minimum: `Subject`, `Status: 'Completed'`, `CallType` (`'Inbound'` or `'Outbound'`), `CallDurationInSeconds`, and either `WhoId` (Contact/Lead) or `WhatId` (Account/Case/Opportunity).
3. In the callback, check `response.success`. Surface an error toast to the agent if logging fails.

**Why not the alternative:** Creating a Task via Apex REST from the telephony vendor backend requires OAuth token management and server-side configuration. `saveLog` runs in the user's browser session with their permissions, is simpler to implement, and creates the Task associated with the correct Call Center activity.

### Pattern: Screen Pop on Inbound Call

**When to use:** When an inbound call arrives with a known caller ID, the agent's browser should automatically navigate to the caller's Contact or Case record.

**How it works:**

1. On inbound call event, perform an ANI (caller ID) lookup — typically via a Salesforce REST API callout or vendor webhook.
2. Once the Salesforce record ID is known, call `sforce.opencti.screenPop` with `type: 'SOBJECT'` and `params: {recordId: '<18-char-id>'}`.
3. If no record is found, use `type: 'SEARCH'` with `params: {searchParams: '<phone-number>'}` to open a search results page.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New third-party telephony integration with browser softphone | Open CTI JavaScript API + `callcenter.xml` | Native platform path; no AppExchange package required for basic integration |
| Need Amazon Connect deep integration (transcription, AI coaching) | Service Cloud Voice — do NOT use Open CTI | Service Cloud Voice is the supported path for Amazon Connect; Open CTI does not provide real-time transcription hooks |
| Rendering a phone field that users can click to call | `lightning-click-to-dial` LWC component | Participates in CTI enable/disable state; preferred over bare anchor tags |
| Need call duration and direction on Task record | `saveLog` with `CallDurationInSeconds` + `CallType` | These are standard Activity fields; `saveLog` maps directly to them |
| Softphone panel is too small for the adapter UI | `setSoftphonePanelHeight` called at adapter load | Dynamic resize after DOM measurement is the correct approach |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites** — Confirm the telephony vendor adapter page URL is available over HTTPS, the domain is added to CSP Trusted Sites and CORS allowed-origins in Setup, and the user has a valid Salesforce license that supports Call Centers.
2. **Author and import callcenter.xml** — Create the Call Center definition file with `CTIVersion` set to `4.0` and `AdapterUrl` pointing to the hosted adapter page. Import via Setup > Call Centers. Assign relevant users to the Call Center.
3. **Register the utility item** — In App Manager, add the Open CTI Softphone utility item to the target Lightning App. Set appropriate panel width and height. Verify the softphone panel renders in the app.
4. **Implement the adapter page** — In the hosted HTML file, call `sforce.opencti.enableClickToDial` on load, register the `onClickToDial` listener, implement `screenPop` for inbound call ANI lookup, and wire call-end events to `saveLog`.
5. **Test click-to-dial and screen pop** — In a sandbox, click a phone field and confirm the `onClickToDial` callback fires with correct `number` and `recordId`. Trigger a screen pop and confirm navigation to the correct record.
6. **Test call logging** — End a test call and verify a Task record with the correct `Subject`, `CallDurationInSeconds`, `CallType`, and related `WhoId`/`WhatId` is created.
7. **Review CSP and CORS** — Confirm no browser console errors related to blocked frames, CORS rejections, or `sforce is not defined` errors before deploying to production.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `callcenter.xml` uses `CTIVersion` 4.0 (not 3.0) and a valid HTTPS `AdapterUrl`
- [ ] Adapter page does not self-load the Open CTI script — it relies on platform injection
- [ ] `enableClickToDial` is called once on adapter load before `onClickToDial` is registered
- [ ] `saveLog` passes at minimum `Subject`, `Status: 'Completed'`, `CallType`, and `WhoId` or `WhatId`
- [ ] `screenPop` falls back to `type: 'SEARCH'` when no record ID is available
- [ ] Adapter domain is in CSP Trusted Sites and CORS allowed-origins
- [ ] Users are assigned to the Call Center in Setup before testing

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **CTIVersion mismatch silently breaks the adapter** — Using `CTIVersion` 3.0 in `callcenter.xml` loads the Classic Open CTI API, not the Lightning API. The `sforce.opencti` namespace is undefined and all calls fail without a clear error message in the Lightning console.
2. **enableClickToDial must resolve before onClickToDial is registered** — Calling `onClickToDial` before the `enableClickToDial` callback succeeds means the listener registers against a deactivated state. Phone field clicks are silently swallowed. Always nest `onClickToDial` inside the `enableClickToDial` success callback.
3. **saveLog requires an active Call Center assignment** — If the logged-in user is not assigned to a Call Center, `saveLog` returns `success: false` with the error `User is not assigned to a Call Center`. The call still appears to complete with no visible UI error unless the adapter explicitly checks `response.success`.
4. **Utility bar is desktop-only** — The Open CTI softphone panel does not render in the Salesforce mobile app or in Salesforce Classic. Agents using mobile or Classic see no softphone. This is a platform constraint, not a configuration error.
5. **CSP and CORS must both be configured** — Adding the adapter domain to CSP Trusted Sites alone is not sufficient. The domain also requires an entry in Setup > CORS Allowed Origins List (or the adapter URL must be framed correctly). Missing CORS causes `sforce is not defined` errors in the browser console because the platform cannot inject the API into a non-allowed origin.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `callcenter.xml` | Call Center definition file to import into Setup > Call Centers |
| Adapter HTML page | Hosted page implementing Open CTI JavaScript API methods |
| Lightning App utility item config | Step-by-step configuration for the softphone utility bar item |
| Task logging snippet | `saveLog` implementation with correct field mapping |
| `lightning-click-to-dial` usage snippet | LWC component markup for phone field rendering |

---

## Related Skills

- `admin/app-and-tab-configuration` — configuring the Lightning App utility bar where the softphone item lives
- `architect/service-cloud-architecture` — when to use Service Cloud Voice vs Open CTI at the architecture level
