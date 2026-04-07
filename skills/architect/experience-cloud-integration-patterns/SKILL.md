---
name: experience-cloud-integration-patterns
description: "Use when designing or reviewing integrations between an Experience Cloud site and external systems — SSO identity providers, third-party widgets, external content sources, and behavioral data platforms. Triggers: 'integrate SSO with Experience Cloud site', 'embed third-party chat widget in LWR site', 'connect Data Cloud to Experience Cloud', 'inject Google Tag Manager into Experience Cloud', 'configure SAML for community login', 'allow external IdP login on portal'. NOT for internal Salesforce-to-Salesforce integration, NOT for Apex callout mechanics within Experience Cloud pages, NOT for multi-IdP SSO login-page routing (use lwc/experience-cloud-multi-idp-sso)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
tags:
  - experience-cloud
  - sso
  - saml
  - oidc
  - oauth
  - lwr
  - privileged-script-tag
  - data-cloud
  - third-party-widgets
  - iframe
  - external-systems
triggers:
  - "integrate SSO with Experience Cloud site using SAML or OIDC"
  - "embed third-party chat widget or Google Tag Manager in LWR site"
  - "connect Data Cloud to Experience Cloud for behavioral tracking"
  - "configure an external identity provider for community login"
  - "inject a global JavaScript library into an LWR Experience Cloud site"
  - "why is iFrame embedding blocked on my Experience Cloud site"
  - "set up Experience Cloud to act as both a service provider and an identity provider simultaneously"
inputs:
  - "Experience Cloud site type (LWR vs Aura vs Visualforce-based) and template"
  - "External system(s) to integrate — identity provider, analytics platform, chat vendor, CMS, or data platform"
  - "Authentication requirements: SAML 2.0, OAuth 2.0, OIDC, or a combination"
  - "Whether the site must also act as an IdP for downstream systems"
  - "Third-party script tags or widgets to inject (GTM, Drift, Intercom, etc.)"
  - "Data Cloud connection intent: behavioral events, identity resolution, or both"
  - "iFrame embedding requirements (who embeds the site, and in what context)"
outputs:
  - "Integration pattern decision record for each external system with mechanism and rationale"
  - "SSO configuration checklist (SAML metadata exchange steps, Auth Provider setup steps, or OIDC endpoint configuration)"
  - "Privileged Script Tag configuration specification for LWR widget injection"
  - "Data Cloud Web SDK connector configuration summary"
  - "iFrame embedding risk assessment and alternative recommendation"
  - "Security review checklist covering token handling, CORS, CSP, and session isolation"
dependencies:
  - lwc/experience-cloud-multi-idp-sso
  - architect/security-architecture-review
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Experience Cloud Integration Patterns

Use this skill when designing or reviewing integrations that connect an Experience Cloud site to systems outside Salesforce — identity providers for SSO, third-party widget vendors, external content sources, or behavioral data platforms like Data Cloud. This skill covers the integration mechanisms available at the site boundary: how external systems authenticate users, how external scripts enter the page safely, and how event data flows out.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Site template:** LWR (Lightning Web Runtime) and Aura sites have different mechanisms for script injection. LWR sites use Privileged Script Tag; Aura sites use a Custom Script component or head markup. Identify the template before recommending any approach.
- **Auth protocol capability:** Confirm whether the external IdP supports SAML 2.0, OIDC, or OAuth 2.0. Salesforce Experience Cloud supports all three per-site, but the setup path differs. If the IdP supports only one protocol, that narrows the choice immediately.
- **Multi-role requirement:** Determine whether the Experience Cloud org also needs to act as an IdP (issuing assertions to a third downstream system). A single org can be both SP and IdP simultaneously, but this is commonly overlooked in initial designs and causes rework.
- **iFrame origin:** If an external site needs to embed the Experience Cloud site in an iFrame, flag this immediately. Default X-Frame-Options: SAMEORIGIN headers block cross-origin iFrame embedding; there is no supported org-level toggle to relax this for all sites.
- **Data Cloud tenant:** Confirm whether the org has Data Cloud provisioned. The Web SDK connector is auto-created on first Data Cloud connect, but it requires explicit activation per site.

---

## Core Concepts

### SSO at the Experience Cloud Site Boundary

Experience Cloud sites support SSO using three protocols: SAML 2.0, OAuth 2.0, and OpenID Connect (OIDC). Configuration is per-site — each site has its own SAML service provider settings and can be associated with a different Auth Provider. When using SAML, Salesforce acts as the Service Provider (SP) and the external system acts as the Identity Provider (IdP). The site's SAML metadata (entity ID, ACS URL, SP certificate) must be exchanged with the external IdP. The entity ID is site-specific and takes the form `https://<site-domain>/saml/metadata`, not the org-level entity ID.

For OIDC and OAuth 2.0, the Auth Provider framework is used. An Auth Provider record maps the external IdP's authorization endpoint, token endpoint, and user info endpoint to a Salesforce registration handler Apex class. The registration handler controls what happens when a new user authenticates for the first time — it can create a new user, match to an existing user by email, or throw an error.

The same org can simultaneously act as an IdP for other downstream systems using the Identity Provider feature (setup at org level, not site level). This means a single Salesforce org can accept SAML assertions from an external IdP for site login while also issuing SAML assertions to a separate downstream system. These two roles are independent and do not conflict, but they are configured in different areas of Setup.

### Privileged Script Tag for Third-Party Widget Injection in LWR

LWR sites enforce a strict Content Security Policy (CSP) that blocks inline scripts and arbitrary external script sources by default. The sanctioned mechanism for injecting global JavaScript libraries — Google Tag Manager containers, chat widgets (Intercom, Drift, Zendesk), analytics scripts (Segment, Heap) — into LWR sites is the **Privileged Script Tag** feature.

Privileged Script Tag is configured per-site in Experience Builder under Settings > Security > Privileged Script Tags. Each entry specifies a script source URL and an optional nonce policy. The feature whitelists the script source in the site's CSP header and renders the tag in the `<head>` of every page in that site.

This is a site-level setting, not an org-level setting. A script tag added to Site A is not active on Site B. This is by design — different portals may have different widget needs and different CSP requirements. Administrators who attempt to inject scripts via custom LWC components (using `lwc:ref` to manipulate the DOM or using `@api` to pass raw HTML) will find their scripts either blocked by CSP or stripped by the LWR renderer.

The Privileged Script Tag mechanism does not apply to Aura-based sites. On Aura sites, global head markup or custom JavaScript files attached to the site's static resources are used instead.

### Data Cloud Integration via Web SDK

When an org with Data Cloud connects an Experience Cloud site to Data Cloud, Salesforce automatically creates a Web SDK data source connector. This connector enables the site to emit behavioral events (page views, clicks, form interactions) and identity signals (email hashing, known-user binding) to Data Cloud via a JavaScript SDK that the platform injects into the site.

The Web SDK connector is activated through the Data Cloud setup wizard, not through Experience Builder. Once connected, the SDK script tag appears automatically on the site without requiring a Privileged Script Tag entry — the platform handles the injection. The SDK captures engagement events and routes them to the Data Cloud event stream, where they can be unified against profile records.

The auto-created connector is org-scoped but requires per-site activation. A common mistake is connecting Data Cloud at the org level and assuming all sites are automatically instrumented. Each site must be individually enabled in Data Cloud's site configuration.

---

## Common Patterns

### SAML 2.0 SSO for Customer or Partner Portal Login

**When to use:** An enterprise needs employees, partners, or customers to log into an Experience Cloud site using credentials managed by an external corporate IdP (Okta, Azure AD, PingFederate, ADFS).

**How it works:**
1. Navigate to Setup > Identity > SAML Single Sign-On Settings and create a new SAML SSO configuration. Provide the external IdP's metadata XML (entity ID, SSO URL, certificate).
2. In the Experience Cloud site's Administration > Login & Registration settings, enable the SAML SSO configuration for that site.
3. Export the site's SP metadata from the SAML configuration record and provide it to the external IdP administrator. Key fields: Salesforce entity ID, ACS URL, certificate.
4. Configure the Salesforce user profile or permission set that newly SSO-authenticated users receive. The Auth Provider registration handler (for OIDC/OAuth) or the SAML user provisioning setting (for SAML) controls this mapping.
5. Test with an incognito session to confirm the redirect chain: site login page → IdP → SAML assertion POST to ACS URL → Salesforce session → site home.
6. If the site must also issue SAML assertions to a downstream system, enable Setup > Identity > Identity Provider (org level) separately. This does not interfere with the inbound SAML configuration.

**Why not the alternative:** Asking users to maintain a separate Salesforce username and password for the portal forces IT to manage two credential stores. SSO allows the enterprise IdP to remain the single system of record for authentication, simplifying onboarding, offboarding, and MFA enforcement.

### Privileged Script Tag for GTM or Chat Widget Injection in LWR Sites

**When to use:** A marketing or customer success team needs Google Tag Manager, a chat widget (Intercom, Drift, Zendesk), or an analytics library (Segment) loaded on every page of an LWR Experience Cloud site.

**How it works:**
1. In Experience Builder, open Settings > Security for the target LWR site.
2. Navigate to the Privileged Script Tags section and click Add.
3. Paste the full script source URL (e.g., `https://www.googletagmanager.com/gtm.js?id=GTM-XXXXXX`). For GTM, also add the noscript fallback if required by the GTM container configuration.
4. Save and publish the site. The platform adds the script URL to the site's CSP `script-src` directive and renders the `<script>` tag in the `<head>` of all pages in that site.
5. For GTM: place the `dataLayer` push configuration in a custom LWC component that fires on page load events. The LWC component is safe to use for `dataLayer` pushes; it cannot inject raw `<script>` tags but does not need to for GTM.
6. Verify using browser DevTools: check the Network panel for the GTM script request and the Application panel for cookies or events the container fires.

**Why not the alternative:** Developers sometimes attempt to inject script tags by placing raw HTML in a custom LWC component's template or by using `eval()`-style workarounds. LWR's renderer strips unrecognized HTML in component templates, and CSP blocks inline scripts. The Privileged Script Tag is the only officially supported, CSP-compliant injection path for LWR sites.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| External IdP supports SAML 2.0, site is the portal login | SAML SSO configuration + site login page setting | Direct SP/IdP SAML exchange; no Apex required |
| External IdP supports OIDC or OAuth 2.0 | Auth Provider + registration handler Apex class | Auth Provider framework handles token exchange; registration handler controls user provisioning |
| Org must act as IdP for a downstream application | Setup > Identity Provider (org level) + Connected App | IdP role is org-level, not site-level; separate from inbound SSO config |
| Inject GTM or chat widget into LWR site | Privileged Script Tag per site | Only CSP-compliant injection path in LWR; org-level settings do not exist |
| Inject script into Aura-based site | Custom head markup or static resource JS | Privileged Script Tag is LWR-only; Aura uses a different mechanism |
| Capture behavioral events and send to Data Cloud | Data Cloud Web SDK via Data Cloud setup wizard | Platform injects SDK automatically on connect; no manual Privileged Script Tag needed |
| External party wants to embed the site in an iFrame | Evaluate alternatives (redirect, widget API) | X-Frame-Options: SAMEORIGIN is set by default; cross-origin iFrame embedding is blocked without a Salesforce Support case for specific trusted domains |
| Site needs to render CMS content from external source | CMS Connect (for Aura) or Headless CMS with Wire Adapter/External Service | CMS Connect is Aura-only; LWR sites use headless pattern with external data via Wire Adapters or External Services |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner designing an Experience Cloud external integration:

1. **Classify each integration by type** — Categorize every external system involved as one of: (a) identity provider for SSO, (b) third-party script or widget, (c) behavioral/analytics data consumer, (d) external content source, or (e) embedded host (iFrame). Each type has a distinct mechanism and risk profile.
2. **Confirm site template and per-site scope** — Identify whether each site is LWR, Aura, or Visualforce-based. Confirm that each integration is configured at the site level, not the org level. Privileged Script Tag, SAML site enablement, and Data Cloud site activation are all per-site.
3. **Design the SSO flow** — For each identity integration, determine the protocol (SAML 2.0, OIDC, or OAuth 2.0), whether Salesforce is purely SP or also acts as IdP, and what user provisioning logic is needed (just-in-time provisioning vs. pre-provisioned users). Draft the SAML metadata exchange or OIDC endpoint configuration before touching Setup.
4. **Inventory scripts and CSP requirements** — List every third-party script that must load on the site. For each, confirm the source URL, whether a nonce is required, and which pages it should appear on. For LWR, map each to a Privileged Script Tag entry. For Aura, map each to head markup or static resource.
5. **Configure and test authentication integration** — Configure SAML SSO or Auth Provider settings. Test with an incognito browser session. Verify that the redirect chain completes correctly, that users land on the correct page post-login, and that JIT provisioning (if used) creates the user with the correct profile and license.
6. **Validate script injection and CSP compliance** — Publish the site after adding Privileged Script Tags. Use browser DevTools to confirm scripts load without CSP violations. Check the console for blocked resource errors.
7. **Review security posture** — Complete the security review checklist: token storage (no tokens in localStorage for public sites), CORS policy on external endpoints called by site pages, CSP `connect-src` for any XHR/fetch calls to external APIs, and session isolation between authenticated and guest user sessions.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Each external system is categorized (SSO, widget, analytics, content, iFrame host) and the correct platform mechanism is used for that category
- [ ] SAML or OIDC SSO is configured at the site level, not just the org level — verify the site's Login & Registration settings include the SSO provider
- [ ] If the org acts as both SP and IdP, the two roles are confirmed as independently configured and non-conflicting
- [ ] Privileged Script Tag entries are site-specific — confirm no assumption that an org-level setting exists
- [ ] Data Cloud Web SDK activation is done per-site in Data Cloud setup, not assumed to be automatic
- [ ] iFrame embedding requirement is flagged and assessed against X-Frame-Options default behavior; alternatives are documented if embedding is required
- [ ] CSP `script-src` includes all third-party script origins via Privileged Script Tag or equivalent Aura mechanism
- [ ] Auth Provider registration handler (for OIDC/OAuth) handles both new-user and existing-user cases without throwing unhandled exceptions
- [ ] Security review covers: no sensitive tokens in browser storage, CORS policy on external APIs, session isolation for guest vs. authenticated users

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **SAML entity ID is site-specific, not org-level** — The SAML SP entity ID for an Experience Cloud site is the site's domain-qualified URL, not the org's entity ID. Providing the org-level entity ID to an external IdP results in assertion validation failures. Always export the SP metadata from the site's SAML configuration, not from the org-level SAML settings.
2. **iFrame embedding is blocked by default via X-Frame-Options** — Salesforce sets `X-Frame-Options: SAMEORIGIN` on Experience Cloud site responses. There is no toggle in Setup or Experience Builder to change this for cross-origin iFrame use. Embedding requires a Salesforce Support case to allowlist specific trusted origins. Architectures that plan on iFrame embedding without this step will fail in production.
3. **Privileged Script Tag is per-LWR-site, not org-wide** — Adding a script tag to one LWR site does not activate it on any other site in the same org. Organizations with multiple portals must configure Privileged Script Tag entries independently for each site. Teams that manage multiple sites frequently miss this when rolling out a new analytics tool.
4. **Data Cloud Web SDK connector is auto-created but not auto-activated per site** — When Data Cloud is connected at the org level, a Web SDK connector is created automatically. However, each Experience Cloud site must be individually activated in the Data Cloud site configuration. Sites that are not explicitly activated do not emit behavioral events regardless of the org-level connection status.
5. **The org can be SP and IdP simultaneously without conflict** — Many practitioners believe configuring Salesforce as an IdP (to issue assertions to a downstream app) will interfere with inbound SAML SSO on Experience Cloud sites. These are independent features configured in different Setup areas. Running both concurrently is fully supported and common in enterprise deployments.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration pattern decision record | Per-system table mapping each external system to its integration mechanism, protocol, and configuration location |
| SSO configuration checklist | Step-by-step SAML metadata exchange or OIDC endpoint configuration for each identity provider |
| Privileged Script Tag inventory | List of all third-party scripts, their source URLs, and the sites they are configured on |
| CSP compliance matrix | Mapping of each external script/API origin to the CSP directive that must include it |
| Data Cloud site activation checklist | List of sites with Data Cloud enabled vs. pending activation |
| iFrame embedding risk assessment | Documented risk and recommended alternative if cross-origin iFrame embedding is required |
| Security review findings | Checklist output covering token handling, CORS, CSP, and session isolation |

---

## Related Skills

- lwc/experience-cloud-multi-idp-sso — Use when multiple identity providers must appear on a single Experience Cloud site login page; this skill covers the routing and selection UX, not covered here
- architect/security-architecture-review — Use for broader org-level security architecture review that includes Experience Cloud as one component
- architect/integration-framework-design — Use when the Experience Cloud integration requires a reusable Apex callout framework for outbound API calls from site components

---

## Official Sources Used

- Salesforce Help — SAML for Experience Cloud Sites — https://help.salesforce.com/s/articleView?id=sf.sso_saml_setting_up.htm
- Salesforce Help — Configure an Authentication Provider — https://help.salesforce.com/s/articleView?id=sf.sso_authentication_providers.htm
- Salesforce Developer — Privileged Script Tag in LWR Sites — https://developer.salesforce.com/docs/platform/lwc/guide/create-lwr-privileged-script.html
- Salesforce Help — Connect Experience Cloud to Data Cloud — https://help.salesforce.com/s/articleView?id=sf.c360_a_experience_cloud_site_setup.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
