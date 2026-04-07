---
name: experience-cloud-site-setup
description: "Use when creating a new Experience Cloud site: selecting LWR vs Aura template, configuring branding and navigation, setting up a custom domain, and using Experience Builder. Trigger keywords: create new Experience Cloud site, LWR vs Aura template, set up community portal domain, Experience Builder page builder, branding sets, navigation menu configuration, Microsite LWR, Build Your Own LWR. NOT for internal Lightning apps, Lightning App Builder configuration, or Flow orchestration inside an existing site."
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
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
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

Experience Cloud sites are accessed via a URL on the pattern `MyDomainName.my.site.com/site-path`. The subdomain is set by My Domain in org settings. The site path is set per-site during creation and cannot be changed after the site goes active.

For LWR sites, clean URL paths work without the `/s` prefix. Aura sites append `/s` to all page paths automatically. This distinction matters when sharing deep links or setting up redirects.

### Experience Builder and Branding

Experience Builder is the drag-and-drop page editor for Experience Cloud. It manages pages, navigation menus, site settings, and branding. For LWR sites:

- **Branding sets** define tokens (colors, typography, spacing) applied site-wide.
- **`--dxp-*` CSS custom properties** are the styling hooks used in LWR themes. Component CSS should consume these tokens rather than hardcoded values, so branding changes propagate across the entire site.
- Navigation menus are configured in Experience Builder under the Navigation section and support nested items, labels, and access-controlled items (visible only to logged-in users or specific profiles).

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

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm prerequisites:** Verify org edition (Enterprise, Performance, Unlimited, or Developer), confirm My Domain is deployed, and inventory all components the site will use (LWC only vs any Aura components). Template selection depends on this inventory.
2. **Select and create the site:** In Setup > Digital Experiences > All Sites > New, choose the appropriate template based on the decision table above. Set the site name and URL path — the path cannot be changed after the site is activated.
3. **Configure branding in Experience Builder:** For LWR sites, open the Branding Set editor and define `--dxp-*` CSS custom property tokens (brand color, background, typography). For Aura sites, use the theme panel. Apply a logo via Site Settings.
4. **Build navigation menus:** In Experience Builder, open the Navigation section. Create the primary navigation menu. Set item visibility (public, authenticated, profile-specific) for each item. Add secondary or footer menus as required.
5. **Assign and configure pages:** Use Page Manager to create or assign custom pages. For LWR sites, add LWC components to page regions via the component panel. Configure component properties and verify mobile responsiveness.
6. **Publish and validate:** Click Publish in Experience Builder. Verify the site resolves at the expected URL (`MyDomainName.my.site.com/path`). Confirm branding, navigation, and page content render correctly. Test with both guest and authenticated user sessions.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Template selection documented and confirmed as appropriate for component inventory
- [ ] Site URL path set correctly — confirm it cannot be changed and matches requirements
- [ ] My Domain is deployed; custom domain pattern (`MyDomainName.my.site.com`) resolves
- [ ] Branding tokens (`--dxp-*` for LWR, theme panel for Aura) applied and consistent with brand guidelines
- [ ] Navigation menus configured with correct visibility rules (public vs authenticated items)
- [ ] Site published after all changes — not just saved
- [ ] Guest user profile permissions set correctly for public pages
- [ ] Site tested with both unauthenticated (guest) and authenticated user sessions

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Template is permanent post-creation** — Once a site is created with a given template, there is no "change template" option. To switch from Aura to LWR (or vice versa), the site must be deleted and recreated. Any customizations, pages, and navigation configuration must be rebuilt from scratch. Always confirm the template before creation.
2. **LWR requires explicit republish** — Changes made in Experience Builder on an LWR site (including branding and component edits) do not go live until the site is republished. The site serves the last published version from cache. Practitioners coming from Aura expect changes to appear immediately; on LWR they do not.
3. **Aura components cannot be used in LWR sites** — The LWR template component panel only exposes LWC-compatible components. Attempting to use an Aura component in an LWR site will fail silently (the component simply will not appear in the picker). The fix is to migrate the component to LWC or switch to an Aura-based template.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Published Experience Cloud site | Live site accessible at `MyDomainName.my.site.com/path` with correct template, branding, and navigation |
| Branding set configuration | LWR branding tokens (`--dxp-*` CSS custom properties) or Aura theme panel settings defining the site's visual identity |
| Navigation menu structure | Primary (and optional secondary/footer) menus with visibility rules configured in Experience Builder |
| Site setup checklist | Completed template from `templates/experience-cloud-site-setup-template.md` documenting decisions and configuration |

---

## Related Skills

- flow-for-experience-cloud — Use when adding Flow screens or automation to pages within an already-created Experience Cloud site
- lwc-for-experience-cloud — Use when building custom LWC components intended for placement in an LWR site
