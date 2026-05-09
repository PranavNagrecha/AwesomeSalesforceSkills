# LLM Anti-Patterns — Chatter Group Governance

Common mistakes AI assistants make when an admin asks for chatter group lifecycle help. Avoid these when generating recommendations.

---

## Anti-Pattern 1: Recommending delete when archive is the right call

**What the LLM generates:** "Run `delete CollaborationGroup` on every group inactive for more than a year to clean up the org."

**Why it's wrong:**
- `delete CollaborationGroup` cascade-deletes the group's `FeedItem` records — that's the conversation history.
- Many "dormant" groups have substantive past content (approval discussions, decision threads, customer escalations) that has audit and institutional-memory value.
- After the 15-day Recycle Bin window, deleted `FeedItem` data is unrecoverable.
- "Cleanup" is rarely worth the permanent loss of audit trail.

**What to do instead:** Default to archive (`IsArchived = true`). Archive preserves all data, just hides the group from active lists and stops new posts. Reserve delete for groups that are demonstrably empty (e.g., 0–2 substantive `FeedItem` records, no description, name pattern like `Test-*`) or were created in error.

---

## Anti-Pattern 2: Suggesting a Flow updates `User.IsActive` AND reassigns groups in one transaction

**What the LLM generates:** A user-offboarding Flow that simultaneously sets `User.IsActive = false` and updates `CollaborationGroup.OwnerId` to a new user, all in the same record-triggered Flow.

**Why it's wrong:**
- A record-triggered Flow on `User` updates can hit governor limits when scanning all owned groups.
- The Flow runs in the context of the deactivating user — but the deactivation may itself disable session privileges mid-DML.
- "Same transaction" means a failure in the group-reassignment step rolls back the user deactivation; the user expects deactivation to be atomic with their HR offboarding workflow.
- Users own many things besides Chatter groups (records, reports, dashboards, queues). A general-purpose ownership-transfer-on-deactivation should not be welded onto a Chatter-specific Flow.

**What to do instead:** Run group ownership transfer *before* the deactivation, as a separate step in the offboarding checklist. Or, if automation is desired, use a *scheduled* job (Schedulable Apex) that runs nightly: query users deactivated in the last 24h who still own active groups, reassign to the steward account, log the action. This decouples failure modes.

---

## Anti-Pattern 3: Confusing Public, Private, and Unlisted as "more secure / less secure"

**What the LLM generates:** "For sensitive content use Unlisted groups — they're the most secure type."

**Why it's wrong:**
- Unlisted hides the group's *existence* from non-members; Private hides the group's *content* from non-members. Both protect content equally for normal users. Unlisted has the additional property of hiding from compliance discovery via the UI — which is a *governance liability*, not a security feature.
- For most internal-sensitive content, Private is correct. Unlisted should be reserved for cases where the group's existence is itself confidential (M&A working group, executive committee, internal investigation).
- Calling Unlisted "more secure" leads admins to over-use it and creates governance blind spots.

**What to do instead:** Recommend Private as the default for sensitive content. Recommend Unlisted only when the user explicitly says "the existence of this group must be confidential," and pair with a documented compliance-discovery workflow (admin SOQL query, not UI search).

---

## Anti-Pattern 4: Treating archive as "stops notifications" or "removes members"

**What the LLM generates:** "Archive the group and members will stop receiving notifications and lose access."

**Why it's wrong:**
- Archive does NOT remove members. `CollaborationGroupMember` records persist.
- Archive does NOT delete `EntitySubscription` records.
- If the group is later un-archived (single field flip), members are still members and notifications resume.
- Archive sets the group to read-only and hides it from default active-group lists. That's it.

**What to do instead:** Be precise about what archive does and doesn't do. If the goal is "remove all traces and stop notifications permanently," that's delete (with the cost of audit-trail loss). If the goal is "stop new posts but preserve history," that's archive. Map the user's intent to the correct lifecycle state.

---

## Anti-Pattern 5: Querying for "inactive" groups using `LastModifiedDate`

**What the LLM generates:**

```sql
SELECT Id FROM CollaborationGroup
WHERE LastModifiedDate < :Date.today().addDays(-365)
```

**Why it's wrong:** `LastModifiedDate` on `CollaborationGroup` reflects metadata changes — description edits, member adds, ownership changes. It does NOT reflect post or comment activity. A group that hasn't been posted to in 5 years but had a member added last week has a recent `LastModifiedDate`. This query under-counts dormant groups.

**What to do instead:** Use `LastFeedModifiedDate` for activity-based queries. It advances on new posts and comments and is the canonical inactivity indicator. Combine with `MemberCount` and `Description` checks for a fuller picture:

```sql
SELECT Id, Name, MemberCount, LastFeedModifiedDate
FROM CollaborationGroup
WHERE IsArchived = false
AND LastFeedModifiedDate < :Date.today().addDays(-365)
```

---

## Anti-Pattern 6: Reassigning orphaned ownership to "any active user" without thought

**What the LLM generates:** "Find any active user and reassign all 240 orphaned groups to them."

**Why it's wrong:**
- Random active users get spammed with notifications and admin responsibilities for groups they have no context on.
- The ownership re-orphans the moment that user leaves.
- A high-status user (VP, director) may decline to be reassigned ownership, creating political friction.

**What to do instead:** Reassign to a dedicated steward service-account user — institutionally owned, never leaves the company, generates no notification noise (the account doesn't have a real human reading the bell). For groups where a named human owner is genuinely needed (e.g., an active project group), find the existing backup manager via `CollaborationGroupMember.CollaborationRole = 'Admin'` for that group and reassign to them. Don't pick at random.

---

## Anti-Pattern 7: Recommending `CollaborationType` change as a routine fix

**What the LLM generates:** "Just change the group type from Unlisted to Public so compliance can find it."

**Why it's wrong:**
- `CollaborationType` cannot be changed from Unlisted to anything else. The platform blocks the conversion to prevent retroactive exposure of confidential content.
- Even Public ↔ Private conversions are technically allowed but have user-experience consequences (members who joined under one set of visibility expectations are now under different ones).

**What to do instead:** Plan group type at creation. If a wrong type is chosen, the migration path is: (a) create a new group of the right type, (b) port relevant content with original posters' consent, (c) archive (or delete) the original. There is no one-step type change for Unlisted, and Public ↔ Private changes should be done sparingly with member communication.
