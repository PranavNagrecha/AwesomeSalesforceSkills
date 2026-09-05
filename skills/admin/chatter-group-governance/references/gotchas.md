# Gotchas — Chatter Group Governance

Non-obvious platform behaviors that bite admins during chatter group lifecycle work.

Line citations are into the Summer '26 / v62 PDFs: `object_reference.txt` (Object Reference),
`api_meta.txt` (Metadata API Developer Guide), `apexrefguide.txt` (Apex Reference Guide),
`salesforce_data_loader.txt` (Data Loader Guide).

---

## Gotcha 1: Archiving a group does NOT delete `EntitySubscription` records

**What happens:** Admin archives a group to "stop notifications." Members remain members, and if the
group is later unarchived, notifications resume exactly as before.

**When it occurs:** Any time archive is used as a substitute for removal. Archive flips
`CollaborationGroup.IsArchived` (object_reference.txt L67274–67281) — a single boolean on the group
record. It touches nothing on `CollaborationGroupMember`, whose rows are separate records with their own
`CollaborationRole` and `NotificationFrequency` (L67430–67540), and nothing on `EntitySubscription`,
where `ParentId` "Refers To" a list that includes `CollaborationGroup` (L111079–111120).

**How to avoid:** Map intent to state before acting. "Stop new posts, keep history and membership" is
archive. "Remove all traces" is delete, with the cascade cost in gotcha 7. If the goal is only to stop a
specific person's email, the lever is that member's `NotificationFrequency` = `N` (Never) — a
`CollaborationGroupMember` update (L67503–67532), not a group-level action.

---

## Gotcha 2: Deactivating the group owner does NOT reassign the group

**What happens:** A user is deactivated during offboarding. Weeks later the org discovers dozens of
active groups still carrying that user as `OwnerId`. Owner-only operations on those groups now need an
admin every time.

**When it occurs:** On every deactivation, because `CollaborationGroup.OwnerId` is a plain lookup —
"ID of the owner of the group… Relationship Type: Lookup, Refers To: User" (L67373–67388) — and the
guide documents no automation that repoints it. The group keeps working for members, because group
managers ("Managers can post and comment, change member roles, edit group settings, add and remove
members, delete posts and comments, and edit the group information field", L67473–67476) cover
day-to-day moderation. Ownership is the part that goes stale silently.

**How to avoid:** Query owned groups *before* the deactivation
(`SELECT Id FROM CollaborationGroup WHERE OwnerId = :userId AND IsArchived = false`) and reassign. The
guide points the same direction from the member side: "To change the group owner, use the `OwnerId` field
on the `CollaborationGroup` object" (L67477–67478) — promoting someone to manager is explicitly *not* a
transfer. `references/metadata-examples.md` section 4 has the bulk script.

---

## Gotcha 3: Only the owner or a Modify All Data holder can repoint `OwnerId` — a manager cannot

**What happens:** A group manager is told to "take over the group" after the owner leaves. They can edit
the group's settings and information, add and remove members — and every attempt to change the owner
fails or the field is not editable for them.

**When it occurs:** Always, and it is stated twice. On the field: "Only the current group owner or people
with the Modify All Data permission can update the `OwnerId`" (L67378–67379). And through the API:
`ConnectApi.ChatterGroups.updateGroup` "is successful only when the context user is the group manager or
owner, or has Modify All Data permission" (apexrefguide.txt L68548–68551), while the `owner` property on
`ConnectApi.ChatterGroupInput` is "available for PATCH requests only" (L111964–111966). A manager can
call `updateGroup`; that does not make the owner field theirs to set.

**How to avoid:** Treat ownership transfer as an admin task with a ticket, not a self-service one. The
practical governance shape is: owner = a steward service account with Modify All Data available to IT,
plus a named human manager (`CollaborationRole = 'Admin'`) for moderation. That keeps day-to-day work
self-service while the transfer stays with the two principals the platform allows.

---

## Gotcha 4: View All Data and Modify All Data do NOT reach unlisted groups

**What happens:** Compliance asks "list every group containing the word 'merger'." A system admin with
Modify All Data runs a SOQL query over `CollaborationGroup`, reports the result — and an unlisted group
containing exactly that content never appears in the output.

**When it occurs:** Whenever an unlisted group exists and the querying user lacks the unlisted-specific
permission. The guide is explicit about both blanket permissions:

- View All Data — "Allows users to view all public and private groups… Users with this permission can't
  view unlisted group information, unless they have the **Modify Unlisted Groups** permission as well"
  (L67109–67112).
- Modify All Data — "Allows users to view, modify, and delete all public and private groups… Users with
  this permission can't view or modify unlisted group information, unless they have the **Manage Unlisted
  Groups** permission as well" (L67112–67115).

The `CollaborationType` value description agrees: "Unlisted — Only members and users with the Manage
Unlisted Groups permission can see the group and post updates" (L67198–67201).

**How to avoid:** Discovery over unlisted groups needs its own named permission grant, not admin
seniority. Provision a small, session-activated `Unlisted_Group_Auditor` permission set carrying Manage
Unlisted Groups (`references/metadata-examples.md` section 2), assign it to named compliance holders, and
review it every release. If nobody in the org holds that permission, an "all groups" audit report is
incomplete by construction — and the person running it will not be told so.

---

## Gotcha 5: Unlisted is not reachable through the Connect API's visibility enum

**What happens:** A developer writes `ConnectApi` code to create or convert a group to unlisted and
cannot find a working value — or writes `groupInput.visibility = ConnectApi.GroupVisibilityType.Unlisted`
and gets behaviour that does not match the enum's name.

**When it occurs:** On every Connect API path. `ConnectApi.GroupVisibilityType` offers three values, and
the guide annotates one of them: "`Unlisted` — **Reserved for future use**" — in both the input class
(apexrefguide.txt L111967–111972) and the output class (L125278–125283). The sObject picklist
`CollaborationGroup.CollaborationType` does carry a real `Unlisted` value (L67198), so SOQL and DML see a
type the Connect API does not offer.

**How to avoid:** Manage unlisted groups through the sObject (`CollaborationType`), not through
`ConnectApi.ChatterGroups`. And do not assume symmetry between the two surfaces in either direction —
Connect API exposes group photos, announcements, and membership requests that plain DML does not, while
the sObject exposes a visibility value Connect API calls reserved.

<!-- UNVERIFIED (2026-09-05): an earlier revision of this file stated that CollaborationType cannot be
     changed from Unlisted to Public or Private and quoted an error message. The Object Reference lists
     CollaborationType as an updateable Restricted picklist (L67189-67201) and documents no one-way
     restriction, and no supplied guide carries that error string. The one-way behaviour that IS grounded
     is on guests, not on type — see gotcha 12. Treat any Unlisted-to-Public conversion as unproven and
     test it in a sandbox before promising it; the migration path in the fix below is safe either way. -->

If a conversion is needed and the sandbox test fails, the migration is: export the relevant `FeedItem`
content, create a new group of the correct type, re-post with the original posters' consent, then archive
or delete the original.

---

## Gotcha 6: Auto-archive uses `LastFeedModifiedDate`, not `LastModifiedDate` or member visit time

**What happens:** A group used as a reference library — members read it constantly but rarely post —
archives itself. The owner protests that people use it every day, and they are right.

**When it occurs:** Whenever reads outnumber writes. `LastFeedModifiedDate` is documented as "The date of
the last post or comment on the group" (L67298–67314). Nothing else advances it: not a description edit,
not a member add, not a view. The platform even tracks reading separately, on the membership record —
`CollaborationGroupMember.LastFeedAccessDate` is "Date and time when a group member last accessed the
group's feed" (L67480–67490) — but that field belongs to the member, not the group, and there is no
documented link from it to archiving.

**How to avoid:** Use the per-group exemption rather than a posting ritual.
`CollaborationGroup.IsAutoArchiveDisabled` — "Indicates whether automatic archiving is disabled for the
group (true) or not (false)" (L67282–67290) — is a create-and-update boolean on each group. Set it `true`
on reference libraries and broadcast channels, and exclude `IsAutoArchiveDisabled = true` from every bulk
archive sweep. Read engagement, if you need to prove it, comes from aggregating `LastFeedAccessDate`
across the group's members.

---

## Gotcha 7: Deleting a group also removes its files from everywhere else they were shared

**What happens:** An admin deletes a batch of dormant groups. Later, unrelated records and other groups
are missing files — files that were posted into a deleted group and *also* shared elsewhere.

**When it occurs:** On every group delete. The guide states the cascade in one sentence: "Deleting a
group permanently deletes all posts and comments to the group. It also deletes all files and links posted
to the group and **removes the files from other locations where they were shared**" (L67402–67404). The
second clause is the one nobody predicts — deletion follows the file, not the group boundary.

**How to avoid:** Before deleting any group with file content, enumerate the group's files and check
whether they are shared anywhere else; a file that is, must be re-uploaded to its other home first.
Prefer archive for anything with substantive history. And never use Data Loader's Bulk API hard-delete
option here — "hard-deleted records are immediately deleted and can't be recovered from the Recycle Bin"
(salesforce_data_loader.txt L605–606, L964), which removes even the short recovery window the ordinary
delete gives you.

<!-- UNVERIFIED (2026-09-05): an earlier revision cited a 15-day Recycle Bin window for the cascaded
     FeedItem rows. No supplied guide states a retention period for this cascade, and the Object
     Reference calls the post/comment deletion "permanent" (L67402). Do not quote a number of days;
     treat the deletion as unrecoverable. -->

---

## Gotcha 8: "Public" means every user with Chatter access, including Experience Cloud sites

**What happens:** Internal users treat a Public group as "internal, open to colleagues" and post
sensitive-but-not-secret content. The audience turns out to be wider than "colleagues."

**When it occurs:** In any org with Experience Cloud. `CollaborationType = 'Public'` is defined as
"Anyone can see and post updates. Anyone can join a public group" (L67193–67194) — with no internal-only
qualifier. The group object's own access rules are scoped "across their org **and its Experience Cloud
sites**" throughout (L67109–67118), and `CollaborationGroup.NetworkId` exists precisely because groups
belong to sites (L67353–67371). Separately, `CanHaveGuests` opens a group to "Chatter customers…people
outside your company's email domains" (L67172–67186).

**How to avoid:** Choose Private for anything internal-sensitive — "Only members can see the group feed
and post updates. Non-members can only see the group name and a few other details" (L67194–67198). Audit
guest exposure explicitly rather than inferring it from type: group by `CollaborationType` **and**
`CanHaveGuests` (`references/metadata-examples.md` section 3), and keep `enableInviteCsnUsers` off in
`Chatter.settings` (api_meta.txt L112564–112581) unless customer groups are a deliberate program.

---

## Gotcha 9: `MemberCount` is a nillable rollup, not a live count

**What happens:** An admin inserts 50 `CollaborationGroupMember` rows, immediately reads `MemberCount`,
sees the old number, and concludes the insert failed. Or an "empty groups" report built on
`MemberCount <= 1` proposes deleting groups that have members.

**When it occurs:** On any read that follows a membership change closely, and on any group where the
rollup has never been populated. `CollaborationGroup.MemberCount` is typed `int` with properties
"Filter, Group, **Nillable**, Sort" and described only as "The number of members in the group"
(L67338–67346) — it is not `Create` or `Update`, so nothing in your transaction writes it, and it can be
null.

**How to avoid:** Use `MemberCount` for dashboards and trend reporting; use a direct aggregate for any
decision that deletes data —
`SELECT CollaborationGroupId, COUNT(Id) FROM CollaborationGroupMember WHERE CollaborationGroupId IN :ids
GROUP BY CollaborationGroupId`. Treat `MemberCount = null` as "unknown", never as "zero".

<!-- UNVERIFIED (2026-09-05): an earlier revision claimed the rollup lags "up to 5 minutes". No supplied
     guide documents a refresh interval for MemberCount. The nillability and the absence of Create/Update
     properties (L67328-67338) are the grounded facts; the specific delay is not. -->

---

## Gotcha 10: Group names are unique across public and private groups — but not for unlisted ones

**What happens:** Two governance surprises from the same rule. First, a bulk group-creation load fails
partway through on name collisions the CSV author did not anticipate. Second, a "duplicate group" audit
that keys on `Name` quietly collapses two genuinely different groups into one row, because one of them
was unlisted.

**When it occurs:** On every create and rename. The guide states it on the `Name` field: "Group names
must be unique across public and private groups. **Unlisted groups don't require unique names**"
(L67345–67352). `Name` is also `idLookup`, so it is a valid external-id-style match key for upserts —
which is exactly why the unlisted exemption is dangerous: an upsert keyed on `Name` has no guarantee of
matching one row when unlisted groups are in scope.

**How to avoid:** Never upsert `CollaborationGroup` on `Name`; upsert on `Id` or do query-then-update.
In any duplicate or inventory report, group by `Name` **and** `CollaborationType`, and treat an unlisted
group sharing a public group's name as a deliberate finding to investigate, not a merge candidate. This
is also the strongest technical argument for a naming convention with a type prefix: it makes collisions
visible at creation time instead of at load time.

---

## Gotcha 11: Bulk-deactivating users hard-deletes reciprocal follow relationships, permanently

**What happens:** An offboarding wave deactivates a batch of users at once. Some of those users followed
each other. When one of them is rehired and reactivated, their follow relationships do not come back —
while a colleague deactivated alone the same week gets everything restored.

**When it occurs:** Only in the multi-user case, and the guide draws the distinction precisely: "If you
deactivate a user, any `EntitySubscription` where the user is associated with the `ParentId` or
`SubscriberId` field, meaning all subscriptions both to and from the user, are **soft deleted**. If the
user is reactivated, the subscriptions are restored. However, if you deactivate **multiple users at once**
and these users follow each other, their subscriptions are **hard deleted**. In this case, the
user-to-user `EntitySubscription` is deleted twice (double deleted). Such subscriptions can't be restored
upon user reactivation" (object_reference.txt L111169–111174).

**How to avoid:** This is an argument for sequencing offboarding rather than batching it, and for
exporting `EntitySubscription` for the affected users before any deactivation wave. It is also why group
membership and record-following must be treated as two separate restore problems during a rehire:
`CollaborationGroupMember` rows survive a deactivation, `EntitySubscription` rows may not.

---

## Gotcha 12: `CanHaveGuests` is a one-way door

**What happens:** A group is opened to customers for one engagement. When the engagement ends, the admin
tries to close it back to internal-only and finds there is no way back.

**When it occurs:** The moment the flag is set. The Connect API input class states it flatly for
`canHaveChatterGuests`: "true if this group allows Chatter customers, false otherwise. **After this
property is set to true, it cannot be set to false**" (apexrefguide.txt L111947–111948). The
corresponding sObject field `CollaborationGroup.CanHaveGuests` is listed as updateable (L67172–67186),
which makes the trap worse — the field looks reversible in a describe and is not in practice.

**How to avoid:** Treat "allow customers" as a decision made once, at group creation, with the same
weight as choosing the group type. When an engagement ends, the exit is to remove the guest members and
archive the group, then create a fresh internal group if the work continues — not to flip the flag back.
The related irreversibility is `NetworkId`: "You can only add a `NetworkId` when creating a group. You
can't change or add a `NetworkId` for an existing group" (L67367–67371), so a group also cannot be moved
into or between Experience Cloud sites after creation.

---

## Gotcha 13: `allowChatterGroupArchiving = false` removes manual archiving too, not just the automatic sweep

**What happens:** An org turns off group archiving to stop unexpected auto-archiving of standing groups.
The archive-vs-delete decision tree then has only one branch left, and cleanup work turns into deletion
work — with the cascade in gotcha 7 attached to every dormant group.

**When it occurs:** As soon as the setting is deployed. The Metadata API guide defines the field as
covering both modes: "Indicates whether **manual and automatic** group archiving are allowed on all
Chatter groups (true) or aren't allowed (false)" (api_meta.txt L112476–112480). It maps to the Setup
checkbox *Allow Group Archiving*.

**How to avoid:** Leave `allowChatterGroupArchiving` at `true` and solve the over-archiving complaint one
level down, with per-group `IsAutoArchiveDisabled` (gotcha 6). Check the org-level flag first in any
governance engagement — a `false` there invalidates every archive recommendation downstream, and the
bundled checker fails the run when it sees archiving disabled while the inventory contains archive
candidates.

---

## Gotcha 14: Apex and Visualforce see every group, including unlisted ones

**What happens:** A custom "group directory" component, or an installed AppExchange package, lists groups
for end users — and surfaces unlisted and private groups to people who are not members of them.

**When it occurs:** In any Apex-backed group listing, because the security model the rest of this file
describes is not enforced there. The guide devotes a block of the Special Access Rules to it: "Apex code
runs in system mode, which means that the permissions of the current user aren't taken into account.
Visualforce pages that display groups might expose unlisted or private group data to users who aren't
members. Because system mode disregards the user's permissions, **all users who are accessing a
Visualforce page that's showing a group can act as an owner of that group**. AppExchange apps that are
written in Apex and that access all groups will expose unlisted groups to users who aren't members"
(L67121–67127).

**How to avoid:** The guide gives its own remedy: "Explicitly filter out unlisted and private group
information from SOQL queries in all Apex code" and "Use permission sets, profile-level permissions, and
sharing checks in your code to further limit group access" (L67129–67131). In governance terms, that
makes any custom group-listing component a review item alongside the settings and permission sets — add
`WHERE CollaborationType = 'Public'` (or an explicit membership join) to it, and re-check it before every
AppExchange install that touches Chatter. The same section notes the constructive use of the same access:
"Use Apex triggers on the `CollaborationGroup` object to monitor and manage the creation of groups. In
Setup, enter Group Triggers in the Quick Find box, then select Group Triggers to add triggers"
(L67131–67133) — the one supported enforcement point for a naming convention.

---

## Gotcha 15: A user can belong to only 300 groups, and pending join requests count against it

**What happens:** A power user in a large org stops being able to join groups, or an automated
onboarding routine that adds every new hire to a standard set of groups starts failing for long-tenured
users it also touches.

**When it occurs:** At 300, counting more than membership. The guide states it in the
`CollaborationGroupMemberRequest` usage notes: "A user can be a member of **300 groups**. **Requests to
join groups count against this limit**" (L67625). Pending requests are therefore consumable capacity,
and a user who has requested membership in groups that were never approved is closer to the ceiling than
their membership list suggests.

**How to avoid:** Two things. Include stale requests in cleanup: `CollaborationGroupMemberRequest.Status`
is `Pending` / `Accepted` / `Declined`, "Status can't be specified on create", "You can only update a
request when the Status is Pending", and "You can't delete or update a request with a Status of Accepted
or Declined" (L67626–67628) — so pending requests are the only ones you can resolve, and resolving them
frees capacity. And check membership headroom before any bulk add:
`SELECT MemberId, COUNT(Id) FROM CollaborationGroupMember GROUP BY MemberId HAVING COUNT(Id) > 250`
gives the users who will fail first.
