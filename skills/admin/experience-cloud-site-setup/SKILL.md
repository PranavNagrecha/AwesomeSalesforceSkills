---
name: experience-cloud-site-setup
description: "Use when creating a new Experience Cloud site: selecting LWR vs Aura template, configuring branding and navigation, setting up a custom domain, and using Experience Builder. Trigger keywords: create new Experience Cloud site, LWR vs Aura template, set up community portal domain, Experience Builder page builder, branding sets, navigation menu configuration, Microsite LWR, Build Your Own LWR. NOT for coding LWR themes or custom components — use lwc/lwr-site-development. NOT for deploying a finished site to another org — use devops/experience-cloud-deployment-admin. Also covers the deployable metadata: Network, CustomSite, NavigationMenu, ExperienceBundle, DigitalExperienceBundle, urlPathPrefix, networkMemberGroups, emailSenderAddress, site status Live vs UnderConstruction."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
tags:
  - experience-cloud
  - lwr
  - aura
  - site-builder
  - community
  - branding
  - custom-domain
  - network-metadata
  - navigation-menu
inputs:
  - Target audience for the site (customers, partners, employees)
  - Required component types (LWC-only vs mixed Aura/LWC)
  - Custom domain name and My Domain configuration
  - Branding assets (logo, colors, fonts)
  - Edition confirmation (Enterprise, Performance, Unlimited, or Developer)
outputs:
  - Published Experience Cloud site with correct template
  - Configured custom domain on MyDomainName.my.site.com pattern
  - Branded site with --dxp CSS styling hooks or branding sets applied
  - Navigation menus and page structure defined in Experience Builder
triggers:
  - "create a new Experience Cloud site"
  - "LWR vs Aura template selection for community portal"
  - "set up custom domain for Experience Cloud site"
  - "configure branding and navigation in Experience Builder"
  - "Build Your Own LWR site template"
  - "experience cloud site changes not showing up after deploy"
  - "network metadata deploy fails on a missing required field"
  - "change the url path prefix on an existing community site"
  - "portal members disappeared after switching to permission sets"
  - "deploy an Experience Cloud site with sf project deploy"
  - "publish an Experience Cloud site from UnderConstruction to Live"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Experience Cloud Site Setup

Use this skill when a practitioner needs to create a new Experience Cloud site from scratch: selecting the right template (LWR vs Aura), configuring branding and navigation menus, setting up a custom domain, and using Experience Builder to manage the page structure. This skill covers the site creation and initial configuration lifecycle — not ongoing content authoring or Flow orchestration inside an established site.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Edition requirement:** Experience Cloud site creation requires Enterprise, Performance, Unlimited, or Developer edition. Confirm the org edition before proceeding.
- **Template choice is permanent:** Once a site is created with a specific template, the template cannot be changed. Changing the template requires recreating the site from scratch. This is the most consequential pre-creation decision.
- **Component library constraint:** LWR-based templates (Build Your Own LWR, Microsite LWR) support Lightning Web Components only. The legacy Aura-based Build Your Own template supports both Aura and LWC but lacks the performance optimizations LWR provides. Confirm which components are already built or planned before choosing a template.
- **My Domain requirement:** A custom branded domain on the pattern `MyDomainName.my.site.com` requires My Domain to be configured and deployed in the org. Verify this is in place before custom domain setup.
- **LWR publish model:** LWR sites freeze component trees at publish time, enabling HTTP caching. Edits require an explicit republish to go live. Practitioners accustomed to Aura sites often miss this.

---

## Questions to Ask Before Configuring

Ask these before creating anything in Setup. Each one traces to a behaviour that is
either irreversible or fails silently, and every row maps to a gotcha in
`references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which components does this site have to render — name them, and say LWC or Aura for each?" | Template family is fixed at creation and the LWR component picker offers LWC only | The component inventory that decides LWR vs Aura before anything is created (Gotchas 1, 3) |
| "What sender address will portal emails come from, and is it already verified in this org?" | `emailSenderAddress` can only be supplied on the deploy that creates the site; later Metadata API updates are ignored with no error | A verified address on day one instead of an unfixable one on day thirty (Gotcha 6) |
| "Is this site enhanced LWR created in Winter '23 or later, or something older?" | It decides whether the content bundle is `DigitalExperienceBundle` or `ExperienceBundle` — and enhanced LWR cannot be packaged | The right retrieve manifest, and an early answer on whether packaging is even available (Gotcha 8) |
| "Who becomes a member, by profile or by permission set, and on which community licence?" | `networkMemberGroups` confers membership, never a licence, and the permission-set path skips Chatter customers | The membership shape plus the licence decision, taken with `admin/portal-requirements-gathering` (Gotcha 11) |
| "Can anyone self-register, and if so onto which profile — and what stops duplicate Contacts?" | `selfRegistration` is one site-wide boolean; `selfRegProfile` is not required by the deploy but is required by reality | A named profile and a matching/duplicate rule pair, not a switch left on (Gotcha 12) |
| "What is the URL path prefix, and who else already links to it?" | The prefix lives in three places (`Network`, the content bundle, `CustomSite`) that must agree, and every email template embeds it | One prefix agreed once, and the list of links a later rename would break (Gotcha 10) |
| "Does this site ever need to come back offline after go-live?" | `UnderConstruction` is a one-way door; `DownForMaintenance` is the only route back | A documented offline procedure rather than a status value that quietly does nothing (Gotcha 7) |

What a proper configuration adds over just clicking through New Site: the template matches
the components that actually exist, the site's settings are in source as `Network` +
`CustomSite` + `NavigationMenu` rather than trapped in Setup, the email sender is right on
the only deploy that can set it, and publishing is a deliberate status change you can prove
with SOQL instead of a screenshot.

---

## Core Concepts

### LWR vs Aura Template Selection

Experience Cloud offers two primary template families. The choice is permanent post-creation.

**LWR templates (Build Your Own LWR, Microsite LWR):**
- Built on Lightning Web Runtime. Support LWC components exclusively — Aura components cannot be added.
- Pages are frozen at publish time. This enables HTTP caching of the full rendered page, giving superior performance at scale.
- Support clean URL paths (e.g., `/products`, `/account`) without the `/s` prefix that Aura sites require.
- Branding is controlled through `--dxp-*` CSS custom properties (styling hooks) and branding sets.
- Microsite LWR is optimized for small, focused public-facing sites (marketing landing pages, microsites). Build Your Own LWR is the general-purpose LWR template.

**Legacy Aura template (Build Your Own):**
- Supports both Aura and LWC components in the same site.
- Does not use publish-time freezing; changes become visible more dynamically.
- URL paths require the `/s` prefix (e.g., `/s/products`).
- Branding through Experience Builder theme panel rather than CSS custom properties.
- Use this template only when Aura components that cannot be migrated are required.

**Partner Central and Customer Account Portal templates:**
- Pre-configured Aura-based templates for specific use cases. Include standard navigation, record detail pages, and case deflection patterns out of the box.
- Faster to stand up for standard partner/customer workflows but less flexible for custom branding.

### Custom Domain Configuration

Experience Cloud sites are accessed via a URL on the pattern `MyDomainName.my.site.com/site-path`. The subdomain is set by My Domain in org settings. The site path is `urlPathPrefix` — the first part of the path that distinguishes this site from other sites (Metadata API Guide, `Network`, api_meta.txt L91084–L91089). The platform does allow it to change: `Network.UrlPathPrefix` carries the `Update` property (Object Reference, `Network`, object_reference.txt L187375–L187378). Treat it as fixed anyway — the same prefix is duplicated in the content bundle and the `CustomSite`, and all three must move together (`references/gotchas.md`, Gotcha 10).

For LWR sites, clean URL paths work without the `/s` prefix. Aura sites append `/s` to all page paths automatically. This distinction matters when sharing deep links or setting up redirects.

### Experience Builder and Branding

Experience Builder is the drag-and-drop page editor for Experience Cloud. It manages pages, navigation menus, site settings, and branding. For LWR sites:

- **Branding sets** define tokens (colors, typography, spacing) applied site-wide.
- **`--dxp-*` CSS custom properties** are the styling hooks used in LWR themes. Component CSS should consume these tokens rather than hardcoded values, so branding changes propagate across the entire site.
- Navigation menus are configured in Experience Builder under the Navigation section and support nested items, labels, and access-controlled items (visible only to logged-in users or specific profiles).

### The Metadata Behind a Site

A site that only exists in Setup cannot be reviewed, diffed or promoted. Four types
carry it, and they are separate files in separate directories:

| Type | Directory | Holds |
|---|---|---|
| `Network` | `networks/` | Site settings: status, members, email senders and templates, self-registration, `urlPathPrefix` |
| `CustomSite` | `sites/` | The container: `active`, `indexPage`, `clickjackProtectionLevel`, `siteAdmin`, `siteType` `ChatterNetwork` |
| `NavigationMenu` | `navigationMenus/` | Menu items — replaced the `navigationLinkSet` subtype on `Network` in API 47.0 (api_meta.txt L90951–L90954) |
| `ExperienceBundle` **or** `DigitalExperienceBundle` | `experiences/` **or** `digitalExperiences/site/` | Pages, routes, themes, branding sets — one type or the other, never both |

`Network.site` is a Required reference to the `CustomSite` (api_meta.txt L91045), so the
two always ship together. Which bundle type applies is not a preference: enhanced LWR
sites created in Winter '23 or later use `DigitalExperienceBundle`; Aura sites and other
LWR sites use `ExperienceBundle` (api_meta.txt L51234–L51236). Full deployable XML,
`package.xml`, retrieve/deploy commands and verification SOQL are in
`references/metadata-examples.md`.

### Publish Model and Cache Implications

LWR sites use a publish-time freeze model. When you publish:
1. Component trees are resolved and frozen.
2. Pages are cached via HTTP caching at the CDN layer.
3. Visitors receive the cached version until the next publish.

Any change to a page, component, or branding requires an explicit republish. Forgetting to republish is the most common reason practitioners report that changes "did not go live."

---

## Common Patterns

### Pattern: New Customer Portal with LWR Template

**When to use:** Building a net-new self-service customer portal where all components are LWC-based or will be built as LWC. Performance at scale is a priority.

**How it works:**
1. In Setup, navigate to Digital Experiences > All Sites > New.
2. Select Build Your Own (LWR) template.
3. Name the site and set the URL path (e.g., `portal`). The full URL becomes `MyDomainName.my.site.com/portal`.
4. Once the site is created, open Experience Builder.
5. Define branding tokens in the Branding Set editor. Set `--dxp-color-brand`, `--dxp-color-background`, and font tokens.
6. Configure navigation menus: add top-level items, set visibility rules (public vs authenticated).
7. Build or assign custom LWC pages using the Page Manager.
8. Publish the site. Verify the published URL resolves correctly.

**Why not Aura:** Aura templates lack publish-time HTTP caching. For high-traffic portals, the LWR CDN caching model significantly reduces server load and page load times.

### Pattern: Partner Community with Pre-Built Template

**When to use:** Standing up a partner portal quickly using standard partner workflows (deal registration, lead sharing, channel dashboards) without heavy custom branding.

**How it works:**
1. Select the Partner Central template during site creation.
2. Enable the Partner Community license on the relevant profiles.
3. Configure sharing settings for Opportunities, Leads, and Accounts as needed.
4. Use Experience Builder to adjust navigation and page layout without full custom builds.
5. Customize branding through the Experience Builder theme panel.

**Why not Build Your Own:** Partner Central ships with pre-wired pages for partner-specific objects. Starting from scratch duplicates work that the template handles automatically.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| All components are LWC, performance matters | Build Your Own (LWR) | Publish-time freeze enables HTTP caching; clean URL paths |
| Must include existing Aura components that cannot be migrated | Build Your Own (Aura) | Only template supporting Aura components |
| Small marketing landing page or microsite | Microsite (LWR) | Lightweight LWR template optimized for minimal, focused public sites |
| Standard partner portal with deal registration | Partner Central | Pre-built pages for partner workflows; faster time to value |
| Standard customer self-service portal | Customer Account Portal | Pre-built case and account pages; appropriate for straightforward use cases |
| Unsure — new build, greenfield | Build Your Own (LWR) | LWR is the strategic direction; Aura templates are not receiving new investment |

---

## Recommended Workflow

1. **Answer the seven questions above and record the template decision.** Work through
   `## Questions to Ask Before Configuring`, then fill the Pre-Creation Checklist and
   Component Inventory in `templates/experience-cloud-site-setup-template.md`. Template
   family and `urlPathPrefix` are settled here, before anything is created, because
   neither is recoverable cheaply afterwards.
2. **Verify the sender address exists and is verified in the target org.** `emailSenderAddress`
   is Required on `Network` and can only be supplied on the deploy that creates the site;
   later Metadata API updates are silently ignored (`references/gotchas.md`, Gotcha 6).
   Template selection itself is `admin/email-templates-and-alerts`.
3. **Create the site, then retrieve it into source immediately.** In Setup → Digital
   Experiences → All Sites → New, choose the template from the Decision Guidance table.
   Then pull `CustomSite`, `Network`, `NavigationMenu` and whichever bundle type the org
   returns — the retrieve tells you whether this is `experiences/` (ExperienceBundle) or
   `digitalExperiences/site/` (DigitalExperienceBundle). Commands are in
   `references/metadata-examples.md`.
4. **Write the settings in source, not in Setup.** Set `networkMemberGroups` (profiles or
   permission sets), `selfRegistration` with its `selfRegProfile`, the email templates,
   `maxFileSizeKb` and `allowedExtensions` on the `Network`; set
   `clickjackProtectionLevel`, `allowStandardPortalPages` and `redirectToCustomDomain` on
   the `CustomSite`. Shape and field semantics are in `references/metadata-examples.md`.
5. **Build branding and navigation.** For LWR, define the branding set (`brandingSetType`
   `APP`, `definitionName` matching the template, e.g. `starter:branding-starter`) and have
   component CSS consume `--dxp-*` tokens rather than literals. Author the primary menu as
   a `NavigationMenu` file, and create a matching page for every `SalesforceObject` item —
   LWR and Help Center templates ship no generic record pages (api_meta.txt L90449–L90452).
6. **Run the checker, then validate, then deploy in dependency order.**
   `python3 skills/admin/experience-cloud-site-setup/scripts/check_experience_cloud_site_setup.py --manifest-dir force-app/main/default`
   catches a Live site with self-registration and no profile, an empty
   `networkMemberGroups`, missing Required `Network` fields, a `requireHttps` element that
   does nothing, weak clickjack protection, non-https external menu targets, and a
   `Network` whose Experience Builder folder is absent. Then
   `sf project deploy validate`, then deploy `sites/` before `networks/`.
7. **Publish and prove it.** Move `Network.status` to `Live`, publish the Builder content,
   and confirm the result with SOQL rather than a page load:
   `SELECT Status, UrlPathPrefix FROM Network WHERE Name = '<site>'` plus
   `SELECT COUNT(Id) FROM NetworkMember WHERE Network.Name = '<site>'`. Test as a guest in
   a private window and as an authenticated member. Guest permissions themselves are
   `admin/experience-cloud-guest-access`.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Template selection documented and confirmed as appropriate for component inventory
- [ ] `urlPathPrefix` agreed once and identical in `Network`, `CustomSite` and the content bundle
- [ ] My Domain is deployed; custom domain pattern (`MyDomainName.my.site.com`) resolves
- [ ] Branding tokens (`--dxp-*` for LWR, theme panel for Aura) applied and consistent with brand guidelines
- [ ] Navigation menus configured with correct visibility rules (public vs authenticated items)
- [ ] Site published after all changes — not just saved
- [ ] Guest user profile permissions set correctly for public pages
- [ ] Site tested with both unauthenticated (guest) and authenticated user sessions
- [ ] `emailSenderAddress` verified in the org **before** the site-creating deploy
- [ ] `networkMemberGroups` non-empty, and `NetworkMember` count reconciled against the assignment count
- [ ] `selfRegistration` either off, or on with a named `selfRegProfile` and a duplicate rule behind it
- [ ] `clickjackProtectionLevel` is `SameOriginOnly` unless an external framing domain is documented
- [ ] `scripts/check_experience_cloud_site_setup.py` run against the retrieved source and clean
- [ ] Status confirmed with `SELECT Status FROM Network WHERE Name = '<site>'`, not from the deploy result

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Template is permanent post-creation** — Once a site is created with a given template, there is no "change template" option. To switch from Aura to LWR (or vice versa), the site must be deleted and recreated. Any customizations, pages, and navigation configuration must be rebuilt from scratch. Always confirm the template before creation.
2. **LWR requires explicit republish** — Changes made in Experience Builder on an LWR site (including branding and component edits) do not go live until the site is republished. The site serves the last published version from cache. Practitioners coming from Aura expect changes to appear immediately; on LWR they do not.
3. **Aura components cannot be used in LWR sites** — The LWR template component panel only exposes LWC-compatible components. Attempting to use an Aura component in an LWR site will fail silently (the component simply will not appear in the picker). The fix is to migrate the component to LWC or switch to an Aura-based template.
4. **`emailSenderAddress` cannot be changed by a second deploy** — the field is Required, is honoured only on the deploy that creates the site, and later Metadata API updates are discarded without an error (api_meta.txt L90784–L90795).
5. **`UnderConstruction` never comes back** — once a site has been published it can never return to that status (object_reference.txt L187373). `DownForMaintenance` is the only way to take a live site offline.
6. **`ExperienceBundle` and `DigitalExperienceBundle` are not interchangeable** — enhanced LWR sites from Winter '23 onward use the latter, everything else the former, and packaging is unsupported for enhanced LWR (api_meta.txt L51234–L51238).

All twelve, with **What happens / When it occurs / How to avoid**, are in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Published Experience Cloud site | Live site accessible at `MyDomainName.my.site.com/path` with correct template, branding, and navigation |
| Branding set configuration | LWR branding tokens (`--dxp-*` CSS custom properties) or Aura theme panel settings defining the site's visual identity |
| Navigation menu structure | Primary (and optional secondary/footer) menus with visibility rules configured in Experience Builder |
| Site setup checklist | Completed template from `templates/experience-cloud-site-setup-template.md` documenting decisions and configuration |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing the deployable XML: `Network`, `CustomSite`, `NavigationMenu`, the content bundle, `package.xml`, retrieve/deploy, verification SOQL |
| `references/gotchas.md` | A deploy succeeded but the org did not change, or a site behaves differently from its source |
| `references/well-architected.md` | Justifying the template and publish model against the pillars, and finding the official sources used |
| `references/examples.md` | Two worked site builds (LWR self-service, Partner Central) and the Aura-in-LWR anti-pattern |
| `references/llm-anti-patterns.md` | Reviewing AI-generated Experience Cloud guidance before acting on it |
| `templates/experience-cloud-site-setup-template.md` | Recording the pre-creation decisions: edition, component inventory, template, URL path |
| `scripts/check_experience_cloud_site_setup.py` | Linting retrieved source before `sf project deploy validate` |

---

## Related Skills

- admin/experience-cloud-guest-access — guest profile permissions, public page access, external OWD; this skill stops at the site, that one owns who can see what without logging in
- admin/portal-requirements-gathering — the requirements and licence catalogue that should precede site creation; source of the self-registration duplicate-Contact control
- admin/experience-cloud-member-management — provisioning the external users that `networkMemberGroups` turns into members
- admin/experience-cloud-cms-content — authoring and managing content inside an established site
- admin/experience-cloud-moderation — flagging, moderation rules and member behaviour after go-live
- admin/experience-cloud-seo-settings — indexing, sitemaps and canonical URLs once the URL structure is settled
- admin/email-templates-and-alerts — the Classic templates named on `Network` for welcome, forgot-password and lockout
- security/experience-cloud-security — hardening the site beyond `clickjackProtectionLevel` and the guest profile
- devops/experience-cloud-deployment-admin — promoting a finished site between orgs, ExperienceBundle API-version pinning, sandbox refresh
- lwc/lwr-site-development — building the LWR theme layouts and custom components this skill only places
- lwc/experience-cloud-lwc-components — LWC targets and property shapes that make a component appear in Experience Builder
- flow/flow-for-experience-cloud — screen flows and automation on pages inside an already-created site
