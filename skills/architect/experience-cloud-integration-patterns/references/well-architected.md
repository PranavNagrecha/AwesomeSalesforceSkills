# Well-Architected Notes — Experience Cloud Integration Patterns

## Relevant Pillars

### Security

Security is the primary pillar for Experience Cloud external integration. Every integration at the site boundary introduces an authentication or script-injection surface that must be explicitly controlled.

- **SSO token handling:** SAML assertions and OIDC tokens must never be logged or stored in browser-accessible storage (localStorage, sessionStorage) on public-facing sites. Salesforce handles assertion validation server-side; the developer's responsibility is to ensure custom registration handlers do not log assertion content.
- **CSP enforcement:** Privileged Script Tag is the mechanism for maintaining CSP integrity while allowing third-party scripts. Bypassing it (via dynamic `<script>` injection or `unsafe-inline` workarounds) degrades the site's XSS posture. Every third-party origin must be explicitly allowlisted.
- **iFrame framing protection:** The default `X-Frame-Options: SAMEORIGIN` header is a security control, not a bug. Relaxing it for cross-origin framing must be a deliberate, reviewed decision with a documented trust boundary.
- **Data Cloud identity signals:** The Web SDK can hash and transmit known-user email addresses to Data Cloud for identity resolution. This must be reviewed against the organization's privacy policy and applicable data residency regulations before activation.

### Reliability

- **SSO failure modes:** If the external IdP is unavailable, users cannot authenticate. Design login pages to display a meaningful error (not a blank page or a raw SAML error) and document the fallback authentication path — particularly for administrators who need break-glass access to Salesforce when SSO is down.
- **Script tag availability:** Third-party scripts loaded via Privileged Script Tag are a dependency for every page load. A vendor CDN outage can degrade or break page functionality. Use asynchronous loading where possible and test site behavior when the external script fails to load.
- **Data Cloud event delivery:** The Web SDK uses an asynchronous event stream. Event delivery is not guaranteed to be real-time. Design analytics and personalization use cases to tolerate eventual consistency in event data.

### Operational Excellence

- **Per-site configuration tracking:** Because Privileged Script Tags, SSO enablement, and Data Cloud activation are all configured per-site, organizations with multiple Experience Cloud portals must maintain an explicit inventory of what is configured on each site. A configuration drift audit should be part of the periodic site operations review.
- **Auth Provider registration handler versioning:** Custom Apex registration handlers must be version-controlled and deployed through standard CI/CD pipelines (sfdx/sf CLI). Changes to registration handler logic affect all users who authenticate through that provider. Regression test coverage for both new-user and existing-user flows is required.
- **Change management for SSO certificate rotation:** External IdP certificates have expiration dates. SAML SSO configurations must be updated before the IdP certificate expires, or all SSO users lose access simultaneously. Add IdP certificate expiry monitoring to the operational calendar.

## Architectural Tradeoffs

**SAML 2.0 vs. OIDC for SSO:** SAML 2.0 is the incumbent standard and is supported by all enterprise IdPs. It requires metadata exchange (XML files) and has more complex configuration. OIDC is simpler to configure (JSON endpoints), supports token refresh, and is the basis of modern mobile-friendly auth flows. Choose OIDC when the IdP supports it and the use case includes mobile app authentication or token refresh requirements. Choose SAML when the IdP is a legacy enterprise system or when the organization has an existing SAML infrastructure.

**Privileged Script Tag vs. headless analytics integration:** Injecting third-party scripts via Privileged Script Tag means the scripts run in the browser with access to the page DOM and any user session context visible to JavaScript. For sensitive portals (financial, healthcare), consider whether the data the third-party script can access in the browser is acceptable. An alternative for analytics is a server-side integration where behavioral events are sent to the analytics platform via Apex callouts or platform events, avoiding client-side script access entirely.

**Data Cloud Web SDK vs. custom event streaming:** The Data Cloud Web SDK provides out-of-the-box behavioral event capture with identity resolution. A custom streaming integration (using Platform Events or Apex to push events to an external analytics system) provides more control over data shape and destination but requires more engineering effort and loses the automatic identity graph enrichment that Data Cloud provides.

## Anti-Patterns

1. **Org-level SSO assumptions** — Configuring SAML at the org level and assuming Experience Cloud sites inherit the configuration. Experience Cloud sites require explicit SSO enablement in the site's Login & Registration settings. This anti-pattern causes all SSO attempts for the site to fail silently or fall back to password login.

2. **Hardcoded script injection in LWC templates** — Placing `<script>` tags directly in LWC component templates or using `eval()` to load third-party JavaScript. LWR strips these at compile time or CSP blocks execution at runtime. This anti-pattern creates a false sense of delivery while the script silently fails to load.

3. **iFrame-first embedding architecture** — Designing a portal integration around iFrame embedding before investigating the `X-Frame-Options` constraint. Discovering the constraint late causes significant rework. Always investigate platform constraints before selecting an embedding approach.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help — SAML for Experience Cloud Sites — https://help.salesforce.com/s/articleView?id=sf.sso_saml_setting_up.htm
- Salesforce Help — Configure an Authentication Provider — https://help.salesforce.com/s/articleView?id=sf.sso_authentication_providers.htm
- Salesforce Developer — Privileged Script Tag in LWR Sites — https://developer.salesforce.com/docs/platform/lwc/guide/create-lwr-privileged-script.html
- Salesforce Help — Connect Experience Cloud to Data Cloud — https://help.salesforce.com/s/articleView?id=sf.c360_a_experience_cloud_site_setup.htm
