# LLM Anti-Patterns — Experience Cloud Moderation

Common mistakes AI coding assistants make when generating or advising on Experience Cloud moderation configuration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing CMS Content Publishing with Community Content Moderation

**What the LLM generates:** Instructions for publishing CMS content, creating content items in Digital Experiences, or configuring CMS workspace workflows when the user asks about "moderating Experience Cloud content" or "approving content before it goes live."

**Why it happens:** "Content" in Experience Cloud context can mean CMS-managed pages/articles or member-generated feed posts/comments. LLMs trained on broad Salesforce documentation conflate the two. CMS content publishing uses Digital Experience Builder and CMS workspaces; community content moderation uses ModerationRule, keyword lists, and the Chatter moderation queue.

**Correct pattern:**
```
Community content moderation applies to member-generated feed posts and comments.
It is configured in: Setup > Experience Cloud Sites > [Site] > Moderation.
Relevant objects: ModerationRule, KeywordList, Chatter moderation queue.

CMS content publishing is a separate workflow using Digital Experience Builder
and Salesforce CMS workspaces. Do not mix these two workflows.
```

**Detection hint:** If the response mentions CMS workspaces, content items, or Digital Experience Builder in the context of a moderation setup request, flag as likely off-target.

---

## Anti-Pattern 2: Omitting the Moderate Experiences Feeds Permission Assignment

**What the LLM generates:** Moderation rule and reputation configuration steps that end without assigning the Moderate Experiences Feeds permission to any user.

**Why it happens:** The permission step is administrative housekeeping that LLMs deprioritize when focused on the "interesting" configuration (rules and reputation). Without this permission, the moderation queue is inaccessible and Review-status content accumulates unseen.

**Correct pattern:**
```
After creating moderation rules, always include:
1. Identify the users who will serve as moderators.
2. Create or select a permission set.
3. Enable "Moderate Experiences Feeds" in the permission set.
4. Assign the permission set to all moderators.
5. Confirm moderators can access the moderation queue in Experience Workspaces.
```

**Detection hint:** If a moderation setup response does not mention "Moderate Experiences Feeds" or permission assignment, the response is incomplete.

---

## Anti-Pattern 3: Treating Flag and Review as Equivalent Actions

**What the LLM generates:** Steps that use Flag and Review interchangeably, or descriptions stating that both actions "hold content for moderator review" without distinguishing visibility behavior.

**Why it happens:** Both actions involve moderator attention, which leads to conflation. LLMs often describe both as "flagging for review" without noting the critical difference: Flag leaves content live and visible to all members; Review hides content from all members except the author and moderators until approved.

**Correct pattern:**
```
Flag:   Content is LIVE and visible to all members. A moderator queue entry is created.
        Use when: content is acceptable to show live but warrants a human look.

Review: Content is HIDDEN from all community members except the author and moderators.
        Moderator must approve before it becomes visible to others.
        Use when: content must not be visible until approved (new member throttling, high-risk keywords).
```

**Detection hint:** Any description of Flag that says content is "hidden" or "held" is incorrect. Any description of Review that says content is "visible to members" is incorrect.

---

## Anti-Pattern 4: Not Addressing Rule Order When Multiple Rules Are Configured

**What the LLM generates:** Lists of moderation rules without specifying order or with rules listed in an arbitrary sequence that places less restrictive rules above more restrictive ones.

**Why it happens:** LLMs generating rule lists focus on what each rule does, not on the evaluation order. The "first match wins" behavior of Salesforce moderation rule evaluation is a non-obvious platform detail that is easy to omit.

**Correct pattern:**
```
Moderation rules are evaluated top to bottom. First matching rule fires; no further rules
are evaluated for the same content item.

Recommended order:
1. Block rules (most restrictive — prevent post submission entirely)
2. Review rules (hold content pending approval)
3. Flag rules (mark live content for moderator attention)

Always review and explicitly state rule order when generating a moderation rule configuration.
```

**Detection hint:** If a multi-rule configuration is presented without an explicit ordering recommendation or without noting "first match wins," the response is incomplete.

---

## Anti-Pattern 5: Recommending Retroactive Reputation Configuration Without Warning

**What the LLM generates:** Instructions to set up or update reputation levels on a live community without noting that points are not retroactive and existing members will start at Level 1.

**Why it happens:** LLMs apply reputation configuration steps without contextualizing them for live vs. new sites. The non-retroactive behavior is a platform constraint that is not highlighted in basic setup documentation.

**Correct pattern:**
```
Reputation points are NOT retroactive. Members who have been active before
reputation was configured will start at 0 points and Level 1.

Before configuring reputation on an active community:
- Audit current member activity and determine whether manual point adjustments are needed.
- Temporarily relax any Member Criteria moderation rules that reference reputation levels
  until members have had time to earn points.
- Communicate changes to the community so members understand the new system.
```

**Detection hint:** Any reputation setup response for a live or existing community that does not mention retroactivity or member communication should be flagged as incomplete.

---

## Anti-Pattern 6: Assuming External Community Members Can Access the Moderation Queue

**What the LLM generates:** Suggestions to assign community manager roles or community-level permissions to external partner or customer users to give them moderation queue access.

**Why it happens:** LLMs conflate Experience Cloud community roles (which can be assigned to external users) with internal Salesforce platform permissions. The Moderate Experiences Feeds permission is a platform permission that cannot be granted to users on Customer Community or Partner Community licenses without an internal user account.

**Correct pattern:**
```
The Moderate Experiences Feeds permission is a Salesforce platform permission.
It can only be assigned to internal Salesforce users via profile or permission set.
External community members (Customer Community, Partner Community license) cannot
be granted this permission.

If the moderation team includes external users:
- Provision them with internal Salesforce user accounts with appropriate licenses.
- Or establish an escalation path to internal moderators.
```

**Detection hint:** Any recommendation to assign moderation queue access to a partner or customer community user without noting the internal license requirement should be flagged.
