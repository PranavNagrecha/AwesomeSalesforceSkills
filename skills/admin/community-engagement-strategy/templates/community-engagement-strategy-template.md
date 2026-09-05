# Community Engagement Strategy — Planning Template

Use this template to design and document the engagement model for an Experience Cloud community site before configuration begins.

---

## 1. Community Overview

**Site Name:**
**Site Type:** (Customer / Partner / Employee)
**Primary Goal:** (Support Deflection / Product Ideation / Content Publishing / Combined)
**Target Launch Date:**
**Community Manager / Owner:**

---

## 2. Engagement Pillars — Scope

Mark which pillars are in scope for this community:

- [ ] Reputation (gamification / member recognition)
- [ ] Ideation (Ideas feature / product feedback)
- [ ] Content Contribution (structured publishing model)

---

## 3. Reputation Tier Design

Complete only if Reputation is in scope.

**Incentivized behaviors** (rank by priority):
1.
2.
3.

**Point weights.** All 16 documented `eventType` values with their platform defaults. Leave a row alone unless you can write the reason; every deviation is something the next admin has to understand.

| `eventType` | Default | Ours | Reason for deviating |
|---|---|---|---|
| `FeedItemWriteAPost` | +1 | | |
| `FeedItemWriteAComment` | +1 | | |
| `FeedItemReceiveAComment` | +5 | | |
| `FeedItemLikeSomething` | +1 | | |
| `FeedItemReceiveALike` | +5 | | |
| `FeedItemMentionSomeone` | +1 | | |
| `FeedItemSomeoneMentionsYou` | +5 | | |
| `FeedItemShareAPost` | +1 | | |
| `FeedItemSomeoneSharesYourPost` | +5 | | |
| `FeedItemPostAQuestion` | +1 | | |
| `FeedItemAnswerAQuestion` | +5 | | |
| `FeedItemReceiveAnAnswer` | +5 | | |
| `FeedItemMarkAnswerAsBest` | +5 | | |
| `FeedItemYourAnswerMarkedBest` | +20 | | |
| `FeedItemEndorseSomeoneForKnowledgeOnATopic` | +5 | | |
| `FeedItemEndorsedForKnowledgeOnATopic` | +20 | | |

`enableKnowledgeable` confirmed on (required for both endorsement rows): [ ] yes  [ ] no — if no, both rows must be 0

**Level table.** There is no upper-bound element in the metadata — the application derives each band's ceiling from the next level's `lowerThreshold`. Fill in the lower bound only, strictly increasing, no duplicates, first level at 0. Every level needs an explicit `label`: omit it and the platform substitutes `Level 1` … `Level 10`.

| Level | `label` (domain-meaningful) | `lowerThreshold` | Reached by (roughly) |
|---|---|---|---|
| 1 | | 0 | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |

**Points-seeding decision** (points accrue forward only; `NetworkMember.ReputationPoints` is updateable via the API):

| Question | Answer |
|---|---|
| How long has this site had active members without Reputation? | |
| Seed, or start everyone at zero? | |
| If seeding: which members, on what basis? | |
| Who approves the seeded totals? | |
| Who is told, and what are they told? | |

---

## 4. Ideation Design

Complete only if Ideation is in scope.

**Zone** (`Idea.CommunityId` — cannot be changed after an idea is created): ____________

**Org-level `IdeasSettings`:** `enableIdeas` ____  `enableIdeaThemes` ____  `enableIdeasReputation` ____  `halfLife` ____

**IdeaThemes** (grouping and curation — `Idea.IdeaThemeID` is nillable, so a theme does not gate submission):

| Theme Name | Scope / Description | Internal Owner | Review Cadence |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

**Status workflow.** `Idea.Status` is a customizable picklist with no standard values — whatever you write here is the whole definition.

| Status | Meaning | Trigger for transition |
|---|---|---|
| New | Default on submission | (automatic) |
| Under Review | PM has evaluated | PM manually updates |
| Planned | Added to roadmap | PM manually updates |
| Implemented | Feature shipped | PM manually updates |
| Closed — Not Planned | Will not pursue | PM adds comment explaining why |

**Vote communication plan:**
How are voters notified of status changes?

---

## 5. Content Ownership Map

| Content Area | Owner Name | Title / Team | Review Cadence | Content Type |
|---|---|---|---|---|
| Welcome / Start Here | | | One-time + quarterly | Article |
| How-to / FAQ articles | | | Monthly | Articles |
| Product announcements | | | As-needed | Posts |
| Idea Themes | | | Monthly | IdeaTheme |
| Other: _____________ | | | | |

---

## 6. Member Role Matrix

| Role Label | Description | Profile / Permission Set | Contribution Rights |
|---|---|---|---|
| Lurker | Read-only access | | View only |
| Contributor | Can post and comment | | Post + comment |
| Power User | Can post and flag peer content | | Post + comment + flag |
| Community Manager | Full community management | | All rights |

---

## 7. New Member Onboarding Path

**First touch content:**
- [ ] Welcome / Start Here article created
- [ ] "Introduce Yourself" thread pinned to home
- [ ] New member welcome email or in-community message configured

**Defined first action for new members:**

---

## 8. Baseline Content — Pre-Launch Checklist

- [ ] 10+ articles or discussion posts seeded
- [ ] At least one IdeaTheme created and active
- [ ] At least one seed idea posted in each active IdeaTheme
- [ ] Welcome article published and pinned
- [ ] Onboarding thread created

---

## 9. Pre-Launch Verification

- [ ] `enableReputation` set; every level carries an explicit `label` (no `Level N` survived the merge)
- [ ] `lowerThreshold` values strictly increasing and unique; first level at 0
- [ ] Every deviating `pointsRule` has a written reason; `enableKnowledgeable` matches the endorsement weights
- [ ] Deployed ladder asserted back out: `SELECT LevelNumber, Label, Threshold FROM ReputationLevel WHERE ParentId = '<networkId>' ORDER BY LevelNumber`
- [ ] Points-seeding decision made and executed (or explicitly declined, with the reason recorded)
- [ ] Managed-topic list inside 25; every calendar item names a topic that exists
- [ ] Every goal has a metric with a SOQL source that runs, and a baseline taken before the first change
- [ ] Escalation queue named, owned, and its trigger conditions written
- [ ] Ideas: the zone is named (not just the theme); `Idea.Status` values written down
- [ ] Content ownership map finalized and owners confirmed
- [ ] Member role matrix mapped to actual profiles / permission sets — no assumption that a tier grants access
- [ ] New member onboarding path tested end-to-end
- [ ] `python3 scripts/check_community_engagement_strategy.py --file <strategy.yaml> --manifest-dir <metadata dir>` exits 0

---

## 10. Managed Topics

The topic list is the index the content calendar hangs off. Navigational and featured topics share a documented maximum of 25 (`position` accepts 0-24), so leave headroom.

| Topic name | Type (Navigational / Featured) | Parent (navigational only) | `position` | Owner |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

Count after this quarter's additions: ____ / 25.  Topics retired this cycle: ____________

---

## 11. Content Calendar

Every item names a topic from section 10 and an owner. An item with no topic has no navigation path and no way to measure it afterwards. Include rituals (sweeps, reviews), not only content.

| Week | Item | Kind (article / post / event / ritual) | Topic | Owner | Goal it moves |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |

---

## 12. Engagement Metrics

One metric per goal. Every metric needs a SOQL source that actually runs — check it against the constraints below before writing it down.

| Goal | Metric | SOQL source object | Baseline (date taken) | Target | Owner |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |

Constraints to check each metric against:

- [ ] No aggregate function over `FeedItem` — it supports none
- [ ] No `WHERE NetworkScope = …` — `FeedItem` cannot be filtered on that field
- [ ] Any `ChatterActivity` query carries a `ParentId` filter, and the denominator comes from `NetworkMember`
- [ ] Any `TopicAssignment` query carries `LIMIT 1100` or a `=` filter on Id/Entity
- [ ] Baseline was read **before** the first change, not after

**Health dashboard.** Which report or dashboard component does each metric feed, and how often does it refresh?

| Metric | Component | Refresh | Audience |
|---|---|---|---|
| | | | |

---

## 13. Moderation and Escalation Policy

The rules themselves belong to `admin/experience-cloud-moderation`; this section is the policy that skill implements. Moderation rules and keyword lists are capped at 30 each **per org, not per site** — confirm the remaining budget before designing around one.

**Member flagging enabled:** [ ] yes  [ ] no    **Reviewed within:** ____ hours    **Owner:** ____________

**Escalation to support:**

| Trigger condition | Action | Queue | Owner | SLA |
|---|---|---|---|---|
| Question with no comment after ____ hours | | | | |
| Member flags a product defect | | | | |
| Post naming a security issue | | | | |

Question-to-Case enabled (required for `Case.FeedItemId`): [ ] yes  [ ] no
Org rule/keyword budget confirmed with: ____________

---

## 14. Quarterly Review

**Reviewer:** ____________    **Cadence:** ____________    **Next date:** ____________

**Levers this reviewer may move without re-approval:**
- [ ] Reputation `lowerThreshold` values
- [ ] `pointsRule` weights
- [ ] Managed-topic list membership
- [ ] Content calendar composition
- [ ] Other: ____________

---

## 15. Notes and Deviations

Record any deviations from the standard engagement model and the rationale:
