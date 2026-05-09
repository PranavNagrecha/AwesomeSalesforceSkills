# Examples — Chatter Group Governance

Concrete, before/after examples for each governance lever. Apply in workflow order — inventory first, policy second, cleanup last.

---

## Example 1 — Inventory: who owns the groups, and how dead are they?

**Symptom:** "We have a lot of Chatter groups. We don't know how many or how many are dead."

Run these in Workbench / Developer Console / `sfdx force:data:soql:query`. They are read-only and safe in production.

**Active vs archived split:**

```sql
SELECT IsArchived, COUNT(Id) cnt
FROM CollaborationGroup
GROUP BY IsArchived
```

**Ownership concentration (find the inactive-owner orphans):**

```sql
SELECT OwnerId, Owner.Name, Owner.IsActive, COUNT(Id) cnt
FROM CollaborationGroup
WHERE IsArchived = false
GROUP BY OwnerId, Owner.Name, Owner.IsActive
ORDER BY COUNT(Id) DESC
```

The rows where `Owner.IsActive = false` are your immediate ownership-transfer queue. In a typical org that has run for 5+ years without governance, this can be 30–60% of active groups.

**Inactivity by group:**

```sql
SELECT Id, Name, MemberCount, LastFeedModifiedDate, OwnerId
FROM CollaborationGroup
WHERE IsArchived = false
ORDER BY LastFeedModifiedDate ASC NULLS FIRST
LIMIT 200
```

`LastFeedModifiedDate` is the canonical inactivity field — it updates on any new post or comment in the group's feed. `LastModifiedDate` on `CollaborationGroup` reflects metadata changes (description edited, member added) and is *not* a good inactivity proxy.

---

## Example 2 — Policy: lock down group creation to trained leaders

**Symptom:** Anyone with an internal license can create groups, and they do — there are 800 groups in a 200-person org.

**Where it lives:** Setup → Permission Sets → New: "Chatter Group Creator." On the permission set, enable *System Permissions → Create and Own New Chatter Groups*. Then on the System Administrator profile (and any other "trusted" profiles), *remove* the permission so it must be granted explicitly.

**Steps:**

1. Setup → Profiles → for each non-admin profile, find "Create and Own New Chatter Groups" and uncheck.
2. Setup → Permission Sets → New: "Chatter Group Creator." On the perm set, enable "Create and Own New Chatter Groups."
3. Assign the perm set to a small, trained group of users (team leads, project managers).
4. Update the org's group-governance runbook with the assignment criteria.

**Effect:** Existing groups are unaffected. New group creation is restricted to perm-set holders. Sprawl rate falls to ~10% of pre-policy levels in most orgs.

**Alternative:** Disable group creation entirely org-wide (Setup → Chatter Settings → uncheck "Allow Group Creation"). Heavy-handed; do this only if the goal is "stop creation entirely until governance is in place" and re-enable selectively after.

---

## Example 3 — Cleanup: bulk reassign orphaned-owner groups

**Symptom:** 240 active groups owned by users with `IsActive = false`. The organization needs ownership transferred to a "Chatter Stewards" service-account user before the legacy users are fully purged.

**Anonymous Apex (run as system administrator):**

```apex
// Replace with the actual service-account / steward user ID
Id stewardUserId = '0050000000ABCDE';

List<CollaborationGroup> orphans = [
    SELECT Id, Name, OwnerId
    FROM CollaborationGroup
    WHERE IsArchived = false
    AND Owner.IsActive = false
    LIMIT 10000
];

System.debug('Found ' + orphans.size() + ' active groups with inactive owners');

for (CollaborationGroup g : orphans) {
    g.OwnerId = stewardUserId;
}

if (!orphans.isEmpty()) {
    update orphans;
    System.debug('Reassigned ' + orphans.size() + ' groups to steward user');
}
```

**Pre-flight checks before running:**

- Confirm the steward user has a *Chatter Plus* or full Salesforce license — Chatter Free / External users cannot own most group types.
- Confirm the steward user is *not* in any of the groups already (they will be added as owner; if they were a manager, role transitions cleanly, but verify).
- Run in a sandbox first to confirm row count matches your audit query.
- Limit batch to 10,000 (the soft DML limit per transaction); for larger orgs use a Batch Apex job instead.

**Why a service-account owner, not a department head:** assigning 240 groups to "Jane Smith, VP Sales" creates a future re-orphan when Jane leaves. A dedicated steward user is owned by IT / Salesforce admin; ownership is institutional rather than personal.

---

## Example 4 — Decide: archive or delete a stale group

A group with 12 members hasn't been posted to in 18 months. Owner left the company a year ago.

**Decision tree:**

| Question | Answer | Action |
|---|---|---|
| Does the group have substantive past posts (>20 `FeedItem` records, qualitative content)? | Yes | **Archive.** Audit trail preserved. |
| Does the group have substantive past posts? | No, mostly empty | Continue. |
| Was the group ever explicitly used (>3 members, named purpose in description)? | Yes | **Archive.** Cheap to keep, hard to restore if deleted in error. |
| Was the group ever explicitly used? | No, looks abandoned | **Delete.** Keep org clean. |

**Archive (preserves data):**

```apex
CollaborationGroup g = [SELECT Id, IsArchived FROM CollaborationGroup WHERE Id = :groupId];
g.IsArchived = true;
update g;
```

**Delete (permanent after 15-day Recycle Bin):**

```apex
CollaborationGroup g = [SELECT Id FROM CollaborationGroup WHERE Id = :groupId];
delete g;
// Cascades: CollaborationGroupMember, FeedItem rows for this group's parent, EntitySubscription rows
```

**Bulk archive of inactive 'Project-*' groups not posted to in >365 days:**

```apex
List<CollaborationGroup> stale = [
    SELECT Id, Name, LastFeedModifiedDate
    FROM CollaborationGroup
    WHERE IsArchived = false
    AND Name LIKE 'Project-%'
    AND LastFeedModifiedDate < :Date.today().addDays(-365)
    LIMIT 5000
];
for (CollaborationGroup g : stale) {
    g.IsArchived = true;
}
update stale;
System.debug('Archived ' + stale.size() + ' stale Project-* groups');
```

This relies on the naming convention being respected. Without prefixes you must qualify by `Description` or by ad-hoc Id list.

---

## Example 5 — Auto-archive setting, configured deliberately

**Where it lives:** Setup → Chatter Settings → "Archive Inactive Groups." Default in many orgs is 90 days but the value is editable.

**Recommended values per group purpose:**

| Group purpose | Auto-archive value | Reason |
|---|---|---|
| Project / sprint groups | 90 days (default) | Projects have natural end dates; auto-archive aligns. |
| Standing team groups (`Team-*`) | 180 days or "Never" | Team groups can have quiet weeks without being abandoned. |
| Topic / interest groups (`Topic-*`) | 180 days | Slow-burn engagement; 90 days under-counts active groups. |
| Broadcast / announcement (`Announce-*`) | "Never" auto-archive | Read-mostly groups have low post velocity by design. |
| Customer-specific groups (`Customer-*`) | 365 days | Customer relationships span quarters; don't archive an active account's group because of a quiet month. |

The org-level setting is single-valued — you pick one number. Per-group exceptions are managed by the owner manually un-archiving the group periodically (the group's member activity won't reset the auto-archive clock since `LastFeedModifiedDate` is post-driven, not visit-driven). For groups that should never auto-archive, the practical defense is the owner posting a "still active — re-checking in" comment quarterly.

If the org has a strong mix of project and standing groups, use a longer org-wide value (180 days) and accept that fully-dead project groups will live a bit longer before auto-archive kicks in — better than over-archiving active team groups.

---

## Example 6 — Group Information Template that encodes the policy

**Where it lives:** Setup → Group Information Templates (note: must be enabled in Setup → Chatter Settings first).

**Template Markdown (saved as the org default for new groups):**

```markdown
## Group Charter
[Single-sentence purpose. If you can't write this in one sentence, the group probably shouldn't exist.]

## Group Type
- [ ] Public — open membership, broadcasts and shared knowledge
- [ ] Private — invitation-only, sensitive but not secret
- [ ] Unlisted — invisible to non-members, executive committees only

(If unsure: choose Public. You can change to Private later. Switching to Unlisted is one-way for visibility purposes.)

## Owner & Backup
- Owner: <user>
- Backup Manager: <user> ← required; reassigns ownership if owner leaves
- Steward Service Account: chatter.stewards@<company>.com ← system reassignment if both above are unavailable

## Cadence
- Expected post frequency: [weekly / monthly / quarterly / event-driven]
- Auto-archive after: [follow org default 90 days / longer if standing group]

## End-of-Life
- Trigger to archive: [project complete / team disbanded / quarterly review found dormant]
- Trigger to delete: [archived >365 days, no historic value, no audit need]
```

**Effect:** Group creators see the prompt. Even if 50% ignore it, the 50% who fill it in produce navigable, governed groups. The "Backup Manager" field, when populated, is the single highest-leverage change for offboarding workflow — it gives the system admin a target user for ownership transfer when the owner leaves.

Templates do not enforce structured fields — they're free-form Markdown rendered in the group's Information tab. So the validation is social, not technical. Combined with restricting group creation to perm-set holders (Example 2), the social pressure is sufficient.
