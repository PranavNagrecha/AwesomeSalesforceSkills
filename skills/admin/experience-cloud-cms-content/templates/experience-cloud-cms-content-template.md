# Experience Cloud CMS Content — Publishing Checklist Template

Use this template when publishing or reviewing CMS content for an Experience Cloud site.

## Request Summary

**Skill:** `experience-cloud-cms-content`

**Request summary:** (describe what content needs to be published and for which site)

**Target site:** (site name and runtime — LWR or Aura)

**Content type:** News | Image | Document | Custom: ___________

**Go-live date/time:** ___________ (UNVERIFIED 2026-10-20: native per-item scheduling and the org-timezone rule are Help-only; state the timezone explicitly)

**Expiry date/time:** ___________ (leave blank if permanent)

---

## Prerequisites

- [ ] Digital Experiences app is enabled in the org
- [ ] Admin has the permission the org uses for CMS authoring (UNVERIFIED 2026-10-20: Manage Experiences / Create and Set Up Experiences is documented for keyword lists and moderation rules, not for CMS)
- [ ] CMS workspace exists for this content domain
- [ ] A channel with `Type` `COMMUNITY` delivers the workspace to the target site (object_reference 264 L180515)
- [ ] If custom content type: `ManagedContentType` (or `ContentTypeBundle`) has been deployed, with exactly one `NAMEFIELD` node and a detail page in the site
- [ ] If audience targeting: the `Audience` metadata exists for the site with `ExperienceVariation` targets, deployed with ExperienceBundle

---

## Content Item Details

| Field | Value |
|---|---|
| Content item name | |
| Content type | |
| Workspace | |
| Channel(s) assigned | |
| Number of variants (language variants) | |
| Audiences targeted (if any, via experience variations) | |
| Planned publish date/time | |
| Planned unpublish date/time | |

---

## Authoring Checklist

- [ ] Content item created in correct workspace
- [ ] All required fields populated (title, body, image alt text as applicable)
- [ ] Image assets uploaded and optimized (verify file size and format)
- [ ] Language variant(s) created with the correct `Language`
- [ ] Publish timing agreed and tested on a non-production item (UNVERIFIED 2026-10-20: native scheduling is Help-only)
- [ ] Unpublish timing agreed if content is time-limited
- [ ] Content reviewed for spelling, legal compliance, and brand alignment

---

## Publishing Checklist

- [ ] Variant status is Published and `IsPublished` is true (not Draft or Revised)
- [ ] The channel `Type` is correct for the audience (UNVERIFIED 2026-10-20: the Channel Assignments panel is Help-only)
- [ ] All language variants are published (not just the default variant)
- [ ] No unpublished dependencies (referenced images or related content items are also published)

---

## Experience Builder Wiring Checklist

- [ ] The CMS component for this runtime is placed on the target page (UNVERIFIED 2026-10-20: component names are Help-only)
- [ ] Component is bound to the correct managed content item (not hardcoded text)
- [ ] Preview in Experience Builder confirms correct content renders
- [ ] A preview as a member of each targeted audience confirms the right experience variation renders
- [ ] Page is published after component binding changes

---

## Post-Launch Verification

- [ ] Content is visible to an unauthenticated visitor (if the site is public) or a test user in the correct audience
- [ ] Any scheduled publish fires at the correct time (verify with a test item if possible; UNVERIFIED 2026-10-20: native per-item scheduling is Help-only)
- [ ] Rollback path documented: previous variant or replacement item identified and ready

---

## Notes

(Record any deviations from standard workflow, stakeholder approvals, or special handling required.)
