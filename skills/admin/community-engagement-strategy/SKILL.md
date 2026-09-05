---
name: community-engagement-strategy
description: "Design the engagement model for an Experience Cloud community: reputation levels, ideation, and content contribution strategy. Triggers: 'community engagement strategy', 'gamification Experience Cloud', 'reputation levels setup', 'ideation community portal', 'member recognition program'. NOT for blocking, flagging or approving what members post — use admin/experience-cloud-moderation. NOT for measuring logins, page views or engagement after launch — use data/community-analytics-data. Also covers: the Network reputation elements that carry the ladder (enableReputation, reputationLevels/level/label/lowerThreshold, reputationPointsRules/pointsRule/eventType/points), the 16 documented reputation eventType values and their default points, ManagedTopics / ManagedTopic (Navigational vs Featured, position 0-24), NetworkMember.ReputationPoints seeding, and why FeedItem cannot carry the engagement dashboard."
category: admin
salesforce-version: "Spring '25+"
triggers:
  - "community engagement strategy"
  - "gamification Experience Cloud"
  - "reputation levels setup"
  - "ideation community portal"
  - "member recognition program"
  - "our community launched six months ago and nobody posts"
  - "design a reputation ladder for a customer community"
  - "what point values should we give community actions"
  - "reputation points did not appear for members who were already active"
  - "reputation level labels came back as Level 1 Level 2 after deploy"
  - "seed reputation points for our known top contributors"
  - "how do we measure whether the community is actually working"
  - "count best answers per member in an Experience Cloud site"
  - "SELECT COUNT() FROM FeedItem returns an error"
  - "cannot filter FeedItem by NetworkScope to scope community metrics"
  - "how many navigational topics can an Experience Cloud site have"
  - "rename a managed topic in a community site"
  - "when should a community question be escalated to a case"
  - "write a content calendar for a customer community"
  - "quarterly community health review checklist"
  - "increase participation in our customer community"
well-architected-pillars:
  - Operational Excellence
tags:
  - experience-cloud
  - community-engagement
  - reputation
  - ideation
  - gamification
  - managed-topics
  - community-metrics
inputs:
  - Experience Cloud site type (Customer, Partner, or Employee community)
  - Target audience segments and their primary goals on the site
  - Desired member behaviors to incentivize (e.g., answering questions, posting ideas, commenting)
  - Existing content plan or content ownership map (if available)
  - "Whether Reputation is already on for the site, and how long members have been active without it"
  - "The managed-topic list the site already navigates by (or the intent to create one)"
outputs:
  - "Reputation ladder: named levels with monotonic, unique lowerThreshold values and a weighted eventType point table"
  - "Deployable Network reputation fragment (enableReputation, reputationLevels, reputationPointsRules) matching the ladder"
  - "Ideation setup checklist: zone, Ideas settings, theme grouping, status workflow, and vote moderation settings"
  - "Content contribution strategy: member role definitions, journey map, content ownership assignments"
  - "Content calendar keyed to the site's managed-topic list, with an owner per item"
  - "Engagement metric set with a queryable SOQL source and a target per goal"
  - "Moderation and escalation-to-support policy naming the escalation queue"
  - Engagement launch checklist covering all three pillars
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Community Engagement Strategy

Use this skill when designing the engagement model for an Experience Cloud community site — covering reputation gamification, ideation workflow, and content contribution strategy. This skill does NOT configure moderation rules, guest user access, or the technical site template.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Experience Cloud site is already provisioned. `Network` is the metadata that carries reputation, and `ManagedTopics` deploys only against an existing site: "The related Experience Cloud site must exist before you deploy managed topics." (Metadata API Developer Guide, ManagedTopics, `api_meta.txt` L86723-L86724).
- Clarify which member behaviors the community sponsor most wants to incentivize. There are 16 documented `eventType` values and each has a platform default point value; the strategy's job is to decide which of them deviate from the default and why (`api_meta.txt` L91675-L91711).
- Establish which reputation system is in scope. `Network` reputation (Experience Cloud site) and Ideas-zone reputation (`IdeaReputationLevel`) are separate systems with separate storage and separate rules — see `references/gotchas.md` Gotcha 6.
- Understand whether content ownership has been decided: who is responsible for each content area (product, support, marketing). Undefined ownership is the most common cause of stale community content after launch.
- Note that reputation points are **not retroactive**: members who acted before Reputation was enabled will not receive points for historical activity. UNVERIFIED (2026-09-05): not stated in the Metadata API or Object Reference guides; retained as practitioner experience. The remedy *is* grounded — `NetworkMember.ReputationPoints` is updateable and "You can directly update reputation points for a member via the Salesforce API" (`object_reference.txt` L188591-L188592).

---

## Questions to Ask Before Configuring

Ask these before anyone opens Experience Workspaces. Each one closes a gotcha; an LLM that skips them ships a ladder that deploys cleanly and rewards nothing anyone cares about.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which one member behaviour, if it doubled, would make this community worth funding?" | The 16 `eventType` values ship with defaults that already reward posting (+1) far below answering well (`FeedItemYourAnswerMarkedBest` +20). If you cannot name the behaviour, you cannot justify deviating from the defaults (`api_meta.txt` L91694-L91711) | The weighted `reputationPointsRules` block, with a written reason for every rule that differs from the platform default |
| "Has anyone been active on this site already, and for how long?" | Points start accruing when Reputation is switched on. A site with two years of history gets a leaderboard that inverts the real contribution order on day one | A decision to seed `NetworkMember.ReputationPoints`, with the seeding query, the members, and who signs it off |
| "What number tells us in 90 days whether this worked, and can we query it today?" | `FeedItem` "doesn't support aggregate functions in queries" and "You can't filter a feed item on the `NetworkScope` field" (`object_reference.txt` L136523, L136183). Half the metrics people ask for cannot be produced the way they assume | The metric set with a queryable source per row — `NetworkMember`, `ChatterActivity`, `Case.FeedItemId`, `Topic.TalkingAbout` — and a pre-launch baseline reading |
| "What is this site's topic list, and who owns each topic?" | Managed topics are the navigation and the content calendar's index. `position` takes "a number between 0 and 24. (The maximum amount of navigational or featured topics is 25.)" (`api_meta.txt` L86768-L86775) | A topic list inside the cap, split Navigational vs Featured, each with a content owner |
| "When a member's question is not answered by the community, who picks it up and where does it land?" | Without a named queue and a trigger condition, unanswered questions are the failure mode that no reputation ladder repairs. `Case.FeedItemId` is the grounded link back to the question, available "only ... where Question-to-Case is enabled" (`object_reference.txt` L62410-L62417) | The escalation policy: trigger condition, named queue, owner, and the SOQL that counts escalations |
| "How much of the org's moderation budget is already spent by other sites?" | Keyword lists and moderation rules are capped at 30 each **per org, not per site** (`api_meta.txt` L82185, L89486). A recognition programme that assumes a rate rule will freeze point-farmers can find the budget gone | A rule count from the platform owner, and the moderation pointer handed to `admin/experience-cloud-moderation` before design closes |
| "Who runs the quarterly review, and what are they allowed to change?" | Thresholds calibrated at launch stop discriminating as average activity rises; nobody re-tunes a ladder without a standing mandate | A named reviewer, a cadence, and the list of levers (thresholds, point weights, topic list) they may move without re-approval |

What a proper configuration adds over just turning Reputation on: every rewarded behaviour traces to a goal, every goal has a metric with SOQL that actually runs, the ladder that deploys is the ladder that was designed, and the unanswered question has somewhere to go.

---

## Core Concepts

### Reputation on an Experience Cloud site (`Network`)

Site reputation is three metadata elements on the `Network` type, and nothing else:

| Element | Type | What it does |
|---|---|---|
| `enableReputation` | boolean | "Determines if reputation is calculated and displayed for members." If on and no levels or rules are supplied, "the default values are used" (`api_meta.txt` L90863-L90873) |
| `reputationLevels` | `ReputationLevelDefinitions` → `level[]` | Each `level` carries an optional `label`, a required `lowerThreshold` (double), and optional `branding` (`api_meta.txt` L91608-L91651) |
| `reputationPointsRules` | `ReputationPointsRules` → `pointsRule[]` | Each rule is an `eventType` + `points` pair (`api_meta.txt` L91654-L91711) |

Two behaviours that decide the design:

- **`label` is optional and the fallback is ugly.** "If not specified, one of the 10 defaults is used" — `Level 1` through `Level 10` (`api_meta.txt` L91633-L91644). Generic labels are what the platform gives you when the strategy step was skipped.
- **The application computes the top of each band.** `lowerThreshold` is "the lower value in the range for this reputation level"; `ReputationLevel` "Represents the name and lower value of the reputation level. The application calculates the upper value." (`api_meta.txt` L91623, L91647-L91651). You never author an upper bound, which is why an out-of-order or duplicated threshold produces a silently wrong ladder rather than a deploy error.

The 16 documented `eventType` values, with their platform defaults (`api_meta.txt` L91675-L91711):

| eventType | Default | eventType | Default |
|---|---|---|---|
| `FeedItemWriteAPost` | +1 | `FeedItemShareAPost` | +1 |
| `FeedItemWriteAComment` | +1 | `FeedItemSomeoneSharesYourPost` | +5 |
| `FeedItemReceiveAComment` | +5 | `FeedItemPostAQuestion` | +1 |
| `FeedItemLikeSomething` | +1 | `FeedItemAnswerAQuestion` | +5 |
| `FeedItemReceiveALike` | +5 | `FeedItemReceiveAnAnswer` | +5 |
| `FeedItemMentionSomeone` | +1 | `FeedItemMarkAnswerAsBest` | +5 |
| `FeedItemSomeoneMentionsYou` | +5 | `FeedItemYourAnswerMarkedBest` | +20 |
| `FeedItemEndorseSomeoneForKnowledgeOnATopic` | +5 | `FeedItemEndorsedForKnowledgeOnATopic` | +20 |

The two endorsement events depend on `Network.enableKnowledgeable`, which "Determines if members can see who's knowledgeable on topics and endorse people for their knowledge on a topic" (`api_meta.txt` L90848-L90851). Weighting them without enabling the setting rewards an action nobody can perform.

Member point totals live on `NetworkMember.ReputationPoints` (double, `Filter, Sort, Update`) — one row per member per site (`object_reference.txt` L188569-L188576). The `ReputationLevel` sObject (`Label`, `LevelNumber`, `ParentId`, `Threshold`) is read-only: its supported calls are `describeSObjects(), query(), retrieve()` (`object_reference.txt` L247325-L247382). Read levels from the API; write points.

### Topics are the engagement surface, not a tagging afterthought

An engagement strategy without a topic list has nowhere to put a content calendar. `ManagedTopics` is one file per site (`SiteNameA.managedTopics`) holding `ManagedTopic` entries (`api_meta.txt` L86721-L86779):

| Field | Notes |
|---|---|
| `name` | The topic name |
| `managedTopicType` | "Navigational" or "Featured" |
| `topicDescription` | "accessible only via the API; there is no corollary in the user interface" |
| `parentName` | "Only navigational topics support parent-child relationships" |
| `position` | "a number between 0 and 24. (The maximum amount of navigational or featured topics is 25.)" |

One discrepancy to know: the `ManagedTopics` metadata documents `managedTopicType` as "Navigational" or "Featured" only (`api_meta.txt` L86747), while the `Topic` sObject's `ManagedTopicType` field lists a third value, `Content`, from API 44.0 onward (`object_reference.txt` L289110-L289127). Author the metadata file with the two the metadata guide documents.

Three `Network` switches shape how topics behave for members: `enableTopicSuggestions` ("Enables topic suggestions when users write posts"), `enableTopicAssignmentRules` (rules that "automatically assign topics to articles in a site ... admins set up rules to map topics to Salesforce Knowledge data categories"), and `enableTalkingAboutStats` (`api_meta.txt` L90893-L90900, L90877-L90882). The last one surfaces `Topic.TalkingAbout` — "Number of people talking about the topic over the last two months" (`object_reference.txt` L289145-L289152), which is the only per-topic engagement number the platform hands you without a build.

### Ideation (Ideas)

The Ideas feature uses the standard **Idea** and **IdeaTheme** objects (`object_reference.txt` L155401, L156037). Its shape is different from what most engagement plans assume:

1. Ideas is an **org-level** setting, not a per-site one: `IdeasSettings` is stored as `Ideas.settings` with `enableIdeas`, `enableIdeaThemes`, `enableIdeasReputation` and `halfLife` (`api_meta.txt` L118310-L118336).
2. The container is the **zone**, not the theme. `Idea.CommunityId` is "The zone ID associated with the idea. Once you create an idea, you can't change the zone ID" (`object_reference.txt` L155493-L155499), while `Idea.IdeaThemeID` is Nillable (L155551-L155557). A theme is "an invitation to zone members to submit ideas that are focused on a specific topic" (L156038-L156039) — a grouping, not a gate.
3. `Idea.Status` is a "Customizable picklist of values used to specify the status of an idea" (`object_reference.txt` L155685) — the guide names no standard values, so the status set is a design decision you must write down.
4. `halfLife` "Indicates how quickly old ideas drop in ranking on the Popular Ideas subtab ... A shorter half-life moves older ideas down the page faster" (`api_meta.txt` L118360-L118365). It is org-wide and it silently governs what members see as "popular".
5. Ideas-zone reputation is its own system: `IdeaReputationLevel`, "You can create up to 25 levels per zone", `Name` unique and max 50 chars, `Threshold` "must be unique within the zone ... and must be greater than or equal to zero" (`object_reference.txt` L155990-L156032).

The Ideas feature is distinct from Q&A. A community question is a `FeedItem` of `Type` `QuestionPost` (`object_reference.txt` L136368) whose accepted answer is `FeedItem.BestCommentId`, "The ID of the comment marked as best answer on a question post" (L135862-L135869). Q&A is for support deflection; ideation is for structured product or service input.

### Content Contribution Strategy

Content contribution strategy defines **who posts what, and when**. It must be decided before launch. The three elements are:

1. **Member roles**: Define role tiers — e.g., Lurker (read-only), Contributor (can post), Power User (can post + moderate peer content), Community Manager (full rights). These map to profile + permission set assignments, not to Reputation levels. Nothing on the `ReputationLevel` sObject grants access.
2. **Content ownership**: Each content area (how-to articles, product announcements, FAQs, idea themes) needs a named internal owner responsible for keeping it current. Without this, content ages out and engagement drops.
3. **Member journey mapping**: New members need an onboarding path — a welcome post, a "Start Here" article, and a low-barrier first action (e.g., "introduce yourself" post). Without a designed first-touch journey, activation rates stay low.

### Measurement, and what the platform will not let you count

Engagement metrics have to be designed against the query surface, not against a wish list:

| Want to know | Query it here | Constraint |
|---|---|---|
| Active members, last-touch recency | `NetworkMember` — `ReputationPoints`, `LastChatterActivityDate` ("The last time the member posted or commented in the Experience Cloud site") | Scoped by `NetworkId`; supports aggregates (`object_reference.txt` L188353-L188359) |
| Per-member post / comment / like-received volume | `ChatterActivity` — `PostCount`, `CommentCount`, `CommentReceivedCount`, `LikeReceivedCount`, `InfluenceRawRank`, `NetworkId` | "To query ChatterActivity, you must provide the ParentId" — no org-wide sweep (`object_reference.txt` L66386-L66388) |
| Questions, best answers, closed threads | `FeedItem` — `Type = 'QuestionPost'`, `BestCommentId`, `IsClosed` | No aggregate functions; no filtering on `NetworkScope`; direct query needs View All Data (`object_reference.txt` L136523, L136183, L136504) |
| Topic reach | `Topic.TalkingAbout`, `TopicAssignment` | `TopicAssignment` SOQL wants `LIMIT 1100` or a `=` filter on Id/Entity (`object_reference.txt` L289283-L289287) |
| Escalation volume and time-to-case | `Case.FeedItemId` | Only where Question-to-Case is enabled; `Case` does support aggregates (`object_reference.txt` L62410-L62417) |
| Moderation load | `NetworkActivityAudit` — `Action`, `EntityId`, `EntityCreatedById` | Audit of moderation actions, API 30.0+ (`object_reference.txt` L187427-L187470) |

`references/worked-examples.md` §6 carries the runnable version of every row.

---

## Common Patterns

### Quality-weighted reputation ladder for a peer-support community

**When to use:** The community's primary goal is peer-to-peer support deflection. Members answer each other's questions, and the business wants to surface trusted advisors.

**How it works:**
1. Set `Network.enableReputation` to `true` and author `reputationLevels` explicitly — leaving `label` off gets you `Level 1`…`Level 10`.
2. Give each level a domain-meaningful `label` and a `lowerThreshold` that is strictly greater than the level before it. The guide's own sample ladder is seven levels at 0 / 51 / 101 / 151 / 201 / 251 / 301 (`api_meta.txt` L91877-L91943) — start from a real spacing curve, not round numbers.
3. Override only the `eventType` rules you have a reason to move. `FeedItemYourAnswerMarkedBest` already defaults to +20 against `FeedItemWriteAPost` at +1; if answering is the goal, the platform default is already close and the interesting decision is whether to *lower* posting further.
4. Run `scripts/check_community_engagement_strategy.py` over both the strategy YAML and the `Network` file so the deployed ladder and the designed ladder cannot drift.

**Why not a flat point system:** A flat system (one action type = one point) rewards volume of posts with no quality signal. Weighting best-answer actions higher encourages members to provide complete, useful answers rather than short replies that farm points.

### Topic-indexed content calendar

**When to use:** A community is technically live and quiet, and the content plan is a list of blog-style ideas with no anchor in the site's navigation.

**How it works:**
1. Take the site's `ManagedTopics` file as the index. Every calendar item names one topic that exists in that file.
2. Split the topic list deliberately: Navigational topics carry the menu and support parent/child nesting; Featured topics carry the home-page thumbnails and do not nest.
3. Keep the combined list inside the documented 25 and leave headroom — `position` accepts 0-24, so a full list has no room for the next quarter's topic.
4. Give each calendar item an owner, a target date, and one of the metric rows from `references/worked-examples.md` §6 that it is supposed to move.
5. Where a topic maps to published Knowledge, consider `enableTopicAssignmentRules` and hand the data-category mapping to `admin/knowledge-base-administration`.

**Why topics rather than a content list:** A calendar item with no topic has no navigation path to it, no `TopicAssignment` row, and therefore no `Topic.TalkingAbout` reading afterwards. The topic is what makes the item measurable.

### Product ideation portal with a defined status workflow

**When to use:** A product or operations team wants structured customer input through a community channel, with clear feedback on what happens to submitted ideas.

**How it works:**
1. Confirm the org-level `IdeasSettings` (`enableIdeas`, and `enableIdeaThemes` if themes are used) and the zone the site's ideas belong to.
2. Decide and document the `Idea.Status` picklist values — the platform ships a customizable picklist and no opinion.
3. Create themes per product area for grouping, knowing that ideas can exist without one.
4. Assign an internal product manager as the owner of each theme; their job is to update statuses on a stated cadence.
5. Announce status updates in the idea's comment thread so voters see progress.
6. Check `halfLife` before blaming the ranking: it is an org-wide dial on how fast old ideas fall down Popular Ideas.

**Why an explicit status workflow matters:** Ideas with no status movement for 90+ days communicate to members that feedback goes unread. This is the top cause of ideation disengagement. An "Under Review" update — even without a decision — signals responsiveness.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Community goal is support deflection | Weight the answer-side `eventType` rules and leave posting at or below the default | `FeedItemYourAnswerMarkedBest` (+20) vs `FeedItemWriteAPost` (+1) already encodes quality over volume |
| Community goal is product input | Prioritize ideation with a written `Idea.Status` set and named theme owners | The status picklist is customizable with no standard values; undocumented means undecided |
| Community goal is content publishing (help center) | Prioritize the contribution strategy: content owners and author roles before contribution rights | Prevents content sprawl and outdated articles |
| The site has an active member base and Reputation is off | Design the ladder *and* the `NetworkMember.ReputationPoints` seeding pass together | Points accrue forward only; the field is updateable via the API |
| Someone asks for "posts per member per month, all members" | Redesign the metric onto `NetworkMember` / `ChatterActivity` per member | `FeedItem` supports no aggregates and cannot be filtered by `NetworkScope` |
| Org has multiple Experience Cloud sites | Configure reputation per site; `NetworkMember` is per member per `NetworkId` | Levels, rules and point totals all hang off one site's `Network` |
| The topic list is already at 20+ entries | Retire before adding, and prefer Featured for campaign topics | Navigational and featured topics share a documented maximum of 25 |
| Someone proposes auto-promoting high-tier members to moderator | Route the permission decision to `admin/experience-cloud-moderation` | `ReputationLevel` is query-only and carries no permission field |

---

## Recommended Workflow

1. **Fill in the Questions table above with the sponsor, then start `templates/community-engagement-strategy-template.md`.** Sections 1-2 (site, pillars in scope) and section 12 (metrics) are the parts that decide everything downstream; the ladder is easier than the goals.
2. **Draft the ladder against `references/worked-examples.md` §3.** Name every level, set `lowerThreshold` strictly increasing, and write the reason beside each `eventType` whose `points` differ from the platform default in `## Core Concepts`. Confirm `enableKnowledgeable` before weighting either endorsement event.
3. **Index the content calendar on the site's managed topics** (`references/worked-examples.md` §4). One topic per calendar item, one owner per item, list length inside 25.
4. **Write the metric set and the escalation policy before configuring anything** (`references/worked-examples.md` §6 and §5). Every goal gets one metric, one SOQL source, and a target. Every metric must survive the constraints in the measurement table above — that is the step that catches `SELECT COUNT() FROM FeedItem`.
5. **Emit the engagement-strategy YAML and the `Network` reputation fragment** using `references/worked-examples.md` §8 and §7 as the shape, and cross-check the moderation half against `admin/experience-cloud-moderation` before assuming a rate rule is available.
6. **Run `python3 scripts/check_community_engagement_strategy.py --manifest-dir <dir>`** (or `--file <strategy.yaml> --manifest-dir <metadata dir>`). It fails on non-monotonic or duplicated thresholds, calendar items pointing at topics that do not exist, goals with no queryable metric, a moderation policy with no escalation queue, and a `Network` file whose levels do not match the ladder.
7. **Book the quarterly review** using `references/worked-examples.md` §9 and record the reviewer in template section 14.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every level in `reputationLevels` has an explicit `label` — no `Level N` survived to the deploy
- [ ] `lowerThreshold` values are strictly increasing and unique across the ladder
- [ ] Every `pointsRule` that differs from the platform default has a written reason
- [ ] `enableKnowledgeable` is on if either endorsement `eventType` is weighted
- [ ] `NetworkMember.ReputationPoints` seeding decision made and recorded (do it, or state why not)
- [ ] Managed-topic list is inside 25 entries, split Navigational vs Featured deliberately
- [ ] Every content-calendar item names an existing topic and a named owner
- [ ] Every engagement goal has one metric, one SOQL source that runs, and a target
- [ ] No metric depends on a `FeedItem` aggregate or a `NetworkScope` filter
- [ ] Escalation policy names a queue, a trigger condition, and an owner
- [ ] Moderation rule / keyword budget confirmed with the platform owner before design closes
- [ ] Quarterly review has a named owner, a date, and a list of levers they may move
- [ ] `scripts/check_community_engagement_strategy.py` exits 0 against the strategy YAML and the `Network` file

---

## Salesforce-Specific Gotchas

Short list; the full form of each — what happens, when, how to avoid — is in `references/gotchas.md`.

1. Points accrue forward only; an existing member base starts at zero.
2. `label` is optional, so an omitted label deploys as `Level 1`…`Level 10`.
3. Only `lowerThreshold` is authored — the platform derives the band's top.
4. `ReputationLevel` is query-only and grants no permission at any tier.
5. Ideas hang off a zone; `Idea.IdeaThemeID` is nillable, so a theme is optional.
6. Site reputation and Ideas-zone reputation are two systems with different caps.
7. `FeedItem` supports no aggregates and cannot be filtered on `NetworkScope`.
8. `ChatterActivity` cannot be queried without a `ParentId`, and lurkers have no row.
9. Renaming a `Topic` is limited to spacing and capitalization.
10. Pre-moderation makes `FeedItem.CommentCount` lag the real comment count.
11. Moderation rules and keyword lists are capped at 30 each per org, not per site.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Reputation ladder | Named levels with monotonic unique `lowerThreshold` values, plus the weighted `eventType` table and the reason for each deviation |
| `Network` reputation fragment | Deployable `enableReputation` / `reputationLevels` / `reputationPointsRules` block matching the ladder |
| Topic-indexed content calendar | Calendar items, each naming an existing managed topic, an owner, a date and the metric it moves |
| Engagement metric set | One row per goal: metric, SOQL source, baseline, target, owner |
| Health dashboard spec | The report/dashboard components each metric feeds, and their refresh cadence |
| Moderation + escalation policy | Trigger conditions, the named escalation queue, and the pointer to the moderation skill for rules |
| Content ownership map | Table mapping each content area to an internal owner, review cadence, and content type |
| Member role matrix | Table mapping member roles to the profile/permission set that backs them |
| Quarterly review checklist | Standing agenda, named reviewer, and the levers they may move without re-approval |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | Filling in the strategy — Acme's customer community six months after launch, worked end to end: personas and goals, the topic-indexed content calendar, the recognition ladder with its `Network` XML, the moderation and escalation policy, six metrics with runnable SOQL, the dashboard spec, the quarterly review, and the YAML the checker lints |
| `references/gotchas.md` | The ladder deployed but ranks people wrongly, a metric query errors, a topic will not rename, or reputation and permissions were assumed to be linked — eleven platform behaviours behind those symptoms |
| `references/examples.md` | Working a real engagement problem end to end: the point-farming leaderboard, the black-hole ideation portal, and the unseeded-launch anti-pattern |
| `references/llm-anti-patterns.md` | Reviewing AI-generated community advice, especially generic tier names and metric plans built on `SELECT COUNT() FROM FeedItem` |
| `references/well-architected.md` | Framing the ladder-depth, ideation-breadth and open-contribution tradeoffs, and locating the source behind each claim |
| `templates/community-engagement-strategy-template.md` | Workflow step 1, and again at review time as the one-page record of every decision |
| `scripts/check_community_engagement_strategy.py` | Workflow step 6, before the strategy leaves your hands and again before the `Network` deploys |

---

## Related Skills

- `admin/experience-cloud-moderation` — Owns `KeywordList` and `ModerationRule`, the moderation queue, and the `Moderate Experiences Feeds` permission behind the escalation policy this skill writes.
- `admin/experience-cloud-site-setup` — Owns the `Network`, `CustomSite`, `NavigationMenu` and `ExperienceBundle` deploy set that this skill's reputation fragment lands inside.
- `admin/self-service-design` — Owns the deflection journeys, article visibility matrix and case exposure model that the peer-support layer sits on top of.
- `admin/knowledge-base-administration` — Owns data categories, record types and the publishing workflow that `enableTopicAssignmentRules` maps topics onto.
- `admin/chatter-group-governance` — Owns the group lifecycle, visibility and ownership-transfer policy behind any group-based contribution model.
- `admin/chatter-notification-tuning` — Owns the digest and notification volume that decides whether recognition is actually seen.
- `data/community-analytics-data` — Owns login, page-view and post-launch engagement reporting once these metrics have a baseline.
