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
1. At least four status values: New, Under Review, Planned, Closed — Not Planned
2. A named internal owner per IdeaTheme with a committed monthly review
3. A process for posting a status-update comment when status changes
4. At least one active IdeaTheme before the feature is opened to members

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

## Anti-Pattern 4: Omitting the IdeaTheme Requirement for Idea Submission

**What the LLM generates:** Instructions that enable Ideas and tell members "click New Idea to submit your feedback" — without creating an IdeaTheme first. The LLM does not mention that IdeaTheme is required for the submission UI to appear.

**Why it happens:** The IdeaTheme prerequisite is a platform-specific constraint not obvious from the feature name. LLMs trained on high-level documentation omit it because it appears to be a configuration detail rather than a functional gate.

**Correct pattern:**

```
Before members can submit ideas, an active IdeaTheme must exist.

Steps:
1. Enable Ideas in site settings.
2. Add the Ideas tab to navigation in Experience Builder.
3. Create at least one IdeaTheme (e.g., "General Product Feedback").
4. Confirm the IdeaTheme status is Active.

Without an active IdeaTheme, the idea submission form will not appear to members
even if the Ideas tab is visible in navigation.
```

**Detection hint:** Any ideation setup guide that does not mention creating an IdeaTheme before directing members to submit ideas is incomplete.

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
