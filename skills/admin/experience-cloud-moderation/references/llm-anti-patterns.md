# LLM Anti-Patterns — Experience Cloud Moderation

Common mistakes AI coding assistants make when generating or advising on Experience Cloud moderation configuration. These patterns help the consuming agent self-check its own output. Cites are to the Winter '27 (264) `api_meta`, `object_reference` and `apexdev` guides.

UNVERIFIED (2026-10-20): Anti-Patterns 3 (Flag stays live), 5 (reputation not retroactive), 6 (external licenses) and the permission API name in the last pattern restate Help-only claims and are marked inside each.

## Anti-Pattern 1: Confusing CMS Content Publishing with Community Content Moderation

**What the LLM generates:** Instructions for publishing CMS content, creating content items in Digital Experiences, or configuring CMS workspace workflows when the user asks about "moderating Experience Cloud content" or "approving content before it goes live."

**Why it happens:** "Content" in Experience Cloud context can mean CMS-managed pages/articles or member-generated feed posts/comments. LLMs trained on broad Salesforce documentation conflate the two. CMS content publishing uses Digital Experience Builder and CMS workspaces; community content moderation uses ModerationRule, keyword lists, and the Chatter moderation queue.

**Correct pattern:**
```
Community content moderation applies to member-generated feed posts and comments.
It is configured with ModerationRule and KeywordList metadata (api_meta 264 L84916, L92203);
the Moderation feed holds flagged items (apexdev 264 L25687-25688).
UNVERIFIED (2026-10-20): the Setup > Experience Cloud Sites > [Site] > Moderation path is Help-only.

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
3. Enable "Moderate Experiences Feeds" (Moderation feed, apexdev 264 L25687-25688) and, for those who publish
   held items, "Can Approve Feed Post and Comment" or Modify All Data (edit and delete, object_reference 264
   L136986-136990; a held comment to Published, L136377-136379).
4. Assign the permission set to all moderators.
5. Confirm moderators can open the Moderation feed. UNVERIFIED (2026-10-20): the Experience Workspaces location is Help-only.
```

**Detection hint:** If a moderation setup response does not mention "Moderate Experiences Feeds", the approval permission, or permission assignment, the response is incomplete.

---

## Anti-Pattern 3: Treating Flag and Review as Equivalent Actions

**What the LLM generates:** Steps that use Flag and Review interchangeably, or descriptions stating that both actions "hold content for moderator review" without distinguishing visibility behavior.

**Why it happens:** Both actions involve moderator attention, which leads to conflation. LLMs often describe both as "flagging for review" without noting the critical difference: Review leaves the item PendingReview, visible only to its author and permitted users (object_reference 264 L136986-136990); UNVERIFIED (2026-10-20): that Flag leaves content live and visible to all members is Help-only.

**Correct pattern:**
```
Flag:   The item appears in the Moderation feed (apexdev 264 L25687).
        UNVERIFIED (2026-10-20): that the content stays LIVE and visible to all members is Help-only.

Review: Status PendingReview: visible to its author and to users who see it and have View All Data or
        Can Approve Feed Post and Comment; those with Can Approve Feed Post and Comment or Modify All Data
        can edit and delete it (object_reference 264 L136986-136990), and change a held comment
        to Published (L136377-136379).
        Use when: content must not be visible until approved (new member throttling, high-risk keywords).
```

**Detection hint:** Any description of Review that says content is "visible to all members" is incorrect (L136986-136990). A description of Flag as "held" is UNVERIFIED (2026-10-20), since the corpus documents only that flagged items reach the Moderation feed.

---

## Anti-Pattern 4: Not Addressing Rule Order When Multiple Rules Are Configured

**What the LLM generates:** Lists of moderation rules without specifying order or with rules listed in an arbitrary sequence that places less restrictive rules above more restrictive ones.

**Why it happens:** LLMs generating rule lists focus on what each rule does, and assume the Setup list order decides precedence. In fact precedence is by action (api_meta 264 L92226-92229).

**Correct pattern:**
```
Rules that block content run first, then rules to review and approve content, then rules that
replace content, and last rules that flag. Among rules with the same action the oldest rule
runs first (by creation date). Replace rules do not run when the content also applies to a
review rule (api_meta 264 L92226-92229).

So: do not tell the user to reorder rules in Setup to change precedence; choose the action.
Count against the org limits: 30 rules (content and rate together), three keyword criteria per rule (L92218-92219).
```

**Detection hint:** Any output that says "first matching rule wins" or "reorder the list so Block is on top" is wrong; precedence is by action.

---

## Anti-Pattern 5: Recommending Reputation Configuration on a Live Community Without Testing Existing Members

**What the LLM generates:** Instructions to set up or update reputation levels on a live community without testing how existing members are treated (UNVERIFIED (2026-10-20): that points are not retroactive and existing members start at Level 1 is Help-only).

**Why it happens:** LLMs apply reputation configuration steps without contextualizing them for live vs. new sites. Whether history earns points is not stated in the corpus, so the safe default is a sandbox test.

**Correct pattern:**
```
UNVERIFIED (2026-10-20): that reputation points are NOT retroactive, so members who were active before
reputation was configured start at 0 points and Level 1, is Help-only; the corpus is silent.

Before configuring reputation on an active community, test with an account that has prior activity, then:
- Audit current member activity and determine whether manual point adjustments are needed.
- Temporarily relax any Member Criteria moderation rules that reference reputation levels
  until members have had time to earn points.
- Communicate changes to the community so members understand the new system.
```

**Detection hint:** Any reputation setup response for a live or existing community that does not mention a prior-activity test or member communication should be flagged as incomplete.

---

## Anti-Pattern 6: Assuming External Community Members Can Access the Moderation Queue

**What the LLM generates:** Suggestions to assign community manager roles or community-level permissions to external partner or customer users to give them moderation queue access.

**Why it happens:** LLMs conflate Experience Cloud community roles (which can be assigned to external users) with internal Salesforce platform permissions. Whether Customer Community or Partner Community license users can hold the moderation permissions is UNVERIFIED (2026-10-20): Help-only.

**Correct pattern:**
```
UNVERIFIED (2026-10-20): that the Moderate Experiences Feeds permission can only be assigned to internal
Salesforce users, and that Customer Community and Partner Community license users cannot be granted
it, is Help-only. Verify the license and permission pairing in a sandbox.

If the moderation team includes external users:
- Provision them with internal Salesforce user accounts with appropriate licenses.
- Or establish an escalation path to internal moderators.
```

**Detection hint:** Any recommendation to assign moderation queue access to a partner or customer community user without a sandbox check of the license pairing should be flagged.

---

## Anti-Pattern: Deriving the Permission's API Name from Its Setup Label

UNVERIFIED (2026-10-20): this whole pattern rests on the metadata API name `ModerateNetworkFeeds`, which is not in the corpus. Neither `ModerateNetworkFeeds` nor `ModerateExperiencesFeeds` appears in any Winter '27 guide; the pattern's advice to look the name up in the org's own retrieved metadata is the only part that holds.

**What the LLM generates:** Deployment metadata, a permission-set XML snippet,
or a validation script that looks for the feed-moderation permission under a
camel-cased version of its Setup label:

```xml
<!-- UNVERIFIED (2026-10-20): not confirmed against a retrieved .permissionset; do not assume this spelling -->
<userPermissions>
    <enabled>true</enabled>
    <name>ModerateExperiencesFeeds</name>
</userPermissions>
```

```python
# UNVERIFIED (2026-10-20): whether this matches a real .permissionset file is not confirmed
if "ModerateExperiencesFeeds" in permission_set_xml:
    ...
```

**Why it happens:** For many Salesforce user permissions, stripping the spaces
out of the Setup label produces the API name (`ManageUsers` appears in the Audience sample,
api_meta 264 L26541). That heuristic becomes a default. UNVERIFIED (2026-10-20): that feed
moderation is a case where the label was renamed across releases while the API name stayed at
an older spelling is Help-only.

**Correct pattern:**

```
Setup label:        Moderate Experiences Feeds
Metadata API name:  retrieve a .permissionset from the org and read it (UNVERIFIED 2026-10-20: the commonly cited
                    value ModerateNetworkFeeds is Help-only)
```

The same label-vs-API drift affects the neighbouring site permissions, so
resolve each one against the metadata rather than transliterating the label.

**Detection hint:** Any permission-set XML that derives the name by stripping spaces from the
Setup label is unverified. Compare it with the names in a `.permissionset` retrieved from the
org. UNVERIFIED (2026-10-20): that the token `ModerateExperiences` never exists in the metadata
vocabulary, and that the underlying object family is `Network`, are Help-only.
