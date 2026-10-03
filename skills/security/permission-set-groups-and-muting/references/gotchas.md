# Gotchas: Permission Set Groups And Muting

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each gotcha names the official source it rests on.

## Gotcha 1: In a Muting Permission Set, "Enabled" Means "Muted"

**What happens:** An admin builds a muting permission set and sets `<allowDelete>false</allowDelete>` on Account, expecting delete to be removed. Nothing changes. Later someone sets a field to `readable=true` in the muting set "so users can still see it" and the field disappears for the whole group.

**When it occurs:** Anyone who reads muting XML as a normal permission set.

**How to avoid:** Put only the permissions you want to remove in the muting set, and set them to `true`. Review muting files with that inversion in mind.

**Source:** Metadata API Developer Guide, MutingPermissionSet: "Unlike PermissionSet, settings enabled by MutingPermissionSet are turned off for the permission set group that it's a component of." Object Reference, FieldPermissions > Muting Permissions ("if a muting permission set is set for read and edit, the read and edit access is muted").

---

## Gotcha 2: Muting Can't Remove a Grant That Comes From Another Path

**What happens:** A PSG for junior agents mutes Delete on Case. Junior agents can still delete cases, because their profile also grants Delete.

**When it occurs:** Profile-heavy orgs adopting PSGs, or users who also hold a directly assigned permission set with the same permission.

**How to avoid:** Before muting, list every grant path for the permission. Remove it from the profile and from directly assigned permission sets, then mute it inside the group.

**Source:** Salesforce Security Guide, "Revoke Permissions and Access": profiles, permission sets, and PSGs "grant access but not to deny access... To revoke a permission, you must remove all instances of the permission from the user." The same section names muting permission sets as a way to mute permissions "for the users assigned to the permission set group."

---

## Gotcha 3: A Permission Set Group File Holds No Permissions

**What happens:** A team retrieves only `PermissionSetGroup` and deploys it to a new org. The group arrives with references to permission sets that don't exist there, or with outdated ones.

**When it occurs:** Manifests that list PSGs without their component permission sets and muting sets.

**How to avoid:** Retrieve and deploy `PermissionSetGroup`, every `PermissionSet` it references, and its `MutingPermissionSet` together.

**Source:** Metadata API Developer Guide, PermissionSetGroup: "Individual permissions are included in the permission set referenced, not in the permission set group," and "to retrieve PermissionSetGroup, you must also retrieve PermissionSet."

---

## Gotcha 4: A Deployed Permission Set Replaces the Set's Contents

**What happens:** A developer deploys a trimmed permission set file containing only the new object permission. In production the permission set loses every other grant that was not in the file, and every PSG that includes it shrinks.

**When it occurs:** Hand-built or partially retrieved permission set files deployed at API version 40.0 or later.

**How to avoid:** Retrieve the full permission set before editing. Treat the file as the complete definition. Review the diff for removed grants before deploying.

**Source:** Metadata API Developer Guide, PermissionSet: "In API version 40.0 and later... when you deploy a permission set, you must include all of its metadata to avoid accidentally overwriting the permission set's contents."

---

## Gotcha 5: Group Access Is Current Only When Status Is Updated

**What happens:** A deployment changes a component permission set. Users report the old access for a while, or the new access never arrives because recalculation failed.

**When it occurs:** Changes to permission sets that are in PSGs, especially large groups.

**How to avoid:** After the change, query `SELECT DeveloperName, Status FROM PermissionSetGroup` and wait for `Updated`. Investigate `Failed` before closing the change.

**Source:** Object Reference, PermissionSetGroup `Status` (Updated, Outdated, Updating, Failed) and PermissionSetGroupComponent ("enables permission set group recalculation to determine the aggregated permissions for the group"). Metadata API Developer Guide, PermissionSetGroup `status`.

---

## Gotcha 6: Temporary Access Stays Unless the Assignment Expires

**What happens:** A contractor gets a PSG for a three-month project. Nobody removes it, and the access lasts for years.

**When it occurs:** Project, audit, or break-glass access granted through ordinary assignments.

**How to avoid:** Set `ExpirationDate` on the `PermissionSetAssignment` for time-boxed access. For step-up access, use a PSG with `hasActivationRequired` so the group applies only to sessions that activate it.

**Source:** Object Reference, PermissionSetAssignment `ExpirationDate` ("The date that the assignment of the permission set or permission set group expires for the specified user", API 52.0+). Metadata API Developer Guide, PermissionSetGroup `hasActivationRequired` (API 53.0+).

---

## Gotcha 7: One Muting Set per Group

**What happens:** A designer plans several muting sets on one PSG, one per restricted feature, and the configuration can't be saved.

**When it occurs:** Designs that treat muting sets like ordinary permission sets.

**How to avoid:** Put all mutes for a group in its single muting permission set, and keep the list short. If the list grows, split the base permission sets instead.

**Source:** Metadata API Developer Guide, PermissionSetGroup `mutingPermissionSets` is documented as "A permission set containing permissions to disable" (singular, type string). UNVERIFIED (2026-10-03): the explicit "one muting permission set per permission set group" rule is stated only in Salesforce Help.
