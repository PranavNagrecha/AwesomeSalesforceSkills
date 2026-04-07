# Experience Cloud CMS Content — Publishing Checklist Template

Use this template when publishing or reviewing CMS content for an Experience Cloud site.

## Request Summary

**Skill:** `experience-cloud-cms-content`

**Request summary:** (describe what content needs to be published and for which site)

**Target site:** (site name and runtime — LWR or Aura)

**Content type:** News | Banner | Image | Custom: ___________

**Go-live date/time (org timezone):** ___________

**Expiry date/time (org timezone):** ___________ (leave blank if permanent)

---

## Prerequisites

- [ ] Digital Experiences app is enabled in the org
- [ ] Admin has Manage Experiences or Create and Set Up Experiences permission
- [ ] CMS workspace exists for this content domain
- [ ] Target site is added as a channel of type `ExperienceChannel` in the workspace
- [ ] If custom content type: `ManagedContentType` metadata has been deployed via SFDX or Metadata API
- [ ] If audience targeting: all required audiences are defined in the Experience Cloud site settings

---

## Content Item Details

| Field | Value |
|---|---|
| Content item name | |
| Content type | |
| Workspace | |
| Channel(s) assigned | |
| Number of variants | |
| Audiences targeted (if any) | |
| Scheduled publish date/time | |
| Scheduled unpublish date/time | |

---

## Authoring Checklist

- [ ] Content item created in correct workspace
- [ ] All required fields populated (title, body, image alt text as applicable)
- [ ] Image assets uploaded and optimized (verify file size and format)
- [ ] Variant(s) created with correct audience assignments
- [ ] Scheduled publish date set in org timezone (confirmed in Company Information > Timezone)
- [ ] Scheduled unpublish date set if content is time-limited
- [ ] Content reviewed for spelling, legal compliance, and brand alignment

---

## Publishing Checklist

- [ ] Content item status is Published (not Draft or Archived)
- [ ] Channel assignment confirmed — target site channel appears under Channel Assignments
- [ ] All variants are published (not just the default variant)
- [ ] No unpublished dependencies (referenced images or related content items are also published)

---

## Experience Builder Wiring Checklist

- [ ] CMS Single Item or CMS Collection component is placed on the target page
- [ ] Component is bound to the correct managed content item (not hardcoded text)
- [ ] Preview in Experience Builder confirms correct content renders
- [ ] Audience preview mode confirms correct variant renders for each targeted audience
- [ ] Page is published after component binding changes

---

## Post-Launch Verification

- [ ] Content is visible to an unauthenticated visitor (if the site is public) or a test user in the correct audience
- [ ] Scheduled publish fires at the correct time (verify with a test item if possible)
- [ ] Rollback path documented: previous content item version or replacement item identified and ready

---

## Notes

(Record any deviations from standard workflow, stakeholder approvals, or special handling required.)
