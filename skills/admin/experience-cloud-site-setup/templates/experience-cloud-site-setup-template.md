# Experience Cloud Site Setup — Work Template

Use this template when creating or reviewing an Experience Cloud site configuration.

## Scope

**Skill:** `experience-cloud-site-setup`

**Request summary:** (fill in what the user asked for)

**Org:** (org name / sandbox name)

**Date:** (fill in)

---

## Pre-Creation Checklist

Complete this section before creating the site. These decisions cannot be undone after site creation.

### Edition and Licensing

- [ ] Org edition confirmed: Enterprise / Performance / Unlimited / Developer (circle one)
- [ ] Experience Cloud licenses provisioned (if applicable)
- [ ] Partner Community or Customer Community licenses allocated (if applicable)

### Component Inventory

List all components that will be used on this site:

| Component Name | Type (LWC / Aura) | Existing or New | Compatible with LWR? |
|---|---|---|---|
| (fill in) | | | |
| (fill in) | | | |
| (fill in) | | | |

- [ ] All components are LWC-only → LWR template is viable
- [ ] One or more Aura components that cannot be migrated → Aura template required (document reason below)

**Reason for Aura template (if applicable):** ___

### Template Selection Decision

- [ ] **Build Your Own (LWR)** — greenfield, all LWC, performance-critical
- [ ] **Microsite (LWR)** — small public-facing site, minimal pages
- [ ] **Partner Central** — standard partner workflows (deal registration, lead sharing)
- [ ] **Customer Account Portal** — standard customer self-service (cases, accounts)
- [ ] **Build Your Own (Aura)** — Aura component dependency documented above

**Rationale:** ___

### URL Path

- Site URL path (set at creation, permanent): `/___`
- Full URL will be: `MyDomainName.my.site.com/___`
- [ ] My Domain is deployed in this org
- [ ] URL path confirmed with stakeholders

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Edition / licensing: ___
- Template selected: ___
- Component inventory complete: Yes / No
- My Domain deployed: Yes / No
- Custom domain requirement: ___
- Known constraints (Aura deps, timeline, etc.): ___

---

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] New customer portal with LWR template
- [ ] Partner community with pre-built template
- [ ] Other: ___

**Justification:** ___

---

## Branding Configuration

For LWR sites (Branding Set tokens):

| Token | Value |
|---|---|
| `--dxp-color-brand` | |
| `--dxp-color-background` | |
| `--dxp-color-text-primary` | |
| `--dxp-font-family-primary` | |
| Logo URL / asset | |

For Aura sites (Theme Panel):

- Primary color: ___
- Secondary color: ___
- Font: ___
- Logo: ___

---

## Navigation Menu Structure

**Primary navigation:**

| Label | URL / Page | Visibility (Public / Authenticated / Profile) |
|---|---|---|
| (fill in) | | |
| (fill in) | | |
| (fill in) | | |

**Secondary / footer navigation (if applicable):**

| Label | URL / Page | Visibility |
|---|---|---|
| (fill in) | | |

---

## Page Inventory

| Page Name | URL Path | Template / Layout | Key Components |
|---|---|---|---|
| Home | / | (fill in) | |
| (fill in) | | | |
| (fill in) | | | |

---

## Post-Publish Validation Checklist

- [ ] Site published (not just saved) — confirmed publish timestamp updated
- [ ] Site URL resolves at `MyDomainName.my.site.com/path`
- [ ] Branding renders correctly (logo, colors, fonts)
- [ ] Navigation menus appear with correct items and visibility
- [ ] Pages load without errors (check browser console)
- [ ] Tested as unauthenticated guest user (incognito/private window)
- [ ] Tested as authenticated user
- [ ] Guest user profile permissions reviewed — no unnecessary object or field access
- [ ] HTTPS confirmed on all pages

---

## Notes

Record any deviations from the standard pattern and why.

___
