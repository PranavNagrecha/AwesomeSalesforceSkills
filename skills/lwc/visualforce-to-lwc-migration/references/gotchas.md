# Gotchas — Visualforce to LWC Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: URL Parameters Get a `c__` Prefix on App Builder Pages

**What happens:** A VF page consumed `?id=abc&mode=edit` from the URL. The migrated LWC is added to a Lightning App Builder page (custom tab, App Page). External callers continue to hit the old URL. The LWC reads `pageRef.state.id` and `pageRef.state.mode` — and gets `undefined` for both.

**Why:** App Builder enforces a `c__` namespace prefix on custom URL parameters to prevent collision with platform parameters. The actual values arrive as `pageRef.state.c__id` and `pageRef.state.c__mode`. An LWC component that does NOT live on an App Builder page (e.g., a Quick Action or community page) may read parameters without the prefix — the rules differ by surface.

**Mitigation:** During migration, document every external caller URL. Either update callers to use `c__paramname` or accept both: `pageRef.state.c__id || pageRef.state.id` during a transition window.

## Gotcha 2: Lightning Web Security Breaks JS Libraries That Worked in VF

**What happens:** The VF page loaded `jquery-3.5.1.js` and `bootstrap.bundle.min.js` via `<apex:includeScript>`. The migrated LWC loads the same files via `loadScript('/resource/jquery')`. The component renders in dev — but in an org with Lightning Web Security enabled, jQuery's selector engine throws because it tries to access cross-origin iframe documents that LWS sandboxes.

**Why:** Visualforce ran scripts under Locker Service (an in-Aura security model) or with no sandboxing at all. LWC under Lightning Web Security uses native browser sandboxing (Trusted Types, secure window proxies) which rejects patterns Locker permitted.

**Mitigation:** Test every static resource library in an LWS-enabled scratch org BEFORE declaring the migration complete. Replace incompatible libraries with native LWC primitives (`<lightning-datatable>` for jQuery DataTables, SLDS classes for Bootstrap layout) or with LWS-compatible alternatives. Maintain a blocked-library list at the org level.

## Gotcha 3: `@AuraEnabled(cacheable=true)` Forbids DML

**What happens:** A VF controller method ran a `SELECT` and an `UPDATE` (e.g., "fetch and mark-read"). The migrated `@AuraEnabled` method copies that logic but adds `cacheable=true` so it can be wired. At runtime: `System.LimitException: cacheable=true methods cannot perform DML`.

**Why:** The Lightning Data Cache layer requires methods to be side-effect-free so it can serve cached results. DML inside a cacheable method would mean cache hits skip the side effect — silently breaking the contract.

**Mitigation:** Split read and write. Cacheable wire for the data fetch; imperative non-cacheable method for the DML. The "mark-read" is a separate UI action triggered after render, not a side effect of the read.

## Gotcha 4: Viewstate Removal Exposes Hidden Coupling

**What happens:** A VF wizard had three steps. Each step had its own controller method that updated a `wizardData` member variable on the controller. The controller was instantiated once per page session and viewstate persisted `wizardData` across postbacks. Migrating step-by-step to LWC keeps wizard step 1 as VF and adds LWC for steps 2–3 — but the data accumulated in step 1's viewstate is gone the moment the user navigates to the LWC.

**Why:** Viewstate is invisible glue. Any code that read controller state in a later postback was implicitly relying on it. Crossing the VF–LWC boundary breaks the implicit handoff.

**Mitigation:** During migration, identify viewstate-bearing flows. Convert intermediate state to either (a) draft records in the database (preferred for multi-step wizards), (b) URL parameters passed forward, or (c) session-storage for client-only state. Avoid preserving viewstate by keeping the whole flow VF — that delays the migration indefinitely.

## Gotcha 5: `PageReference` Returns Don't Translate 1:1 to NavigationMixin

**What happens:** A VF `save()` method returned `new PageReference('/apex/Confirm?id=' + caseId)` which redirected the user to a confirmation VF page after save. The migration replaces the VF with an LWC and re-implements `save` as imperative Apex — the developer assumes returning a similar string from Apex will trigger navigation. It doesn't.

**Why:** `PageReference` is a Visualforce framework object. The LWC has no analogous mechanism — Apex can return data, not navigation intents. Navigation is purely a client-side concern in LWC, expressed via `NavigationMixin.Navigate({type, attributes})` from the JS layer after the imperative call resolves.

**Mitigation:** Apex returns the success DTO; the LWC's `await save(...)` callback then explicitly invokes `this[NavigationMixin.Navigate]({...})`. The navigation logic moves up to the client.

## Gotcha 6: `<apex:outputText escape="false">` Breaks the Sanitization Default

**What happens:** A VF page used `<apex:outputText value="{!description}" escape="false" />` to allow stored `<br>` tags in a text-area to render as line breaks. The naive migration uses `lwc:dom="manual"` and sets `innerHTML = description` to preserve the behavior. A user injects `<img src=x onerror=alert(1)>` into the text-area — the LWC renders it and executes the script.

**Why:** `escape="false"` was already a security trap in VF; LWC's default sanitization through template binding existed precisely to prevent this. Bypassing the default with `innerHTML` recreates the original XSS surface in the new code.

**Mitigation:** Use `<lightning-formatted-text>` (preserves whitespace and renders URLs as links) or a Markdown renderer with explicit allow-list sanitization. Never set `innerHTML` from user-controlled data. Treat the migration as an opportunity to close the XSS hole, not preserve it.

## Gotcha 7: Lightning Out Wrapper Doubles the Page Weight

**What happens:** A Lightning Out wrapper VF page is deployed to keep an old URL working. The page mounts the new LWC inside Aura. The page now loads (a) the Lightning Out runtime, (b) Aura framework, (c) the LWC framework, (d) the LWC bundle itself — for a single component that, on a Lightning Experience surface, would load only the LWC. End users complain the page loads more slowly than the original VF.

**Why:** Lightning Out is a coexistence bridge, not a performance-optimized container. The overhead is acceptable for short-lived migration windows; it is not a permanent architecture.

**Mitigation:** Track every Lightning Out wrapper with a removal date. Update upstream callers to navigate directly to the Lightning record/app page within one or two release cycles. Do not let wrappers accumulate.

## Gotcha 8: VF-Embedded Static Resources Need `loadScript` in LWC

**What happens:** A VF page used `<apex:includeScript value="{!URLFOR($Resource.MyLib, 'lib.js')}" />`. The migrated LWC tries `import 'c/myLib'` (assuming there's a sibling LWC) — but the resource is a JS file, not a component. The component fails to compile.

**Why:** Static resources are loaded asynchronously in LWC via `lightning/platformResourceLoader`. They are not module-importable.

**Mitigation:**

```js
import { loadScript } from 'lightning/platformResourceLoader';
import MY_LIB from '@salesforce/resourceUrl/MyLib';

connectedCallback() {
    loadScript(this, MY_LIB + '/lib.js')
        .then(() => { /* library is now on window */ });
}
```

The library lives on `window` after load; treat it as a side effect, not an import.
