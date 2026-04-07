---
name: experience-cloud-moderation
description: "Use when setting up or tuning Experience Cloud community content moderation: keyword/criteria-based rules, member reputation system, and moderation queue management. Triggers: 'set up community content moderation', 'configure reputation levels', 'flagging rules Experience Cloud', 'moderation queue setup', 'keyword blocking community', 'approve community posts before publishing'. NOT for CMS content publishing workflows or Digital Experiences page publishing."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "how do I set up content moderation rules in Experience Cloud to block banned words"
  - "configure reputation levels and points for community members"
  - "moderation queue setup — who needs permission to review flagged posts"
  - "keyword flagging rules are not hiding posts from other community members"
  - "new member posts should not be visible until a moderator approves them"
tags:
  - experience-cloud
  - moderation
  - reputation
  - community
  - content-approval
inputs:
  - "Experience Cloud site name and type (Customer Community, Partner Community, LWR)"
  - "List of keywords or topics to moderate"
  - "Desired moderation actions (Block, Replace, Flag, Review)"
  - "Target reputation levels and point thresholds for member actions"
  - "Identity of users who will serve as moderators (permission set or profile to assign)"
outputs:
  - "Configured ModerationRule records in the org (keyword/criteria rules with correct actions)"
  - "Reputation levels and point configuration per site"
  - "Permission assignment plan for the Moderate Experiences Feeds permission"
  - "Moderation queue review process documentation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Experience Cloud Moderation

Use this skill to configure the three-layer moderation system for an Experience Cloud community: automated rule-based content filtering, a reputation system that assigns levels and points to members, and a moderation queue where human moderators review flagged or held content. Activate when a practitioner needs to control what community members can post, build trust through member reputation, or establish a review workflow before content goes live.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Experience Cloud site exists and is in a sandbox or scratch org. Moderation rules are site-specific; confirm which site(s) are in scope.
- Identify who will moderate: one or more users need the "Moderate Experiences Feeds" permission (via permission set or profile). Without this permission, users cannot access the moderation queue.
- Understand the desired content actions — Block (prevents post), Replace (substitutes offending text), Flag (marks for human review without hiding), Review (hides content from everyone except the author and moderators until approved). Each has a different user-facing impact.
- Reputation points are not retroactive. Any levels configured after member activity begins will not credit historical actions. Clarify whether a migration plan is needed.
- The site must have Chatter/feeds enabled. Reputation and rules apply to feed posts and comments, not CMS content pages.

---

## Core Concepts

### Rule-Based Automated Moderation

Moderation rules are created in Setup > Experience Cloud Sites > Moderation. Each rule defines:

- **Criteria type**: Keyword list (matches text content) or Member criteria (targets members by join date, post count, or reputation level — useful for throttling new members).
- **Content type**: Posts, comments, files, or all feed items.
- **Action**: Block, Replace, Flag, or Review.

Rules are evaluated in the order they appear in Setup. The **first matching rule wins**; subsequent rules are not evaluated for the same content item. Order matters and should be intentional — place high-priority Block rules above lower-priority Flag rules.

Keyword rules match partial words unless wildcards are explicitly excluded. A keyword of "spam" will match "spammy" and "asparagus" does not match unless it appears in the keyword list literally. Test keyword lists in a sandbox before activating in production.

### Four Moderation Actions and Their User Impact

| Action | What Happens | Visible to Author? | Visible to Others? |
|---|---|---|---|
| Block | Post or comment is rejected at submission | Author sees rejection message | Never posted |
| Replace | Offending text is substituted with *** or custom text | Author sees altered version | Altered version shown |
| Flag | Item is posted and marked for moderator review | Yes — post is live | Yes — post is live |
| Review | Item is held pending approval | Yes — author sees own post | No — hidden until approved |

**Review** is the most restrictive action. Content under Review is invisible to all community members except the author (who can see it but not edit it) and any user with the Moderate Experiences Feeds permission. This makes Review suitable for new-member or high-risk keyword scenarios where live visibility before approval is unacceptable.

### Reputation System

Each site supports up to 10 reputation levels. Each level has:
- A name (e.g., "Contributor", "Expert")
- A point threshold — the minimum cumulative points to reach that level
- An optional image

Points are awarded for specific member actions: posting, commenting, liking, receiving likes, having a best answer selected, and logging in. The point value for each action is configurable per site. **Points are not retroactive** — configuring levels after site launch does not award points for past activity.

Reputation levels can be used as Member Criteria in moderation rules. For example: require Review action for posts by members below Level 2 to throttle spam from new accounts.

### Moderation Queue

The moderation queue (Chatter > Moderation or the Feed Moderation page in Experience Workspaces) aggregates all content in Review status or explicitly flagged via the Flag action. To access it a user must have the **Moderate Experiences Feeds** permission — this is a granular permission within the Salesforce user license, not an Experience Cloud-specific setting. Moderators can Approve (make content live), Delete, or Dismiss (remove flag without deleting).

---

## Common Patterns

### Pattern: Throttle New-Member Posts with Review Action

**When to use:** Community launches and the team wants to prevent spam from brand-new accounts before they have established any reputation.

**How it works:**
1. Create a Member Criteria rule targeting members with fewer than 5 posts and a join date within the last 7 days (or reputation below Level 2).
2. Set the action to Review.
3. Assign the Moderate Experiences Feeds permission to community managers.
4. New member posts are held until a moderator approves them. Approved posts are visible immediately.

**Why not Flag instead:** Flag leaves the post live for other members to see. A spam post under Flag is visible to the entire community until a moderator acts. Review prevents public exposure entirely.

### Pattern: Keyword Block for Prohibited Terms

**When to use:** Compliance or community guidelines prohibit specific words (profanity, competitor names, regulated terms).

**How it works:**
1. Create a keyword list under Setup > Experience Cloud Sites > Keyword Lists. Add exact terms and common variants.
2. Create a Moderation Rule that references the keyword list, applies to Posts and Comments, and uses the Block action.
3. Place this rule at the top of the rule order so it fires before any Flag or Review rules.

**Why not Replace:** Replace is suitable for borderline content where the post intent is acceptable but specific language is not. For strictly prohibited content, Block gives the clearest signal to the author and prevents any altered version of the problematic post from reaching other members.

### Pattern: Reputation-Gated Contribution Levels

**When to use:** The community wants to increase trust as members demonstrate engagement over time — e.g., allow posting links only after reaching a certain reputation threshold.

**How it works:**
1. Define 5–10 reputation levels under Experience Workspaces > Reputation.
2. Set point values for relevant actions (posting, commenting, best answer).
3. Create Member Criteria rules tied to reputation level thresholds for high-risk content types (e.g., posts containing URLs require Review if member is below Level 3).
4. As members earn points and advance levels, restrictive moderation rules no longer apply to them.

---

## Decision Guidance

| Situation | Recommended Action | Reason |
|---|---|---|
| Post contains a prohibited term and must never be visible | Block | Rejects submission entirely; no version of the post reaches other members |
| Post language is borderline but intent is acceptable | Replace | Substitutes offending text; post remains with corrected wording |
| Post is suspicious but should be reviewable before removal | Flag | Post goes live; moderators can evaluate in queue without hiding from community |
| New member posts that must not be visible until approved | Review | Holds content from all community members until moderator approves |
| Reputation needed before relaxing moderation rules | Reputation + Member Criteria rule | Levels gate rule application automatically as members accumulate points |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner setting up Experience Cloud moderation:

1. **Identify moderation requirements.** Confirm the site name, which content types need moderation (posts, comments, files), which keywords or member conditions are in scope, and the desired action for each scenario. Get moderator names or profiles for permission assignment.

2. **Assign the Moderate Experiences Feeds permission.** In Setup > Permission Sets (or the relevant profile), grant "Moderate Experiences Feeds" to all designated moderators. Without this permission, the moderation queue is inaccessible and moderators cannot take action on Review-status content.

3. **Configure keyword lists.** Navigate to Setup > Experience Cloud Sites > [Site] > Moderation > Keyword Lists. Create one or more keyword lists. Test terms in a sandbox to confirm partial-match behavior is acceptable before enabling in production.

4. **Create and order moderation rules.** Under Moderation Rules, create rules for each keyword list and/or member criteria scenario. Assign the correct action (Block / Replace / Flag / Review). Reorder rules so the most restrictive (Block) appears first. Verify rule order reflects intent.

5. **Configure reputation levels and points.** In Experience Workspaces > Reputation, define up to 10 levels with meaningful names and point thresholds. Set point values for each member action (post, comment, like, best answer, login). If using reputation as a criteria in moderation rules, confirm levels are active before rules referencing them go live.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All designated moderators have the Moderate Experiences Feeds permission assigned
- [ ] Moderation rules are ordered correctly (Block rules before Flag/Review rules)
- [ ] Keyword lists have been tested in sandbox for partial-match false positives
- [ ] Review-action behavior (hidden from all but author and moderators) has been demonstrated to stakeholders and accepted
- [ ] Reputation levels are defined before any Member Criteria rules that reference them go live
- [ ] Moderators know how to access the moderation queue in Experience Workspaces or Chatter
- [ ] Rule actions and their user-facing messages have been reviewed for tone and compliance requirements

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Review-status content is invisible to everyone except the author and moderators** — Stakeholders often assume Flag and Review behave the same way (the post is live but marked). They do not. Content under Review is not visible to any community member other than the author. If a community manager asks "why can't I see the new post?" — the member likely hit a Review rule and the manager does not have the Moderate Experiences Feeds permission.

2. **Reputation points are not retroactive** — If reputation levels are configured after members have been active in the community, no historical points are awarded. Members who have been active for months may start at Level 1. Plan reputation configuration before or at launch, not as a post-launch addition.

3. **Moderation rules fire in order; the first match wins** — If a Block rule appears below a Flag rule and content matches both, only the Flag action fires. Admins who add a new Block rule at the bottom of the list may be surprised that flagged content is still appearing live. Always review rule order after adding or editing rules.

4. **Keyword rules match partial words by default** — A keyword of "ban" will match "banner", "abandon", and "band". Review keyword lists carefully and use specific multi-word phrases where precision is required.

5. **The Moderate Experiences Feeds permission is a Salesforce platform permission, not an Experience Cloud role** — It is assigned through permission sets or profiles in the internal org, not through community member roles. External community members (Customer Community or Partner Community licenses) typically cannot be granted this permission unless they are also internal Salesforce users.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Moderation rules configuration | Ordered list of active rules with criteria type, action, and content type per site |
| Keyword lists | Named keyword lists referenced by moderation rules |
| Reputation configuration | Up to 10 levels with point thresholds and per-action point values |
| Permission assignment record | List of users or permission sets assigned the Moderate Experiences Feeds permission |
| Moderation queue access guide | Brief instructions for moderators on accessing and processing the queue |

---

## Related Skills

- experience-cloud-setup — Site creation, network settings, and member access configuration; complete before moderation rules
- permission-set-management — Assigning the Moderate Experiences Feeds permission to moderators via permission sets
