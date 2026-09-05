# Examples — Community Engagement Strategy

## Example 1: A Leaderboard That Rewarded Volume Instead of Expertise

**Context:** A software company launches a customer community for peer support. The goal is deflecting 20% of support case volume within six months. Members help each other by answering questions.

**Problem:** The initial deployment left `label` off every level — so the site displayed `Level 1` through `Level 5` — and flattened the point weights so that every action scored the same. Members farmed points by posting short, low-quality replies. The leaderboard did not reflect actual expertise. Trusted advisors, who wrote thorough answers, were outranked by members posting volume.

**Diagnosis first.** Before redesigning the ladder, confirm what is actually deployed rather than what the spreadsheet says. `ReputationLevel` is query-only and therefore a clean assertion target:

```sql
-- What the org actually has. Any Label matching 'Level N' is a dropped <label>
-- element, not a naming decision.
SELECT LevelNumber, Label, Threshold
FROM ReputationLevel
WHERE ParentId = '0DB5g000000XXXXGAW'
ORDER BY LevelNumber

-- Who is at the top, and whether their activity mix explains it.
SELECT MemberId, ReputationPoints, LastChatterActivityDate
FROM NetworkMember
WHERE NetworkId = '0DB5g000000XXXXGAW'
ORDER BY ReputationPoints DESC
LIMIT 20
```

Then, per top member (`ChatterActivity` needs a `ParentId` — you cannot sweep it):

```sql
SELECT ParentId, PostCount, CommentCount, CommentReceivedCount,
       LikeReceivedCount, InfluenceRawRank
FROM ChatterActivity
WHERE ParentId = '0055g00000XXXXXAAI'
  AND NetworkId = '0DB5g000000XXXXGAW'
```

A top-20 whose `PostCount` is high and whose `LikeReceivedCount` and best-answer share are not is the point-farming signature. That is a weighting problem, not a member problem.

**Solution:**

Seven levels, every one explicitly labelled, thresholds strictly increasing. Note what the table does *not* have: an upper bound. There is no upper-bound element in the metadata — the platform derives each band's ceiling from the next level's lower threshold, so a "Max Points" column in a design document is a comment, not a configuration.

```
Reputation ladder — Tech Support Community

Level | label              | lowerThreshold
------|--------------------|----------------
1     | Newcomer           | 0
2     | Asking Around      | 60
3     | Contributor        | 200
4     | Regular            | 600
5     | Trusted Advisor    | 1500
6     | Acme Expert        | 4000
7     | Community Legend   | 10000

Weights that deviate from the platform default, and why:
  FeedItemLikeSomething        0   (was +1)  zero-cost action, cheapest farm
  FeedItemReceiveAComment      2   (was +5)  rewarded controversy, not help
  FeedItemReceiveAnAnswer      2   (was +5)  asking already scores once
  FeedItemYourAnswerMarkedBest 30  (was +20) the behaviour we are buying

Everything else left at the platform default — the defaults already
weight FeedItemYourAnswerMarkedBest (+20) far above FeedItemWriteAPost (+1).
```

Steps taken:
1. Retrieve the site's `Network` file — never author one from scratch; it carries dozens of settings this work does not own.
2. Merge the `reputationLevels` and `reputationPointsRules` blocks (shape in `worked-examples.md` §7).
3. Run `scripts/check_community_engagement_strategy.py` to catch a duplicated or out-of-order threshold before it deploys silently.
4. Deploy, then re-run the `ReputationLevel` query above and assert all seven labels came back as written.
5. Seed `NetworkMember.ReputationPoints` for the known top contributors so the corrected ladder does not reset two years of standing.

**Why it works:** The four deviations each buy one behaviour and each carry a reason a future admin can read. Domain-meaningful labels signal community standing without anyone calculating point totals. And the diagnosis step means the redesign is aimed at what the org has, not at what the last strategy document claimed.

---

## Example 2: Product Ideation Portal with Defined Status Workflow

**Context:** A SaaS company wants to collect structured product feedback through their customer community. Previously, feature requests came in via support tickets with no visibility to other customers on whether ideas were considered.

**Problem:** Ideation was enabled but with no status workflow defined and no assigned owners. Ideas sat at "New" status for months. Customers stopped voting because feedback appeared to disappear into a black hole. Engagement on the ideation section dropped to near zero within 60 days of launch.

**Solution:**

```
Ideation Setup — Product Feedback Portal

Step 1: Confirm the ORG-LEVEL settings
  Ideas is an org setting, not a per-site one. IdeasSettings deploys as
  Ideas.settings and carries:
    enableIdeas           = true
    enableIdeaThemes      = true    (only if themes will be used)
    enableIdeasReputation = false   (a separate reputation system — do not
                                     confuse with the site's Network reputation)
    halfLife              = 2.6     (org-wide dial on how fast old ideas fall
                                     down Popular Ideas — check before blaming
                                     the ranking on member behaviour)

Step 2: Name the ZONE
  Idea.CommunityId is the zone and it cannot be changed after an idea is
  created. Getting the zone wrong is the one ideation mistake that is not
  cheaply reversible. Write it into the strategy before naming any theme.

Step 3: Create IdeaThemes — for grouping, not gating
  Idea.IdeaThemeID is nillable, so members CAN post without a theme.
  Themes are a curation device with an owner:
    Theme 1: "Mobile App Improvements"  — Owner: Sara Chen, PM (Mobile)
    Theme 2: "API & Integration Requests" — Owner: Dev Partnerships Team
    Theme 3: "Reporting & Analytics"      — Owner: Analytics PM

Step 4: WRITE DOWN the status values
  Idea.Status is a "Customizable picklist of values used to specify the
  status of an idea" — the platform ships no standard values, so there is
  no default workflow to inherit. This org's set:
    New                    (default on submission)
    Under Review           (PM has read and is evaluating)
    Planned                (added to roadmap)
    Implemented            (shipped)
    Closed — Not Planned   (comment required explaining why)

Step 5: Assign Owners and Review Cadence
  Each theme owner reviews and updates statuses on a 30-day cycle.
  Status change must include a comment visible to voters.
```

**Why it works:** The status workflow makes the idea lifecycle visible to members, and writing it down is not documentation hygiene — it is the only place the workflow exists, because the platform has no opinion. A monthly cadence maintains responsiveness signals. The "Closed — Not Planned" status with a required explanation preserves trust even when ideas are declined. Naming the zone first avoids the one migration that cannot be undone.

---

## Anti-Pattern: Launching with No Seed Content and No Onboarding Path

**What practitioners do:** Enable the Experience Cloud site and open it to members without creating any baseline content, without writing a "Start Here" article, and without defining a member onboarding journey.

**What goes wrong:** The first member to arrive sees an empty community. No questions to answer, no articles to read, no ideas to vote on. The empty-state experience communicates that the community is inactive. Activation rates remain low in the first 30 days. Once members form the habit of not engaging, reversing the pattern is difficult — and the reputation ladder makes it visibly worse, because everyone is on level 1 and the leaderboard is empty too.

**Correct approach:** Treat the seed as a checkable artefact with owners and a topic each, not a to-do list. Every row names a topic that exists in the site's `ManagedTopics` file, so each seeded item is measurable afterwards:

```yaml
launch_seed:
  site: acme-community
  gate: "Site status stays UnderConstruction until every row below is done"
  owner: "J. Muir (Community Manager)"
  items:
    - id: seed-welcome
      kind: article
      title: "Start Here: what this community is for"
      topic: "Getting Started"
      pinned: true
      owner: "J. Muir (Community Manager)"
    - id: seed-intro-thread
      kind: post
      title: "Introduce yourself"
      topic: "Getting Started"
      pinned: true
      first_action_for_new_members: true
      owner: "J. Muir (Community Manager)"
    - id: seed-faq-questions
      kind: question_batch
      title: "Top 12 support FAQs, posted as QuestionPosts with accepted answers"
      topic: "Getting Started"
      count: 12
      source: "Highest-volume case contact reasons, last 2 quarters"
      owner: "T. Alvarez (Support Lead)"
    - id: seed-topic-anchors
      kind: article_batch
      title: "One anchor article per navigational topic"
      count: 6
      one_per_topic: true
      owner: "S. Devi (Solution Engineer)"
    - id: seed-idea
      kind: idea
      title: "One seeded idea per active theme, posted by an internal account"
      owner: "P. Chen (PM, Integrations)"
  verification:
    - "Every navigational topic returns at least one TopicAssignment row"
    - "At least 12 FeedItems of Type QuestionPost carry a BestCommentId"
    - "Reputation seeding pass complete for pre-existing members (if any)"
```

Verify the last two before flipping the site live:

```sql
-- Every navigational topic has something under it. TopicAssignment needs a
-- bound: LIMIT 1100 or a '=' filter on Id/Entity.
SELECT TopicId, EntityType, COUNT(Id)
FROM TopicAssignment
WHERE NetworkId = '0DB5g000000XXXXGAW'
GROUP BY TopicId, EntityType
LIMIT 1100

-- Seeded questions actually carry an accepted answer. FeedItem supports no
-- aggregate functions, so this is a paged read you count client-side.
SELECT Id, Title, BestCommentId
FROM FeedItem
WHERE Type = 'QuestionPost'
  AND BestCommentId != NULL
  AND CreatedDate = LAST_N_DAYS:14
```

This baseline gives the first cohort something to interact with, and — because every seeded item is topic-anchored — gives the first quarterly review something to measure.
