# Gotchas — Community Engagement Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Reputation Points Are Not Retroactive

**What happens:** When Reputation is enabled on an Experience Cloud site, members who were previously active receive zero points for any historical actions (posts, comments, likes, best answers). The system only begins awarding points from the moment the feature is enabled forward. A member who answered 200 questions before Reputation was turned on will appear as a Newcomer on the leaderboard alongside someone who joined the day Reputation went live.

**When it occurs:** Every deployment that enables Reputation on an existing community with an established member base.

**How to avoid:** Communicate the non-retroactive behavior to the community sponsor before go-live. If preserving historical contribution is important, consider manually seeding point totals for known top contributors via the Reputation object (accessible via Data Loader or API). Alternatively, launch Reputation at the same time as the community site to avoid the disparity.

---

## Gotcha 2: Ideation Requires the Ideas Tab in Community Navigation

**What happens:** Enabling Ideas in site settings (Setup > Digital Experiences > All Sites > [Site] > Ideas Settings) is a necessary but not sufficient step. If the **Ideas tab** is not explicitly added to the community navigation via Experience Builder, the Ideas section will not appear to members. Members navigating the site will find no entry point to submit or vote on ideas, and there will be no error message explaining why — the feature simply will not be visible.

**When it occurs:** Admins who enable Ideas in Setup but do not also configure navigation in Experience Builder. This is especially common when the setup is split between an admin (who handles backend settings) and a designer (who manages the Builder), with no handoff checkpoint.

**How to avoid:** Include "Add Ideas tab to community navigation in Experience Builder" as an explicit step in the ideation launch checklist, separate from "Enable Ideas in Setup." Test the Ideas feature as a non-admin community member before launch.

---

## Gotcha 3: Undefined Content Ownership Leads to Stale Content and Disengagement

**What happens:** Communities launched without a defined content ownership model accumulate stale articles, outdated announcements, and unresponsive discussion threads within 60–90 days. Members who return and see unupdated content stop returning. The community sponsor attributes this to poor adoption, but the root cause is an operational gap, not a product limitation.

**When it occurs:** Whenever content ownership is treated as a post-launch operational concern rather than a pre-launch architecture decision.

**How to avoid:** Before go-live, produce a content ownership map: a table that assigns each content section (FAQs, how-to articles, product announcements, idea themes) to a named internal owner with a defined review cadence (monthly minimum). This map should be a formal deliverable of the community engagement strategy, not an informal understanding.

---

## Gotcha 4: Reputation Levels Do Not Grant Moderation Permissions

**What happens:** Admins or community managers sometimes assume that high-reputation members automatically gain elevated moderation rights — the ability to flag and remove posts, manage members, or access moderation queues. In Salesforce Experience Cloud, Reputation is a display and incentive mechanism only. It has no integration with the permission model. A "Legend"-tier member has exactly the same community access rights as a "Newcomer" unless their underlying profile or permission set has been changed.

**When it occurs:** When community design decisions assume a reputation-based escalation path for member moderation rights without a corresponding permissions plan.

**How to avoid:** Treat member permission escalation as a separate configuration concern from Reputation. If elevated members should gain moderation abilities, create a distinct process (manual promotion via permission set assignment, or a threshold-triggered flow) that grants the required permissions explicitly.

---

## Gotcha 5: IdeaTheme Is Required for Idea Submission — There Is No Default

**What happens:** Members cannot post a free-standing idea. The Idea submission UI is always scoped to an IdeaTheme. If no active IdeaTheme exists when the Ideas feature launches, the idea submission form will not appear to members. The Ideas tab will load but members will see no option to create a new idea.

**When it occurs:** When admins enable Ideas and add the tab but forget to create at least one IdeaTheme before opening the site to members.

**How to avoid:** Include "Create at least one active IdeaTheme" as a mandatory pre-launch step in the ideation checklist. A general-purpose theme (e.g., "General Product Feedback") can serve as a catch-all until more specific themes are defined.
