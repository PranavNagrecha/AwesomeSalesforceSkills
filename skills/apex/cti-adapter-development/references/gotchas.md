# Gotchas — CTI Adapter Development

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: CTIVersion 3.0 vs 4.0 — Silent API Failure

**What happens:** When `callcenter.xml` uses `CTIVersion` 3.0, Salesforce loads the Classic Open CTI API instead of the Lightning API. The `sforce.opencti` namespace is undefined in the adapter page context. Every method call (including `enableClickToDial`) throws a JavaScript `TypeError: Cannot read properties of undefined`. There is no warning in the Setup UI — the import succeeds and the utility item appears to render normally.

**When it occurs:** Any new adapter built for Lightning Experience but authored from outdated documentation or copied from a Classic integration example. Classic Open CTI adapters targeting Salesforce Classic used version 3.0.

**How to avoid:** Always use `<CTIVersion>4.0</CTIVersion>` in `callcenter.xml` for Lightning-based integrations. If you inherit an existing definition, re-import the corrected XML and reassign users — the `InternalName` must remain the same for users to stay assigned.

---

## Gotcha 2: enableClickToDial Must Precede onClickToDial Registration

**What happens:** If `sforce.opencti.onClickToDial` is called before `sforce.opencti.enableClickToDial` has succeeded (i.e., before its callback fires with `success: true`), the listener registers against a deactivated click-to-dial state. Phone fields render with a tel link appearance but clicking them produces no event. The `onClickToDial` callback never fires. No error is thrown.

**When it occurs:** Adapter pages that call both methods on `DOMContentLoaded` without sequencing, or that use `Promise.all` style parallel initialization.

**How to avoid:** Always nest the `onClickToDial` call inside the `enableClickToDial` success callback:

```javascript
sforce.opencti.enableClickToDial({
  callback: (res) => {
    if (res.success) {
      sforce.opencti.onClickToDial({ listener: myHandler });
    }
  }
});
```

---

## Gotcha 3: saveLog Silently Fails When User Is Not Assigned to a Call Center

**What happens:** `sforce.opencti.saveLog` returns `response.success: false` with the error message `"User is not assigned to a Call Center"`. No Task record is created. The adapter page receives this in its callback, but if the adapter does not explicitly check `response.success` and surface an error to the agent, the agent sees nothing and assumes the call was logged.

**When it occurs:** During initial setup (user not yet assigned to the Call Center), after sandbox refreshes that clear Call Center user assignments, or in orgs where users are occasionally removed from the Call Center list during maintenance.

**How to avoid:** Always check `response.success` in the `saveLog` callback and display a user-visible error if logging fails. Proactively verify Call Center user assignments after sandbox refreshes.

---

## Gotcha 4: Adapter Domain Missing from Both CSP Trusted Sites AND CORS

**What happens:** The `sforce` global is injected into the adapter iframe only if Salesforce can communicate with the page's origin. If the adapter domain is missing from CORS Allowed Origins, the injection fails and `sforce` is `undefined`. Missing from CSP Trusted Sites alone also causes frame-loading errors. Both lists must include the adapter origin.

**When it occurs:** When the adapter domain is added to CSP Trusted Sites (a common first step) but the developer assumes that is sufficient. The CORS list is a separate Setup page (**Setup > CORS Allowed Origins List**) and is frequently missed.

**How to avoid:** After adding the adapter domain to CSP Trusted Sites, also add it to CORS Allowed Origins. Verify by opening the adapter page in the utility panel and checking the browser console — `sforce is not defined` indicates a CORS or CSP gap.

---

## Gotcha 5: Softphone Utility Panel Does Not Appear in Salesforce Mobile or Classic

**What happens:** Agents who access Salesforce via the Salesforce mobile app or Salesforce Classic see no softphone panel at all — the utility bar is a Lightning Experience desktop-only feature. If agents are trained to expect the softphone to always be present, they may believe the adapter is broken when switching to mobile.

**When it occurs:** Any org with a mixed desktop/mobile or Lightning/Classic user population.

**How to avoid:** Document this limitation in rollout communications and training. For mobile call handling, evaluate Salesforce CTI with the Salesforce Mobile SDK directly — Open CTI's browser-based JavaScript API is not available in the mobile app.

---

## Gotcha 6: screenPop Navigates Away from Agent's Current Context Without Warning

**What happens:** `sforce.opencti.screenPop` immediately navigates the agent's primary browser tab to the target record, even if the agent has unsaved changes on a record they are currently editing. There is no platform-level confirmation dialog.

**When it occurs:** Inbound-call screen-pop workflows where an agent is actively editing a record when a call arrives.

**How to avoid:** Consider delaying the automatic screen pop until the agent accepts the call (rather than on call ring), or use `type: 'SEARCH'` with the caller's phone number so the agent can choose the correct record rather than being forcibly navigated. Add a confirmation step in the adapter UX before calling `screenPop`.
