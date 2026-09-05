# Worked Examples — Community Engagement Strategy

One scenario, worked end to end. Copy the fenced blocks and change the names.

**Scenario.** Acme Software launched `acme-community` (Customer Community, LWR) six months ago. 4,100 members are enrolled; roughly 180 post in a given month. Support case volume has not moved. Reputation was never switched on. There are eleven managed topics, three of which nobody has posted under since week two. Nobody owns the content calendar. The support lead wants to know whether to keep funding it.

The strategy below is what "an engagement strategy, filled in" looks like. It ends in §8 as a single YAML artefact that `scripts/check_community_engagement_strategy.py` lints, and in §7 as the `Network` fragment that deploys.

---

## 1. Personas and engagement goals

| Persona | Who they are | What they come for | Engagement goal | Goal id |
|---|---|---|---|---|
| Evaluator | Pre-sales, unauthenticated | "Does this product do X" | Not a goal for this site — route to marketing | — |
| New admin (0-90 days) | Just bought, configuring | Setup answers, fast | 60% of first questions answered by a peer within 24h | `g-first-response` |
| Working admin | Day-to-day user | Specific how-tos, workarounds | Grow monthly active posters from 180 to 300 | `g-active-members` |
| Power user | Answers other people's questions | Recognition, early access | 25 members with 5+ best answers per quarter | `g-answer-depth` |
| Product manager (internal) | Owns a topic | Signal on what to build | Every idea gets a status change within 30 days | `g-idea-throughput` |
| Support agent (internal) | Picks up what the community drops | Fewer duplicate cases | Escalate unanswered questions within 48h, no silent drops | `g-escalation` |

Personas that are not goals are as important as the ones that are. Evaluator traffic is why the site's page views look healthy while its post count does not.

---

## 2. What is already true (baseline, taken before anything changes)

Take the baseline **before** the first change. A number read after launch is not a baseline.

```sql
-- Enrolled members, and how many have ever posted or commented in this site.
-- NetworkMember is one row per member per site; LastChatterActivityDate is
-- "The last time the member posted or commented in the Experience Cloud site".
SELECT COUNT(Id) enrolled
FROM NetworkMember
WHERE NetworkId = '0DB5g000000XXXXGAW'

SELECT COUNT(Id) ever_active
FROM NetworkMember
WHERE NetworkId = '0DB5g000000XXXXGAW'
  AND LastChatterActivityDate != NULL

SELECT COUNT(Id) active_30d
FROM NetworkMember
WHERE NetworkId = '0DB5g000000XXXXGAW'
  AND LastChatterActivityDate = LAST_N_DAYS:30
```

```sql
-- Topic reach. Topic.TalkingAbout is "Number of people talking about the topic
-- over the last two months" — the only per-topic engagement figure the platform
-- gives you without a build.
SELECT Name, ManagedTopicType, TalkingAbout
FROM Topic
WHERE NetworkId = '0DB5g000000XXXXGAW'
ORDER BY TalkingAbout DESC
```

Acme's reading: 4,100 enrolled, 1,240 ever active, 181 active in 30 days, and four topics with `TalkingAbout = 0`. That is the number the quarterly review in §9 will be measured against.

---

## 3. The recognition ladder

Acme's goal ranking is `g-answer-depth` > `g-first-response` > `g-active-members`. That ordering, not taste, decides the point weights.

**Levels.** Seven, not ten. `lowerThreshold` is the only bound you author — "The application calculates the upper value" — so the values must be strictly increasing and unique, and there is no top level to close off.

| Level | `label` | `lowerThreshold` | Reached by (roughly) |
|---|---|---|---|
| 1 | Newcomer | 0 | Enrolment |
| 2 | Asking Around | 60 | ~10 questions, or 3 answered questions |
| 3 | Contributor | 200 | First accepted answer plus regular commenting |
| 4 | Regular | 600 | ~20 accepted answers' worth of activity |
| 5 | Trusted Advisor | 1500 | Sustained answering over two quarters |
| 6 | Acme Expert | 4000 | Top ~1% of the member base |
| 7 | Community Legend | 10000 | Awarded in practice, not in theory |

**Point weights.** Only four rules deviate from the platform default; each deviation carries its reason. The defaults are already answer-weighted (`FeedItemYourAnswerMarkedBest` +20 against `FeedItemWriteAPost` +1), so most of the table is deliberately left alone.

| `eventType` | Default | Acme | Reason for deviating |
|---|---|---|---|
| `FeedItemWriteAPost` | +1 | 1 | — |
| `FeedItemWriteAComment` | +1 | 1 | — |
| `FeedItemReceiveAComment` | +5 | **2** | Receiving a comment is not an achievement; at +5 it rewarded whoever posted the most controversial thing |
| `FeedItemLikeSomething` | +1 | **0** | Zero-cost action; at +1 it is the cheapest farm on the board |
| `FeedItemReceiveALike` | +5 | 5 | — |
| `FeedItemMentionSomeone` | +1 | 1 | — |
| `FeedItemSomeoneMentionsYou` | +5 | 5 | — |
| `FeedItemShareAPost` | +1 | 1 | — |
| `FeedItemSomeoneSharesYourPost` | +5 | 5 | — |
| `FeedItemPostAQuestion` | +1 | 1 | — |
| `FeedItemAnswerAQuestion` | +5 | 5 | — |
| `FeedItemReceiveAnAnswer` | +5 | **2** | Asking is already rewarded once; paying twice for one question inflates askers over answerers |
| `FeedItemMarkAnswerAsBest` | +5 | 5 | Keeps askers closing their own threads, which `g-first-response` depends on |
| `FeedItemYourAnswerMarkedBest` | +20 | **30** | The single behaviour `g-answer-depth` exists to buy; widened against posting on purpose |
| `FeedItemEndorseSomeoneForKnowledgeOnATopic` | +5 | 5 | Requires `enableKnowledgeable` — confirmed on for this site |
| `FeedItemEndorsedForKnowledgeOnATopic` | +20 | 20 | Same prerequisite |

**Seeding.** 1,240 members were active before Reputation existed. Acme seeds the top 40 by historical best answers rather than letting a two-year contributor sit at Newcomer:

```sql
-- Read what each candidate already earned. ChatterActivity must be queried one
-- ParentId at a time: "To query ChatterActivity, you must provide the ParentId."
SELECT ParentId, PostCount, CommentCount, CommentReceivedCount,
       LikeReceivedCount, InfluenceRawRank
FROM ChatterActivity
WHERE ParentId = '0055g00000XXXXXAAI'
  AND NetworkId = '0DB5g000000XXXXGAW'
```

```bash
# Then write the seeded totals. NetworkMember.ReputationPoints is updateable —
# "You can directly update reputation points for a member via the Salesforce API."
# Seed file: Id,ReputationPoints  (Id = the NetworkMember row, not the User)
sf data update bulk \
  --sobject NetworkMember \
  --file seed-reputation-points.csv \
  --target-org acme-prod \
  --wait 10
```

Sign-off for the seeding pass sits with the community manager, and the seeded members are listed by name in the strategy YAML (§8) so the leaderboard on day one is explainable to everyone else.

---

## 4. The content calendar, indexed on managed topics

Every calendar item names a topic that exists in `acme-community.managedTopics`. An item with no topic has no navigation path, no `TopicAssignment` row, and no `TalkingAbout` reading afterwards.

The topic list first — kept at nine of a documented maximum of 25, deliberately, so next quarter has room:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ManagedTopics>
    <ManagedTopic>
        <name>Getting Started</name>
        <managedTopicType>Navigational</managedTopicType>
        <topicDescription>First-90-days setup, provisioning and licensing</topicDescription>
        <parentName></parentName>
        <position>0</position>
    </ManagedTopic>
    <ManagedTopic>
        <name>Automation</name>
        <managedTopicType>Navigational</managedTopicType>
        <topicDescription>Flow, triggers and scheduled jobs</topicDescription>
        <parentName></parentName>
        <position>1</position>
    </ManagedTopic>
    <ManagedTopic>
        <name>Flow Errors</name>
        <managedTopicType>Navigational</managedTopicType>
        <topicDescription>Fault paths and common runtime failures</topicDescription>
        <parentName>Automation</parentName>
        <position>0</position>
    </ManagedTopic>
    <ManagedTopic>
        <name>Bulk Data</name>
        <managedTopicType>Navigational</managedTopicType>
        <topicDescription>Loads, exports and migration questions</topicDescription>
        <parentName></parentName>
        <position>2</position>
    </ManagedTopic>
    <ManagedTopic>
        <name>Integrations</name>
        <managedTopicType>Navigational</managedTopicType>
        <topicDescription>APIs, middleware and outbound connections</topicDescription>
        <parentName></parentName>
        <position>3</position>
    </ManagedTopic>
    <ManagedTopic>
        <name>Reporting</name>
        <managedTopicType>Navigational</managedTopicType>
        <topicDescription>Reports, dashboards and analytics questions</topicDescription>
        <parentName></parentName>
        <position>4</position>
    </ManagedTopic>
    <ManagedTopic>
        <name>Release Readiness</name>
        <managedTopicType>Featured</managedTopicType>
        <topicDescription>Seasonal release prep — rotated each release</topicDescription>
        <parentName></parentName>
        <position>0</position>
    </ManagedTopic>
    <ManagedTopic>
        <name>Ask the Product Team</name>
        <managedTopicType>Featured</managedTopicType>
        <topicDescription>Monthly AMA and idea drives</topicDescription>
        <parentName></parentName>
        <position>1</position>
    </ManagedTopic>
    <ManagedTopic>
        <name>Member Spotlight</name>
        <managedTopicType>Featured</managedTopicType>
        <topicDescription>Recognition posts for the reputation programme</topicDescription>
        <parentName></parentName>
        <position>2</position>
    </ManagedTopic>
</ManagedTopics>
```

How to read it:

- `Flow Errors` nests under `Automation` because `parentName` works only for navigational topics — "Only navigational topics support parent-child relationships."
- The three Featured topics carry the home-page thumbnails; `position` orders those thumbnails, not the menu.
- `topicDescription` is API-only — "This field is accessible only via the API; there is no corollary in the user interface" — so it is a note to the next admin, never member-facing copy.
- Nine entries against a documented ceiling of 25 (`position` accepts 0-24). Retire before adding.

Now the quarter's calendar. Every row has an owner, a topic from the file above, and the goal it is meant to move:

```markdown
| Week | Item | Type | Topic | Owner | Goal it moves |
|---|---|---|---|---|---|
| W1  | "Winter release: what breaks" walkthrough | Article | Release Readiness | R. Okafor (Product Marketing) | g-active-members |
| W2  | Weekly unanswered-question sweep | Ritual | Getting Started | J. Muir (Community Manager) | g-first-response |
| W3  | "Five Flow fault paths you are missing" | Article | Flow Errors | S. Devi (Solution Engineer) | g-answer-depth |
| W4  | Member Spotlight: top 3 answerers of the month | Post | Member Spotlight | J. Muir (Community Manager) | g-answer-depth |
| W5  | Bulk API 2.0 office hours thread | Event thread | Bulk Data | T. Alvarez (Support Lead) | g-first-response |
| W6  | AMA: integrations roadmap | Event thread | Ask the Product Team | P. Chen (PM, Integrations) | g-idea-throughput |
| W7  | "Reporting on community answers" how-to | Article | Reporting | R. Okafor (Product Marketing) | g-active-members |
| W8  | Idea drive: what should we build next | Post | Ask the Product Team | P. Chen (PM, Integrations) | g-idea-throughput |
| W9  | Weekly unanswered-question sweep | Ritual | Getting Started | J. Muir (Community Manager) | g-first-response |
| W10 | Member Spotlight: quarter's Trusted Advisors | Post | Member Spotlight | J. Muir (Community Manager) | g-answer-depth |
| W11 | Topic retirement review (drop TalkingAbout = 0) | Ritual | Getting Started | J. Muir (Community Manager) | g-active-members |
| W12 | Quarterly review (§9) | Ritual | Getting Started | T. Alvarez (Support Lead) | all |
```

Two rows are rituals rather than content. A calendar made only of articles is a publishing plan, not an engagement plan.

---

## 5. Moderation and escalation-to-support policy

This skill writes the policy. `admin/experience-cloud-moderation` owns the `KeywordList` and `ModerationRule` metadata that enforces the automated half, and the `Moderate Experiences Feeds` permission behind the queue. Check the org's remaining budget with that skill's owner before assuming a rule is available: rules and keyword lists are capped at **30 each per org, not per site**.

```yaml
moderation_policy:
  member_flagging:
    enabled: true                       # Network.allowMembersToFlag — "Flagged items are
                                        # sent to a moderator for review"
    reviewed_within_hours: 24
    owner: "J. Muir (Community Manager)"
  automated_rules:
    owned_by: "skills/admin/experience-cloud-moderation"
    requested:
      - intent: "Block the three competitor-spam phrases from last quarter"
        rule_kind: content
      - intent: "Rate-limit a member posting more than 15 items in 10 minutes"
        rule_kind: rate                 # NetworkActivityAudit records these as
                                        # ModerationRuleFreeze / ModerationRuleNotify
    org_budget_confirmed_with: "Platform owner (org-wide cap is 30 rules and 30 keyword lists)"
  escalation_to_support:
    escalation_queue: "Community Escalations"
    queue_owner: "T. Alvarez (Support Lead)"
    triggers:
      - condition: "QuestionPost with no comment after 48 business hours"
        action: "Create a Case linked via Case.FeedItemId, assign to Community Escalations"
      - condition: "Member flags a post as a product defect"
        action: "Community Manager triages; escalate to Community Escalations if reproducible"
      - condition: "Any post naming a security issue"
        action: "Escalate immediately; do not reply in-thread"
    prerequisite: "Question-to-Case enabled in the org — Case.FeedItemId is 'only accessible
                   in organizations where Question-to-Case is enabled'"
    silent_drop_check: "Weekly sweep, calendar W2 / W9 — the queue is the evidence that
                        nothing was dropped, so an empty queue is a finding, not a pass"
```

The escalation queue is the part most engagement plans omit. A reputation ladder rewards answering; it does nothing at all for the questions that no member answers, and those are the ones the sponsor hears about.

---

## 6. Metrics — one per goal, each with a source that actually runs

Design the metric against the query surface. Three of the obvious formulations do not work on this platform, and §6b says why.

| Goal | Metric | SOQL source | Baseline | Target (90 days) | Owner |
|---|---|---|---|---|---|
| `g-active-members` | Members with activity in the last 30 days | `NetworkMember.LastChatterActivityDate` | 181 | 300 | J. Muir |
| `g-first-response` | Median hours to first comment on a `QuestionPost` | `FeedItem` + `FeedComment`, page-and-compute | 31h | 24h | J. Muir |
| `g-answer-depth` | Members with 5+ best answers this quarter | `FeedItem.BestCommentId` → `FeedComment.InsertedById` | 9 | 25 | S. Devi |
| `g-answer-depth` | Best-answer rate: questions with `BestCommentId` ÷ questions | `FeedItem` where `Type = 'QuestionPost'` | 22% | 40% | S. Devi |
| `g-idea-throughput` | Ideas with a status change in 30 days | `Idea.Status` + `LastModifiedDate` | 12% | 90% | P. Chen |
| `g-escalation` | Cases opened from community questions, and their age | `Case.FeedItemId` | not measured | 100% within 48h | T. Alvarez |

Runnable forms:

```sql
-- g-active-members. NetworkMember supports aggregates and is scoped by NetworkId.
SELECT COUNT(Id) active_30d
FROM NetworkMember
WHERE NetworkId = '0DB5g000000XXXXGAW'
  AND LastChatterActivityDate = LAST_N_DAYS:30
```

```sql
-- g-answer-depth, best-answer rate. FeedItem supports no aggregate functions, so
-- this is a paged read that you count client-side, not a COUNT() query.
-- Requires View All Data to query FeedItem directly (API 23.0+).
SELECT Id, CreatedDate, CreatedById, BestCommentId, IsClosed
FROM FeedItem
WHERE Type = 'QuestionPost'
  AND CreatedDate = THIS_QUARTER
ORDER BY CreatedDate DESC
```

```sql
-- g-escalation. Case DOES support aggregates, so the escalation metric is the one
-- community metric you can put straight into a report type.
SELECT COUNT(Id) escalated, Status
FROM Case
WHERE FeedItemId != NULL
  AND CreatedDate = LAST_N_DAYS:90
GROUP BY Status
```

```sql
-- Topic reach for the calendar retirement ritual (W11).
SELECT Name, ManagedTopicType, TalkingAbout
FROM Topic
WHERE NetworkId = '0DB5g000000XXXXGAW'
  AND ManagedTopicType != NULL
ORDER BY TalkingAbout ASC
```

```sql
-- Which content actually carries a topic. TopicAssignment wants a bounded query:
-- "Specify a LIMIT clause of 1,100 records or fewer" or filter on Id/Entity with "=".
SELECT TopicId, EntityId, EntityType
FROM TopicAssignment
WHERE NetworkId = '0DB5g000000XXXXGAW'
LIMIT 1100
```

### 6b. Three metrics people ask for that you must redesign

| Asked for | Why it fails | Replace with |
|---|---|---|
| `SELECT COUNT() FROM FeedItem WHERE ...` | "The FeedItem object doesn't support aggregate functions in queries" | Page the rows and count client-side, or move the metric onto `Case` / `NetworkMember` |
| "Scope community posts with `WHERE NetworkScope = :siteId`" | "You can't filter a feed item on the NetworkScope field" | Scope by the parent (`Group`/`User`) that belongs to the site, or by `NetworkMember` membership |
| "Average posts per member across all members" | `ChatterActivity` needs a `ParentId` per query, and members who never posted have no `ChatterActivity` row at all | Denominator from `NetworkMember`, numerator per-member from `ChatterActivity` in a loop or batch |

---

## 7. The deployable `Network` reputation fragment

The ladder in §3, in the shape the platform takes. This is a fragment of the site's `Network` file — merge it into the existing `acme-community.network-meta.xml`; `admin/experience-cloud-site-setup` owns the rest of that file.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Network xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableKnowledgeable>true</enableKnowledgeable>
    <enableReputation>true</enableReputation>
    <enableTalkingAboutStats>true</enableTalkingAboutStats>
    <enableTopicSuggestions>true</enableTopicSuggestions>
    <allowMembersToFlag>true</allowMembersToFlag>
    <reputationLevels>
        <level>
            <label>Newcomer</label>
            <lowerThreshold>0</lowerThreshold>
        </level>
        <level>
            <label>Asking Around</label>
            <lowerThreshold>60</lowerThreshold>
        </level>
        <level>
            <label>Contributor</label>
            <lowerThreshold>200</lowerThreshold>
        </level>
        <level>
            <label>Regular</label>
            <lowerThreshold>600</lowerThreshold>
        </level>
        <level>
            <label>Trusted Advisor</label>
            <lowerThreshold>1500</lowerThreshold>
        </level>
        <level>
            <label>Acme Expert</label>
            <lowerThreshold>4000</lowerThreshold>
        </level>
        <level>
            <label>Community Legend</label>
            <lowerThreshold>10000</lowerThreshold>
        </level>
    </reputationLevels>
    <reputationPointsRules>
        <pointsRule>
            <eventType>FeedItemWriteAPost</eventType>
            <points>1</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemWriteAComment</eventType>
            <points>1</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemReceiveAComment</eventType>
            <points>2</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemLikeSomething</eventType>
            <points>0</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemReceiveALike</eventType>
            <points>5</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemMentionSomeone</eventType>
            <points>1</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemSomeoneMentionsYou</eventType>
            <points>5</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemShareAPost</eventType>
            <points>1</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemSomeoneSharesYourPost</eventType>
            <points>5</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemPostAQuestion</eventType>
            <points>1</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemAnswerAQuestion</eventType>
            <points>5</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemReceiveAnAnswer</eventType>
            <points>2</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemMarkAnswerAsBest</eventType>
            <points>5</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemYourAnswerMarkedBest</eventType>
            <points>30</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemEndorseSomeoneForKnowledgeOnATopic</eventType>
            <points>5</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemEndorsedForKnowledgeOnATopic</eventType>
            <points>20</points>
        </pointsRule>
    </reputationPointsRules>
</Network>
```

How to read it:

- Every `level` has an explicit `label`. Omit it and the platform substitutes one of ten defaults, `Level 1` through `Level 10` — that is where generic ladders come from, not from a lazy admin.
- Only `lowerThreshold` appears. There is no upper bound element; the application derives it, so a duplicated or out-of-order threshold produces a wrong ladder rather than a deploy error. The checker in `scripts/` is what catches that.
- `points` of `0` is a legitimate value and the cleanest way to switch an event off without argument later about whether it was forgotten.
- `enableKnowledgeable` is in the fragment on purpose: the two endorsement `eventType` rules reward an action that does not exist without it.
- The fragment omits `site` and `status`, which the full `Network` file requires — this is a merge, not a standalone deploy.

`package.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>acme-community</members>
        <name>Network</name>
    </types>
    <types>
        <members>acme-community</members>
        <name>ManagedTopics</name>
    </types>
    <version>62.0</version>
</Package>
```

Retrieve, merge, deploy:

```bash
# Retrieve first — never author a Network file from scratch; it carries dozens of
# settings this skill does not own.
sf project retrieve start --manifest package.xml --target-org acme-uat

# Merge the reputation fragment into force-app/main/default/networks/acme-community.network-meta.xml,
# then lint before deploying.
python3 scripts/check_community_engagement_strategy.py \
  --file acme-engagement-strategy.yaml \
  --manifest-dir force-app/main/default

sf project deploy start --manifest package.xml --target-org acme-uat --wait 20
```

**Verification.** After the deploy, the levels are readable back as data — `ReputationLevel` is query-only, which makes it a clean assertion target:

```sql
SELECT LevelNumber, Label, Threshold
FROM ReputationLevel
WHERE ParentId = '0DB5g000000XXXXGAW'
ORDER BY LevelNumber
```

Expect seven rows, labels matching §3, thresholds 0 / 60 / 200 / 600 / 1500 / 4000 / 10000. If any `Label` reads `Level N`, a `label` element was dropped in the merge. In Setup, confirm at Digital Experiences → All Sites → Workspaces → Administration → Reputation Levels.

---

## 8. The strategy artefact (what the checker lints)

One file, `acme-engagement-strategy.yaml`. Everything above, in the shape `scripts/check_community_engagement_strategy.py` reads.

```yaml
site:
  name: acme-community
  network_id: "0DB5g000000XXXXGAW"
  type: customer
  live_since: "2026-03-02"
  owner: "J. Muir (Community Manager)"
  reviewed_on: "2026-09-05"

personas:
  - id: new-admin
    name: "New admin (0-90 days)"
  - id: working-admin
    name: "Working admin"
  - id: power-user
    name: "Power user"
  - id: internal-pm
    name: "Product manager (internal)"
  - id: support-agent
    name: "Support agent (internal)"

goals:
  - id: g-active-members
    persona: working-admin
    statement: "Grow monthly active posters from 180 to 300"
    owner: "J. Muir (Community Manager)"
    status: approved
    metric:
      name: "Members with activity in the last 30 days"
      soql: "SELECT COUNT(Id) FROM NetworkMember WHERE NetworkId = '0DB5g000000XXXXGAW' AND LastChatterActivityDate = LAST_N_DAYS:30"
      source_object: NetworkMember
      baseline: 181
      target: 300
  - id: g-first-response
    persona: new-admin
    statement: "60% of first questions answered by a peer within 24 hours"
    owner: "J. Muir (Community Manager)"
    status: approved
    metric:
      name: "Median hours to first comment on a QuestionPost"
      soql: "SELECT Id, CreatedDate, CreatedById, BestCommentId FROM FeedItem WHERE Type = 'QuestionPost' AND CreatedDate = THIS_QUARTER"
      source_object: FeedItem
      aggregate: false
      baseline: 31
      target: 24
  - id: g-answer-depth
    persona: power-user
    statement: "25 members with 5+ best answers per quarter"
    owner: "S. Devi (Solution Engineer)"
    status: approved
    metric:
      name: "Best-answer rate"
      soql: "SELECT Id, BestCommentId FROM FeedItem WHERE Type = 'QuestionPost' AND CreatedDate = THIS_QUARTER"
      source_object: FeedItem
      aggregate: false
      baseline: 22
      target: 40
  - id: g-idea-throughput
    persona: internal-pm
    statement: "Every idea gets a status change within 30 days"
    owner: "P. Chen (PM, Integrations)"
    status: approved
    metric:
      name: "Ideas with a status change in 30 days"
      soql: "SELECT COUNT(Id) FROM Idea WHERE LastModifiedDate = LAST_N_DAYS:30 AND CommunityId = '09a5g000000XXXXAAO'"
      source_object: Idea
      baseline: 12
      target: 90
  - id: g-escalation
    persona: support-agent
    statement: "Unanswered questions escalated within 48 hours, no silent drops"
    owner: "T. Alvarez (Support Lead)"
    status: approved
    metric:
      name: "Cases opened from community questions"
      soql: "SELECT COUNT(Id) FROM Case WHERE FeedItemId != NULL AND CreatedDate = LAST_N_DAYS:90"
      source_object: Case
      baseline: 0
      target: 100

reputation:
  enabled: true
  enable_knowledgeable: true
  network_file: "force-app/main/default/networks/acme-community.network-meta.xml"
  seeding:
    performed: true
    member_count: 40
    basis: "Historical best answers, 2024-03 to 2026-08"
    approved_by: "J. Muir (Community Manager)"
  ladder:
    - level: 1
      label: Newcomer
      lower_threshold: 0
    - level: 2
      label: "Asking Around"
      lower_threshold: 60
    - level: 3
      label: Contributor
      lower_threshold: 200
    - level: 4
      label: Regular
      lower_threshold: 600
    - level: 5
      label: "Trusted Advisor"
      lower_threshold: 1500
    - level: 6
      label: "Acme Expert"
      lower_threshold: 4000
    - level: 7
      label: "Community Legend"
      lower_threshold: 10000
  points_rules:
    - event_type: FeedItemWriteAPost
      points: 1
    - event_type: FeedItemWriteAComment
      points: 1
    - event_type: FeedItemReceiveAComment
      points: 2
      reason: "Receiving a comment is not an achievement; +5 rewarded controversy"
    - event_type: FeedItemLikeSomething
      points: 0
      reason: "Zero-cost action, cheapest farm on the board"
    - event_type: FeedItemReceiveALike
      points: 5
    - event_type: FeedItemMentionSomeone
      points: 1
    - event_type: FeedItemSomeoneMentionsYou
      points: 5
    - event_type: FeedItemShareAPost
      points: 1
    - event_type: FeedItemSomeoneSharesYourPost
      points: 5
    - event_type: FeedItemPostAQuestion
      points: 1
    - event_type: FeedItemAnswerAQuestion
      points: 5
    - event_type: FeedItemReceiveAnAnswer
      points: 2
      reason: "Asking already scores once; paying twice inflates askers over answerers"
    - event_type: FeedItemMarkAnswerAsBest
      points: 5
    - event_type: FeedItemYourAnswerMarkedBest
      points: 30
      reason: "The behaviour g-answer-depth exists to buy"
    - event_type: FeedItemEndorseSomeoneForKnowledgeOnATopic
      points: 5
    - event_type: FeedItemEndorsedForKnowledgeOnATopic
      points: 20

managed_topics:
  file: "force-app/main/default/managedTopics/acme-community.managedTopics"
  topics:
    - name: "Getting Started"
      type: Navigational
      owner: "J. Muir (Community Manager)"
    - name: "Automation"
      type: Navigational
      owner: "S. Devi (Solution Engineer)"
    - name: "Flow Errors"
      type: Navigational
      parent: "Automation"
      owner: "S. Devi (Solution Engineer)"
    - name: "Bulk Data"
      type: Navigational
      owner: "T. Alvarez (Support Lead)"
    - name: "Integrations"
      type: Navigational
      owner: "P. Chen (PM, Integrations)"
    - name: "Reporting"
      type: Navigational
      owner: "R. Okafor (Product Marketing)"
    - name: "Release Readiness"
      type: Featured
      owner: "R. Okafor (Product Marketing)"
    - name: "Ask the Product Team"
      type: Featured
      owner: "P. Chen (PM, Integrations)"
    - name: "Member Spotlight"
      type: Featured
      owner: "J. Muir (Community Manager)"

content_calendar:
  - id: cc-w1
    week: 1
    item: "Winter release: what breaks"
    kind: article
    topic: "Release Readiness"
    owner: "R. Okafor (Product Marketing)"
    goal: g-active-members
  - id: cc-w2
    week: 2
    item: "Weekly unanswered-question sweep"
    kind: ritual
    topic: "Getting Started"
    owner: "J. Muir (Community Manager)"
    goal: g-first-response
  - id: cc-w3
    week: 3
    item: "Five Flow fault paths you are missing"
    kind: article
    topic: "Flow Errors"
    owner: "S. Devi (Solution Engineer)"
    goal: g-answer-depth
  - id: cc-w4
    week: 4
    item: "Member Spotlight: top 3 answerers"
    kind: post
    topic: "Member Spotlight"
    owner: "J. Muir (Community Manager)"
    goal: g-answer-depth
  - id: cc-w5
    week: 5
    item: "Bulk API 2.0 office hours"
    kind: event
    topic: "Bulk Data"
    owner: "T. Alvarez (Support Lead)"
    goal: g-first-response
  - id: cc-w6
    week: 6
    item: "AMA: integrations roadmap"
    kind: event
    topic: "Ask the Product Team"
    owner: "P. Chen (PM, Integrations)"
    goal: g-idea-throughput
  - id: cc-w7
    week: 7
    item: "Reporting on community answers"
    kind: article
    topic: "Reporting"
    owner: "R. Okafor (Product Marketing)"
    goal: g-active-members
  - id: cc-w8
    week: 8
    item: "Idea drive: what should we build next"
    kind: post
    topic: "Ask the Product Team"
    owner: "P. Chen (PM, Integrations)"
    goal: g-idea-throughput
  - id: cc-w11
    week: 11
    item: "Topic retirement review"
    kind: ritual
    topic: "Getting Started"
    owner: "J. Muir (Community Manager)"
    goal: g-active-members

moderation:
  member_flagging_enabled: true
  escalation_queue: "Community Escalations"
  escalation_owner: "T. Alvarez (Support Lead)"
  escalation_sla_hours: 48
  rules_owned_by: "skills/admin/experience-cloud-moderation"
  org_rule_budget_confirmed: true

review:
  cadence: quarterly
  next_date: "2026-12-04"
  reviewer: "T. Alvarez (Support Lead)"
  levers:
    - "Reputation lowerThreshold values"
    - "pointsRule weights"
    - "Managed-topic list membership"
    - "Content calendar composition"

consumed_by:
  - "agents/experience-cloud-admin-designer/AGENT.md"
  - "skills/admin/experience-cloud-site-setup"
  - "skills/admin/experience-cloud-moderation"
```

---

## 9. Quarterly review checklist

Run at calendar W12. The reviewer is named in the YAML; the levers they may move without re-approval are named there too.

```markdown
## Acme community — quarterly engagement review

Date: ____________   Reviewer: T. Alvarez (Support Lead)   Quarter: ____

### A. Did the numbers move
- [ ] Re-read all six metrics in §6 with the same queries; record value and delta vs baseline
- [ ] Any metric that did not move: is the mechanism wrong, or was the target wrong?
- [ ] Any metric that could not be re-read: which query broke, and why

### B. Is the ladder still discriminating
- [ ] Distribution of members per level (query ReputationLevel for thresholds, then bucket
      NetworkMember.ReputationPoints) — a ladder with 90% at level 1 or 40% at the top is broken
- [ ] Any level nobody has reached in two quarters: lower the threshold or delete the level
- [ ] Any pointsRule being farmed: check the top 10 members' ChatterActivity mix against their rank

### C. Is the topic list earning its place
- [ ] Topics with TalkingAbout = 0 for two quarters: retire (frees headroom under the 25 cap)
- [ ] Any content the calendar produced with no topic assigned: fix or explain
- [ ] Managed-topic count after retirement: ____ / 25

### D. Did the calendar happen
- [ ] Items shipped vs planned, by owner
- [ ] Rituals (sweeps, retirement review) — completed or quietly dropped?
- [ ] Owners who shipped nothing: reassign the topic, do not reassign the guilt

### E. Is anything being dropped
- [ ] Community Escalations queue: volume, median age, anything older than the 48h SLA
- [ ] Unanswered QuestionPosts older than 7 days that never reached the queue
- [ ] Moderation load from NetworkActivityAudit: flag volume, and whether one member drives it

### F. Decisions
- [ ] Levers moved this quarter (thresholds / weights / topics / calendar): ____________
- [ ] Anything requiring re-approval outside the lever list: ____________
- [ ] Next review date booked: ____________
```

---

## Where each artefact goes

| Artefact | Consumed by |
|---|---|
| §7 `Network` reputation fragment | `skills/admin/experience-cloud-site-setup` — owns the full `Network` file this merges into |
| §4 `ManagedTopics` XML | Deployed with the site; `skills/admin/knowledge-base-administration` owns the data-category mapping if `enableTopicAssignmentRules` is used |
| §5 moderation policy | `skills/admin/experience-cloud-moderation` — turns the intents into `ModerationRule` and `KeywordList` |
| §6 metric set | `skills/data/community-analytics-data` — owns the ongoing reporting once a baseline exists |
| §8 strategy YAML | `scripts/check_community_engagement_strategy.py`, and `agents/experience-cloud-admin-designer/AGENT.md` as the engagement input to a site design |
| §9 review checklist | The named reviewer, quarterly |
