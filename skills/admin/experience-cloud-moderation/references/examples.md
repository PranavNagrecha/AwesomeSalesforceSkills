# Examples — Experience Cloud Moderation

## Example 1: Keyword Block Rule for Spam Prevention

**Context:** A B2B partner community receives posts containing competitor product names that violate community guidelines. The compliance team requires that these terms never appear in any feed post or comment.

**Problem:** Without a Block rule, posts containing prohibited terms are submitted and visible immediately. A Flag rule would leave the content live until a moderator acts — potentially hours. A Replace rule would alter the wording but still reveal the author's intent to other members.

**Solution:**

Setup path: Setup > Experience Cloud Sites > [Partner Community] > Moderation

Step 1 — Create the keyword list:
```
Keyword List Name: Competitor Terms
Keywords: [CompetitorA], [CompetitorB product], [competitive term]
```

Step 2 — Create the moderation rule:
```
Rule Name:      Block Competitor Mentions
Criteria Type:  Keyword List
Keyword List:   Competitor Terms
Content Type:   Posts and Comments
Action:         Block
Rule Order:     1  (top of list)
Active:         true
```

Step 3 — Verify rule order in Setup. The Block rule must appear above any Flag or Review rules in the ordered rule list.

**Why it works:** The Block action rejects the submission at the time of posting. The author receives an error message that their post was not allowed. No version of the content reaches other members. Because the rule is at position 1, it fires before any lower-priority rules would evaluate the same content.

---

## Example 2: Reputation Tiers for Community Contributors

**Context:** A customer community wants to reduce friction for experienced, trusted members while keeping stricter moderation on new accounts. The community team wants members who have demonstrated sustained participation to be exempt from the new-member Review hold.

**Problem:** Applying a blanket Review rule to all new posts would slow down trusted contributors and create moderator queue overload. Applying no rule leaves the community open to spam from brand-new accounts.

**Solution:**

Step 1 — Define reputation levels in Experience Workspaces > Reputation:
```
Level 1: New Member       — 0 points
Level 2: Contributor      — 100 points
Level 3: Trusted Member   — 500 points
Level 4: Community Expert — 2000 points
```

Step 2 — Configure point values per action:
```
Post a question:        10 points
Post an answer:         10 points
Receive a like:         5 points
Best answer selected:   25 points
```

Step 3 — Create a Member Criteria moderation rule:
```
Rule Name:        New Member Content Review
Criteria Type:    Member Criteria
Criteria:         Reputation Level is below Level 2
Content Type:     Posts and Comments
Action:           Review
Active:           true
```

Step 4 — Place this rule below any Block rules in rule order so Block fires first for prohibited keywords regardless of member level.

**Why it works:** Members below Level 2 (under 100 points) have their posts held for moderator approval. As members engage — posting, receiving likes, having answers selected — they accumulate points and cross the Level 2 threshold. Once at Level 2 or above, the Member Criteria rule no longer applies to them. Moderator queue load naturally decreases as the community matures.

---

## Anti-Pattern: Using Flag Instead of Review for New Member Throttling

**What practitioners do:** Create a new-member moderation rule using the Flag action rather than Review, expecting that new member posts will be held for approval.

**What goes wrong:** Flag marks a post for moderator attention but the post is **immediately visible to all community members**. A spam post or policy-violating content is live from the moment of submission. The moderator queue entry is advisory, not a hold. Other community members can read, like, and respond to the flagged content before a moderator acts.

**Correct approach:** Use the Review action when the requirement is "content must not be visible until approved." Use Flag only when the requirement is "post is acceptable to show live, but moderators should take a look." These are meaningfully different actions with different security and compliance implications. Document which scenarios use each action in the community moderation policy before configuring rules.
