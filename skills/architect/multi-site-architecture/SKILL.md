---
name: multi-site-architecture
description: "Use when designing a strategy for multiple Experience Cloud sites within one Salesforce org, selecting a domain and URL pattern, planning shared LWC component libraries, designing cross-site navigation, managing the org's 100-site quota, or deciding between multi-site vs multi-org for portal needs. Trigger phrases: 'multiple Experience Cloud sites architecture', 'multi-portal strategy Salesforce', 'cross-site navigation Experience Cloud', 'domain strategy community portals', 'shared components across sites', 'how many Experience Cloud sites can I have', 'customer and partner portal same org', 'regional sub-portals Salesforce'. NOT for single Experience Cloud site setup (use admin/experience-cloud-site-setup). NOT for Experience Cloud page layout or component development in isolation. NOT for multi-org strategy (use architect/multi-org-strategy)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Scalability
  - Operational Excellence
tags:
  - experience-cloud
  - multi-site
  - domain-strategy
  - community-portals
  - cross-site-navigation
  - lwc-reuse
  - cdn
  - site-quota
  - digital-experience
  - architecture-decision
triggers:
  - "multiple Experience Cloud sites architecture for customer partner and employee portals"
  - "multi-portal strategy Salesforce — how do we structure several community sites in one org"
  - "cross-site navigation Experience Cloud — linking between a customer portal and a partner portal"
  - "domain strategy for community portals — custom domains vs default my.site.com URLs"
  - "shared LWC components across multiple Experience Cloud sites"
  - "how many Experience Cloud sites can my org have — we're approaching the limit"
  - "should we use separate orgs or one org with multiple sites for different audiences"
inputs:
  - "Number and types of intended audiences (customers, partners, employees, public)"
  - "Current active, preview, and inactive site count in the org"
  - "Org edition (Essential, Professional, Enterprise, Unlimited, Developer)"
  - "Custom domain requirements — whether branded URLs are required vs default my.site.com"
  - "Whether sites need to share user records, data, or component libraries"
  - "CDN and performance requirements per audience segment"
  - "License types purchased (Customer Community, Partner Community, Employee Community, etc.)"
outputs:
  - "Multi-site topology recommendation: how many sites, grouped by audience, with naming and domain conventions"
  - "Domain strategy: custom domain vs default my.site.com, environment-specific rules"
  - "Shared component library design: which LWC components to build once and deploy across sites"
  - "Cross-site navigation pattern: explicit web links, URL conventions, authenticated vs guest hand-off"
  - "Site quota management plan: which sites count against the 100-site org limit and how to track usage"
  - "License allocation map: which license types are required per site audience"
  - "Multi-site vs multi-org recommendation with explicit reasoning"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

Use this skill when designing or reviewing a strategy for deploying multiple Experience Cloud sites within a single Salesforce org. It covers quota management, domain configuration, shared component architecture, cross-site navigation patterns, license planning, and the decision between multi-site and multi-org. It does not cover single-site setup, deep component development, or unrelated multi-org architecture.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Current site inventory:** Run `Setup > Digital Experiences > All Sites` and count active, preview, and inactive sites. All three statuses count toward the 100-site org limit.
- **Org edition:** Custom domain configuration on Experience Cloud requires Enterprise edition or higher. Professional edition orgs are limited to the default `MyDomainName.my.site.com` URL pattern.
- **License types purchased:** Experience Cloud licensing is per user and per site type (Customer Community, Partner Community, Employee Apps, etc.). A user with a Customer Community license cannot access a Partner Community site.
- **Is this actually a multi-org question?** If the requirement is data residency, regulatory isolation, or M&A integration, use `architect/multi-org-strategy` instead. Multi-site within one org assumes a shared data model.

---

## Core Concepts

### The 100-Site Org Limit

Every Salesforce org supports a maximum of 100 Experience Cloud sites. This limit is cumulative across all site statuses:

- **Active sites** (published and accessible to users) count toward the limit.
- **Preview sites** (published to admins only, not yet public) count toward the limit.
- **Inactive sites** (deactivated but not deleted) count toward the limit.

A site is only removed from the quota count when it is permanently **deleted**, not when it is deactivated. Orgs that have used the site builder repeatedly — including demos, proofs of concept, and abandoned prototypes — can accumulate inactive sites that silently consume quota.

Practical implication: treat the 100-site limit as a capacity constraint that must be actively monitored. Build a site inventory process. Delete obsolete sites rather than deactivating them indefinitely.

### Domain Strategy and Custom Domains

Every Experience Cloud site has a URL. The structure differs depending on whether a custom domain has been configured.

**Default URL pattern (all editions):**
`https://MyDomainName.my.site.com/SiteName`

- `MyDomainName` is the org's My Domain name.
- `SiteName` is the site-specific path segment, set at site creation.
- This pattern is available in all editions and requires no additional setup.

**Custom domain pattern (Enterprise+ only):**
`https://portal.company.com/SiteName` or `https://portal.company.com/`

- Configured via `Setup > Custom URLs` in the production org.
- Custom domains require a valid SSL certificate and DNS CNAME configuration pointing to the Salesforce CDN endpoint.
- **Custom domain configuration must be done in production.** Sandbox orgs use the default `*.sandbox.my.site.com` URL pattern and do not support custom domain configuration.
- Custom domains are applied at the org level; individual site paths remain configurable.

**CDN:**
Experience Builder sites automatically receive CDN caching starting in Winter '19. This applies to Lightning-based Experience Builder sites on custom domains. The CDN caches static assets and page content at edge nodes. No manual CDN configuration is required.

### Shared Component Architecture

Experience Cloud sites are separate deployments but they run in the same org and can consume the same Salesforce metadata — including LWC components, Apex classes, permission sets, and custom objects.

**What can be shared across sites:**
- LWC components deployed to the org are available in Experience Builder for any site (if the component is declared `isExposed: true` in the component's `.js-meta.xml`).
- Apex classes backing shared components are shared automatically — they are org-scoped.
- Custom objects, fields, and relationships are shared across all sites in the org.
- Flows built with `Run in System Context` can be reused across sites.

**What is site-specific:**
- Experience Builder theme, layout, and navigation are per-site.
- Guest user profile is per-site. Guest user permissions must be configured independently for each site.
- Site-level security settings (clickjack protection, CSP, HTTPS enforcement) are per-site.
- CDN cache settings and custom domain binding are per-site.

**Theme layouts** are the primary reuse mechanism within a single site — they allow consistent header/footer/navigation across pages of that site. They do not natively span multiple sites. Shared navigation across sites requires explicit linking.

### Cross-Site Navigation

There is no native Salesforce feature for automatic cross-portal navigation or session hand-off between Experience Cloud sites. When a user navigates from one site to another:

- They are leaving one site's URL context and entering another's.
- Authenticated sessions are not automatically transferred. A user authenticated in Site A will need to authenticate separately in Site B unless SSO is configured.
- Navigation is implemented using explicit hyperlinks (web links, rich text components, or custom LWC navigation) pointing to the target site's URL.

For orgs using a single IdP for SSO, a user can navigate between sites without re-entering credentials if both sites are configured as Service Providers registered with the same IdP. The user will receive a new SAML assertion for the destination site transparently if the IdP already has an active session.

Without SSO, cross-site navigation drops the user to the target site's login page. Design navigation UI and user journeys to account for this boundary.

---

## Common Patterns

### Pattern 1: Audience-Segmented Site Topology

**When to use:** The org needs separate portals for distinct audience types — for example, a customer self-service portal, a partner deal registration portal, and an employee benefits portal — each requiring different branding, navigation, and access controls.

**How it works:**
- Create one site per audience type. Each site has its own theme, navigation, and guest/authenticated user profile.
- All sites share the same underlying Salesforce data model, custom objects, and LWC component library.
- Build reusable LWC components with audience-neutral logic and configure the experience (labels, links, display rules) via component properties or custom metadata per site.
- Assign users the license type that matches the site audience: Customer Community Plus for customer sites, Partner Community for partner sites.
- Apply separate sharing rules and permission sets per audience to control record visibility — the data model is shared but access is governed per site.

**Why not the alternative:** Trying to serve multiple audiences in a single site using conditional rendering and permission-based page variants is technically possible but produces unmanageable complexity. Separate sites allow distinct guest profiles, clean URL branding, and independent release cadences.

### Pattern 2: Regional Sub-Portal with Shared Component Library

**When to use:** A global org needs multiple regional sites (EMEA, APAC, AMER) that share branding standards and component logic but require regional customization of language, content, and compliance copy.

**How it works:**
1. Build a shared LWC component library targeted for Experience Cloud (`isExposed: true`).
2. Use component properties (`@api` decorated attributes) to externalize configurable content — labels, links, legal disclaimers — so Experience Builder admins can configure each site without code changes.
3. For translated content, enable Translation Workbench and use the Language Switcher component within each site. The component library does not need to duplicate content per region.
4. Assign unique `SiteName` path segments per region (e.g., `/emea`, `/apac`, `/amer`) under the same custom domain base URL, or use separate CNAME subdomains per region.
5. Maintain a single deployment pipeline that pushes shared LWC components to all sites simultaneously via a Salesforce DX project structure.

**Why not the alternative:** Forking separate LWC code per site produces drift and doubles (or triples) maintenance overhead. Component property externalization is the correct abstraction point.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Two audiences (customers and partners) in the same org | Two separate Experience Cloud sites, one per audience type | Clean URL separation, distinct guest profiles, independent release cadence |
| Multiple regional variants of the same site | One site per region with shared LWC components and Translation Workbench | Avoid code duplication; externalize regional content via component properties |
| Org approaching 100-site limit | Audit and delete inactive/unused sites; assess whether preview sites can be merged | Inactive and preview sites consume quota; deletion is the only way to reclaim it |
| Custom-branded URL required (e.g., portal.company.com) | Enterprise+ org; configure custom domain in production only | Custom domain config is not available in sandbox; requires Enterprise edition |
| Cross-site navigation needed | Explicit hyperlinks between site URLs; SSO via external IdP for seamless auth | No native cross-portal session sharing; SSO is the only transparent auth hand-off |
| Requirement appears to need multiple orgs for portal isolation | Stay in single org with multiple sites unless data residency or regulatory isolation is required | Multi-org for portal isolation introduces cross-org sync complexity with no benefit |
| Sandbox testing with custom domain | Use default `.sandbox.my.site.com` URL in sandbox; custom domain testing only in production scratch orgs or UAT using default URL | Custom domains cannot be configured in sandbox |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Inventory the current org.** Count active, preview, and inactive sites in `Setup > Digital Experiences > All Sites`. Confirm the org edition. Determine how many of the 100-site quota remain. Identify any obsolete or prototype sites that should be deleted before the project begins.
2. **Define audience segments and site boundaries.** For each distinct audience (customers, partners, employees, public), determine whether a separate site is required or whether a single site with permission-based access can serve the need. Document the site topology with audience, license type, URL pattern, and guest vs authenticated access model.
3. **Design the domain strategy.** Decide between default `my.site.com` URLs and custom domains. If custom domains are required, confirm Enterprise+ edition and note that configuration happens in production only. Define the URL path segment naming convention for all planned sites.
4. **Design the shared component library.** Identify which LWC components will be reused across sites. Ensure components use `@api` properties to externalize configurable content. Confirm `isExposed: true` in each component's `.js-meta.xml`. Review guest user profile permissions per site — shared components must handle the widest permission set safely.
5. **Design cross-site navigation and user journeys.** For each user journey that crosses site boundaries, document the source URL, target URL, and authentication state at the boundary. Determine whether SSO via an external IdP is in scope. If not, design the UX to surface the login context clearly when the user arrives at the destination site.
6. **Validate and document.** Run through the Review Checklist below. Record the site topology, domain strategy, and component architecture in the project's architecture decision record. Confirm the license allocation is consistent with the site audience types.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Site inventory completed: active + preview + inactive count is below 100. Unused sites are deleted, not just deactivated.
- [ ] Org edition confirmed: if custom domains are required, org is Enterprise edition or higher.
- [ ] Custom domain configuration is documented as production-only. Sandbox testing uses default `.sandbox.my.site.com` URL.
- [ ] Each site has a documented audience type with the corresponding license type (Customer Community, Partner Community, Employee Community, etc.).
- [ ] Guest user profile for each site is configured independently and follows the least-privilege principle.
- [ ] Shared LWC components are marked `isExposed: true` and use `@api` properties for per-site customization. No hard-coded site-specific content in shared component logic.
- [ ] Cross-site navigation is implemented as explicit hyperlinks. The behavior when an unauthenticated user follows a cross-site link is documented and user-tested.
- [ ] If SSO is used for transparent cross-site auth, each site is registered as a separate Service Provider in the IdP.
- [ ] Site-level security settings (CSP, HTTPS enforcement, clickjack protection) are reviewed and configured for each site individually.
- [ ] CDN enablement is confirmed for Experience Builder sites (automatic post-Winter '19; no manual steps required).

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Preview sites consume the 100-site quota.** Teams routinely create preview versions of upcoming site refreshes, accumulate them across multiple projects, and then discover the org is approaching 100 sites. A preview site that is never published and never deleted still counts. Establish a practice of deleting preview sites when the associated project is closed.

2. **Deactivating a site does not free the quota.** An inactive (deactivated) site still counts toward the 100-site limit. The only way to reclaim that slot is to delete the site permanently. Orgs that have been running Experience Cloud since the Community Cloud era frequently have double-digit counts of inactive sites that silently consume quota.

3. **Custom domain configuration cannot be done in sandbox.** Teams that try to configure custom domains (Setup > Custom URLs) in a sandbox org will find the option either missing or non-functional. Custom domain configuration must be performed in the production org. Sandbox sites use the default `.sandbox.my.site.com` URL pattern. Plan UAT and pre-production testing around this constraint.

4. **Cross-site navigation does not transfer the authenticated session.** There is no native Salesforce capability that allows a user authenticated in one Experience Cloud site to follow a link and arrive authenticated in another site. Without SSO configured against an external IdP, the user arrives at the destination site's login page. User journeys that cross site boundaries must account for this re-authentication step.

5. **Guest user profiles are per-site and are not inherited from a shared profile.** A common mistake is assuming that a permission granted to one site's guest user profile applies to all sites, or that there is a single guest profile to manage. Each site has its own guest user record and guest user profile. Shared LWC components that rely on guest access must be tested against each site's guest profile independently.

6. **License types are not interchangeable across site audiences.** A user with a Customer Community license cannot access a Partner Community site. A user with a Partner Community license can access a Customer Community site but consumes a Partner Community license to do so. Mixing license types across audiences in a single site is not the intended design and creates license audit risk.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Multi-site topology diagram | Visual or tabular map of all planned sites with audience type, URL, license type, and data access scope |
| Domain strategy document | Defines custom vs default URL pattern per site, environment-specific rules (prod vs sandbox), and DNS/SSL requirements |
| Shared component inventory | List of LWC components targeted for multi-site reuse with `@api` property definitions and per-site configuration notes |
| Cross-site navigation map | User journeys that cross site boundaries with source URL, target URL, auth state, and SSO dependency |
| Site quota tracker | Running count of active + preview + inactive sites with owner, purpose, and planned deletion date for obsolete sites |
| License allocation plan | License type per site audience with user count estimate and cost implications |

---

## Related Skills

- `architect/multi-org-strategy` — use when data residency, regulatory isolation, or M&A requirements make single-org untenable; this is the escalation path when multi-site within one org is insufficient
- `architect/experience-cloud-licensing-model` — use for detailed Experience Cloud license selection, permission set licenses, and usage allocation
- `admin/experience-cloud-site-setup` — use for setting up a single Experience Cloud site from scratch (this skill covers multi-site strategy, not initial site provisioning)
- `flow/flow-for-experience-cloud` — use when designing flows that run in the context of Experience Cloud sites, including guest-user flow behavior
- `admin/multi-language-and-translation` — use when regional multi-site deployments require translation and localization
