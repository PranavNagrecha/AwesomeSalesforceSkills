---
name: experience-cloud-moderation
description: "Set up or tune Experience Cloud content moderation: keyword/criteria rules, member reputation system, moderation queue. Triggers: 'set up community content moderation', 'configure reputation levels', 'flagging rules Experience Cloud', 'moderation queue setup', 'keyword blocking community', 'approve community posts before publishing'. NOT for publishing or scheduling CMS articles on the site — use admin/experience-cloud-cms-content. NOT for deciding which behaviours to reward or how to name reputation tiers — use admin/community-engagement-strategy."
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
  - "Permission assignment plan for the Moderate Experiences Feeds and Can Approve Feed Post and Comment permissions"
  - "Moderation queue review process documentation"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Experience Cloud Moderation

Use this skill to configure the three-layer moderation system for an Experience Cloud community: automated rule-based content filtering, a reputation system that assigns levels and points to members, and a moderation queue where human moderators review flagged or held content. Activate when a practitioner needs to control what community members can post, build trust through member reputation, or establish a review workflow before content goes live.

Cites: `api_meta`, `object_reference` and `apexdev` are the Winter '27 (264) guides; line numbers are those files'.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Experience Cloud site exists and is in a sandbox or scratch org. Moderation rules and keyword lists are named `site_name.<developer_name>` and stored in the `moderation` folder (api_meta 264 L84937-84938, L92233-92234), so confirm which site(s) are in scope.
- Identify who will moderate. Three different permissions are involved, and they are not interchangeable: users with **Moderate Experiences Feeds** can read the Moderation feed of items flagged for moderation (apexdev 264 L25687-25688), can view the moderation audit trail with reports (object_reference 264 L189821), and receive flag emails (L190716-190719); users with View All Data or **Can Approve Feed Post and Comment** can see pending-review feed items and comments, the author and users with Can Approve Feed Post and Comment or Modify All Data can edit and delete them, and users with Can Approve Feed Post and Comment or Modify All Data can change a comment from PendingReview to Published (object_reference 264 L136986-136990, L136371-136379, L4347-4348). The corpus states that publish step for comments only, not for feed items. UNVERIFIED (2026-10-20): which of these a given Setup permission set screen grants together is Help-only.
- Understand the desired actions: Block, Review, Replace, Flag, and FreezeAndNotify (reserved for future use) (api_meta 264 L92248-92254). Block shows the member a user message (`userMessage`, default "You can't use %BLOCKED_KEYWORD% or other inappropriate words in this site. Review your content and try again."; L92283-92288). Review leaves the item in `PendingReview` status (object_reference 264 L136986-136994). Each has a different user-facing impact.
- UNVERIFIED (2026-10-20): that reputation points are not retroactive, so levels configured after member activity begins do not credit historical actions, is Help-only; no corpus line says either way. Clarify whether a migration plan is needed.
- Rules apply to feed content: `entityName` `FeedItem` with `fieldName` `RawBody`, `FeedComment` with `RawCommentBody`, and other fields such as `LinkUrl`, `Title` and poll `ChoiceBody` (api_meta 264 L92296-92306, L92357-92383). Post and comment rules apply to content created in groups and user profiles; all feed types, such as polls and links, are supported (L92296-92298). The org setting `canModerateAllFeedPosts` (default false) decides whether moderation features apply to all feed posts, including those visible in sites, or only to posts in sites (api_meta 264 L115876-115879).

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which content must never be visible, and which only needs a look? | Block, Review, Replace and Flag differ in visibility (Core Concept 2; Gotcha 1) | An action per scenario, written into the moderation policy |
| How many rules and keyword lists will there be, and across how many sites? | The limits are per org, not per site: 30 rules (content and rate together), 30 keyword lists, three keyword criteria per rule (Core Concept 1) | A rule inventory counted against the org limits |
| Who approves held items, and do they hold Can Approve Feed Post and Comment? | Approving pending-review items needs that permission or Modify All Data, not Moderate Experiences Feeds alone (Gotcha 5) | A named approver list mapped to permissions |
| Is a rule built in the Experience Management UI or the Metadata API? | A rule created through the Metadata API should not be edited in the UI, or fields are overwritten or ignored (Core Concept 1) | One authoring channel per rule |
| Which keywords, and how will they be matched? | Matching ignores capitalization and trailing punctuation and has no wildcards (Gotcha 4) | A tested list with explicit variants |
| Which reputation events earn points, and are Member Criteria rules tied to levels? | Points come from a fixed list of 16 feed events (Core Concept 3) | A points table using only the documented events |
| Is reputation being introduced to a live community? | Whether earlier activity earns points is unverified (Gotcha 2) | A sandbox check or a migration plan before any reputation-based rule goes live |

A proper moderation setup states the action per scenario, counts rules and lists against the org limits, assigns the approval permission explicitly and tests every rule with a real post; "just doing it" creates rules, then discovers who can see and approve held content in production.

---

## Core Concepts

### 1. Rule-Based Automated Moderation

A `ModerationRule` (suffix `.rule`, folder `moderation`, API 36.0 and later) specifies the member-generated content it applies to, the criteria, and the action (api_meta 264 L92203-92207, L92233-92238). Its required fields are `action`, `active` and `masterLabel`; each `entitiesAndFields` entry requires `entityName` and may carry a `keywordList` (L92248-92308). A rule's `type` is Content or Rate (L92312-92320); rate rules use `actionLimit`, `notifyLimit` and a `timePeriod` of Short or Medium (L92256-92270, L92336-92340). Member criteria are carried in `userCriteria` (L92271-92272).

Limits: up to 30 rules per org, not per site, counting content rules and rate rules; up to three keyword criteria per rule (api_meta 264 L92218-92219). Keyword lists: up to 30 per org, up to 2,000 keywords per list, each keyword up to 100 characters, wildcards not supported, and capitalization and trailing punctuation ignored when matching (L84924-84927, L84964-84967).

Rule precedence is by action, not by the order shown in Setup: rules that block content run first, then rules to review and approve, then rules that replace content, and last rules that flag; if two or more rules perform the same action the oldest rule runs first, and replace rules do not run when the content also applies to a review rule (api_meta 264 L92226-92229).

Rules created with the Metadata API are more powerful than rules set up in the UI (for example one that moderates only the Link Name of a Link feed type), and a rule created through the Metadata API should not be updated in the UI, which overwrites or ignores its fields (api_meta 264 L92211-92216).

UNVERIFIED (2026-10-20): that rules and keyword lists are created in Setup > Experience Cloud Sites > Moderation, that member criteria are join date, post count and reputation level, that the content type choices are "posts, comments, files or all feed items", and that a keyword matches inside longer words (so "ban" would match "banner") are Help-only or unstated; the corpus says only that matching ignores capitalization and trailing punctuation.

### 2. Four Moderation Actions and Their User Impact

| Action | What the corpus supports | Author | Others |
|---|---|---|---|
| Block | The member sees the rule's `userMessage` when content is blocked (api_meta 264 L92283-92288) | Sees the message | Never sees it |
| Replace | A replace rule does not run when the content also applies to a review rule (L92228-92229) | See below | See below |
| Flag | A moderation rule can flag an item (flag reason `FlaggedByRule`, apexref 262 L134804); flags are also created when a member flags an item or a trigger does (object_reference 264 L191021-191022); flagged items appear in the Moderation feed (apexdev 264 L25687) | See below | See below |
| Review | The item is `PendingReview`: visible to its author and to users who see it and have View All Data or Can Approve Feed Post and Comment; the author and users with Can Approve Feed Post and Comment or Modify All Data can edit and delete it (object_reference 264 L136986-136990) | Sees it and can edit and delete it | Cannot see it |

UNVERIFIED (2026-10-20): what Replace substitutes (asterisks or custom text), that a Flag keeps the item live and visible to everyone, and that Flag and Review feed one queue, are Help-only; the corpus does not state them. For a held item, comments, likes, bookmarks and shares are blocked while it is pending review (object_reference 264 L136995-136999), and a held comment does not raise `CommentCount` until it is published (L4345-4348).

### 3. Reputation System

A site's reputation is defined in the `Network` metadata type: `enableReputation` turns it on, and if no `reputationLevels` or `reputationPointsRules` are defined the default values are used (api_meta 264 L93597-93603, L93766-93770). `ReputationLevelDefinitions` holds `ReputationLevel` entries: `lowerThreshold` is Required, `label` is optional (the defaults are Level 1 to Level 10, api_meta 264 L94370-94382), and `branding` is an optional custom image (L94359-94388). The upper value is calculated by the platform (L94360). `ReputationPointsRules` holds one rule per event type with a Required `points` value; the event types are FeedItemWriteAPost, FeedItemWriteAComment, FeedItemReceiveAComment, FeedItemLikeSomething, FeedItemReceiveALike, FeedItemMentionSomeone, FeedItemSomeoneMentionsYou, FeedItemShareAPost, FeedItemSomeoneSharesYourPost, FeedItemPostAQuestion, FeedItemAnswerAQuestion, FeedItemReceiveAnAnswer, FeedItemMarkAnswerAsBest, FeedItemYourAnswerMarkedBest, FeedItemEndorseSomeoneForKnowledgeOnATopic and FeedItemEndorsedForKnowledgeOnATopic (L94391-94431), with defaults such as +1 for a post and +5 for receiving a like (L94433-94448). Logging in is not an event type.

UNVERIFIED (2026-10-20): the cap of 10 levels (the corpus gives ten default labels but no maximum), that points are not retroactive, and that reputation level is usable as Member Criteria in a moderation rule are Help-only.

### 4. Moderation Queue

The Moderation feed contains all feed items that are flagged for moderation, except direct messages, and is available only to users with Moderate Experiences Feeds permissions (apexdev 264 L25687-25688). Users with Can Approve Feed Post and Comment or Modify All Data can change a pending-review comment from PendingReview to Published (object_reference 264 L136377-136379); even on a closed conversation, publishing a pending-review comment stays available to admins and moderators (L137134-137135, L137154). A flag is a `NetworkModeration` record (object_reference 264 L190960-190961), and `NetworkActivityAudit` holds an audit trail of moderation activity (L189686, L189818-189820).

UNVERIFIED (2026-10-20): the queue's location (Chatter > Moderation or the Feed Moderation page in Experience Workspaces) and the Approve, Delete and Dismiss buttons are Help-only.

---

## Common Patterns

### Pattern: Throttle New-Member Posts with Review Action

**When to use:** Community launches and the team wants to hold posts from brand-new accounts before they are visible.

**How it works:**
1. Create a rule with the Review action whose `userCriteria` targets new members. UNVERIFIED (2026-10-20): the criteria choices (join date, post count, reputation level) are Help-only.
2. Give the people who approve held items Can Approve Feed Post and Comment (or Modify All Data), and Moderate Experiences Feeds for the Moderation feed.
3. Held posts stay `PendingReview` until a permitted user publishes them.

**Why not Flag instead:** UNVERIFIED (2026-10-20): that Flag leaves the item live is Help-only. Review has a documented visibility rule (author plus permitted users, object_reference 264 L136986-136990), which is what makes it the hold.

### Pattern: Keyword Block for Prohibited Terms

**When to use:** Compliance or community guidelines prohibit specific words (profanity, competitor names, regulated terms).

**How it works:**
1. Create a `KeywordList` (suffix `.keywords`, up to 2,000 keywords of up to 100 characters each; api_meta 264 L84924-84938, L84964-84967). Add exact terms and variants; wildcards are not supported.
2. Create a `ModerationRule` with the Block action whose `entitiesAndFields` list `FeedItem` / `RawBody` and `FeedComment` / `RawCommentBody` (api_meta 264 L92302-92306) against that list.
3. No ordering step is needed for Block: block rules run before review, replace and flag rules (L92226-92227).

**Why not Replace:** Replace is suited to borderline content where specific language is not acceptable but the post is; and a replace rule does not run when a review rule also applies (L92228-92229).

### Pattern: Reputation-Gated Contribution Levels

**When to use:** The community wants to increase trust as members demonstrate engagement over time.

**How it works:**
1. Define the levels (`lowerThreshold`, optional `label` and image) and the points per event in the `Network` reputation settings (api_meta 264 L94345-94448).
2. Reference reputation in a rule's member criteria only after confirming in a sandbox that the criteria are available (UNVERIFIED 2026-10-20, Help-only).
3. As members earn points and advance levels, level-based rules stop applying to them (UNVERIFIED 2026-10-20: this depends on reputation being usable as member criteria, which is Help-only).

---

## Decision Guidance

| Situation | Recommended Action | Reason |
|---|---|---|
| Post contains a prohibited term and must never be visible | Block | Block rules run first and show the member the user message (api_meta 264 L92226, L92283-92288) |
| Post language is borderline but intent is acceptable | Replace | A replace rule does not run if a review rule also applies (L92228-92229); the substituted text is UNVERIFIED (2026-10-20) |
| Post is suspicious but should be reviewable | Flag | Flagged items appear in the Moderation feed (apexdev 264 L25687); whether the item stays live is UNVERIFIED (2026-10-20) |
| New member posts that must not be visible until approved | Review | `PendingReview` is visible only to the author and permitted users (object_reference 264 L136986-136990) |
| Reputation needed before relaxing moderation rules | Reputation + member criteria rule | UNVERIFIED (2026-10-20): reputation as member criteria is Help-only |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner setting up Experience Cloud moderation:

1. **Identify moderation requirements.** Confirm the site name, which content types need moderation (feed posts, comments, links, polls), which keywords or member conditions are in scope, and the desired action for each scenario. Count planned rules and keyword lists against the org limits (30 rules, 30 lists).

2. **Assign the permissions.** Grant Moderate Experiences Feeds to people who work the Moderation feed, and Can Approve Feed Post and Comment (or Modify All Data) to people who publish, edit or delete pending-review items. UNVERIFIED (2026-10-20): the metadata API name of the Moderate Experiences Feeds permission. Earlier versions of this skill gave `ModerateNetworkFeeds` and said that `ModerateExperiencesFeeds` matches nothing; neither spelling is in the corpus, so look the name up in a retrieved `.permissionset` from the org instead of searching for either.

3. **Configure keyword lists.** Create `KeywordList` files (or use the UI; UNVERIFIED 2026-10-20: the UI path is Help-only). Test terms in a sandbox with real posts.

4. **Create moderation rules.** Create each `ModerationRule` with its action, keyword list or `userCriteria`, and `entitiesAndFields`. Run `python3 scripts/check_experience_cloud_moderation.py --manifest-dir <metadata dir>` over the retrieved `moderation` folder. Do not edit a Metadata API rule in the UI (api_meta 264 L92215-92216).

5. **Configure reputation levels and points.** Set `ReputationLevelDefinitions` and `ReputationPointsRules` in the site's `Network` metadata using only the documented event types (api_meta 264 L94391-94448). Confirm the levels are in place before any rule that depends on them goes live.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Approvers hold Can Approve Feed Post and Comment (or Modify All Data); Moderation-feed users hold Moderate Experiences Feeds
- [ ] Rule and keyword list counts are within the org limits (30 and 30; three keyword criteria per rule)
- [ ] Rules were tested with real posts for each action; Block precedence was not assumed to follow the Setup order
- [ ] Keyword lists were tested in a sandbox for false positives (matching ignores capitalization and trailing punctuation; no wildcards)
- [ ] Review-action behaviour (visible only to the author and permitted users) has been demonstrated to stakeholders and accepted
- [ ] Reputation levels and points use only the documented event types, and exist before any rule depends on them
- [ ] Rule actions and their user messages have been reviewed for tone and compliance requirements

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Review-status content is hidden from everyone but its author and permitted users** — A pending-review item is visible to its author and to users who see it and have View All Data or Can Approve Feed Post and Comment; the author and users with Can Approve Feed Post and Comment or Modify All Data can edit and delete it (object_reference 264 L136986-136990). If a community manager asks "why can't I see the new post?" the manager likely lacks one of those permissions. The earlier text that the author cannot edit a held post is contradicted by that passage.

2. **Reputation points and existing members** — UNVERIFIED (2026-10-20): that points are not retroactive, so members who were active before reputation was configured start at Level 1, is Help-only. Test in a sandbox before enabling reputation on a live community.

3. **Rule precedence is by action, not by Setup order** — Block rules run first, then review, then replace, then flag; the oldest rule runs first among rules with the same action (api_meta 264 L92226-92227). A Block rule added at the bottom still runs before an existing Flag rule. The earlier text that the first matching rule in the Setup list wins is contradicted by this passage.

4. **Keyword matching** — Capitalization and trailing punctuation are ignored, so BadWord matches BADWORD and badword, and wildcards are not supported (api_meta 264 L84926-84927, L84967). UNVERIFIED (2026-10-20): that a keyword also matches inside longer words, so "ban" would match "banner", "abandon" and "band", is unstated; test short keywords in a sandbox.

5. **Moderate Experiences Feeds is not the approval permission** — It opens the Moderation feed (apexdev 264 L25687-25688); publishing, editing or deleting pending-review items needs Can Approve Feed Post and Comment or Modify All Data (object_reference 264 L136986-136990). UNVERIFIED (2026-10-20): that external Customer Community or Partner Community users cannot be given these permissions is Help-only.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Moderation rules configuration | `ModerationRule` files with action, type, `entitiesAndFields` and `userCriteria` per site |
| Keyword lists | `KeywordList` files referenced by moderation rules |
| Reputation configuration | `ReputationLevelDefinitions` and `ReputationPointsRules` in the site's `Network` metadata |
| Permission assignment record | Users or permission sets holding Moderate Experiences Feeds and Can Approve Feed Post and Comment |
| Moderation queue access guide | Brief instructions for moderators on the Moderation feed and publishing held items |

---

## Related Skills

- `admin/experience-cloud-site-setup` -- Site creation, network settings, and member access configuration; complete before moderation rules
- `admin/permission-set-architecture` -- Assigning the moderation permissions to moderators via permission sets
