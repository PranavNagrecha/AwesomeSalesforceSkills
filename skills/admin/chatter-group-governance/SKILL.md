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
  - "audit every chatter group for compliance but unlisted ones do not show up"
  - "our system admin cannot see the unlisted group compliance asked about"
  - "bulk transfer chatter group ownership to a service account with apex"
  - "deploy chatter settings to disable unlisted groups across orgs"
  - "chatter group name already exists error when creating groups in bulk"
  - "exempt a broadcast group from auto archive without turning archiving off"
  - "deleting a chatter group removed files that were shared somewhere else"
  - "reassign collaboration group owner before deactivating a departing user"
  - "which permission set grants create and own new chatter groups"
  - "report on collaboration groups with no active owner and no manager"
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
  - "Deployable Chatter.settings and PermissionSet XML for the governance baseline"
  - "SOQL / Apex / Data Loader artefacts: inventory, transfer, archive, orphan detection"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
runtime_orphan: true
---

# Chatter Group Governance

Activate this skill when an admin needs to design or repair Chatter group lifecycle controls — naming, visibility, ownership, archival, and cleanup. The skill is about *governance* of the group population, not about feed noise inside a single group (use `admin/chatter-notification-tuning` for that).

---

## Before Starting

Gather this context before proposing changes:

- **How many groups exist and how many are dormant.** Run a quick `SELECT COUNT(Id) FROM CollaborationGroup` and a follow-up grouped by `IsArchived`. Most orgs that ask for "governance" have 5–20× more groups than active people, with the bulk dormant for 12+ months.
- **Who can create groups today.** Group creation is a *user permission*, not a Chatter Settings checkbox: "Any user with the **Create and Own New Chatter Groups** permission can create public, private, and unlisted groups, including in any Experience Cloud sites they belong to" (Object Reference, `CollaborationGroup` Special Access Rules, object_reference.txt L67098–67099). Retrieve the profiles and permission sets and read who actually holds it — broad grants are the single biggest driver of sprawl. Unlisted groups are separately gated by the org setting `unlistedGroupsEnabled` in `Chatter.settings` (api_meta.txt L112602–112608).
  <!-- UNVERIFIED (2026-09-05): "out of the box every internal user can create groups" and "unlisted groups are off by default" are both plausible and both unsourced — no supplied guide states either default. Read the retrieved metadata rather than assuming a default. -->
- **What ownership currently looks like.** Run `SELECT OwnerId, COUNT(Id) FROM CollaborationGroup WHERE IsArchived = false GROUP BY OwnerId ORDER BY COUNT(Id) DESC`. Concentrations of ownership on inactive users (`User.IsActive = false`) are the primary cleanup target. The `OwnerId` of a group remains pointed at the deactivated user — Salesforce does not auto-reassign on user deactivation.
- **Archiving levers, in order.** Three of them, at different scopes. Org-wide: `allowChatterGroupArchiving` in `Chatter.settings` covers "whether **manual and automatic** group archiving are allowed on all Chatter groups" (api_meta.txt L112476–112480) — a `false` here removes the archive option entirely, not just the sweep. Per group, automatic: `CollaborationGroup.IsAutoArchiveDisabled` exempts one group from the sweep (object_reference.txt L67282–67290). Per group, manual: `IsArchived` (L67274–67281). Inactivity is measured against `LastFeedModifiedDate` — "the date of the last post or comment on the group" (L67298–67314) — so a description edit or a member add does not reset the clock.
  <!-- UNVERIFIED (2026-09-05): the widely-repeated "90 days of inactivity" auto-archive default is not in any supplied guide, and ChatterSettings carries no day-count element at all (api_meta.txt L112470-112608). Read the number out of Setup for the org in front of you; do not quote 90. -->
- **Are end users creating private groups for sensitive content?** Private and Unlisted groups bypass the standard sharing model for posts inside the group — a Private group is a parallel data island. Compliance teams care.

---

## Questions to Ask Before Configuring

Ask these before touching Setup or writing a cleanup script. Each one maps to a gotcha that turns a
tidy-looking cleanup into an irreversible one.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Who in this org holds **Manage Unlisted Groups**, and can they name themselves?" | View All Data and Modify All Data do not reach unlisted groups (L67109–67115), so an "all groups" report run by a system admin is silently incomplete | Either a named compliance holder, or the decision to set `unlistedGroupsEnabled` to `false` |
| "Is `allowChatterGroupArchiving` on, and has anyone turned it off to stop surprise archiving?" | That flag covers manual archiving too (api_meta.txt L112476–112480); with it off, delete is the only lever and delete cascades to files shared elsewhere | The right fix — per-group `IsAutoArchiveDisabled` — instead of an org-wide switch |
| "For the groups you want to keep alive, is anyone *posting*, or only *reading*?" | The archive clock runs on `LastFeedModifiedDate`, the last post or comment (L67298–67314); reads never advance it | The exemption list to set `IsAutoArchiveDisabled = true` on, before the next sweep |
| "Do any of these groups hold files that are also shared somewhere else?" | Deleting a group "removes the files from other locations where they were shared" (L67402–67404) | The archive-vs-delete split, decided on evidence rather than on inactivity alone |
| "Who is the transfer target, and are they a person or a service account?" | Only the owner or a Modify All Data holder can repoint `OwnerId` (L67378–67379); a person-owner re-orphans on their next departure | A steward account for ownership plus a named human manager for moderation |
| "Is this cleanup happening alongside a batch user deactivation?" | Deactivating multiple users at once hard-deletes the `EntitySubscription` rows between them, unrecoverable on reactivation (L111169–111174) | A sequencing decision, and an `EntitySubscription` export taken before the wave |
| "Are guests (`CanHaveGuests`) already true on any group in scope?" | That flag "cannot be set back to false" once true (apexrefguide.txt L111947–111948) | An honest exit plan — remove guests and archive — instead of a promise to close the group later |

What a proper configuration adds over just archiving the dead groups: the org keeps a discoverable,
auditable group population — every active group has a reachable owner, every exemption from the archive
sweep is a deliberate per-group flag rather than an org-wide switch, unlisted groups are either governed
by a named permission holder or turned off, and the settings baseline lives in source control so the next
org inherits the same policy instead of rediscovering it.

---

## Core Concepts

### Concept 1 — Three group types, three sharing models

`CollaborationGroup.CollaborationType` is a picklist with three values that drive visibility very differently:

| Type | Discoverable in group list | Posts visible to | Membership requires approval |
|---|---|---|---|
| **Public** | Yes | All internal users (and Customer Community users with feed access if so configured) | No — anyone can join |
| **Private** | Yes (name + description visible, posts not) | Members only | Yes — owner / manager approves |
| **Unlisted** | No — and *not* to View All Data / Modify All Data holders either; only Manage Unlisted Groups reaches it | Members and Manage Unlisted Groups holders | Invitation only |

Two consequences admins miss:
- A **Public** group is the only type where post content is visible to non-members. If the goal is "broadcast announcement," Public is correct. If the goal is "team workspace with sensitive material," it must be Private or Unlisted.
- **Unlisted** groups are invisible to admin seniority as well as to end users, and this is the most-often-wrong belief in the topic. The guide states it twice: a View All Data holder "can't view unlisted group information, unless they have the **Modify Unlisted Groups** permission as well," and a Modify All Data holder "can't view or modify unlisted group information, unless they have the **Manage Unlisted Groups** permission as well" (L67109–67115). A SOQL query run by an ordinary system admin therefore returns an incomplete group list and says nothing about what it omitted. Either provision Manage Unlisted Groups to named compliance holders or set `unlistedGroupsEnabled` to `false` — `references/metadata-examples.md` sections 1 and 2 carry both.

### Concept 2 — Archived ≠ Inactive ≠ Deleted

Three distinct lifecycle states. Confusing them is the most common admin error:

- **Active** — `IsArchived = false`. Group accepts new posts, members receive notifications, group counts against any per-org group limits in shipped product features.
- **Archived** — `IsArchived = true`. Set by the org's automatic sweep against `LastFeedModifiedDate`, or manually by the owner or a Modify All Data holder. Archived groups:
  - Stay in `CollaborationGroup` — *not deleted*.
  - Past posts and members are preserved and queryable.
  - No new posts accepted via UI; the group becomes read-only.
  - Members continue to be members; `EntitySubscription` records persist.
  - The group can be unarchived (manually only) and resume activity.
- **Deleted** — record-level `delete` on `CollaborationGroup`, and the cascade reaches outside the group: "Deleting a group permanently deletes all posts and comments to the group. It also deletes all files and links posted to the group and **removes the files from other locations where they were shared**" (L67402–67404). Compliance impact: the audit trail of group conversations is gone, and so is any file that also lived in three other places.

There is no "Inactive" state in metadata — the term is colloquial for "Archived but not yet Deleted." Decide explicitly: archive (preserve audit trail, hide from active lists) or delete (purge permanently).

### Concept 3 — Group ownership and the deactivated-owner problem

`CollaborationGroup.OwnerId` is a hard reference to a `User` record. Two non-obvious behaviors:

1. **Deactivating the owner does NOT reassign the group.** The user is set `IsActive = false`. The group's `OwnerId` still points at them. The group continues to function — members can post, the group can be modified by other group managers — but the *owner-only* operations (deleting the group, transferring it, changing its type) are now stuck unless a system admin intervenes.
2. **Only the current owner or a Modify All Data holder can transfer ownership** — "Only the current group owner or people with the Modify All Data permission can update the `OwnerId`" (L67378–67379). Not "an admin" loosely: that specific permission. The member-side note says the same thing from the other direction — "To change the group owner, use the `OwnerId` field on the `CollaborationGroup` object" (L67477–67478) — so promoting someone to group manager is explicitly not a transfer.

The governance pattern: every group should have a *backup manager* (a `CollaborationGroupMember` with `CollaborationRole = 'Admin'` — "Managers can post and comment, change member roles, edit group settings, add and remove members, delete posts and comments, and edit the group information field", L67473–67476). The backup manager covers moderation but cannot transfer ownership; a Modify All Data holder must do that. So the offboarding workflow is:
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

1. **Retrieve the metadata baseline and lint it.** `sf project retrieve start --metadata Settings:Chatter,PermissionSet,Profile`, then run the bundled checker:
   ```bash
   python3 scripts/check_chatter_group_governance.py --manifest-dir force-app/main/default
   ```
   Two findings stop everything else: `CGG-UNLISTED-UNGOV` (unlisted groups are on and nobody holds
   Manage Unlisted Groups, so your inventory in step 2 will be incomplete) and `CGG-ARCHIVE-OFF`
   (archiving is disabled org-wide, so the archive branch of step 4 does not exist yet).
   `references/metadata-examples.md` sections 1–2 carry the deployable `Chatter.settings` and
   `PermissionSet` shapes for whatever you have to change.

2. **Export the group population and lint that too.** Groups are data, not metadata — the export query
   is in `references/metadata-examples.md` section 3. Run it as a user who holds Manage Unlisted Groups
   if step 1 says one exists, then:
   ```bash
   python3 scripts/check_chatter_group_governance.py \
       --manifest-dir force-app/main/default \
       --group-inventory groups.csv \
       --name-prefixes Project- Team- Topic- Announce- Customer- \
       --inactive-days 365
   ```
   `CGG-INV-ORPHAN` is the ownership-transfer queue, `CGG-INV-STALE` the archive queue,
   `CGG-INV-EMPTY` the delete candidates, `CGG-INV-NAMING` the convention debt. Record the counts —
   they are the baseline you re-measure against in step 7.

3. **Decide creation policy, and write it as metadata.** Move Create and Own New Chatter Groups off
   profiles and onto a named `Chatter_Group_Creator` permission set; add `Unlisted_Group_Auditor` if
   the org keeps unlisted groups. Both shapes are in `references/metadata-examples.md` section 2 —
   read the UNVERIFIED note there about the permission API names before you deploy them.

4. **Reassign every orphaned owner, before you archive anything.** Use the manager-first script in
   `references/metadata-examples.md` section 4: it prefers an active group manager and falls back to a
   steward service account, in three queries and one partial-success DML. Archiving a group whose owner
   is already gone just hides the problem — gotchas 2 and 3.

5. **Split stale from empty, then archive or delete.** Archive (`IsArchived = true`) anything with
   substantive history; delete only groups the checker flagged `CGG-INV-EMPTY` *and* whose direct
   `CollaborationGroupMember` count you confirmed — `MemberCount` is a nillable rollup, gotcha 9. Before
   any delete, check the group's files: the delete cascade removes them from every other location they
   were shared into, gotcha 7. Standing groups that should never auto-archive get
   `IsAutoArchiveDisabled = true` instead (section 5 of the metadata examples), not an org-wide setting
   change.

6. **Wire the offboarding hook and sequence it.** Ownership transfer runs *before* `User.IsActive` flips.
   Read `references/llm-anti-patterns.md` anti-pattern 2 first — the obvious record-triggered Flow is the
   wrong shape here. And if this is a deactivation *wave*, read gotcha 11: deactivating several users at
   once hard-deletes the follow relationships between them, with no restore on reactivation.

7. **Re-measure quarterly and diff the counts.** Re-run both checker invocations from steps 1–2.
   `CGG-INV-ORPHAN` should trend to zero, `CGG-INV-NAMING` should fall as the permission set narrows who
   creates groups, and a rising archived-to-active ratio is health, not decay. Commit the
   `Chatter.settings` and permission-set files so the policy travels with the org.

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing the deployable `Chatter.settings` and `PermissionSet` XML, the package.xml and `sf project` commands, or any of the data-side artefacts — inventory SOQL, ownership-transfer Apex and CSV, archive/unarchive updates, orphan and empty-group detection |
| `references/gotchas.md` | The cleanup ran and something is irreversible, invisible, or missing — unlisted groups absent from an audit, files vanished from unrelated records, a manager who cannot take over a group, a name collision on a bulk load |
| `references/examples.md` | Working a scenario end to end before any XML exists — inventory, creation lockdown, bulk reassignment, the archive-vs-delete call, auto-archive tuning, and the Group Information Template |
| `references/well-architected.md` | Justifying open creation vs permission-set restriction, archive vs delete, or person-owner vs steward-owner — and locating the official source behind a claim in this skill |
| `references/llm-anti-patterns.md` | Reviewing output an AI assistant produced here, especially "just delete the dormant groups" or an offboarding Flow that deactivates and reassigns in one transaction |
| `templates/chatter-group-governance-template.md` | Running workflow steps 1–2 — the inventory, policy, and disposition worksheet |
| `scripts/check_chatter_group_governance.py` | Workflow steps 1, 2, and 7 — before any settings deploy and before any bulk archive or delete |

---

## Related Skills

- `admin/chatter-notification-tuning` — feed noise, digest frequency, and notification volume tuning *inside* groups (this skill governs the group population; that skill governs what's noisy inside a group)
- `apex/apex-connect-api-chatter` — programmatic group creation / membership / posting via Connect API
- `admin/user-management` — broader user-deactivation workflow that this skill plugs into for the ownership-transfer step
