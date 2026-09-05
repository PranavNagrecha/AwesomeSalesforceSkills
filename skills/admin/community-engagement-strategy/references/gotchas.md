# Gotchas — Community Engagement Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Line citations are into the Summer '26 / v62 PDF text: `api_meta.txt` = Metadata API Developer Guide, `object_reference.txt` = Object Reference for Salesforce.

## Gotcha 1: Reputation Points Are Not Retroactive

**What happens:** When Reputation is enabled on an Experience Cloud site, members who were previously active receive zero points for any historical actions (posts, comments, likes, best answers). The system only begins awarding points from the moment the feature is enabled forward. A member who answered 200 questions before Reputation was turned on will appear as a Newcomer on the leaderboard alongside someone who joined the day Reputation went live.

UNVERIFIED (2026-09-05): the forward-only behaviour is not stated in the Metadata API Developer Guide or the Object Reference; it is retained here as practitioner experience. The remedy below is grounded.

**When it occurs:** Every deployment that enables Reputation on an existing community with an established member base.

**How to avoid:** Communicate the behaviour to the community sponsor before go-live, and plan a seeding pass. `NetworkMember.ReputationPoints` is a `double` whose properties include `Update`, and the Object Reference is explicit: "You can directly update reputation points for a member via the Salesforce API. You can also use Apex triggers to send custom notifications based on changes to reputation points." (`object_reference.txt` L188569-L188576, L188591-L188592). Note the object: the writable field is on `NetworkMember`, not on `ReputationLevel`, which is query-only — see Gotcha 4.

---

## Gotcha 2: An Omitted `label` Deploys As `Level 1` … `Level 10`

**What happens:** `ReputationLevel.label` is optional in the `Network` metadata. When it is missing, the platform does not fail the deploy and does not leave the level unnamed — it substitutes a numbered default. The Metadata API Developer Guide lists them: "This field is optional. If not specified, one of the 10 defaults is used" followed by `Level 1` through `Level 10` (`api_meta.txt` L91633-L91644). A ladder that was carefully named in a spreadsheet reappears in the site as a numbered list, and the admin is blamed for laziness that was actually a dropped element in a merge.

**When it occurs:** Most often when the reputation block is hand-merged into an existing retrieved `Network` file, or when a level is added late and copied from a sibling without its `label`.

**How to avoid:** Assert the labels back out of the org after deploy rather than trusting the deploy result. `ReputationLevel` is queryable: `SELECT LevelNumber, Label, Threshold FROM ReputationLevel WHERE ParentId = '<networkId>' ORDER BY LevelNumber`. Any row whose `Label` matches `Level <n>` is a dropped element, not a design choice. `scripts/check_community_engagement_strategy.py` flags the same shape in the XML before it ships.

---

## Gotcha 3: You Author Only the Bottom of Each Band, So a Bad Threshold Fails Silently

**What happens:** There is no upper-bound element on a reputation level. `ReputationLevel` "Represents the name and lower value of the reputation level. The application calculates the upper value." (`api_meta.txt` L91623), and `lowerThreshold` is "Required. The lower value in the range for this reputation level." (`api_meta.txt` L91647-L91651). Because the ceiling is derived, a ladder with a duplicated threshold, or with levels listed out of order, deploys without complaint and then ranks members into bands nobody designed. There is no error to search for — only a leaderboard that looks subtly wrong.

**When it occurs:** When a ladder is edited by hand after the fact (inserting a level, lowering a threshold to "make level 3 reachable") without re-checking the whole sequence, and whenever a ladder is assembled from two drafts.

**How to avoid:** Treat "strictly increasing, no duplicates" as a validated property of the artefact rather than a habit. The checker enforces exactly that over both the strategy YAML and the `Network` XML, and cross-checks the two against each other so a hand-edit to one is caught by the other.

---

## Gotcha 4: Reputation Levels Do Not Grant Any Permission

**What happens:** Admins or community managers sometimes assume that high-reputation members automatically gain elevated moderation rights — flagging and removing posts, managing members, or reaching a moderation queue. Reputation carries no such wiring. The `ReputationLevel` sObject has exactly four fields (`Label`, `LevelNumber`, `ParentId`, `Threshold`) and its supported calls are `describeSObjects(), query(), retrieve()` — read-only, with nothing resembling a permission reference (`object_reference.txt` L247325-L247382). Access in a site comes from the profile and permission sets behind the member, and from `NetworkMemberGroup` membership.

**When it occurs:** When community design assumes a reputation-based escalation path for member moderation rights without a matching permissions plan — usually because the designer's mental model came from a platform where reputation and privileges are the same system.

**How to avoid:** Keep the two decisions on separate lines of the strategy. If elevated members should moderate, that is a permission-set assignment with a named approver, designed with `admin/experience-cloud-moderation` (which owns the `Moderate Experiences Feeds` permission), not an automatic consequence of crossing a threshold.

---

## Gotcha 5: Ideas Hang Off a Zone, Not Off a Theme — and Not Off the Site

**What happens:** Two beliefs are common and both are wrong. The first is that an `IdeaTheme` is required before members can submit an idea; the second is that Ideas is configured per Experience Cloud site. `Idea.IdeaThemeID` is Nillable (`object_reference.txt` L155551-L155556), and an `IdeaTheme` is described as "an invitation to zone members to submit ideas that are focused on a specific topic" (L156038-L156039) — a grouping, not a gate. The container that *is* mandatory is the zone: `Idea.CommunityId` is "The zone ID associated with the idea. Once you create an idea, you can't change the zone ID associated with that idea." (L155493-L155499). Meanwhile the feature switches live in an org-level settings file, `IdeasSettings` stored as `Ideas.settings`, carrying `enableIdeas`, `enableIdeaThemes`, `enableIdeasReputation` and `halfLife` (`api_meta.txt` L118310-L118336).

**When it occurs:** When an ideation plan is written from the site outwards, so the zone never appears in it; and when a theme is treated as the unit of governance, which then quietly fails to stop uncategorised ideas from arriving.

**How to avoid:** Name the zone in the strategy before naming any theme, and treat themes as a curation device with an owner rather than a submission gate. Because ideas cannot be moved between zones after creation, getting the zone wrong is the one ideation mistake that is not cheaply reversible.

---

## Gotcha 6: There Are Two Reputation Systems and They Obey Different Rules

**What happens:** "Reputation" in a Salesforce context means at least two unrelated implementations, and guidance written for one is wrong about the other.

| | Experience Cloud site reputation | Ideas-zone reputation |
|---|---|---|
| Config | `Network.enableReputation`, `reputationLevels`, `reputationPointsRules` (`api_meta.txt` L90863-L90873, L91020-L91024) | `IdeasSettings.enableIdeasReputation` (`api_meta.txt` L118334), `IdeaReputationLevel` records |
| Levels | `ReputationLevel`, read-only, `Threshold` is a `double` | `IdeaReputationLevel`, writable, "You can create up to 25 levels per zone or internal organization" (`object_reference.txt` L155990-L155992) |
| Name rules | `label` optional, defaults to `Level N` | `Name` "must be unique within the zone or internal organization. Maximum size is 50 characters" (L156020-L156021) |
| Threshold rules | No documented uniqueness rule; the app derives the upper bound | "The threshold must be unique within the zone or internal organization and must be greater than or equal to zero" (L156026-L156029) |
| Points | `NetworkMember.ReputationPoints` | `IdeaReputation` statistics per user per zone |
| Scope | Per Experience Cloud site | Per Ideas zone or internal org |

A third, older variant exists: the `Community` (Zone) metadata type carries `reputationLevels` with `chatterAnswersReputationLevels` and `ideaReputationLevels` children, and states "You can create up to 25 reputation levels per zone" (`api_meta.txt` L34124-L34125). `ChatterAnswersSettings.enableReputation` is org-wide — "Reputation is enabled across all zones" (`api_meta.txt` L112309-L112313).

**When it occurs:** Any time a limit or a rule is quoted without naming which system it belongs to. The "25 levels" figure is real and belongs to the zone systems; it is not a cap on site reputation levels, and no such cap for `Network` appears in these guides.

**How to avoid:** State the system in the strategy document, not just the word "reputation". If the artefact names `Network` elements, the zone rules do not apply to it, and vice versa.

---

## Gotcha 7: `FeedItem` Supports No Aggregates and Cannot Be Filtered by Site

**What happens:** The obvious engagement metrics are counts of posts, questions and best answers — and `FeedItem` refuses both halves of the obvious query. The Object Reference states flatly: "The FeedItem object doesn't support aggregate functions in queries." (`object_reference.txt` L136523). Separately, among the `NetworkScope` exceptions: "You can't filter a feed item on the NetworkScope field." (L136183). So neither `SELECT COUNT() FROM FeedItem` nor `WHERE NetworkScope = :siteId` will run, and a dashboard specified on either is dead before it is built. Direct `FeedItem` querying also requires View All Data from API 23.0 onward (L136504).

**When it occurs:** At the point someone tries to build the report the engagement strategy promised — typically weeks after the strategy was signed off, when changing the metric is expensive.

**How to avoid:** Design the metric set against the query surface up front (`references/worked-examples.md` §6 and §6b). Move counts onto objects that do support aggregates — `NetworkMember` for membership and recency, `Case` for escalation volume via `Case.FeedItemId` — and where the metric genuinely needs feed rows, page them and count client-side rather than asking SOQL to do it.

---

## Gotcha 8: `ChatterActivity` Cannot Be Swept, and Lurkers Have No Row

**What happens:** `ChatterActivity` looks like the per-member engagement table you want: `PostCount`, `CommentCount`, `CommentReceivedCount`, `LikeReceivedCount`, `InfluenceRawRank`, all filterable and groupable, with a `NetworkId`. Two constraints break the sweep. First, "To query ChatterActivity, you must provide the ParentId. In API version 66.0, the ParentId must be a UserId or SelfServiceUser ID." (`object_reference.txt` L66386-L66388) — there is no org-wide or site-wide read. Second, "A ChatterActivity record is created for users the first time they post or comment. Users who have never posted or commented don't have ChatterActivity records." (L66389-L66391), so any denominator taken from this object silently excludes every lurker and flatters the participation rate.

**When it occurs:** Building a leaderboard or a participation-rate metric that reads naturally as one query and turns out to need one query per member.

**How to avoid:** Take the denominator from `NetworkMember` (one row per enrolled member per site) and the numerator per-member from `ChatterActivity` in a batch or a loop. If the report needs to run interactively, precompute it — do not put a per-member query behind a dashboard refresh.

---

## Gotcha 9: You Cannot Rename a Topic, Only Re-Case It

**What happens:** `Topic.Name` is updateable, but with a restriction buried in its properties list: "You can change only the spacing and capitalization of a topic name with the update property." (`object_reference.txt` L289129-L289134). So `Billing` → `Billing and Invoicing` is not an update; it is a new topic plus a migration of every `TopicAssignment` that pointed at the old one, plus a `ManagedTopics` redeploy, plus whatever the old topic's URL was doing in published content. The `TalkingAbout` history does not follow.

**When it occurs:** During the first content-strategy review, when the topic list drafted before launch meets the vocabulary members actually use.

**How to avoid:** Spend the extra hour on topic naming before the site opens, and prefer broader names that survive a pivot. When a rename is genuinely needed, plan it as a migration with a `TopicAssignment` inventory (bounded per Gotcha 11), not as an edit.

---

## Gotcha 10: Pre-Moderation Makes `FeedItem.CommentCount` Lie

**What happens:** In a feed with moderation rules that hold content for review, the comment counter and the comments diverge. The Object Reference's own example: "say that you comment on a post that already has one published comment and your comment triggers moderation. Now there are two comments on the post, but the count says there's only one. In a moderated feed, comments aren't counted until approved by an admin or someone with Can Approve Feed Post and Comment or Modify All Data." (`object_reference.txt` L135899-L135912). It also changes how you read a thread: "In a moderated feed, rather than retrieving comments by looping through CommentCount, go through pagination until the end of comments is returned."

**When it occurs:** Whenever a review-and-approve moderation rule is added to a site whose engagement metrics or integrations already read `CommentCount` — the metric degrades quietly and nobody connects it to the moderation change.

**How to avoid:** If the site pre-moderates, treat `CommentCount` as a display hint and never as a metric input or a loop bound. Any code that walks comments must paginate. Flag this to `admin/experience-cloud-moderation` when a review rule is proposed, because that is where the change originates.

---

## Gotcha 11: `TopicAssignment` Queries Need an Explicit Bound

**What happens:** `TopicAssignment` is the join between topics and the feed items, records and files that carry them — the natural source for "what content exists under this topic". Its usage notes attach a SOQL constraint that most people meet as a runtime error: "There is no SOQL limit if the logged-in user has the 'View All Data' permission. If they do have that permission, do one of the following: Specify a LIMIT clause of 1,100 records or fewer. Filter on Id or Entity when using a WHERE clause with '='." (`object_reference.txt` L289283-L289287). The two sentences contradict each other as printed, which is itself worth knowing — the safe reading is that an unbounded `TopicAssignment` query is not guaranteed to run, so always bound it. A related note: "Querying topic assignments for the ManagedContentVersion entity type isn't supported."

**When it occurs:** Building a content inventory per topic, or a topic-retirement report, as an ad-hoc query that worked in a sandbox with fifty rows.

**How to avoid:** Always ship `LIMIT 1100` or a `=` filter on `Id`/`Entity`. If the inventory genuinely needs everything, page it. Note the escape hatch the guide provides for reporting: "When you create a report type on the TopicAssignment object, all queries are generated in SQL, which does not enforce the 1,100 record limit clause." (L289291-L289292) — a report type, not SOQL, is the supported way to see the whole set.
