# Well-Architected Notes — Community Engagement Strategy

## Relevant Pillars

- **Adaptable** — The engagement model must be designed to evolve. Reputation thresholds and point weights should be revisited as community behavior matures, and the managed-topic list must be pruned as well as extended: navigational and featured topics share a documented ceiling of 25, so a list that only grows eventually cannot accept next quarter's campaign topic.
- **Operational Excellence** — Content ownership maps, status review cadences, and member onboarding paths are operational disciplines, not one-time configurations. Without these, a technically correct community setup degrades in quality over time. The engagement model is only as durable as the operational processes behind it.
- **Trusted** — Reputation levels and idea status workflows are trust mechanisms. Members trust the community when they can see that their contributions are recognized (reputation display) and that their feedback is acted on (idea status updates). Breaking either signal damages member trust in ways that are difficult to reverse. The escalation queue is part of the same promise: a question the community cannot answer must visibly go somewhere.

## Architectural Tradeoffs

**Ladder depth vs. calibration cost:** A long ladder creates a fine-grained progression path that keeps experienced members engaged longer. It also multiplies the calibration burden — thresholds that feel aspirational at launch become trivially achievable as average activity rises, and because the platform derives each band's upper bound from the next level's `lowerThreshold`, every re-tune is a whole-sequence edit rather than a local one. Prefer fewer levels with wide, deliberate gaps, and book the review that will move them.

**Platform defaults vs. bespoke weights:** The 16 documented `eventType` rules ship with defaults that already favour quality (`FeedItemYourAnswerMarkedBest` +20 against `FeedItemWriteAPost` +1). Every deviation is a claim that you know the community better than that baseline, and every deviation is something a future admin has to understand. Deviate deliberately, in writing, and leave the rest alone.

**Ideation breadth vs. focus:** Creating many themes allows granular feedback collection but dilutes vote density — if 500 ideas are spread across 20 themes, few ideas accumulate the vote signal needed for confident product prioritization. Prefer fewer, broader themes early and split them as volume warrants. Remember that themes group rather than gate, so breadth costs curation attention without buying containment.

**Open contribution vs. quality control:** Granting all members contribution rights maximizes content volume but requires moderation investment. Restricting contribution to vetted member roles reduces volume but improves average quality. Choose based on the community's staffing model for moderation, and check the org-wide budget before designing around automated rules: moderation rules and keyword lists are capped at 30 each per org, not per site.

**Measurability vs. the metric people asked for:** The most-requested community metrics are feed counts, and the feed is the object least willing to be counted. Choosing a metric the platform can produce — membership recency, escalation volume, topic reach — over one that reads better in a slide is an architectural decision, not a reporting detail. It is cheapest to make before the strategy is signed off.

## Anti-Patterns

1. **Shipping the platform's default labels** — Leaving `label` off a reputation level does not leave it unnamed; it names it `Level 1` through `Level 10`. A numbered ladder communicates no community identity and removes the social signal that makes reputation worth having. Assert the labels back out of the org after deploy.

2. **Enabling ideation without a written status set and named owners** — `Idea.Status` is a customizable picklist with no standard values, so "the standard statuses" do not exist until someone writes them down. An ideation feature with no status movement communicates that feedback is not read, which is worse than no ideation feature at all.

3. **Treating content ownership as a post-launch concern** — Content that has no owner ages out. Assigning ownership after launch is harder because the community sponsor's attention has shifted to adoption and moderation. Ownership must be a pre-launch deliverable.

4. **A calendar of content with no topics** — A calendar item that names no managed topic has no navigation path, no `TopicAssignment` row, and therefore no way to tell afterwards whether it worked. The topic is what makes the item measurable.

5. **A recognition programme with no escalation path** — Rewarding answering does nothing for the questions nobody answers, and those are the ones that reach the sponsor as complaints. The engagement strategy owns the escalation trigger and the named queue even though the moderation skill owns the rules.

## Official Sources Used

- Metadata API Developer Guide — `Network`: `enableReputation`, `reputationLevels`, `reputationPointsRules`, `enableKnowledgeable`, `enableTopicSuggestions`, `enableTopicAssignmentRules`, `enableTalkingAboutStats`, `allowMembersToFlag` (the reputation and topic switches in SKILL.md § Core Concepts and the deployable fragment in worked-examples.md §7); `ReputationLevelDefinitions` / `ReputationLevel` / `ReputationPointsRules` / `ReputationPointsRule` including the 16 `eventType` values, their default points, the optional `label` with its ten `Level N` defaults, and `lowerThreshold` as the only authored bound (Gotchas 2, 3 and 6)
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `ManagedTopics` / `ManagedTopic`: `managedTopicType` values, `parentName` restricted to navigational topics, API-only `topicDescription`, and `position` "between 0 and 24. (The maximum amount of navigational or featured topics is 25.)" (the topic list in worked-examples.md §4 and the Adaptable pillar above); `IdeasSettings` and `Community` (Zone) `reputationLevels` (Gotchas 5 and 6); `ModerationRule` and `KeywordList` org-wide caps of 30 each (the moderation tradeoff above and worked-examples.md §5)
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference for Salesforce — `NetworkMember` (`ReputationPoints` updateable, `LastChatterActivityDate`, and "You can directly update reputation points for a member via the Salesforce API"), `ReputationLevel` (query-only, four fields), `ChatterActivity` (the `ParentId` requirement and the missing rows for members who never posted), `FeedItem` (no aggregate functions, no `NetworkScope` filter, `BestCommentId`, `IsClosed`, `Type` `QuestionPost`, the pre-moderation `CommentCount` tip), `Topic` (`TalkingAbout`, the spacing-and-capitalization-only rename), `TopicAssignment` (the 1,100-row bound), `Idea` / `IdeaTheme` / `IdeaReputationLevel`, `Case.FeedItemId`, `NetworkActivityAudit` — the whole measurement table in SKILL.md and Gotchas 1, 4, 5, 6, 7, 8, 9, 10 and 11
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Salesforce Developer Limits and Allocations Quick Reference — checked for community, Chatter, topic, reputation and member allocations; **no applicable limit found**, which is why every numeric claim in this skill is cited to the Metadata API guide or the Object Reference instead (negative result recorded deliberately so the next author does not re-run the search)
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- `skills/admin/experience-cloud-moderation/SKILL.md` — owns `KeywordList`, `ModerationRule`, the moderation queue and the `Moderate Experiences Feeds` permission that the escalation policy in worked-examples.md §5 hands off to; its own description scopes tier naming and behaviour choice back to this skill
- `skills/admin/self-service-design/SKILL.md` — owns the deflection journeys, article visibility matrix and case exposure model that the peer-support layer of this strategy sits on top of, and grounds the same org-wide moderation cap from the requirements side
- `agents/experience-cloud-admin-designer/AGENT.md` — the run-time consumer: cites this skill in its Mandatory Reads as "engagement mechanics (reputation, recognition, gamification) that decide whether the site is used at all", and takes the §8 strategy YAML as its engagement input
- Salesforce Well-Architected — architecture quality framing for the Trusted / Adaptable / Operational Excellence pillars used above
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
