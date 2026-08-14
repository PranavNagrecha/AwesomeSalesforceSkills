---
name: chatter-group-governance
description: "Use when admins are governing the Chatter group lifecycle — creation policy, public/private/unlisted visibility decisions, group ownership transfer when owners leave, archived vs inactive vs deleted state changes, auto-archive behavior, naming conventions, group templates (Information Templates), and orphan-group cleanup after user terminations. Triggers: 'we have 800 dead chatter groups', 'group owner left the company who owns it now', 'should this group be public private or unlisted', 'when does a chatter group auto-archive', 'how do I delete vs archive a chatter group', 'we need a chatter group naming convention'. NOT for Chatter notification / digest / feed-noise tuning (use admin/chatter-notification-tuning), NOT for Chatter REST API integration patterns (use apex/apex-connect-api-chatter), NOT for Custom Notifications API (use apex/apex-custom-notifications-from-apex), NOT for Experience Cloud / Customer Community group access (different sharing model)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
tags:
  - chatter-group-governance
  - chatter
  - collaboration-group
  - group-lifecycle
  - group-archival
  - ownership-transfer
triggers:
  - "we have hundreds of dead chatter groups nobody uses"
  - "the chatter group owner left the company, who owns it now"
  - "should this collaboration group be public, private, or unlisted"
  - "what happens when a chatter group auto-archives"
  - "how do I delete vs archive a chatter group and what's the difference"
  - "we need a naming convention for chatter groups before they multiply"
  - "user offboarding left orphaned chatter groups, how do we reassign ownership"
  - "is there a way to bulk-archive groups inactive for a year"
  - "how do I stop end users from creating private chatter groups"
inputs:
  - "Symptom: dead groups, orphaned ownership, naming chaos, or visibility-policy gap"
  - "Scope: org-wide governance baseline vs targeted cleanup vs offboarding response"
  - "Whether end-user group creation is currently allowed (Setup → Chatter Settings)"
  - "Whether unlisted groups are enabled (separate org permission)"
outputs:
  - "Group lifecycle policy: when to archive, when to delete, who owns transfer"
  - "Naming convention + creation-permission recommendation"
  - "Cleanup plan: bulk owner reassignment, archive-stale, delete-empty"
  - "Offboarding hook: detect groups owned by deactivated users and reassign"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-08
runtime_orphan: true
---

# Chatter Group Governance

Activate this skill when an admin needs to design or repair Chatter group lifecycle controls — naming, visibility, ownership, archival, and cleanup. The skill is about *governance* of the group population, not about feed noise inside a single group (use `admin/chatter-notification-tuning` for that).

---

## Before Starting

Gather this context before proposing changes:

- **How many groups exist and how many are dormant.** Run a quick `SELECT COUNT(Id) FROM CollaborationGroup` and a follow-up grouped by `IsArchived`. Most orgs that ask for "governance" have 5–20× more groups than active people, with the bulk dormant for 12+ months.
- **Who can create groups today.** Setup → Chatter Settings has *Group Creation* and *Allow Records in Groups*. Out of the box every internal user can create groups — that's the single biggest driver of group sprawl. Unlisted groups are a separate toggle (*Enable Unlisted Groups*) and are off by default.
- **What ownership currently looks like.** Run `SELECT OwnerId, COUNT(Id) FROM CollaborationGroup WHERE IsArchived = false GROUP BY OwnerId ORDER BY COUNT(Id) DESC`. Concentrations of ownership on inactive users (`User.IsActive = false`) are the primary cleanup target. The `OwnerId` of a group remains pointed at the deactivated user — Salesforce does not auto-reassign on user deactivation.
- **Auto-archive setting.** Setup → Chatter Settings → "Archive groups after n days of inactivity." Default value (in most orgs) is 90 days. Inactivity is measured against `LastFeedModifiedDate`, not `LastModifiedDate` — a group's metadata edit doesn't reset the clock.
- **Are end users creating private groups for sensitive content?** Private and Unlisted groups bypass the standard sharing model for posts inside the group — a Private group is a parallel data island. Compliance teams care.

---

## Core Concepts

### Concept 1 — Three group types, three sharing models

`CollaborationGroup.CollaborationType` is a picklist with three values that drive visibility very differently:

| Type | Discoverable in group list | Posts visible to | Membership requires approval |
|---|---|---|---|
| **Public** | Yes | All internal users (and Customer Community users with feed access if so configured) | No — anyone can join |
| **Private** | Yes (name + description visible, posts not) | Members only | Yes — owner / manager approves |
| **Unlisted** | No (invisible to non-members, even via SOQL for non-admins) | Members only | Invitation only |

Two consequences admins miss:
- A **Public** group is the only type where post content is visible to non-members. If the goal is "broadcast announcement," Public is correct. If the goal is "team workspace with sensitive material," it must be Private or Unlisted.
- **Unlisted** groups are *invisible* — even members of other groups, even managers, even compliance officers cannot find an Unlisted group they aren't a member of without an `IsArchived = false` SOQL run as admin. This is by design (think "executive committee") but it means content in Unlisted groups bypasses normal discoverability for governance/audit. Many orgs leave Unlisted groups disabled (Setup → Chatter Settings) for this reason.

### Concept 2 — Archived ≠ Inactive ≠ Deleted

Three distinct lifecycle states. Confusing them is the most common admin error:

- **Active** — `IsArchived = false`. Group accepts new posts, members receive notifications, group counts against any per-org group limits in shipped product features.
- **Archived** — `IsArchived = true`. Set automatically by the org's auto-archive setting (default 90 days of `LastFeedModifiedDate` inactivity) or manually by the owner / system admin. Archived groups:
  - Stay in `CollaborationGroup` — *not deleted*.
  - Past posts and members are preserved and queryable.
  - No new posts accepted via UI; the group becomes read-only.
  - Members continue to be members; `EntitySubscription` records persist.
  - The group can be unarchived (manually only) and resume activity.
- **Deleted** — record-level `delete` on `CollaborationGroup`. Cascade-deletes `CollaborationGroupMember` and `FeedItem` for that group. *Permanent* after the 15-day Recycle Bin window. Compliance impact: any audit trail of group conversations is gone.

There is no "Inactive" state in metadata — the term is colloquial for "Archived but not yet Deleted." Decide explicitly: archive (preserve audit trail, hide from active lists) or delete (purge permanently).

### Concept 3 — Group ownership and the deactivated-owner problem

`CollaborationGroup.OwnerId` is a hard reference to a `User` record. Two non-obvious behaviors:

1. **Deactivating the owner does NOT reassign the group.** The user is set `IsActive = false`. The group's `OwnerId` still points at them. The group continues to function — members can post, the group can be modified by other group managers — but the *owner-only* operations (deleting the group, transferring it, changing its type) are now stuck unless a system admin intervenes.
2. **Only the current owner or a system admin can transfer ownership.** Transfer is a UI action (group page → Edit Group → Owner) or a SOQL/Apex `UPDATE CollaborationGroup SET OwnerId = :newOwnerId WHERE Id = :groupId` — admins can do this via Anonymous Apex; group managers cannot.

The governance pattern: every group should have a *backup manager* (a `CollaborationGroupMember` with `CollaborationRole = 'Admin'`). The backup manager can post and moderate but cannot transfer ownership; the system admin must do the transfer. So the offboarding workflow is:
- Detect groups owned by users being deactivated (run before the deactivation, ideally).
- Reassign owner to the named backup manager (or to a generic "Chatter Stewards" service account if no backup exists).
- Then deactivate the user.

Doing it in the other order leaves orphaned-owner groups that require manual cleanup later.

### Concept 4 — Group templates (Information Templates) and naming conventions

Salesforce ships *Group Information Templates* — admin-configured Markdown-style templates that prefill the group's "Information" tab on creation. Two practical uses:

- **Encode naming convention in the template.** The template can include explicit guidance ("Name format: `Team-<Department>-<Purpose>`") and required sections (Charter, Members, Cadence). Users who follow the template produce navigable groups; users who skip the template produce orphans.
- **Encode lifecycle policy in the template.** Include "Owner backup," "Auto-archive after N days," "Delete trigger" sections. This makes the policy visible at creation time, not buried in admin docs.

Templates do not *enforce* anything — a determined user can ignore them. But combined with restricting group creation to a permission set (so only "trained" users can create groups at all), they cut sprawl materially.

A common structural naming convention for orgs of any size:

```
<Type>-<Scope>-<Purpose>

Examples:
  Project-AcmeMigration-CoreTeam        ← a project workstream
  Team-Sales-EnterpriseAEs              ← a standing team
  Topic-Salesforce-ReleaseTrack          ← an interest / topic group
  Announce-AllHands                      ← broadcast group
  Customer-AcmeCorp-AccountTeam         ← a customer-specific group
```

Prefixes like `Project-`, `Team-`, `Topic-`, `Announce-`, `Customer-` make bulk operations (archive all `Project-*` groups closed last quarter) trivial via SOQL `WHERE Name LIKE 'Project-%'`.

---

## Recommended Workflow

1. **Inventory groups and ownership distribution.** Run the bundled `scripts/check_chatter_group_governance.py` against your retrieved metadata, plus this SOQL pair in Workbench:
   ```sql
   SELECT IsArchived, COUNT(Id) cnt FROM CollaborationGroup GROUP BY IsArchived
   SELECT OwnerId, Owner.IsActive, COUNT(Id) cnt FROM CollaborationGroup
       WHERE IsArchived = false GROUP BY OwnerId, Owner.IsActive
       ORDER BY COUNT(Id) DESC
   ```
   Bucket the population: active-active-owner, active-inactive-owner, archived. The middle bucket is your immediate ownership-transfer queue.
2. **Decide the org's group-creation policy.** Two choices: (a) leave open to all internal users (default), or (b) restrict to a permission set "Chatter Group Creator" assigned to trained team leads. For most orgs >100 users, restricting beats sprawl. Setup → Profiles / Permission Sets → "Create and Own New Chatter Groups."
3. **Set the auto-archive baseline.** Setup → Chatter Settings → "Archive Inactive Chatter Groups." 90 days is a reasonable default for project / topic groups. For broadcast / announcement groups (which have low post frequency by nature), set per-group `IsArchived = false` explicitly and document in the group's Information template that auto-archive is suppressed via member activity.
4. **Reassign orphaned-owner groups.** For every active group owned by an inactive user, transfer ownership. Either to a named backup manager (preferred — find via `CollaborationGroupMember.CollaborationRole = 'Admin'` for that group) or to a "Chatter Stewards" generic service-account user. Anonymous Apex bulk-update is the fastest path; see `references/examples.md` Example 3.
5. **Archive vs delete the dormant population.** For groups inactive >365 days *and* with <5 members *and* with `Description` empty (or a known disposable name pattern like `Test-*`): delete after a 30-day notification window. For inactive >365 days with substantive history (members, posts): archive with note that data is preserved. Document the decision tree in the org's group-governance runbook.
6. **Wire the offboarding hook.** When a user is being deactivated, run a check: any active groups they own? If yes, reassign owner first, deactivate second. Bake this into the user-offboarding checklist or automate with a Flow that runs before the User record's `IsActive` flips to false. (A simple Flow can't update `User.IsActive` mid-DML, but a scheduled job that scans nightly for "owners deactivated in last 24h with active groups" works fine.)
7. **Re-measure.** Quarterly, re-run the checker and the SOQL pair. Total active groups should plateau or decline; orphan-owner count should be near zero; archived-group ratio should be high (an archive-heavy org is a healthy one — old work *should* be archived).

---

## Related Skills

- `admin/chatter-notification-tuning` — feed noise, digest frequency, and notification volume tuning *inside* groups (this skill governs the group population; that skill governs what's noisy inside a group)
- `apex/apex-connect-api-chatter` — programmatic group creation / membership / posting via Connect API
- `admin/user-management` — broader user-deactivation workflow that this skill plugs into for the ownership-transfer step
