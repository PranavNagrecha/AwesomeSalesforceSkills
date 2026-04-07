# Examples — Experience Cloud Integration Patterns

## Example 1: SAML 2.0 SSO for a Partner Portal Using Okta as IdP

**Context:** A manufacturing company runs a partner portal on Experience Cloud (LWR template). Partners authenticate using their corporate Okta accounts. The Salesforce org also issues SAML assertions to a separate downstream order management system (Salesforce acting as IdP).

**Problem:** The implementation team initially configured SAML at the org level using the default org entity ID and provided that to Okta. Assertions were rejected because the ACS URL and entity ID on the SP metadata did not match the site-specific values Salesforce expects for an Experience Cloud site.

**Solution:**

1. In Salesforce Setup > Identity > SAML Single Sign-On Settings, create a new SAML SSO configuration:
   - **Issuer (IdP Entity ID):** `http://www.okta.com/<okta-app-id>` (from Okta metadata)
   - **Identity Provider Certificate:** upload the Okta signing certificate
   - **Entity ID:** leave blank — Salesforce auto-generates the site-scoped entity ID
   - **ACS URL:** Salesforce generates this as `https://<site-domain>/login?so=<org-id>`

2. Export the Salesforce SP metadata XML from the SAML configuration record's "Download Metadata" button. Provide this XML to the Okta admin to configure the Salesforce application in Okta. Do not manually copy the org-level entity ID.

3. In Experience Builder > Administration > Login & Registration for the partner portal site, enable the Okta SAML SSO configuration.

4. Enable Setup > Identity > Identity Provider to allow the org to issue assertions to the order management system (Connected App). This is configured entirely separately from the inbound Okta SSO setup.

5. Test by navigating to the partner portal in an incognito window. Confirm the redirect to Okta, successful assertion validation, and redirect back to the portal homepage.

```
SP Entity ID (site-specific):   https://partnerportal.example.com/saml/metadata
ACS URL:                        https://partnerportal.example.com/login?so=00D...
IdP Issuer (Okta):              http://www.okta.com/abc123def456
Protocol:                       SAML 2.0
Org acting as IdP:              Yes (separate Connected App for order mgmt system)
```

**Why it works:** The SAML configuration is site-scoped. The SP metadata exported from the SAML configuration record reflects the correct site entity ID and ACS URL, not the org defaults. Enabling the org's Identity Provider role does not touch or disable the inbound SAML SSO setup — the two configurations are independent.

---

## Example 2: Privileged Script Tag to Inject Google Tag Manager on an LWR Site

**Context:** A financial services company's customer portal runs on LWR. The marketing team needs GTM loaded on every portal page for conversion tracking and A/B testing. A developer initially tried to create a custom LWC component with a `<script>` tag in the template to load GTM.

**Problem:** The custom LWC approach was blocked in two ways: (1) LWR's renderer strips `<script>` tags from LWC component templates, and (2) even if the tag rendered, the LWR CSP policy would block execution of scripts from `www.googletagmanager.com` because it was not in the `script-src` allowlist.

**Solution:**

1. In Experience Builder, open Settings > Security for the customer portal site.
2. Under Privileged Script Tags, click Add and enter:
   - Script URL: `https://www.googletagmanager.com/gtm.js?id=GTM-XXXXXX`
   - Load order: Head (ensures GTM fires before page content renders)
3. Save and publish the site. Salesforce adds `https://www.googletagmanager.com` to the site's CSP `script-src` directive and injects the `<script>` tag in the `<head>` of every page.
4. For the `dataLayer.push()` calls (e.g., tracking page views, user IDs), create a standard LWC component that fires `connectedCallback()` and calls `window.dataLayer.push({...})`. This is safe — LWC can call `window.dataLayer` once it exists; it does not need to inject a `<script>` tag.
5. Place this tracking LWC component in the Experience Builder page template (not individual pages) so it runs on every page load.

```javascript
// tracking-component.js — fires on every LWC component connect
import { LightningElement, wire } from 'lwc';
import { CurrentPageReference } from 'lightning/navigation';

export default class TrackingComponent extends LightningElement {
    @wire(CurrentPageReference) pageRef;

    connectedCallback() {
        if (window.dataLayer) {
            window.dataLayer.push({
                event: 'pageview',
                pagePath: window.location.pathname,
            });
        }
    }
}
```

**Why it works:** The Privileged Script Tag is the only CSP-compliant injection path in LWR sites. Once GTM is loaded via Privileged Script Tag, the `window.dataLayer` array is available in the global scope. LWC components can safely push to it without needing to create additional `<script>` tags.

---

## Anti-Pattern: Injecting Widget Scripts via Custom LWC Component Template

**What practitioners do:** A developer creates a custom LWC component with a hardcoded `<script src="https://widget.vendor.com/loader.js"></script>` in the HTML template, then places it on every Experience Cloud page to load a chat widget.

**What goes wrong:** LWR's HTML template compiler strips `<script>` elements from LWC component templates at compile time. The component renders without the script tag. If the developer works around this by dynamically creating a `<script>` element in JavaScript and appending it to `document.head`, the LWR CSP policy blocks script execution from the vendor domain because it is not in `script-src`. The chat widget silently fails to load, often with no visible error for end users — only a CSP violation in the browser console.

**Correct approach:** Use Privileged Script Tag in Experience Builder Settings > Security to add the vendor's script URL. This is the only mechanism that simultaneously (1) adds the domain to `script-src`, and (2) injects the `<script>` tag into the site `<head>`. Once the Privileged Script Tag is configured, the vendor script loads correctly without any custom LWC component needed for the injection itself.
