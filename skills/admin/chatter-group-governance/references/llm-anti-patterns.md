# LLM Anti-Patterns — Chatter Group Governance

Common mistakes AI assistants make when an admin asks for chatter group lifecycle help. Avoid these when generating recommendations.

---

## Anti-Pattern 1: Recommending delete when archive is the right call

**What the LLM generates:** "Run `delete CollaborationGroup` on every group inactive for more than a year to clean up the org."

**Why it's wrong:**
- The guide calls the deletion permanent and puts the cascade outside the group: "Deleting a group permanently deletes all posts and comments to the group. It also deletes all files and links posted to the group and **removes the files from other locations where they were shared**" (object_reference.txt L67402–67404). A file shared into the group and into three other records disappears from all four.
- Many "dormant" groups hold substantive content (approval discussions, decision threads, customer escalations) with audit and institutional-memory value.
- "Cleanup" is rarely worth an irreversible loss of audit trail plus collateral file deletion elsewhere in the org.

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
- Unlisted hides the group's *existence*; Private hides its *content*. Both protect content equally from ordinary users. What Unlisted adds is hiding from the org's own auditors: a View All Data holder "can't view unlisted group information, unless they have the Modify Unlisted Groups permission as well," and a Modify All Data holder "can't view or modify unlisted group information, unless they have the Manage Unlisted Groups permission as well" (object_reference.txt L67109–67115). That is a governance liability, not a security feature.
- For most internal-sensitive content, Private is correct. Unlisted should be reserved for cases where the group's existence is itself confidential (M&A working group, executive committee, internal investigation).
- Calling Unlisted "more secure" leads admins to over-use it and creates governance blind spots.

**What to do instead:** Recommend Private as the default for sensitive content. Recommend Unlisted only when the user explicitly says "the existence of this group must be confidential," and in the same breath require a named holder of Manage Unlisted Groups — because without one, no query anybody in the org can run will return a complete group list, and it will not say so.

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
SELECT Id, Name, MemberCount, LastFeedModifiedDate, IsAutoArchiveDisabled
FROM CollaborationGroup
WHERE IsArchived = false
AND (LastFeedModifiedDate < LAST_N_DAYS:365 OR LastFeedModifiedDate = NULL)
```

---

## Anti-Pattern 6: Reassigning orphaned ownership to "any active user" without thought

**What the LLM generates:** "Find any active user and reassign all 240 orphaned groups to them."

**Why it's wrong:**
- Random active users get spammed with notifications and admin responsibilities for groups they have no context on.
- The ownership re-orphans the moment that user leaves.
- A high-status user (VP, director) may decline to be reassigned ownership, creating political friction.

**What to do instead:** Prefer the group's own manager, fall back to a steward service account — the manager-first script in `references/metadata-examples.md` section 4 does exactly that in three queries and one partial-success DML. A steward account is institutionally owned and never leaves; a group manager has context. Picking at random has neither property. And whoever runs the reassignment needs Modify All Data: "Only the current group owner or people with the Modify All Data permission can update the `OwnerId`" (object_reference.txt L67378–67379).

---

## Anti-Pattern 7: Recommending `CollaborationType` change as a routine fix

**What the LLM generates:** "Just change the group type from Unlisted to Public so compliance can find it."

**Why it's wrong:**
- Changing type does not solve the stated problem. Compliance cannot find the group because nobody holds Manage Unlisted Groups (object_reference.txt L67112–67115); the fix is a permission grant, not a data change.
- Type changes have user-experience consequences either way: members who joined under one set of visibility expectations are silently moved to another, with no notification.
- The Connect API cannot express the change at all — `ConnectApi.GroupVisibilityType.Unlisted` is "Reserved for future use" (apexrefguide.txt L111967–111972), so any generated `ConnectApi` code for it is wrong on its face.

<!-- UNVERIFIED (2026-09-05): an earlier revision of this file asserted that CollaborationType cannot be
     changed from Unlisted at all. The Object Reference lists it as an updateable Restricted picklist
     (L67189-67201) and documents no one-way restriction. Do not state the block as fact; test it in a
     sandbox. The advice below holds regardless. -->

**What to do instead:** Answer the actual question — a compliance discovery gap is closed with a
permission set, described in `references/metadata-examples.md` section 2. If a type change is genuinely
wanted, plan it at creation instead; and if the group already exists, the safe migration is: create a new
group of the right type, port relevant content with the original posters' consent, then archive the
original. Never promise an in-place Unlisted conversion you have not tested in that org.

---

## Anti-Pattern 8: Generating an "all Chatter groups" audit and calling it complete

**What the LLM generates:** "Run this as a System Administrator and you'll get every group in the org:"

```sql
SELECT Id, Name, CollaborationType, OwnerId FROM CollaborationGroup
```

**Why it's wrong:** The query is fine; the claim about it is not. Unless the running user holds Manage
Unlisted Groups (or Modify Unlisted Groups for read), unlisted groups are absent from the result — and
Modify All Data does not confer it (object_reference.txt L67109–67117). The result set is silently
partial. Nothing in the output distinguishes "there are no unlisted groups" from "you cannot see the
unlisted groups," which is exactly the distinction a compliance request turns on.

**What to do instead:** State the precondition alongside the query. If the org has
`unlistedGroupsEnabled = true`, the audit is only complete when run by a Manage Unlisted Groups holder;
if nobody holds it, say so as a finding rather than shipping the incomplete list. The bundled checker
raises this as `CGG-UNLISTED-UNGOV` before the export happens.

---

## Anti-Pattern 9: Fixing over-archiving by turning archiving off

**What the LLM generates:** "Your standing groups keep archiving — disable group archiving in Chatter
Settings," or a `Chatter.settings` deploy with `<allowChatterGroupArchiving>false</allowChatterGroupArchiving>`.

**Why it's wrong:** That element is not the automatic sweep alone. The Metadata API guide defines it as
covering "whether **manual and automatic** group archiving are allowed on all Chatter groups"
(api_meta.txt L112476–112480). Setting it `false` removes the *manual* archive action too, which deletes
the safe half of the archive-vs-delete decision for every group in the org — and delete carries the
file-removal cascade at L67402–67404. The recommendation trades a nuisance for an irreversible one.

**What to do instead:** Exempt the affected groups individually with
`CollaborationGroup.IsAutoArchiveDisabled = true` (L67282–67290), a per-group create-and-update boolean
that leaves everyone else's archiving intact. `references/examples.md` Example 5 has the query that finds
which groups deserve it — read-heavy, post-light — and the DML to set it.
