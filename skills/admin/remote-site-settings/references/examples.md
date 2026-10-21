# Examples — Remote Site Settings and CSP Trusted Sites

UNVERIFIED (2026-10-21), applies to this file: the quoted exception text `CalloutException: Unauthorized endpoint, please check Setup>Security>Remote Site Settings` and the Change Set UI steps are Help-only; the corpus says only that an unregistered callout fails (apexdev 264 L34758-34759).

## Example 1: Apex Callout Failing After Change Set Deployment

**Context:** A developer builds an Apex integration class that calls a payment processing API (https://api.payments.com). The class works correctly in sandbox — the Remote Site Setting was added manually during development. The developer deploys via Change Set, which includes the Apex class, the trigger that calls it, and test classes. After deployment, every payment attempt fails with `CalloutException: Unauthorized endpoint, please check Setup>Security>Remote Site Settings` (UNVERIFIED text, see top).

**Problem:** The Remote Site Setting `https://api.payments.com` exists in sandbox but was not included in the Change Set, so production has no registration for the site. The class deployed successfully — the setting was simply missing in production.

**Solution:**

1. In sandbox, open the Change Set.
2. Click "Add" to add components.
3. Change "Component Type" dropdown to "Remote Site Setting."
4. Select the `api_payments_com` Remote Site Setting and add it.
5. Upload the updated Change Set to production.
6. Deploy in production — both the Apex class and the Remote Site Setting are now included.
7. Test a payment — the callout succeeds.

For source-driven deploys, the same setting is `remoteSiteSettings/api_payments_com.remoteSite` (api_meta 264 L106503-106504):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<RemoteSiteSetting xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Payment processor callouts from PaymentService.cls</description>
    <disableProtocolSecurity>false</disableProtocolSecurity>
    <isActive>true</isActive>
    <url>https://api.payments.com</url>
</RemoteSiteSetting>
```

**Why it works:** Remote Site Settings are independent metadata components (`RemoteSiteSetting`, api_meta 264 L106496) — they must be deployed alongside the Apex code that depends on them.

---

## Example 2: Distinguishing Remote Site Settings from CSP Trusted Sites

**Context:** A Lightning Web Component uses a `fetch()` call to load data from an external analytics service (https://data.analytics-vendor.com). The component also calls an Apex method that makes a server-side callout to the same URL. The LWC fetch fails in the browser with a CSP violation. The Apex callout fails as unregistered.

**Problem:** Two failures, two different root causes requiring two different configurations.

**Solution:**

For the LWC browser-side fetch:
1. Add a Trusted URL (the `CspTrustedSite` type, formerly CSP Trusted Sites, api_meta 264 L41578-41582).
2. Name `analytics_vendor`, URL `https://data.analytics-vendor.com` — "For a third-party API, the URL must begin with https://" (api_meta 264 L41658).
3. Set `isApplicableToConnectSrc` (connect-src, for fetch/XHR; api_meta 264 L41687).
4. Save. The LWC fetch should now succeed.

For the Apex server-side callout:
1. From Setup, enter Remote Site Settings in the Quick Find box (apexdev 264 L34765).
2. Click New Remote Site.
3. Enter Remote Site Name: `analytics_vendor`, Remote Site URL: `https://data.analytics-vendor.com`.
4. Save. The Apex Http.send() should now succeed.

**Why it works:** The same external URL requires two separate allowlist entries because the two calling contexts (browser and Salesforce server) are governed by separate mechanisms. Adding only one entry fixes only one of the two failures.

---

## Anti-Pattern: Adding External URL to CSP Trusted Sites to Fix Apex CalloutException

**What practitioners do:** An Apex callout fails as unregistered. The admin searches for "Salesforce unauthorized endpoint" and finds advice to add the URL to "Trusted Sites", then adds it as a Trusted URL.

**What goes wrong:** The Apex callout continues to fail. Trusted URLs set CSP directives for Lightning components, third-party APIs and WebSocket connections (api_meta 264 L41579-41580); they do not register a site for Apex. The admin may try different directive flags, changing nothing for the Apex callout.

**Correct approach:** For a failing Apex Http.send() callout, open Remote Site Settings from Setup Quick Find (not Trusted URLs) and add the external URL, or switch the endpoint to a named credential (apexdev 264 L34761).
