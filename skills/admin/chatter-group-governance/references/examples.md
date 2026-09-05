# Examples — Chatter Group Governance

Concrete, before/after examples for each governance lever. Apply in workflow order — inventory first, policy second, cleanup last.

---

## Example 1 — Inventory: who owns the groups, and how dead are they?

**Symptom:** "We have a lot of Chatter groups. We don't know how many or how many are dead."

Run these in Workbench, Developer Console, or `sf data query --target-org <alias>`. They are read-only and safe in production.

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

The rows where `Owner.IsActive = false` are your immediate ownership-transfer queue, and in a long-running org without governance the share is usually large — measure it rather than estimating, because the number is the argument for doing the work.

`Owner` resolving to null is a separate and worse case: the group still functions, but no UI can show you an owner. Catch both in one pass with `WHERE Owner.IsActive = false OR OwnerId = NULL`.

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

**What the platform actually gates.** There is no "allow group creation" switch in `ChatterSettings` — the Metadata API guide's field list for that type has no such element (api_meta.txt L112470–112608). Creation is a *user permission*: "Any user with the Create and Own New Chatter Groups permission can create public, private, and unlisted groups, including in any Experience Cloud sites they belong to" (object_reference.txt L67098–67099). So the lever is where that permission is granted, and nowhere else.

**Steps:**

1. Retrieve the profiles and permission sets, and find every place the permission is enabled — the checker's `CGG-PERM-BROAD` finding does this for you.
2. Remove it from each profile. Profiles apply to everyone assigned; a profile grant is not reviewable.
3. Deploy a `Chatter_Group_Creator` permission set carrying it (shape in `references/metadata-examples.md` section 2).
4. Assign it to the trained team leads and project managers, by name.
5. Record the assignment criteria in the runbook so the next admin knows who qualifies.

**Assign and audit from the CLI**, so the holder list is a command rather than a memory:

```bash
# Assign to the trained cohort
sf org assign permset --name Chatter_Group_Creator \
    --on-behalf-of ateam.lead@example.com \
    --on-behalf-of bteam.lead@example.com \
    --target-org prod

# Audit the resulting holder list, including anyone who has left
sf data query --target-org prod --query "
  SELECT Assignee.Username, Assignee.IsActive, Assignee.Profile.Name
  FROM PermissionSetAssignment
  WHERE PermissionSet.Name = 'Chatter_Group_Creator'
  ORDER BY Assignee.IsActive DESC, Assignee.Username"

# And the escape hatch: anyone with Modify All Data can still act on any public
# or private group regardless of the permission set (object_reference.txt L67112-67115)
sf data query --target-org prod --query "
  SELECT Assignee.Username FROM PermissionSetAssignment
  WHERE PermissionSet.PermissionsModifyAllData = true"
```

**Effect:** Existing groups are unaffected — the permission gates creation, not ownership of what already exists. New creation is restricted to holders.

<!-- UNVERIFIED (2026-09-05): "sprawl rate falls to ~10% of pre-policy levels" was an unsourced figure in an earlier revision of this file and has been removed. Measure the org's own before/after creation rate from CollaborationGroup.CreatedDate rather than quoting a number. -->

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

- Confirm the steward user holds **Modify All Data** — "Only the current group owner or people with the Modify All Data permission can update the `OwnerId`" (object_reference.txt L67378–67379), so an ordinary admin login is not necessarily enough to run this.
  <!-- UNVERIFIED (2026-09-05): an earlier revision claimed Chatter Free / External users cannot own most group types and that a Chatter Plus or full Salesforce license is required. No supplied guide states a license restriction on CollaborationGroup.OwnerId. Verify the steward account's license in a sandbox before relying on it. -->
- Confirm the steward user is *not* in any of the groups already (they will be added as owner; if they were a manager, role transitions cleanly, but verify).
- Run in a sandbox first to confirm row count matches your audit query.
- Keep the query under the 10,000-row DML ceiling per transaction; for larger populations, run this as Batch Apex.
- Prefer `Database.update(list, false)` over bare `update` — one group with a dangling owner should not roll back the other 239. The partial-success version of this script is in `references/metadata-examples.md` section 4.

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

**Delete (treat as permanent):**

```apex
CollaborationGroup g = [SELECT Id FROM CollaborationGroup WHERE Id = :groupId];
delete g;
// Object Reference L67402-67404: "Deleting a group permanently deletes all posts and
// comments to the group. It also deletes all files and links posted to the group and
// removes the files from other locations where they were shared."
// That last clause is why the file check in the decision tree above is not optional.
```

**Bulk archive of inactive 'Project-*' groups not posted to in >365 days:**

```apex
List<CollaborationGroup> stale = [
    SELECT Id, Name, LastFeedModifiedDate
    FROM CollaborationGroup
    WHERE IsArchived = false
    AND IsAutoArchiveDisabled = false
    AND Name LIKE 'Project-%'
    AND LastFeedModifiedDate < LAST_N_DAYS:365
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

## Example 5 — Auto-archive tuned per group, not per org

**Symptom:** A reference-library group and a broadcast channel keep archiving themselves. The first
instinct — raise the org-wide inactivity window, or turn archiving off — is the wrong lever twice over.

**The three levers, and what each one costs:**

| Lever | Scope | Where it lives | Cost of using it |
|---|---|---|---|
| `allowChatterGroupArchiving` | Whole org | `Chatter.settings` (api_meta.txt L112476–112480) | `false` disables **manual** archiving too, so cleanup has only the delete branch left |
| Inactivity window | Whole org | Setup → Chatter Settings | One number for every group purpose; tuning it for standing groups under-archives dead project groups |
| `IsAutoArchiveDisabled` | One group | `CollaborationGroup` field (object_reference.txt L67282–67290) | None — it is a create-and-update boolean, per group, reversible |

**So the pattern is: leave the org-wide setting alone, exempt the named groups.**

Query for the groups that need exempting — read-heavy but post-light — using the members' own read
timestamps rather than the group's post timestamp. `CollaborationGroupMember.LastFeedAccessDate` is
"Date and time when a group member last accessed the group's feed" (L67480–67490), which is exactly the
signal the archive sweep ignores:

```sql
SELECT CollaborationGroupId, CollaborationGroup.Name,
       MAX(LastFeedAccessDate) lastRead, COUNT(Id) readers
FROM CollaborationGroupMember
WHERE LastFeedAccessDate = LAST_N_DAYS:90
GROUP BY CollaborationGroupId, CollaborationGroup.Name
HAVING COUNT(Id) > 5
```

Any group in that result whose `LastFeedModifiedDate` is old is being read but not posted to — an
auto-archive false positive waiting to happen. Exempt it:

```apex
List<CollaborationGroup> exempt = [
    SELECT Id, Name, IsAutoArchiveDisabled
    FROM CollaborationGroup
    WHERE Id IN :readButNotPostedGroupIds
      AND IsAutoArchiveDisabled = false
];
for (CollaborationGroup g : exempt) {
    g.IsAutoArchiveDisabled = true;
}
update exempt;
```

**Which purposes usually earn an exemption:**

| Group purpose | Exempt? | Reason |
|---|---|---|
| Project / sprint (`Project-*`) | No | Projects have natural end dates; the sweep is doing its job |
| Standing team (`Team-*`) | Case by case | Quiet weeks are normal; exempt only the ones the read query flags |
| Topic / interest (`Topic-*`) | Case by case | Slow-burn engagement; the read query separates alive from abandoned |
| Broadcast / announcement (`Announce-*`) | Yes | Read-mostly by design — post velocity is a bad proxy for value here |
| Customer-specific (`Customer-*`) | Yes, while the account is live | The account relationship outlasts the posting cadence |

The old workaround — having the owner post a "still active" comment quarterly to reset the clock — is
strictly worse than the flag: it depends on a human remembering, and it pollutes the feed with content
that exists only to defeat a sweep.

---

## Example 6 — Group Information Template that encodes the policy

**What the platform gives you.** Two fields on the group carry this content: `InformationTitle`, "The
title of the Information section," and `InformationBody`, "The text of the Information section" — both
"For private groups, only visible to members and users with Modify All Data or View All Data permissions"
(object_reference.txt L67247–67273). They are `Create` and `Update`, so the content below can be written
by DML or `ConnectApi.GroupInformationInput`, not only typed by hand.

<!-- UNVERIFIED (2026-09-05): "Setup → Group Information Templates" as a named admin feature, and any
     requirement to enable it in Chatter Settings first, are not in any supplied guide — ChatterSettings
     has no such element (api_meta.txt L112470-112608). What IS grounded is the pair of Information
     fields on CollaborationGroup. If the Setup feature does not exist in the org in front of you, seed
     InformationBody at creation time from the trigger in the note below instead. -->

**Body content to seed on every new group:**

```markdown
## Group Charter
[Single-sentence purpose. If you can't write this in one sentence, the group probably shouldn't exist.]

## Group Type
- [ ] Public — open membership, broadcasts and shared knowledge
- [ ] Private — invitation-only, sensitive but not secret
- [ ] Unlisted — invisible to non-members, executive committees only

(If unsure: choose Public. Public and Private are set at creation and changed only with admin
involvement — see gotchas.md 5 on what is and is not reversible.)

## Owner & Backup
- Owner: <user>
- Backup Manager: <user> ← required; reassigns ownership if owner leaves
- Steward Service Account: chatter.stewards@<company>.com ← system reassignment if both above are unavailable

## Cadence
- Expected post frequency: [weekly / monthly / quarterly / event-driven]
- Auto-archive: [follow the org sweep / exempt via IsAutoArchiveDisabled, with the reason]

## End-of-Life
- Trigger to archive: [project complete / team disbanded / quarterly review found dormant]
- Trigger to delete: [archived >365 days, no historic value, no audit need]
```

**Effect:** Creators see the prompt, and the "Backup Manager" line is the highest-leverage part — it
gives a Modify All Data holder a named transfer target when the owner leaves, instead of a search.

**The one enforcement point that is real.** Information content is advisory; a trigger is not. The
Object Reference names the hook explicitly: "Use Apex triggers on the `CollaborationGroup` object to
monitor and manage the creation of groups. In Setup, enter Group Triggers in the Quick Find box, then
select Group Triggers to add triggers" (L67131–67133). That is where a naming convention becomes
enforceable rather than aspirational:

```apex
trigger CollaborationGroupGovernance on CollaborationGroup (before insert) {
    // Prefixes agreed with the business; keep them in Custom Metadata in a real org.
    Set<String> allowed = new Set<String>{
        'Project-', 'Team-', 'Topic-', 'Announce-', 'Customer-'
    };
    for (CollaborationGroup g : Trigger.new) {
        Boolean ok = false;
        for (String prefix : allowed) {
            if (g.Name != null && g.Name.startsWith(prefix)) { ok = true; break; }
        }
        if (!ok) {
            g.Name.addError(
                'Group names must start with one of: ' + String.join(new List<String>(allowed), ', ')
            );
        }
        if (String.isBlank(g.InformationBody)) {
            g.InformationBody = GroupCharterDefaults.SEED_BODY;
        }
    }
}
```

Two cautions before deploying it. Apex on this object "runs in system mode, which means that the
permissions of the current user aren't taken into account" (L67121–67123), so a trigger that *queries*
groups sees unlisted ones too. And name uniqueness is asymmetric — "Group names must be unique across
public and private groups. Unlisted groups don't require unique names" (L67345–67352) — so a trigger
that dedupes by `Name` must also compare `CollaborationType`.
