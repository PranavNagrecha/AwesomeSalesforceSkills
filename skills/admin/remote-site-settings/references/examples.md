# Examples — Remote Site Settings and CSP Trusted Sites

## Example 1: Apex Callout Failing After Change Set Deployment

**Context:** A developer builds an Apex integration class that calls a payment processing API (https://api.payments.com). The class works correctly in sandbox — the Remote Site Setting was added manually during development. The developer deploys via Change Set, which includes the Apex class, the trigger that calls it, and test classes. After deployment, every payment attempt fails with `CalloutException: Unauthorized endpoint, please check Setup>Security>Remote Site Settings`.

**Problem:** The Remote Site Setting `https://api.payments.com` exists in sandbox but was not included in the Change Set. The Change Set tool does not automatically detect Remote Site Settings as dependencies of Apex code. The class deployed successfully — the setting was simply missing in production.

**Solution:**

1. In sandbox, open the Change Set.
2. Click "Add" to add components.
3. Change "Component Type" dropdown to "Remote Site Setting."
4. Select the `api_payments_com` Remote Site Setting and add it.
5. Upload the updated Change Set to production.
6. Deploy in production — both the Apex class and the Remote Site Setting are now included.
7. Test a payment — the callout succeeds.

For future deployments, add a note in the project documentation or team runbook: "Apex callout classes require their Remote Site Settings to be included in every Change Set that deploys the Apex code."

**Why it works:** Remote Site Settings are independent metadata components — they must be explicitly included in Change Sets and deployment packages to be deployed alongside the Apex code that depends on them.

---

## Example 2: Distinguishing Remote Site Settings from CSP Trusted Sites

**Context:** A Lightning Web Component uses a `fetch()` call to load data from an external analytics service (https://data.analytics-vendor.com). The component also calls an Apex method that makes a server-side callout to the same URL. The LWC fetch fails in the browser with a CSP violation. The Apex callout fails with `CalloutException: Unauthorized endpoint`.

**Problem:** Two failures, two different root causes requiring two different configurations.

**Solution:**

For the LWC browser-side fetch:
1. Navigate to Setup > Security > CSP Trusted Sites.
2. Click New Trusted Site.
3. Enter Site Name: `analytics_vendor`, Site URL: `https://data.analytics-vendor.com`.
4. Select "connect-src" directive (for fetch/XHR).
5. Save. The LWC fetch should now succeed.

For the Apex server-side callout:
1. Navigate to Setup > Security > Remote Site Settings.
2. Click New Remote Site.
3. Enter Remote Site Name: `analytics_vendor`, Remote Site URL: `https://data.analytics-vendor.com`.
4. Save. The Apex Http.send() should now succeed.

**Why it works:** The same external URL requires two separate allowlist entries because the two calling contexts (browser and Salesforce server) are governed by completely separate security mechanisms. Adding only one entry fixes only one of the two failures.

---

## Anti-Pattern: Adding External URL to CSP Trusted Sites to Fix Apex CalloutException

**What practitioners do:** An Apex callout fails with `CalloutException: Unauthorized endpoint`. The admin searches for "Salesforce unauthorized endpoint" and finds advice to add the URL to "Trusted Sites." They navigate to Setup > Security > CSP Trusted Sites and add the external URL.

**What goes wrong:** The Apex callout continues to fail with the same error. CSP Trusted Sites have no effect on server-side Apex Http.send() callouts. The admin may try different CSP directives (all-sources, connect-src, script-src), changing nothing for the Apex callout. This can waste hours of troubleshooting time.

**Correct approach:** For a failing Apex Http.send() callout, always go to Setup > Security > Remote Site Settings (not CSP Trusted Sites) and add the external URL. CSP Trusted Sites are for browser-side Lightning component resource loading — not Apex server-side callouts. The error message itself names the correct location: "check Setup > Security > Remote Site Settings."
