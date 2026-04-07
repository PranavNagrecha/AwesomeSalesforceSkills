# Examples — Experience Cloud CMS Content

## Example 1: Creating Banner Content for a Portal Homepage

**Context:** A financial services firm is launching a customer portal built on an LWR Experience Cloud site. The marketing team needs to manage a rotating hero banner on the homepage without developer involvement for each update.

**Problem:** Without a managed CMS setup, content updates require a developer to edit static resource files or hardcoded Experience Builder page properties and redeploy. Marketing cannot publish independently, and there is no versioning or scheduling.

**Solution:**

Step 1 — Create the workspace and channel:

In Digital Experiences > Workspaces, create a workspace named `PortalContent`. Click Channels > New Channel. Select `Experience Cloud Site` as the channel type, choose the target LWR site, and save. The channel now links the workspace to the site.

Step 2 — Author a Banner content item:

In the workspace, click Add Content > Banner. Fill in:
- Title: `Q2 Promotion — Loyalty Rewards`
- Body: Short promotional text (plain text or rich text depending on the CMS version)
- Image: Upload or select from the asset library

Save as draft, then click Publish. Confirm the item shows Published status and the channel appears under Channel Assignments.

Step 3 — Wire to Experience Builder:

In Experience Builder, drag the CMS Single Item component onto the homepage. In the component properties panel, select the workspace and the Banner content item. Set the component to render the correct fields (title, image, body). Save and publish the page.

**Why it works:** The Banner content item is now the single source of truth for that homepage section. When marketing needs a new banner, they update the CMS item and publish — no page deploy required. The CMS item is versioned, so rolling back to a previous banner is a one-click operation from the workspace.

---

## Example 2: Scheduling Seasonal Content with Audience Targeting

**Context:** A retail portal needs a holiday promotion banner visible only to loyalty members from December 1 through December 31. Non-members should see a default banner year-round.

**Problem:** Without scheduling and audience targeting, swapping banners requires a developer to manually update the page and re-deploy on the correct date — a fragile, timezone-sensitive process that creates unnecessary release risk.

**Solution:**

Step 1 — Define audiences in Experience Cloud:

In the Experience Cloud site settings, create two audiences:
- `LoyaltyMembers` — membership criterion: Contact record has Loyalty_Tier__c = `Gold` or `Silver`
- `AllVisitors` — default audience (all authenticated or guest users not in another audience)

Step 2 — Author the content item with two variants:

Create a Banner content item named `Homepage Hero`. In the Variants panel, add Variant A:
- Name: `Holiday Promotion`
- Target audience: `LoyaltyMembers`
- Scheduled publish: December 1, 00:00 org local time
- Scheduled unpublish: January 1, 00:00 org local time
- Content: Holiday promotional text and image

Add Variant B:
- Name: `Default Banner`
- Target audience: `AllVisitors`
- No schedule (always active)
- Content: Standard homepage banner

Step 3 — Publish and validate:

Publish the content item. In Experience Builder preview, switch the audience context to `LoyaltyMembers` and confirm the holiday variant renders. Switch to `AllVisitors` and confirm the default renders. Use the site's Audience Preview mode to simulate the scheduled date if needed.

**Why it works:** The platform enforces variant visibility based on audience membership and the scheduled dates. On December 1 the holiday variant goes live automatically for loyalty members; on January 1 it archives automatically. No deployment window is needed, and both variants are managed in one content item with full version history.

---

## Anti-Pattern: Using Unmanaged Content for Shared Promotional Banners

**What practitioners do:** They author promotional banners directly in Experience Builder as page content or rich-text components rather than creating CMS workspace items. This is faster to set up initially and requires no workspace or channel configuration.

**What goes wrong:** Unmanaged content is site-local. It cannot be reused across multiple portals or communities. It has no version history, no scheduling, and no audience targeting. After a sandbox refresh the content is gone and must be re-authored. As the content inventory grows, there is no centralized view of what content is published across the organization's sites. Content governance becomes impossible.

**Correct approach:** Even for a single site, create a CMS workspace and publish all reusable or governed content as managed content items. Reserve unmanaged content only for truly one-off, ephemeral page content that will never be reused, scheduled, or targeted.
