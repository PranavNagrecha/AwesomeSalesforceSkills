# LLM Anti-Patterns — Community Engagement Strategy

Common mistakes AI coding assistants make when generating or advising on Community Engagement Strategy.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Generic Tier Names for Reputation Levels

**What the LLM generates:** Instructions to create reputation tiers labeled "Level 1", "Level 2", ... "Level 10" without recommending meaningful names. The LLM treats tier naming as cosmetic rather than functional.

**Why it happens:** Training data includes many generic reputation system tutorials that use numeric labels as placeholders. The LLM treats the placeholder as the recommendation.

**Correct pattern:**

```
Reputation tiers must use role-meaningful names tied to the community domain.

For a technology support community:
  Tier 1: Newcomer
  Tier 2: Explorer
  Tier 3: Contributor
  Tier 4: Helper
  Tier 5: Advisor
  Tier 6: Expert
  Tier 7: Trusted Expert
  Tier 8: Community Champion
  Tier 9: Master
  Tier 10: Legend

Tier names are displayed on member profile cards and beside posts.
They are the primary recognition signal visible to all community members.
```

**Detection hint:** Look for "Level 1", "Level 2" or "(Point Threshold)" placeholders in tier configuration output. Any tier list using numeric labels without domain-specific names is incomplete.

---

## Anti-Pattern 2: Enabling Ideation Without Defining a Status Workflow

**What the LLM generates:** Steps to enable Ideas in Setup and add the Ideas tab to navigation, stopping there without specifying status values, a review cadence, or named theme owners.

**Why it happens:** LLMs pattern-match to "enable the feature" as the complete task. The operational workflow (who reviews, what statuses exist, how frequently) is not surfaced by standard setup documentation.

**Correct pattern:**

```
Ideation setup is incomplete without:
1. The ZONE named. Idea.CommunityId cannot be changed after an idea is created,
   so this is the one decision that is not cheaply reversible.
2. Status values WRITTEN DOWN. Idea.Status is a "Customizable picklist of values
   used to specify the status of an idea" — the platform ships no standard set,
   so whatever you write is the entire definition. Four is a reasonable floor:
   New, Under Review, Planned, Closed — Not Planned.
3. A named internal owner per IdeaTheme with a committed review cadence.
4. A process for posting a status-update comment when status changes.
5. halfLife checked — it is an org-wide dial on how fast old ideas fall down
   Popular Ideas, and it is often blamed on member behaviour instead.

Ideas sitting at "New" for 60+ days will kill member trust in the ideation channel.
```

**Detection hint:** Any ideation setup that ends after "Enable Ideas + add tab" without mentioning status workflow, theme ownership, or review cadence is incomplete.

---

## Anti-Pattern 3: Conflating Reputation Levels with Moderation Permissions

**What the LLM generates:** Advice that high-reputation members should be "given moderation rights" or "escalated to moderator status" based on their tier level, as if Reputation tiers automatically confer permissions.

**Why it happens:** Many community platforms (Reddit, Stack Overflow) tie reputation scores to elevated permissions natively. LLMs trained on general community management content assume this model applies to Salesforce Experience Cloud.

**Correct pattern:**

```
In Salesforce Experience Cloud, Reputation is a display mechanism only.
It has no integration with the profile or permission model.

To grant a high-reputation member moderation rights:
1. Assign a Permission Set that includes the relevant community moderation permissions.
2. OR manually adjust the member's profile assignment.

Do NOT assume reputation tier escalation triggers any permission change.
```

**Detection hint:** Watch for phrases like "once a member reaches [tier], they automatically gain..." — Reputation never automatically grants permissions.

---

## Anti-Pattern 4: Inventing an IdeaTheme Gate That Does Not Exist

**What the LLM generates:** "Members cannot post an idea until an active IdeaTheme exists — create one first or the submission form will not appear." It is stated with the confidence of a platform constraint, and it is wrong.

**Why it happens:** The claim is plausible, widely repeated in community-management blog content, and structurally similar to real Salesforce prerequisites (record types, data categories). LLMs reproduce it because nothing in the surface documentation contradicts it loudly.

**Correct pattern:**

```
What the Object Reference actually says:

  Idea.IdeaThemeID   Properties: Create, Filter, Group, Nillable, Sort, Update
                     -> nillable. An idea can exist with no theme.

  Idea.CommunityId   Properties: Create, Filter, Group, Sort
                     "The zone ID associated with the idea. Once you create an
                      idea, you can't change the zone ID associated with that idea."
                     -> the zone is the container that matters, and the one
                        decision that cannot be reversed later.

  IdeaTheme          "Represents an invitation to zone members to submit ideas
                      that are focused on a specific topic."
                     -> a grouping and curation device, not a gate.

So: name the ZONE in the strategy before naming any theme. Treat themes as
curation with an owner. Do not promise that a theme prevents uncategorised ideas
from arriving, because it does not.
```

**Detection hint:** Any sentence asserting that something "is required for the idea submission UI to appear" — check the field's Nillable property before repeating it. The same test catches the sibling claim that Ideas is configured per Experience Cloud site; `IdeasSettings` is an org-level settings file.

---

## Anti-Pattern 5: Treating Content Ownership as a Post-Launch Operational Concern

**What the LLM generates:** A community launch plan that defers content ownership assignment to a "Phase 2" or "post-go-live" operational task, focusing only on technical configuration (site templates, permissions, navigation).

**Why it happens:** LLMs separate technical setup from operational process. Technical setup produces a visible artifact (a configured site). Content ownership is invisible in the configuration, so LLMs omit it from setup guidance.

**Correct pattern:**

```
Content ownership must be resolved before go-live, not after.

Pre-launch deliverable — Content Ownership Map:

| Content Area        | Owner Name       | Review Cadence | Content Type  |
|---------------------|------------------|----------------|---------------|
| Product how-to articles | Jane Smith (PM)  | Monthly        | Articles      |
| Support FAQs        | Tom Rivera (Support) | Quarterly   | Articles      |
| Announcements       | Community Manager | As-needed      | Posts         |
| Idea Themes         | Relevant PM      | Monthly        | IdeaTheme     |

Without this map, content ages out within 60–90 days of launch.
```

**Detection hint:** Any community engagement plan that does not include a content ownership assignment table before go-live is missing a critical operational component.

---

## Anti-Pattern 6: Not Seeding Baseline Content Before Launch

**What the LLM generates:** A launch checklist focused on technical configuration (permissions, navigation, branding) that does not include a step for seeding baseline content before opening the site to members.

**Why it happens:** LLMs treat "launch" as equivalent to "technically ready." The distinction between technically ready and member-ready is an operational nuance LLMs miss without explicit framing.

**Correct pattern:**

```
Before opening the community to members, ensure:

1. Welcome/Start Here article: explains the community purpose and first actions
2. 10–15 seeded discussion posts or Q&A threads (based on FAQ content)
3. At least one active IdeaTheme with one seed idea already posted
4. A "Introduce Yourself" thread pinned to the community home

Empty communities have low first-session activation rates.
Members who visit and find nothing to read or respond to do not return.
```

**Detection hint:** Any launch checklist that ends at "configure settings and open registration" without a content seeding step is incomplete.

---

## Anti-Pattern 7: Specifying Engagement Metrics `FeedItem` Cannot Produce

**What the LLM generates:** A measurement plan built on feed counts — `SELECT COUNT() FROM FeedItem WHERE Type = 'QuestionPost'`, "filter by `NetworkScope` to scope it to the site", "group by month for the trend". It reads like every other Salesforce reporting answer and none of it runs.

**Why it happens:** Aggregate SOQL over a standard object is the single most common shape in Salesforce training data. `FeedItem` is an exception, and exceptions are exactly what pattern-matching erases.

**Correct pattern:**

```
Two hard constraints from the Object Reference, FeedItem:

  "The FeedItem object doesn't support aggregate functions in queries."
  "You can't filter a feed item on the NetworkScope field."

  (Plus: direct FeedItem querying requires View All Data, API 23.0 and later.)

So these do NOT work:
  SELECT COUNT() FROM FeedItem WHERE ...
  SELECT Type, COUNT(Id) FROM FeedItem GROUP BY Type
  SELECT Id FROM FeedItem WHERE NetworkScope = '0DB...'

Redesign onto objects that answer:
  Active members / recency  -> NetworkMember (aggregates fine, scoped by NetworkId)
  Per-member activity       -> ChatterActivity, one ParentId per query
  Escalation volume         -> Case, via Case.FeedItemId (Case DOES aggregate)
  Topic reach               -> Topic.TalkingAbout
  Best-answer rate          -> page FeedItem rows and count client-side
```

**Detection hint:** Any community metric plan containing `COUNT(` against `FeedItem`, or a `WHERE NetworkScope =` clause. Also treat "average posts per member across the community" as a red flag: the denominator needs `NetworkMember` because members who never posted have no `ChatterActivity` row at all.

---

## Anti-Pattern 8: Quoting a Reputation Limit Without Saying Which System

**What the LLM generates:** "Experience Cloud supports up to 10 reputation levels per site" or "you can create up to 25 reputation levels". Both numbers appear in Salesforce documentation. Neither means what the sentence implies.

**Why it happens:** Salesforce ships several unrelated features called reputation, and the guides describe them in different chapters. An LLM retrieving on the word "reputation" pulls facts from whichever one matched, then presents them as one system.

**Correct pattern:**

```
The "10" is a set of DEFAULT LABELS, not a cap:
  Metadata API, ReputationLevel.label — "This field is optional. If not
  specified, one of the 10 defaults is used" -> Level 1 ... Level 10.
  No maximum level count for Network reputation appears in the guide.

The "25" belongs to the ZONE systems, not to the site:
  IdeaReputationLevel — "You can create up to 25 levels per zone or internal
  organization", Name unique and max 50 chars, Threshold unique and >= 0.
  Community (Zone).reputationLevels — "You can create up to 25 reputation
  levels per zone."

Site reputation lives on Network: enableReputation, reputationLevels,
reputationPointsRules, with points on NetworkMember.ReputationPoints.
Ideas-zone reputation is a separate system with separate storage.

Say which system before quoting any number.
```

**Detection hint:** A reputation limit stated without the words `Network`, `zone`, or `Ideas` beside it. Also watch for advice that mixes the two vocabularies in one paragraph — `reputationPointsRules` (site) next to `IdeaReputationLevel` (zone) is a sign the answer was assembled from two sources that do not describe the same feature.
