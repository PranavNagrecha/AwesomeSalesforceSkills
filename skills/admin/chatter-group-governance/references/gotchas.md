# Gotchas — Chatter Group Governance

Non-obvious platform behaviors that bite admins during chatter group lifecycle work.

---

## Gotcha 1: Archiving a group does NOT delete `EntitySubscription` records

**Symptom:** Admin archives a group to "stop notifications." Members continue to receive notifications about activity if the group is later unarchived, and members continue to count toward feed-following limits.

**Why:** Archive flips `CollaborationGroup.IsArchived = true` and stops new posts. It does not touch `CollaborationGroupMember` (members stay members) or `EntitySubscription` records (any record-following relationships persist). The group becomes read-only but the membership graph is intact.

**Fix:** If the goal is "remove all traces of this group," archive is the wrong tool — delete is. If archive is correct (preserve audit trail) but you also want to stop *follow notifications* from the group's parent record, separately purge `EntitySubscription` records pointing at that group's content (rare; usually unnecessary).

---

## Gotcha 2: Deactivating the group owner does NOT reassign the group

**Symptom:** Admin deactivates a user during offboarding. Weeks later discovers 30 active groups still have the deactivated user as `OwnerId`. Group is now "stuck" — owner-only operations (delete, ownership transfer) fail unless a system admin intervenes.

**Why:** `CollaborationGroup.OwnerId` is a hard reference to `User.Id`. There is no Salesforce-side automation that reassigns ownership when `User.IsActive` flips to false. The group continues to function for member posting because group managers can run the day-to-day, but the owner-only privileges are inaccessible until an admin updates `OwnerId`.

**Fix:** Before deactivating any user, query their owned groups (`SELECT Id FROM CollaborationGroup WHERE OwnerId = :userId AND IsArchived = false`) and reassign to the named backup manager (or to a steward service account). Bake this into the offboarding checklist.

---

## Gotcha 3: A deleted user's Id can still appear as `OwnerId`

**Symptom:** Admin runs `SELECT OwnerId, Owner.IsActive FROM CollaborationGroup WHERE OwnerId = '0050000000ABCDE'` and gets back rows where `Owner` is `null`. Group functions but ownership transfer UI errors out with "Invalid User."

**Why:** A `User` record can be deactivated (`IsActive = false`) and stays in the system, queryable. But certain destructive operations (full purge, sandbox refresh from prod with reduced data, GDPR / DSR delete workflows) can remove the underlying user row. The `OwnerId` field on `CollaborationGroup` is then dangling.

**Fix:** When auditing ownership, also handle the `Owner = null` case — these are the worst-case orphans because the UI can't show you an owner name. Anonymous Apex `UPDATE CollaborationGroup SET OwnerId = :stewardId WHERE OwnerId = '0050000000ABCDE'` works even with a dangling reference.

---

## Gotcha 4: Unlisted groups are invisible to admins via UI search but visible via SOQL

**Symptom:** Compliance team asks "list every group containing the word 'merger'." Admin uses Setup → All Chatter Groups search, finds 4 groups. Compliance later discovers a 5th — an Unlisted group that the searching admin wasn't a member of.

**Why:** Unlisted groups (`CollaborationType = 'Unlisted'`) are invisible to non-members in the UI by design. They do not appear in group search, group recommendations, or group lists. They DO appear in SOQL queries run by admins with "View All Data" / "Modify All Data" permissions — `SELECT Id, Name FROM CollaborationGroup WHERE CollaborationType = 'Unlisted'` returns the full set.

**Fix:** Compliance / audit / discovery work must use SOQL, not the UI. Train the audit team on `SELECT * FROM CollaborationGroup` rather than UI search. If Unlisted groups are not needed for the org's use case, disable them entirely (Setup → Chatter Settings → "Enable Unlisted Groups" off).

---

## Gotcha 5: `CollaborationType` cannot be changed from Unlisted to Public/Private

**Symptom:** Admin tries to convert an Unlisted group to Public after the executive committee disbands. Update silently fails or returns "Unlisted groups cannot be converted to other types."

**Why:** Unlisted is one-way. The platform reasoning is that converting an Unlisted-to-Public would expose previously-private content to a wider audience without an explicit opt-in by every prior poster. Public ↔ Private is bidirectional; Unlisted is a sealed lifecycle.

**Fix:** If an Unlisted group's content should become broader visibility, the path is: (a) export the relevant `FeedItem` content, (b) create a new Public/Private group, (c) re-post relevant content there with the original posters' consent, (d) archive (or delete) the original Unlisted group. There is no in-place migration.

---

## Gotcha 6: Auto-archive uses `LastFeedModifiedDate`, not `LastModifiedDate` or member visit time

**Symptom:** A group used as a "reference library" — members view content but rarely post — auto-archives unexpectedly. The owner protests "people use this every day."

**Why:** Auto-archive measures inactivity by `LastFeedModifiedDate`, which advances only when there is a new post or comment in the group's feed. Member views, group description edits, member additions, and metadata changes do *not* advance it.

**Fix:** For "reference library" or "broadcast announcement" groups where reads matter more than writes, either set the org auto-archive setting to "Never," or have the owner post a placeholder comment ("Still actively used — refreshing the clock") quarterly. The placeholder comment is the lowest-effort defense.

---

## Gotcha 7: Deleting a group cascade-deletes `FeedItem` records — that's an audit-trail loss

**Symptom:** Admin deletes 200 dormant groups for cleanup. Compliance team later asks for the conversation history of one of them (regulatory inquiry). Data is gone — the group's `FeedItem` records were cascade-deleted with the group.

**Why:** `delete CollaborationGroup` cascade-deletes the group's `CollaborationGroupMember` (membership rows) AND its associated `FeedItem` records (the feed posts that had `ParentId = <groupId>`). The `FeedItem` rows go to Recycle Bin for 15 days, then are purged. After that, conversation history is unrecoverable.

**Fix:** If the group has *any* substantive `FeedItem` content (>10 posts with qualitative content, or any post older than ~12 months), prefer **archive** to **delete**. Archived groups preserve the audit trail in `CollaborationGroup` + `FeedItem` indefinitely; deleted groups don't. Reserve delete for empty / abandoned / clearly-test groups.

---

## Gotcha 8: Public groups expose posts to Customer Community users with feed access

**Symptom:** Internal users post sensitive-but-not-secret content in a "Public" Chatter group ("Public" = "open to all internal users"). External Customer Community users with feed access on the parent record (or who somehow gained group view rights) see the posts.

**Why:** "Public" in Chatter group context means "open to all users with Chatter access in the org" — and if Experience Cloud / Customer Community users have Chatter feed access enabled (set per-license, per-feature), they CAN see Public group posts depending on community visibility configuration. The post's `Visibility` defaults to `AllUsers`. "Public" in Chatter group naming language is not the same as "Internal-only."

**Fix:** For internal-sensitive content, use **Private** groups (invitation-only, members only see posts) or set `FeedItem.Visibility = 'InternalUsers'` on individual posts. If the entire group should be internal-only, Private is the right group type. Don't trust the word "Public" to mean what it means in everyday usage.

---

## Gotcha 9: `CollaborationGroup.MemberCount` lags membership changes by up to 5 minutes

**Symptom:** Admin adds 50 members to a group via Apex `insert CollaborationGroupMember`. Immediately queries `MemberCount` and sees the old number. Concludes the insert failed.

**Why:** `MemberCount` is a denormalized rollup field updated by an internal asynchronous job. Same-transaction reads return the pre-update value. The lag is normally seconds but can be up to several minutes in busy orgs.

**Fix:** Don't trust `MemberCount` as a real-time count. For accurate post-DML counts, query `SELECT COUNT(Id) FROM CollaborationGroupMember WHERE CollaborationGroupId = :groupId`. Use `MemberCount` for periodic reporting and dashboards where freshness within a few minutes is acceptable.
