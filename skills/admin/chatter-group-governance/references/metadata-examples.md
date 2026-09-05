# Metadata Examples — Chatter Group Governance

Chatter group governance is unusual: **half the artefacts are metadata, half are data.**

- `ChatterSettings` (the `Chatter.settings` file) and a `PermissionSet` are true metadata — retrievable,
  deployable, diffable, reviewable in a pull request.
- `CollaborationGroup`, `CollaborationGroupMember`, `CollaborationGroupRecord` are **standard sObjects**,
  not metadata components. They move via SOQL / DML / Data Loader, never via `package.xml`.

Both halves are here. Shapes for the metadata half are taken from the Metadata API Developer Guide
(v62 PDF — `ChatterSettings` api_meta.txt L112452–112648, `PermissionSet` `userPermissions` L94863,
L95214–95217) and extended to one worked governance baseline. Field semantics for the data half come
from the Object Reference (`CollaborationGroup` object_reference.txt L67087–67405,
`CollaborationGroupMember` L67430–67540, `CollaborationGroupMemberRequest` L67544–67632,
`CollaborationGroupRecord` L67636–67700).

---

## Where the files live

| Artefact | package.xml `<name>` | `<members>` | Wildcard `*` | DX source file | API |
|---|---|---|---|---|---|
| `ChatterSettings` | `Settings` | `Chatter` | **Not supported** — the wildcard applies only when retrieving *all* settings (L112640–112648) | `settings/Chatter.settings-meta.xml` | 47.0+ (L112464) |
| `PermissionSet` | `PermissionSet` | perm-set API name | Supported | `permissionsets/Chatter_Group_Creator.permissionset-meta.xml` | — |
| `CollaborationGroup` | **none — it is data** | — | — | CSV / SOQL / Apex | sObject, API 19.0+ (L67088) |

`ChatterSettings` "appears in the `Chatter.settings` file, and is stored in the `settings` folder…
there's only one settings file for each settings component" (L112459–112461). You cannot deploy two
variants of it, and you cannot scope it per profile — it is one org-wide record.

---

## 1. `Chatter.settings` — the governance baseline

`force-app/main/default/settings/Chatter.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ChatterSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <allowChatterGroupArchiving>true</allowChatterGroupArchiving>
    <allowRecordsInChatterGroup>true</allowRecordsInChatterGroup>
    <enableApprovalRequest>false</enableApprovalRequest>
    <enableChatter>true</enableChatter>
    <enableChatterEmoticons>true</enableChatterEmoticons>
    <enableFeedEdit>true</enableFeedEdit>
    <enableFeedPinning>true</enableFeedPinning>
    <enableFeedsDraftPosts>false</enableFeedsDraftPosts>
    <enableFeedsRichText>true</enableFeedsRichText>
    <enableInviteCsnUsers>false</enableInviteCsnUsers>
    <enableOutOfOfficeEnabledPref>false</enableOutOfOfficeEnabledPref>
    <enableRichLinkPreviewsInFeed>true</enableRichLinkPreviewsInFeed>
    <enableTodayRecsInFeed>false</enableTodayRecsInFeed>
    <unlistedGroupsEnabled>false</unlistedGroupsEnabled>
</ChatterSettings>
```

### How to read it

- **`allowChatterGroupArchiving`** (L112476–112480) is the master archiving switch: it "indicates whether
  manual *and* automatic group archiving are allowed on all Chatter groups." Set it `false` and you lose
  the archive lever entirely — every dormant group must then be deleted or left active. Governance work
  starts by confirming this is `true`.
- **`unlistedGroupsEnabled`** (L112602–112608) — "Unlisted groups don't appear on the Groups list page.
  Membership in unlisted groups is by invitation only." Set `false` here unless the org has a named
  use case *and* a named holder of the Manage Unlisted Groups permission (section 2). Turning it off
  governs *creation*; it is not documented as retroactively converting groups that already exist.
  <!-- UNVERIFIED (2026-09-05): the guide describes unlistedGroupsEnabled=false as preventing creation
       (L112602-112605) and says nothing about the fate of existing unlisted groups. Verify in a sandbox
       before flipping it in an org that already has unlisted groups. -->
- **`allowRecordsInChatterGroup`** (L112481–112486) — "If groups already have record data, setting this
  field to `false` doesn't delete it." A `false` here hides existing `CollaborationGroupRecord` rows from
  the UI without removing them; they remain queryable. Deleting the association is a separate DML on
  `CollaborationGroupRecord`.
- **`enableInviteCsnUsers`** (L112564–112581) — whether a licensed user can invite customers to *private*
  groups they own or manage. This is the org-level gate behind the per-group `CanHaveGuests` flag; the
  pair is what lets external people see internal group content, so review them together.
- **`enableApprovalRequest`** (L112490–112496) — approval requests appear as posts in Chatter feeds when
  `true`; default `false`. Relevant to governance because it changes what a "dormant" group's feed
  actually contains: approval noise advances `LastFeedModifiedDate` and therefore defers auto-archive.
- Nothing in `ChatterSettings` carries a **number of days** before auto-archive, and nothing in it grants
  group *creation*. Creation is a user permission (section 2); the day count lives only in Setup, and
  `references/gotchas.md` gotcha 13 covers what turning archiving off org-wide actually costs.

### package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Chatter</members>
        <name>Settings</name>
    </types>
    <types>
        <members>Chatter_Group_Creator</members>
        <name>PermissionSet</name>
    </types>
    <version>62.0</version>
</Package>
```

Shape follows the guide's own `ChatterSettings` manifest sample (L112638–112648), which uses
`<members>Chatter</members>` under `<name>Settings</name>`.

### Retrieve and deploy

```bash
# Retrieve the current baseline before changing anything
sf project retrieve start --metadata Settings:Chatter --target-org prod-audit

# Diff, edit, then validate against production without committing the change
sf project deploy validate --manifest manifest/package.xml --target-org prod

# Deploy
sf project deploy start --manifest manifest/package.xml --target-org prod
```

### Verify

Settings have no queryable record, so verify in Setup rather than SOQL: **Setup → Feature Settings →
Chatter → Chatter Settings**, and confirm *Allow Group Archiving* is checked and *Enable Unlisted Groups*
is unchecked (the guide gives these as the Setup labels for `allowChatterGroupArchiving` and
`unlistedGroupsEnabled` at L112478–112480 and L112606–112608). Then re-run
`scripts/check_chatter_group_governance.py --manifest-dir force-app/main/default` against the
*re-retrieved* tree — a clean run on the retrieved copy is the deploy's receipt.

---

## 2. `PermissionSet` — who may create and own groups

`force-app/main/default/permissionsets/Chatter_Group_Creator.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Chatter Group Creator</label>
    <description>Grants group creation to trained team leads. Governance owner: Collaboration CoE. Reviewed quarterly.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <license>Salesforce</license>
    <userPermissions>
        <enabled>true</enabled>
        <name>ChatterOwnGroups</name>
    </userPermissions>
</PermissionSet>
```

And the separate, deliberately narrow one for compliance discovery:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Unlisted Group Auditor</label>
    <description>Compliance discovery over unlisted groups. Two named holders. Access reviewed every release.</description>
    <hasActivationRequired>true</hasActivationRequired>
    <license>Salesforce</license>
    <userPermissions>
        <enabled>true</enabled>
        <name>ManageUnlistedGroups</name>
    </userPermissions>
</PermissionSet>
```

### How to read it

- The `<userPermissions>` shape — one `<enabled>` plus one `<name>` per permission — is the guide's own
  `PermissionSet` sample (api_meta.txt L95214–95217, L95373–95393).
- The **permission labels** are grounded: "Any user with the **Create and Own New Chatter Groups**
  permission can create public, private, and unlisted groups" (object_reference.txt L67098–67099), and
  "**Manage Unlisted Groups** — Allows users to search for, access, and modify any unlisted group in an
  org and its Experience Cloud sites" (L67116–67117).
- The **API names** `ChatterOwnGroups` and `ManageUnlistedGroups` are the `<name>` values above.
  <!-- UNVERIFIED (2026-09-05): the Metadata API Developer Guide documents the userPermissions element
       shape but does not publish the catalogue of permission API names, so these two strings are not
       grounded in the supplied PDFs. Confirm them by retrieving one Profile that already has the
       permission and grepping the retrieved file, before deploying a permission set that names them.
       An earlier revision of this skill's checker used `CreateAndOwnNewChatterGroups`, which is the
       Setup *label* run together, not an observed API name. -->
- `hasActivationRequired` on the auditor set makes it a session-activated permission set, so the
  Manage Unlisted Groups grant is not carried in every session by default.
- Do **not** grant Manage Unlisted Groups by handing out Modify All Data. The guide is explicit that
  Modify All Data alone is not enough: users with it "can't view or modify unlisted group information,
  unless they have the Manage Unlisted Groups permission as well" (L67112–67114).

### Verify

```sql
SELECT Assignee.Name, Assignee.IsActive, PermissionSet.Name
FROM PermissionSetAssignment
WHERE PermissionSet.Name IN ('Chatter_Group_Creator', 'Unlisted_Group_Auditor')
ORDER BY PermissionSet.Name, Assignee.Name
```

Every row should be a person you can name. `Assignee.IsActive = false` rows are the cleanup queue.

---

## 3. The data half — inventory SOQL

These are not metadata. Run them in Workbench, Developer Console, or
`sf data query --query "…" --target-org <alias>`. All four are read-only.

**Orphaned owners — the immediate transfer queue.** `OwnerId` "is a relationship field… Refers To User"
(L67373–67388), and there is no platform automation that repoints it when the owner is deactivated:

```sql
SELECT Id, Name, CollaborationType, OwnerId, Owner.Name, Owner.IsActive,
       MemberCount, LastFeedModifiedDate
FROM CollaborationGroup
WHERE IsArchived = false AND Owner.IsActive = false
ORDER BY MemberCount DESC
```

**Archive candidates.** `LastFeedModifiedDate` is "the date of the last post or comment on the group"
(L67298–67314) — the only field that tracks feed activity:

```sql
SELECT Id, Name, MemberCount, LastFeedModifiedDate, IsAutoArchiveDisabled, OwnerId
FROM CollaborationGroup
WHERE IsArchived = false
  AND (LastFeedModifiedDate < LAST_N_DAYS:365 OR LastFeedModifiedDate = NULL)
ORDER BY LastFeedModifiedDate ASC NULLS FIRST
```

Include `IsAutoArchiveDisabled` (L67282–67288): a `true` there means someone deliberately exempted the
group from automatic archiving, and it should not be swept up in a bulk archive.

**Groups whose only manager is the owner.** `CollaborationRole = 'Admin'` means group *manager*:
"Managers can post and comment, change member roles, edit group settings, add and remove members, delete
posts and comments, and edit the group information field" (L67473–67476):

```sql
SELECT CollaborationGroupId, COUNT(Id) managerCount
FROM CollaborationGroupMember
WHERE CollaborationRole = 'Admin'
GROUP BY CollaborationGroupId
HAVING COUNT(Id) < 2
```

**Visibility distribution and guest exposure.** `CanHaveGuests` = "the group allows customers…
people outside your company's email domains" (L67172–67186):

```sql
SELECT CollaborationType, CanHaveGuests, COUNT(Id) cnt
FROM CollaborationGroup
WHERE IsArchived = false
GROUP BY CollaborationType, CanHaveGuests
```

---

## 4. The data half — ownership transfer DML

Only two principals can repoint `OwnerId`: "Only the current group owner or people with the **Modify All
Data** permission can update the `OwnerId`" (L67378–67379). A group *manager* cannot — the guide says so
directly on `CollaborationRole`: "To change the group owner, use the `OwnerId` field on the
`CollaborationGroup` object" (L67477–67478).

**Anonymous Apex, prefer the group's own manager, fall back to the steward.** One query for members,
one for groups, one DML — no SOQL or DML inside the loop:

```apex
// Fallback owner when a group has no manager other than the departing owner.
Id stewardUserId = [SELECT Id FROM User WHERE Username = 'chatter.stewards@example.com' LIMIT 1].Id;

List<CollaborationGroup> orphans = [
    SELECT Id, Name, OwnerId
    FROM CollaborationGroup
    WHERE IsArchived = false AND Owner.IsActive = false
    LIMIT 10000
];

// Preferred successor: an active group manager who is not the current owner.
Map<Id, Id> successorByGroup = new Map<Id, Id>();
for (CollaborationGroupMember m : [
        SELECT CollaborationGroupId, MemberId
        FROM CollaborationGroupMember
        WHERE CollaborationRole = 'Admin'
          AND Member.IsActive = true
          AND CollaborationGroupId IN :orphans]) {
    if (!successorByGroup.containsKey(m.CollaborationGroupId)) {
        successorByGroup.put(m.CollaborationGroupId, m.MemberId);
    }
}

List<CollaborationGroup> toUpdate = new List<CollaborationGroup>();
for (CollaborationGroup g : orphans) {
    Id successor = successorByGroup.get(g.Id);
    g.OwnerId = (successor != null) ? successor : stewardUserId;
    toUpdate.add(g);
}

Database.SaveResult[] results = Database.update(toUpdate, false);
Integer failed = 0;
for (Database.SaveResult r : results) {
    if (!r.isSuccess()) {
        failed++;
        System.debug(LoggingLevel.ERROR, r.getErrors()[0].getMessage());
    }
}
System.debug('Reassigned ' + (results.size() - failed) + ' of ' + results.size() + ' groups');
```

`Database.update(list, false)` (partial-success mode) matters here: one group with a dangling
`OwnerId` should not roll back the other 239.

**Data Loader path, when the transfer list came from a spreadsheet.** `CollaborationGroup` supports
`update()` (L67092–67094), so a two-column CSV is a valid load:

```csv
Id,OwnerId
0F9xx0000004CAaCAM,005xx000001Sv1AAAS
0F9xx0000004CAbCAM,005xx000001Sv1AAAS
0F9xx0000004CAcCAM,005xx000001Sv2BAAS
```

Operation `Update`, object `CollaborationGroup`, mapping `Id → Id` and `OwnerId → OwnerId`. Run it as a
user with Modify All Data, or the update silently matches zero groups you do not own. Keep the success
file — it is your rollback list.

---

## 5. The data half — archive, unarchive, and delete

Archive and unarchive are the same one-field update in both directions:

```apex
// Archive every stale Project-* group, skipping ones deliberately exempted.
List<CollaborationGroup> stale = [
    SELECT Id, Name
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
```

```apex
// Unarchive one group that was archived in error.
CollaborationGroup g = [SELECT Id, IsArchived FROM CollaborationGroup WHERE Id = :groupId];
g.IsArchived = false;
update g;
```

Equivalent Data Loader CSVs, object `CollaborationGroup`, operation `Update`:

```csv
Id,IsArchived
0F9xx0000004CAaCAM,true
0F9xx0000004CAbCAM,true
```

To exempt a standing group from automatic archiving without archiving anything, update
`IsAutoArchiveDisabled` instead — it is a per-group flag (L67282–67288), so the org-wide archiving
switch stays on while named groups opt out:

```csv
Id,IsAutoArchiveDisabled
0F9xx0000004CBaCAM,true
```

**Delete is not the archive twin.** The guide: "Deleting a group permanently deletes all posts and
comments to the group. It also deletes all files and links posted to the group and removes the files
from other locations where they were shared" (L67402–67404). The last clause is the one that surprises
people — a file shared into the group *and* into three other places disappears from all four.

If you delete via Data Loader with Bulk API's hard-delete option, "hard-deleted records are immediately
deleted and can't be recovered from the Recycle Bin" (salesforce_data_loader.txt L605–606, L964). Use the
ordinary `Delete` operation, never `Hard Delete`, for groups.

---

## 6. The data half — orphan and empty-group detection

Two group shapes are worth separating, because they need different actions.

**Orphan group** — active, and its owner is inactive or the `Owner` relationship resolves to null:

```sql
SELECT Id, Name, OwnerId, Owner.Name, Owner.IsActive, MemberCount
FROM CollaborationGroup
WHERE IsArchived = false
  AND (Owner.IsActive = false OR OwnerId = NULL)
```

**Empty group** — active with no feed activity ever recorded and at most the owner as a member. Note
that `MemberCount` is a rollup and lags; confirm with a direct count before deleting anything:

```sql
SELECT Id, Name, MemberCount, LastFeedModifiedDate, Description
FROM CollaborationGroup
WHERE IsArchived = false
  AND LastFeedModifiedDate = NULL
  AND MemberCount <= 1
ORDER BY CreatedDate ASC
```

```sql
SELECT CollaborationGroupId, COUNT(Id) trueMemberCount
FROM CollaborationGroupMember
WHERE CollaborationGroupId IN ('0F9xx0000004CAaCAM','0F9xx0000004CAbCAM')
GROUP BY CollaborationGroupId
```

Export the first query to CSV, add an `owner_active` column from the ownership query in section 3, and
feed the result to the checker's data-side linter:

```bash
sf data query \
  --query "SELECT Id, Name, CollaborationType, OwnerId, Owner.Name, Owner.IsActive, MemberCount, LastFeedModifiedDate, IsArchived FROM CollaborationGroup" \
  --result-format csv --target-org prod > groups.csv

python3 scripts/check_chatter_group_governance.py \
    --manifest-dir force-app/main/default \
    --group-inventory groups.csv \
    --name-prefixes Project- Team- Topic- Announce- Customer- \
    --inactive-days 365
```

---

## 7. Records in groups — the seven-object ceiling

If `allowRecordsInChatterGroup` is `true`, groups can carry related records through
`CollaborationGroupRecord`. Its `RecordId` is polymorphic but the guide enumerates exactly what it
refers to: **Account, Campaign, Case, Contact, Contract, Lead, Opportunity** (object_reference.txt
L67670–67693). Nothing else — no custom objects.

```apex
CollaborationGroupRecord link = new CollaborationGroupRecord(
    CollaborationGroupId = groupId,
    RecordId = accountId
);
insert link;
```

Governance consequence: a team that wants "the group for this Work Order" cannot have it, and will build
a naming convention instead. That is a reason to standardise names (`Customer-AcmeCorp-AccountTeam`)
rather than to rely on record association.
