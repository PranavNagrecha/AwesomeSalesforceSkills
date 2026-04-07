---
name: community-engagement-strategy
description: "Use this skill to design and configure the engagement model for an Experience Cloud community: reputation levels, ideation, and content contribution strategy. Triggers: 'community engagement strategy', 'gamification Experience Cloud', 'reputation levels setup', 'ideation community portal', 'member recognition program'. NOT for moderation configuration (see experience-cloud-moderation). NOT for technical Experience Cloud site setup or Lightning template selection."
category: admin
salesforce-version: "Spring '25+"
triggers:
  - "community engagement strategy"
  - "gamification Experience Cloud"
  - "reputation levels setup"
  - "ideation community portal"
  - "member recognition program"
well-architected-pillars:
  - Operational Excellence
tags:
  - experience-cloud
  - community-engagement
  - reputation
  - ideation
  - gamification
inputs:
  - Experience Cloud site type (Customer, Partner, or Employee community)
  - Target audience segments and their primary goals on the site
  - Desired member behaviors to incentivize (e.g., answering questions, posting ideas, commenting)
  - Existing content plan or content ownership map (if available)
outputs:
  - "Reputation tier configuration: up to 10 named levels with per-action point thresholds"
  - "Ideation setup checklist: Ideas tab, status workflow, and vote moderation settings"
  - "Content contribution strategy: member role definitions, journey map, content ownership assignments"
  - Engagement launch checklist covering all three pillars
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Community Engagement Strategy

Use this skill when designing the engagement model for an Experience Cloud community site — covering reputation gamification, ideation workflow, and content contribution strategy. This skill does NOT configure moderation rules, guest user access, or the technical site template.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Experience Cloud site is already provisioned and the domain is active; reputation and ideation cannot be enabled on a site that has not yet been activated.
- Clarify which member behaviors the community sponsor most wants to incentivize — answering questions, posting ideas, writing articles, or some combination — because point thresholds must reflect that priority.
- Understand whether content ownership has been decided: who is responsible for each content area (product, support, marketing). Undefined ownership is the most common cause of stale community content after launch.
- Note that reputation points are **not retroactive**: members who acted before Reputation was enabled will not receive points for historical activity.

---

## Core Concepts

### Reputation (Gamification)

Experience Cloud Reputation is a point-based system with up to **10 configurable tiers** per community site. Admins assign point thresholds and meaningful tier names to each level. Points are awarded per action type:

| Action | Configurable? | Notes |
|---|---|---|
| Writing a post | Yes | Base engagement action |
| Commenting | Yes | Separate threshold from posting |
| Receiving a like | Yes | Passive recognition |
| Marking a best answer | Yes | High-value behavior to incentivize |
| Asking a question | Yes | Distinguish from answering |

Tier names matter significantly. Generic labels ("Level 1", "Level 2") generate less engagement than role-meaningful names ("Newcomer", "Trusted Advisor", "Community Expert"). Reputation level and tier name are displayed on the member profile card across all community pages. Members can see each other's levels, creating social incentive.

**Key platform constraint:** Reputation is enabled at the community level, not org-wide. Each community site maintains its own reputation configuration and member point totals. Points do not transfer between sites.

### Ideation (Ideas Feature)

The Ideas feature uses the standard **Idea** and **IdeaTheme** objects. It requires:

1. An **Ideas tab** surfaced in the community navigation — ideation will not appear without it.
2. An **IdeaTheme** (campaign or category) to group ideas — members post ideas within a theme.
3. A defined **status workflow**: standard statuses include New, Under Review, Considered for Future Release, Implemented, and Closed — Not Planned. Statuses must be communicated to members; ideas sitting at "New" for months destroy community trust.
4. **Voting**: members upvote ideas; votes surface prioritization signals to product or operations teams.
5. **Duplicate merging**: admins or moderators can merge duplicate ideas and transfer votes to the canonical record.

The Ideas feature is distinct from Q&A (Chatter Questions). Do not conflate them — Q&A is for support deflection; ideation is for structured product or service input.

### Content Contribution Strategy

Content contribution strategy defines **who posts what, and when**. It must be decided before launch. The three elements are:

1. **Member roles**: Define role tiers — e.g., Lurker (read-only), Contributor (can post), Power User (can post + moderate peer content), Community Manager (full rights). These map loosely to profile + permission set assignments, not to Reputation levels.
2. **Content ownership**: Each content area (how-to articles, product announcements, FAQs, idea themes) needs a named internal owner responsible for keeping it current. Without this, content ages out and engagement drops.
3. **Member journey mapping**: New members need an onboarding path — a welcome post, a "Start Here" article, and a low-barrier first action (e.g., "introduce yourself" post). Without a designed first-touch journey, activation rates stay low.

---

## Common Patterns

### 10-Tier Reputation System for a Technical Support Community

**When to use:** The community's primary goal is peer-to-peer support deflection. Members answer each other's questions, and the business wants to surface trusted advisors.

**How it works:**
1. Enable Reputation in Setup > Digital Experiences > All Sites > [Site] > Reputation.
2. Define 10 tiers with meaningful names tied to support expertise, for example:
   - 1: Newcomer (0–99 pts)
   - 2: Explorer (100–299 pts)
   - 3: Contributor (300–699 pts)
   - 4: Helper (700–1,499 pts)
   - 5: Advisor (1,500–2,999 pts)
   - 6: Expert (3,000–5,999 pts)
   - 7: Trusted Expert (6,000–9,999 pts)
   - 8: Community Champion (10,000–19,999 pts)
   - 9: Master (20,000–49,999 pts)
   - 10: Legend (50,000+ pts)
3. Weight "best answer received" and "comment liked" actions higher than raw post volume to incentivize quality over quantity.
4. Display reputation level prominently on the member profile and beside posts so peers can identify trusted voices.

**Why not flat point systems:** A flat system (one action type = one point) rewards volume of posts with no quality signal. Weighting best-answer actions higher encourages members to provide complete, useful answers rather than short replies that farm points.

### Product Ideation Portal with Status Workflow

**When to use:** A product or operations team wants structured customer input through a community channel, with clear feedback on what happens to submitted ideas.

**How it works:**
1. Enable Ideas in Setup > Digital Experiences > All Sites > [Site] > Ideas Settings.
2. Add the Ideas tab to the community navigation via Experience Builder.
3. Create an IdeaTheme for each product area or feedback campaign (e.g., "Mobile App Features Q3").
4. Configure the status workflow with at least four states: New, Under Review, Planned, Closed — Not Planned.
5. Assign an internal product manager as the owner of each theme; their job is to update statuses monthly.
6. Announce status updates in the idea's comment thread so voters see progress.

**Why explicit status workflow matters:** Ideas with no status movement for 90+ days communicate to members that feedback goes unread. This is the top cause of ideation disengagement. An "Under Review" update — even without a decision — signals responsiveness.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Community goal is support deflection | Prioritize Reputation with high weight on best-answer actions | Incentivizes quality answers over post volume |
| Community goal is product input | Prioritize Ideation with defined status workflow and named theme owners | Surfaces actionable prioritization data; shows members their votes matter |
| Community goal is content publishing (help center) | Prioritize Content Contribution strategy: define content owners and author roles before enabling contribution rights | Prevents content sprawl and outdated articles |
| Community launching in < 30 days | Seed 10–20 articles and one IdeaTheme before go-live; do not launch with empty content | Empty communities create poor first impressions and low activation rates |
| Org has multiple Experience Cloud sites | Configure Reputation separately per site; point totals do not sync across sites | Each site has an independent engagement model |
| Members ask "what do my points mean" | Rename generic tier labels to role-meaningful names | Tier names are the primary recognition signal visible to all members |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Define the engagement goal**: Confirm whether the priority is support deflection (Reputation-first), product input (Ideation-first), content publishing (Contribution strategy-first), or a combination. This determines which pillar to configure first and how to weight point actions.
2. **Design the Reputation tier structure**: Draft 10 tier names and point thresholds aligned to the target member behavior. Weight best-answer and high-quality-contribution actions more heavily than raw post counts. Confirm tier names are role-meaningful.
3. **Configure Ideation if applicable**: Enable Ideas in site settings, add the Ideas tab to navigation, create IdeaThemes per product or topic area, define the status workflow, and assign an internal owner to each theme.
4. **Establish content ownership before launch**: Map each content area to an internal owner. Define member roles (Contributor, Power User, Community Manager) and the permission sets or profiles that back them. Write a "Start Here" article and a new-member welcome post.
5. **Seed baseline content and test the member journey**: Before go-live, create at least one IdeaTheme with a seed idea, 10+ help articles, and a test member onboarding flow. Confirm the reputation tier display appears correctly on member profile cards. Verify that the Ideas tab renders in navigation.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Reputation enabled; tiers have meaningful names (not generic "Level N")
- [ ] Point thresholds are weighted toward quality actions (best answer, liked comment) not just raw post volume
- [ ] Ideas tab is present in community navigation if ideation is enabled
- [ ] At least one IdeaTheme exists with a defined status workflow and a named internal owner
- [ ] Content ownership map exists: each content area has a named owner and a review cadence
- [ ] New member onboarding path exists: "Start Here" article, welcome post, and a defined first action
- [ ] Baseline content (10+ articles or posts) seeded before launch
- [ ] Reputation points confirmed non-retroactive: communicated to site sponsor

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Reputation points are not retroactive** — Points are only awarded for actions taken after Reputation is enabled. Members who were active before the feature was turned on will not receive credit for historical posts, answers, or likes. This creates an initial leaderboard that does not reflect true community contribution history. Communicate this clearly to the community sponsor before launch and consider a points-seeding strategy for known top contributors.
2. **Ideation requires the Ideas tab in navigation** — Enabling Ideas in site settings is not sufficient. If the Ideas tab is not explicitly added to the community navigation in Experience Builder, the Ideation feature will not be visible to members. This is a common post-launch support ticket.
3. **Undefined content ownership leads to stale content** — The most common cause of long-term community disengagement is articles and announcements that go unupdated after launch. Assign a named internal owner to each content section before go-live, not as a post-launch task.
4. **Reputation levels and moderation permissions are separate** — Reputation tier does not grant any moderation or administrative permission within the community. Member access rights are controlled by profile and permission sets. A "Legend"-tier member cannot moderate posts unless the underlying profile or permission set grants that access.
5. **IdeaTheme required for idea submission** — Members cannot post a free-standing idea without an active IdeaTheme to post into. If no IdeaTheme is active, the idea submission UI will not appear. Always create at least one theme before enabling ideation for members.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Reputation tier matrix | 10-tier table with tier names, point thresholds, and weighted action types |
| Ideation setup checklist | Step-by-step record of Ideas settings enabled, tabs added, themes created, and status workflow configured |
| Content ownership map | Table mapping each content area to an internal owner, review cadence, and content type |
| Member role matrix | Table mapping member roles (Lurker/Contributor/Power User/Manager) to the profile/permission set that backs them |
| Engagement launch checklist | Combined pre-launch verification list across all three pillars |

---

## Related Skills

- experience-cloud-moderation — use alongside this skill for flagging, moderation rules, and member blocking configuration
