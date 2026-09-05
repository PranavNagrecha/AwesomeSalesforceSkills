# Gotchas — Delegated Administration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Group Membership Alone Grants Nothing — the Delegated Admin Needs a Setup Permission Too

**What happens:** After a Salesforce admin creates a Delegated Administrator group and adds users to it, those users still see no change in their Setup experience. The "Manage Users" button does not appear. The admin assumes the group configuration is broken and reconfigures it repeatedly.

**When it occurs:** Any time a user is added to a Delegated Administrator group but their own profile and permission sets do not carry the Setup permission the feature requires. The Metadata API Developer Guide states the requirement on the `DelegateGroup` type directly: "Only users with the 'View Setup and Configuration' permission can be delegated administrators. As of Spring '20 and later, only users with 'View Setup' or 'Configuration' permission can access this object." The delegate group supplies *scope*; the user permission supplies *entry*.

**How to avoid:** Before testing, confirm the candidate delegated administrator's profile or one of their permission sets enables **View Setup and Configuration** (`ViewSetup` in Profile/PermissionSet metadata). `scripts/check_delegated_administration.py` reports which retrieved profiles and permission sets grant it. UNVERIFIED (2026-09-04): the widely-repeated claim that the **Manage Users** (`ManageUsers`) permission is *also* required does not appear in the Metadata API Developer Guide or the Object Reference — those files ground only "View Setup and Configuration". `ManageUsers` is a real permission name in both files (it appears in profile `userPermissions` and gates `UserLogin` access), and enabling it is harmless, but treat "Manage Users is required for delegated administration" as unconfirmed until you verify it in the org.

---

## Gotcha 2: System Administrator Users Are Always Protected — No Workaround

**What happens:** A delegated admin tries to reset the password of, or edit the record of, a user with the System Administrator profile. Salesforce silently excludes those users from the Manage Users view, or shows an error if accessed directly. The delegated admin reports that the feature "doesn't work" for specific users.

**When it occurs:** Any time a user with the System Administrator profile is in a role that falls within the delegated admin's configured role scope. Even if the role hierarchy technically places the System Admin under the delegated admin's scope, Salesforce does not allow delegated admins to touch any System Administrator profile user.

**How to avoid:** Document this constraint clearly when handing off delegated admin rights. For any action that requires modifying a System Administrator user, the request must be escalated to a full System Administrator. When designing role-scoped admin groups, plan on System Admin users in those roles being out of reach. UNVERIFIED (2026-09-04): the Metadata API Developer Guide's `DelegateGroup` field table and Special Access Rules do not state this protection, and the Object Reference documents no delegate-group SObject to check it against. Verify the behaviour in a sandbox before relying on it as a control — and do not rely on it *instead of* keeping the System Administrator profile out of the group's `profiles` list, which is the escalation path that is actually documented and actually checkable.

---

## Gotcha 3: Users Without a Role Are Invisible to Delegated Admins

**What happens:** A delegated admin is configured to manage users in a specific role branch. After setup, they report they can manage some users but not others. Upon investigation, the invisible users have no role assigned to their user record.

**When it occurs:** When users are created or migrated without a role assignment, or when a role is removed from a user record during an org cleanup. The `DelegateGroup` type scopes user administration entirely through its `roles` field — "the roles and subordinates for which delegated administrators of the group can create and edit users" (Metadata API Developer Guide). A user with a null role matches no entry in that list and no subordinate of one, so no delegate group can reach them.

**How to avoid:** Before assigning the delegated admin group, audit all users in the intended scope to confirm they have roles assigned. Add role assignment as a mandatory step in the user provisioning checklist. When troubleshooting "missing users" for a delegated admin, the first check should always be whether the missing users have a role.

---

## Gotcha 4: `customObjects` Is Wider Than Expected, and Its Two Documented Exclusions Are the Two That Matter

**What happens:** A business unit owner is granted Custom Object Administration rights for their custom object and turns out to be able to do far more than the admin who granted it expected — including creating a custom tab that puts the object in front of the whole org. Then the same owner hits a wall on the one change they actually needed: adding a lookup to Account. They ask why they cannot see the Flows section, or edit validation rules on Account, or write a trigger.

**When it occurs:** Whenever `customObjects` is read as "fields and layouts on that object". The Metadata API Developer Guide's `DelegateGroup` field table is both broader and sharper than that: delegated administrators "can customize nearly every aspect of each of those custom objects, including creating a custom tab. However, they can't create or modify relationships on the objects or set organization-wide sharing defaults." Everything outside the named objects — standard objects, Flows, Apex, reports — is untouched by the field, because the field names objects, not Setup areas.

**How to avoid:** Treat `customObjects` as delegating the object, not a list of allowed operations, and gate it on the object's blast radius rather than on the requester's seniority. Then plan for the two exclusions up front: relationship changes and org-wide sharing defaults on those objects always route back to a full administrator, so a business unit whose backlog is mostly "add a lookup to X" gets no relief from this feature. One further consequence from the same field description: "Delegated administrators must have access to custom objects to access the merge fields on those objects from formulas" — omitting an object here can break the delegated admin's ability to author formulas that reference it.

---

## Gotcha 5: Role Scope Is Additive — Adding a High Role Grants Access to All Subordinate Roles

**What happens:** An admin configures a Delegated Administrator group to cover a regional manager's role and adds "EMEA Director" to the "Users in Delegated Group" list. The intent is to let the delegated admin manage the EMEA Director and their direct reports. Instead, the delegated admin can manage every user under the EMEA Director's entire branch — hundreds of users across multiple departments.

**When it occurs:** When the admin does not fully understand that Salesforce automatically includes all subordinate roles when a role is added to the group. The "Users in Delegated Group" configuration is not a single-role assignment — it is a branch assignment.

**How to avoid:** Map the role hierarchy before configuring group scope. Only add the lowest-level roles that represent the actual intended scope. If you need to give access to just the direct reports of a manager, add those individual subordinate roles explicitly rather than the manager's role. Review the role hierarchy diagram after configuration to confirm the actual scope matches intent.

---

## Gotcha 6: `loginAccess` Is an Impersonation Grant Hidden Inside a User-Admin Feature — and the Target User Can Still Veto It

**What happens:** A delegate group is deployed with `<loginAccess>true</loginAccess>` because it was in the guide's sample and nobody questioned it. Every administrator in that group can now log in as the users they administer and act with those users' data access, not their own. Separately — and confusingly for whoever is debugging it — the same delegated administrator finds that log-in-as works for some managed users and is refused for others.

**When it occurs:** `loginAccess` is a **required** boolean on `DelegateGroup`, so it is present in every file whether or not anyone made a decision about it. The Metadata API Developer Guide defines it as: "Allows users in this group to log in as users in the role hierarchy that they administer (true) or not (false). Depending on your organization settings, individual users must grant login access to allow their administrators to log in as them." Those organization settings live in `SecuritySettings` — `canUsersGrantLoginAccess` and `enableAdminLoginAsAnyUser` — which is why the same delegate group behaves differently in two orgs, and why per-user grants make it inconsistent within one org.

**How to avoid:** Decide `loginAccess` explicitly for every group and default it to `false`; a group that exists to reset passwords and assign profiles does not need impersonation. When it must be `true`, record it as a privileged-access grant rather than a delegated-admin detail (`security/privileged-access-management`), and read the org's `SecuritySettings` in the same pass so you know whether target users must grant access individually or whether the org-wide setting already permits it. `scripts/check_delegated_administration.py` raises a WARN on every group with `loginAccess` true so the decision cannot pass a review silently.

---

## Gotcha 7: A Delegate Group Is Not a Public Group, and the `groups` Field Is Not the Delegate Group's Membership

**What happens:** An admin looks for the delegated administrators inside the deployed `.delegateGroup` file, finds a `<groups>` element, and assumes it lists them. Or they try to reference the delegate group in a sharing rule and cannot find it in the picker. Or they create a public group of the same name expecting the two to be linked.

**When it occurs:** Three separate collisions on the word "group", all in the same feature. The Metadata API Developer Guide opens the `DelegateGroup` type with the disclaimer: "Represents a group of users who have the same administrative privileges. These groups are different from public groups used for sharing." Meanwhile the type's own `groups` field means something else again — "the groups with users assigned by delegated administrators", i.e. the public groups into which this group's administrators may place their managed users. And the delegated administrators themselves are not a field in the guide's table at all; they are configured on the group in Setup.

**How to avoid:** Read the file as three distinct populations: the administrators (Setup, not in the XML), the managed users (`roles`), and the public groups those managed users may be dropped into (`groups`). Never expect a delegate group to appear anywhere in the sharing model — it grants administrative privilege, not record access, so it will not show up in sharing rules, queues, or `GroupMember`. Name delegate groups distinctly from public groups (`..._Delegated_Admins`) so an access review cannot confuse the two.

---

## Gotcha 8: `roles` Is the Only Field That Scopes Users — Everything Else Is a Menu, Not a Boundary

**What happens:** An admin trims a delegate group's `profiles` list to one profile, believing that narrows *who* the delegated administrator can touch. It does not. The administrator still reaches every user in the whole role branch; they simply have one profile to offer them. Conversely, a group is given a long `permissionSets` list "to be safe" and the reviewer reads it as a widened user scope, which it also is not.

**When it occurs:** Whenever the field list is read as a flat set of restrictions. The guide scopes `permissionSets` and `permissionSetGroups` explicitly to "users in specified roles and all subordinate roles", and `roles` is the field that defines those specified roles — "the roles and subordinates for which delegated administrators of the group can create and edit users". `profiles`, `permissionSets`, `permissionSetGroups`, and `groups` all operate *inside* that population; none of them narrows it.

**How to avoid:** Review the two halves separately and in order. First `roles`: expand every listed role's subtree and count the users it actually covers, because that number is the group's real blast radius. Only then review the assignment menus for privilege content. A group whose `roles` is empty manages nobody, which makes any `profiles` or `permissionSets` entries on it dead configuration that still has to be explained at audit time.

---

## Gotcha 9: The Assignable Profile and Permission Set Lists Are Unchecked Privilege Ladders

**What happens:** A delegate group is deployed listing an innocuous-sounding permission set — `Data_Steward`, say — that happens to enable Modify All Data. Every delegated administrator in the group can now grant Modify All Data to any user in their role branch, and then log in as one of them if `loginAccess` is true. The delegate group file itself looks entirely reasonable in review.

**When it occurs:** At deploy time, always. Nothing in the `DelegateGroup` schema inspects what a listed profile or permission set actually grants — the fields are plain `string[]` name references, and the guide describes them only as what "can be assigned". The privilege lives in the referenced `.profile` or `.permissionset` file, which is usually reviewed in a different pull request, by a different person, at a different time. `System Administrator` in `profiles` is the same failure with a more obvious name.

**How to avoid:** Review a delegate group and the permission sets it names as one change, never separately. Run `scripts/check_delegated_administration.py --manifest-dir <dir>` over a manifest containing both: it errors when `profiles` names System Administrator and when any listed permission set or profile file contains `<modifyAllData>true</modifyAllData>`. Where a delegated administrator genuinely needs to hand out a strong permission, split it into a narrow permission set that carries only that permission, so the escalation is visible in the group file's own field list.

---

## Gotcha 10: Setting Up Delegated Administration Exposes Profile Names Even When Profile Filtering Is On

**What happens:** An org enables Profile Filtering to hide profile names from users who have no business seeing the org's profile inventory. A security reviewer then finds profile names visible to non-administrators anyway, and cannot work out which permission leaked them.

**When it occurs:** The Metadata API Developer Guide's `Profile` type and the `enableProfileFiltering` setting both list delegated administration among the tasks that expose profile names regardless: "Set up delegated admins where looking up profiles is needed to identify assignable profiles", "Administer an org as a delegated customer admin", and "Administer an org as a delegated admin to view and assign profiles of the delegated group." Profile Filtering is available in API version 50.0 and later.

**How to avoid:** Treat profile-name visibility as a known, documented consequence of delegating administration rather than a misconfiguration to hunt for, and say so in the org's Profile Filtering design note. If specific profile *names* are themselves sensitive (they encode customer names, project code names, or an acquisition), rename them before delegating — the exposure follows from the feature and cannot be configured away while the delegate group exists.

---

## Gotcha 11: Every Reference in the File Is a Bare Name, So the Group Deploys Against the Wrong Things After a Rename

**What happens:** A delegate group deployed months ago quietly stops covering part of its intended scope. Nothing errored. A role was renamed during a hierarchy restructure, or a permission set was retired and recreated under a new API name, and the delegate group now points at names that no longer mean what they meant.

**When it occurs:** Every field on `DelegateGroup` except `label` and `loginAccess` is `string[]` — a list of names, not IDs: `customObjects`, `groups`, `permissionSetGroups`, `permissionSets`, `profiles`, `roles`. Nothing inside the file records what a name pointed at when it was written, and the type carries no per-entry version. This makes delegate groups particularly exposed to the role-hierarchy edits and permission-set consolidations that happen in ordinary org maintenance.

**How to avoid:** Retrieve delegate groups with `--metadata DelegateGroup` (the type supports the `*` wildcard, so one retrieve gets all of them) whenever roles, profiles, or permission sets are renamed or retired, and diff. `scripts/check_delegated_administration.py` warns on every referenced role, profile, permission set, permission set group, and custom object that has no matching file in the manifest directory — run it over a full retrieve, not a partial one, or the dangling-reference warnings will all be false. UNVERIFIED (2026-09-04): the guide does not state whether a deploy naming a nonexistent role or permission set fails or silently drops the entry, so verify with the retrieve round-trip in `references/metadata-examples.md` rather than assuming a deploy error would have caught it.
