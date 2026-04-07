---
name: experience-cloud-guest-access
description: "Use when designing or configuring public pages on an Experience Cloud site — guest user profile setup, page-level access settings in Experience Builder, object/field visibility for unauthenticated visitors, and explicit sharing rules that expose data on public pages. Triggers: 'configure public pages Experience Cloud', 'guest user profile setup', 'unauthenticated site access', 'public community page visibility', 'make page visible without login'. NOT for authenticated user features (use admin/experience-cloud-member-management). NOT for security hardening or remediation of guest user exposure (use security/guest-user-security)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
tags:
  - experience-cloud
  - guest-user
  - public-pages
  - unauthenticated-access
  - experience-builder
triggers:
  - "configure public pages Experience Cloud"
  - "guest user profile setup for public site"
  - "unauthenticated visitors cannot see the page I built"
  - "public community page visibility not working"
  - "make this Experience Builder page accessible without login"
  - "set up product catalog accessible without login"
inputs:
  - "Experience Cloud site name and template type (LWR, Aura, Microsite)"
  - "List of pages that must be publicly accessible vs. members-only"
  - "Objects and fields that public pages need to display (e.g., Knowledge articles, Products)"
  - "Whether any public pages require record submission by unauthenticated visitors"
outputs:
  - "Page-level access configuration guidance for Experience Builder"
  - "Guest user profile permission review for public object and field access"
  - "Explicit sharing rule recommendations to expose records on public pages"
  - "Public page access checklist (see templates/)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Experience Cloud Guest Access

This skill activates when a practitioner needs to design, configure, or troubleshoot public-facing pages in an Experience Cloud site — pages reachable by unauthenticated visitors. It covers the one-guest-user-profile-per-site model, how to configure page access in Experience Builder, what object and field permissions the guest profile needs, and how explicit sharing rules govern which records appear on public pages.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the site template: LWR (Lightning Web Runtime), Aura (Community), or Microsite. Page access configuration steps differ slightly across templates.
- Confirm the org is on Spring '21 or later. The Secure Guest User Record Access toggle became mandatory in Spring '21 and changes how guest record visibility works — any site designed before this release may need sharing rule restructuring.
- Know which pages must be public and which should require login. Page-level access is set in Experience Builder per page; this is the primary mechanism for controlling unauthenticated access.
- Confirm whether any public pages require guests to submit records (e.g., contact forms, case deflection). Guest Create permissions on a profile are different from Read-only object access.

---

## Core Concepts

### One Guest User Profile Per Site

Each Experience Cloud site has exactly one guest user profile, generated automatically when the site is created. This profile controls all unauthenticated access for every public page on that site. It cannot be deleted or shared with another site — if you have three sites, you have three independent guest profiles.

The guest profile lives at Setup > Digital Experiences > All Sites > [Site] > Workspaces > Administration > Guest User Profile. Changes to the profile take effect for all public pages on that site immediately.

### Page-Level Access in Experience Builder

Experience Builder controls whether an individual page is accessible to guests or requires login. The setting lives on each page under Page Properties > Page Access:

- **Public** — the page is accessible without login; the guest user profile governs what data loads.
- **Requires Login** — unauthenticated visitors are redirected to the login page.

This is the first gate. Even if the guest profile has object Read access, a page set to "Requires Login" will not render for unauthenticated visitors. The most common configuration mistake is setting the page to Public but neglecting to configure the guest profile, resulting in empty components on the page.

### Object and Field Permissions for Public Data

The guest user profile must explicitly grant Read access to any object whose records a public page displays. The principle is least-privilege:

- Grant Read on the specific objects the page needs (e.g., Knowledge__kav for a help center, Product2 for a catalog).
- Never grant Create, Edit, Delete, View All, or Modify All unless the page has a form submission use case that strictly requires Create.
- Grant field-level Read access for only the fields the page components actually display. Unused fields on the guest profile are a latent data exposure risk.

### External OWD and Explicit Sharing Rules for Public Records

For objects where external OWD is Private, guest users see zero records regardless of page or profile configuration. To expose specific records publicly:

1. Set external OWD to **Private** (recommended default — least privilege).
2. Create **Guest User Sharing Rules** (Setup > Sharing Settings > Guest User Sharing Rules for [Site]) that grant Read access to the specific records the page should display.
3. These rules evaluate against criteria or owner-based conditions, letting you expose only the records that belong on a public page (e.g., Published Knowledge articles, Featured Products).

If you set external OWD to Public Read Only, all records of that object become readable by every guest user on every site — which is almost never the right choice for custom objects.

### API Settings on the Guest Profile

Two settings on the guest profile must stay disabled for any public site:

- **API Enabled** — allows the guest user to make direct API calls. Disable unless specifically required.
- **Allow guest users to access public APIs** — a site-level setting in Administration > Preferences. Disable unless the site hosts a Force.com Site that needs REST endpoint access.

Leaving these enabled expands the attack surface of the public site beyond the pages you designed.

---

## Common Patterns

### Public Knowledge Base Page

**When to use:** A help center or support site where Knowledge articles should be readable without login.

**How it works:**
1. Set each Knowledge article page to Public in Experience Builder Page Properties.
2. On the guest user profile, grant Read on Knowledge object and Read on the fields displayed (Title, Summary, Body, Article Number).
3. Set external OWD for Knowledge to Public Read Only OR keep it Private and create a Guest User Sharing Rule based on the Publication Status = Online criteria.
4. Confirm that "Allow guest users to access public APIs" is OFF in Site Preferences.

**Why not the alternative:** Granting View All on Knowledge to bypass OWD exposes draft and archived articles to guests. The sharing rule approach lets you surface only Published/Online records.

### Public Product Catalog Without Login

**When to use:** An e-commerce or partner site where Product records should be visible to unauthenticated visitors browsing before they register.

**How it works:**
1. Set product catalog and product detail pages to Public in Experience Builder.
2. On the guest profile, grant Read on Product2, Pricebook2, and PricebookEntry for the fields shown on the page.
3. Keep external OWD on Product2 at Public Read Only (Product2 is a Salesforce object with no sensitive owner data — broadly readable is acceptable).
4. Do not grant Read on custom objects related to pricing or account-specific discounts — those should be members-only pages.
5. Test in an incognito browser before publishing; confirm only intended Product fields render.

**Why not the alternative:** Adding the product object to a page that requires login defeats the purpose of unauthenticated browsing. The combination of page-level Public access plus guest profile Read gives clean separation from authenticated catalog features.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Page must be visible to visitors without an account | Set Page Access = Public in Experience Builder, configure guest profile | Page-level access is the primary control gate |
| Object records must appear on a public page but external OWD is Private | Create Guest User Sharing Rules (criteria-based) | Sharing rules selectively expose only matching records |
| Object records must appear on a public page, external OWD is Public Read Only | Grant Read on guest profile; no sharing rules needed | Public OWD makes all records readable to guests |
| Guest needs to submit a form (case deflection, contact us) | Grant Create-only on the target object in guest profile | Never grant Edit or Delete for form submissions |
| Mix of public and members-only pages on the same site | Set each page individually in Experience Builder | Page access is per-page, not per-site |
| Unsure which records a public page currently exposes | Run as guest user in incognito, review guest profile permissions and sharing rules | Test first — do not guess |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Identify scope** — list all pages on the site and classify each as Public or Requires Login. Confirm site template (LWR vs Aura) so the correct Experience Builder navigation applies.
2. **Configure page access** — for each public page, open Page Properties in Experience Builder and set Page Access to Public. Save and publish after all pages are configured.
3. **Set guest profile permissions** — open the guest user profile for this site. Grant Read on objects and fields required by public pages. Add Create on specific objects only where a public form submission is required. Remove any permissions not directly needed.
4. **Configure sharing for public records** — review external OWD for each object the public pages display. For Private OWD objects, create Guest User Sharing Rules that expose only the intended records (e.g., criteria-based on Status = Published). For objects that should not be publicly readable, confirm external OWD is Private and no sharing rule exists.
5. **Disable API settings** — confirm API Enabled is OFF on the guest user profile. Confirm "Allow guest users to access public APIs" is OFF in Site Administration > Preferences.
6. **Test as a guest** — open the site in an incognito browser. Navigate all public pages. Confirm intended records load and no unexpected records or fields appear. Confirm members-only pages redirect to login.
7. **Handoff to security review** — if the site has custom Apex controllers called from public pages, hand off to security/guest-user-security for FLS and WITH USER_MODE review.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All pages intended for unauthenticated access are set to Public in Experience Builder Page Properties.
- [ ] All pages that should require login are set to Requires Login.
- [ ] Guest user profile grants Read only on the objects public pages need — no Create/Edit/Delete unless a form submission use case requires Create.
- [ ] Field-level permissions on the guest profile are limited to the fields actually displayed on public pages.
- [ ] External OWD and Guest User Sharing Rules are aligned — Private OWD objects have explicit sharing rules; no object inadvertently set to Public OWD.
- [ ] API Enabled is OFF on the guest user profile.
- [ ] "Allow guest users to access public APIs" is OFF in Site Administration > Preferences.
- [ ] Site tested in incognito browser — all public pages load expected content and no unexpected records are visible.

---

## Salesforce-Specific Gotchas

1. **Each site has exactly one guest profile — and it is shared across all public pages** — changing the guest profile to support a new public page also affects every other public page on the same site. Adding Read access to a new object on the guest profile means that object is now readable on any public page that happens to query it, not only the new one.
2. **FLS on the guest profile applies to all guest Apex calls, not just page components** — if an Apex class runs in guest context and you remove a field from the guest profile, the field will appear blank or throw an error in any public page that calls that class, not only the page you intended to change.
3. **External OWD controls record visibility for guest users — not internal OWD** — internal OWD governs authenticated user sharing. Guest users respect external OWD only. Setting internal OWD to Public Read Only does not automatically make records readable by guests if external OWD is Private.
4. **Guest User Sharing Rules for a site are site-specific** — a sharing rule created for Site A's guest user does not apply to Site B's guest user. Each site's guest user is a distinct system user and requires its own sharing rules.
5. **Page Access = Public does not override empty guest profile permissions** — a page set to Public will render for a guest, but if the guest profile has no Read access to the objects the page components query, the components will return empty results or errors. Both the page setting AND the profile permissions are required.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Public page access checklist | Completed template documenting page access settings, guest profile permissions, and sharing rule configuration for the site (see templates/) |
| Guest profile permission summary | Object-by-object and field-by-field list of what Read/Create access was granted on the guest profile and why |
| Sharing rule inventory | List of Guest User Sharing Rules configured for the site, with criteria and objects covered |

---

## Related Skills

- `security/guest-user-security` — use when the question is hardening, auditing, or remediating security exposure on the guest user profile rather than configuring public page access.
- `admin/experience-cloud-site-setup` — use when the task is creating or initially configuring an Experience Cloud site rather than configuring guest access on an existing site.
- `admin/experience-cloud-member-management` — use when the question involves authenticated external user access, sharing sets, or member profiles rather than guest access.
- `admin/sharing-and-visibility` — use when the broader sharing model design (OWD strategy, role hierarchy, internal sharing rules) is the primary question.
