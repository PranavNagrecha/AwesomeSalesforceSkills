# Metadata Examples — Delegated Administration

Deployable shapes for the `DelegateGroup` metadata type, taken from the Metadata API Developer Guide (v66 PDF, `DelegateGroup`, pp. 918–919) and extended to a realistic regional-admin group.

`DelegateGroup` "represents a group of users who have the same administrative privileges. These groups are different from public groups used for sharing" (Metadata API Developer Guide, `DelegateGroup`). It extends the `Metadata` type and inherits `fullName`.

## Where the file lives

| Item | Value | Source |
|---|---|---|
| package.xml `<name>` | `DelegateGroup` (wildcard `*` supported) | Guide, *Wildcard Support in the Manifest File* |
| MDAPI file | `delegateGroups/APAC_Sales_Delegated_Admins.delegateGroup` | Guide, *File Suffix and Directory Location* |
| DX source file | `force-app/main/default/delegateGroups/APAC_Sales_Delegated_Admins.delegateGroup-meta.xml` | same suffix, `-meta.xml` in source format |
| Minimum API version | 36.0 | Guide, *Version* |
| Who may be a delegated administrator | users with the "View Setup and Configuration" permission; as of Spring '20, only users with "View Setup" or "Configuration" permission can access the object | Guide, *Special Access Rules* |

The file prefix must match the developer name of the delegate group — a group whose developer name is `MyDelegateGroup` lives in `MyDelegateGroup.delegateGroup`.

## Every field, and which side of the fence it sits on

The guide's field table splits cleanly into three groups. Confusing them is the single most common design error in this domain.

| Field | Type | Scope it controls | What the guide says |
|---|---|---|---|
| `roles` | `string[]` | **Which users are managed** | "The roles and subordinates for which delegated administrators of the group can create and edit users." |
| `profiles` | `string[]` | **What can be assigned** | "The profiles that can be assigned to users by delegated administrators." |
| `permissionSets` | `string[]` | **What can be assigned** | "The permission sets that can be assigned to users in specified roles and all subordinate roles by delegated administrators." |
| `permissionSetGroups` | `string[]` | **What can be assigned** | "The permission set groups that can be assigned to users in specified roles and all subordinate roles by delegated administrators." |
| `groups` | `string[]` | **What can be assigned** | "The groups with users assigned by delegated administrators." |
| `customObjects` | `string[]` | **What can be administered** | Delegated admins "can customize nearly every aspect of each of those custom objects, including creating a custom tab. However, they can't create or modify relationships on the objects or set organization-wide sharing defaults." |
| `loginAccess` | `boolean` | **Impersonation** | Required. "Allows users in this group to log in as users in the role hierarchy that they administer (true) or not (false)." |
| `label` | `string` | Naming | Required. "The delegated group's non-API name." |

`roles` is the *only* field that decides which users are in scope. Everything else is a menu the delegated administrator may hand out to users already in that scope.

## Regional manager group — two roles, two profiles, two permission sets, one custom object

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DelegateGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <customObjects>Territory_Request__c</customObjects>
    <groups>APAC_Field_Sales</groups>
    <label>APAC Sales Delegated Admins</label>
    <loginAccess>true</loginAccess>
    <name>APAC_Sales_Delegated_Admins</name>
    <permissionSetGroups>APAC_Sales_Rep_PSG</permissionSetGroups>
    <permissionSets>Territory_Request_Editor</permissionSets>
    <permissionSets>Sales_Console_User</permissionSets>
    <profiles>APAC Sales Rep</profiles>
    <profiles>APAC Sales SDR</profiles>
    <roles>APAC_Sales_Manager</roles>
    <roles>APAC_SDR_Manager</roles>
</DelegateGroup>
```

How to read it:

- **`roles` is a branch, not a role.** The guide's wording is "the roles **and subordinates**". Listing `APAC_Sales_Manager` puts every role beneath it in scope too, so this group covers the two named manager roles plus everything under them. Add the lowest roles that cover the intent, not the top of the branch (`references/gotchas.md` #5).
- **`roles` values are role API names.** A `Role`'s `fullName` "corresponds to Role Name in the user interface" (Guide, `Role`), so `APAC_Sales_Manager` is the developer name from `roles/APAC_Sales_Manager.role-meta.xml`, not the role label.
- **`profiles` values are profile names, and there is no privilege check in the file.** Nothing in the XML stops you writing `<profiles>System Administrator</profiles>`; the deploy succeeds and the delegated administrator can then mint full administrators. `scripts/check_delegated_administration.py` errors on exactly that.
- **`permissionSets` / `permissionSetGroups` are assignment menus, not grants.** They say what this group's administrators may attach to a managed user. The permission set's own contents are unconstrained by this file — a permission set with `<modifyAllData>true</modifyAllData>` listed here is a privilege-escalation path, which the checker also errors on.
- **`groups` is public-group membership, not the delegate group's own membership.** The delegate group's administrators are configured in Setup, not in this field; `groups` lists the public groups into which those administrators may place their managed users.
- **`customObjects` is broader than most people assume and narrower in two specific places.** "Nearly every aspect … including creating a custom tab", but *not* creating or modifying relationships and *not* org-wide sharing defaults. Also from the guide: "Delegated administrators must have access to custom objects to access the merge fields on those objects from formulas."
- **`loginAccess>true` turns this into an impersonation grant.** The delegated administrator can log in as users in the role hierarchy they administer. The guide adds: "Depending on your organization settings, individual users must grant login access to allow their administrators to log in as them" — those settings are `SecuritySettings.canUsersGrantLoginAccess` and `SecuritySettings.enableAdminLoginAsAnyUser`.
- **`<name>` is in the guide's own sample but not in its field table.** The field table documents `label` as the required non-API name and inherits `fullName`; the sample definition nonetheless includes `<name>MyDelegateGroup</name>`. Keep it and make it match the file name. UNVERIFIED (2026-09-04): the Metadata API Developer Guide does not say whether `<name>` is required, optional, or ignored on deploy for this type — the field table omits it while the sample definition includes it. If a deploy rejects the element, remove it and rely on the file name for `fullName`.
- **Element order.** The guide's sample orders the elements `label`, `loginAccess`, `name`, `profiles`, `permissionSetGroups`, `permissionSets`, `roles` — not alphabetical. The block above is alphabetical because that is what a retrieve emits. UNVERIFIED (2026-09-04): the guide does not state whether `DelegateGroup` child elements must appear in a fixed sequence. If a deploy rejects the file with a schema error, reorder to match the guide's sample.

## Custom-object-only group — no user management at all

A delegate group with no `roles` administers objects and manages nobody. `loginAccess` is still required, so it must be present and `false`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DelegateGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <customObjects>Product_Request__c</customObjects>
    <label>Product Ops Object Admins</label>
    <loginAccess>false</loginAccess>
    <name>Product_Ops_Object_Admins</name>
</DelegateGroup>
```

With `roles` empty there is nothing for `profiles`, `permissionSets`, `permissionSetGroups`, or `groups` to act on — the guide scopes all four to "users in specified roles and all subordinate roles". Listing them here is dead configuration that still shows up in an access review.

## The guide's own sample definition, verbatim

Reproduced so you can diff any hand-written file against it:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DelegateGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>MyDelegateGroup</label>
    <loginAccess>true</loginAccess>
    <name>MyDelegateGroup</name>
    <profiles>Chatter Free User</profiles>
    <profiles>Chatter Moderator User</profiles>
    <profiles>Marketing User</profiles>
    <permissionSetGroups>My Permission Set Group</permissionSetGroups>
    <permissionSets>My Permset</permissionSets>
    <roles>LesserBossMan</roles>
</DelegateGroup>
```

## package.xml

Everything the group references must already exist in the target org, so deploy roles, profiles, permission sets, permission set groups, public groups, and custom objects **before** the delegate group, or in the same package.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>APAC_Sales_Delegated_Admins</members>
        <members>Product_Ops_Object_Admins</members>
        <name>DelegateGroup</name>
    </types>
    <types>
        <members>APAC_Sales_Manager</members>
        <members>APAC_SDR_Manager</members>
        <name>Role</name>
    </types>
    <version>62.0</version>
</Package>
```

`DelegateGroup` supports the `*` wildcard, so `<members>*</members>` retrieves every delegate group in the org — the fastest way to start an access review.

## Retrieve, check, deploy

```bash
# Pull every delegate group in the org for review
sf project retrieve start --metadata DelegateGroup --target-org my-sandbox

# Pull one group plus the roles it names
sf project retrieve start \
  --metadata DelegateGroup:APAC_Sales_Delegated_Admins \
  --metadata Role --target-org my-sandbox

# Static checks before the deploy: escalation paths, dangling references, log-in-as
python3 skills/admin/delegated-administration/scripts/check_delegated_administration.py \
  --manifest-dir force-app/main/default

# Validate-only first — delegate groups fail late if a referenced name is wrong
sf project deploy start --source-dir force-app/main/default/delegateGroups \
  --dry-run --target-org my-sandbox

sf project deploy start --source-dir force-app/main/default/delegateGroups \
  --target-org my-sandbox
```

## Verification after deploy

The Object Reference documents no `DelegateGroup`, `DelegateGroupMember`, or `DelegateGroupGrant` SObject, so there is no SOQL verification path for this type. Verify these three ways instead.

1. **Retrieve round-trip.** Re-run the retrieve above and diff the returned file against the one you deployed. Silently dropped `roles`, `profiles`, or `permissionSets` entries mean the referenced name did not resolve in the target org.

   ```bash
   sf project retrieve start --metadata DelegateGroup:APAC_Sales_Delegated_Admins --target-org my-sandbox
   git diff --stat force-app/main/default/delegateGroups
   ```

2. **Setup check.** Setup → Users → Delegated Administrators → *APAC Sales Delegated Admins*. Confirm the related lists match the file: the roles, the assignable profiles, the assignable permission sets and permission set groups, the public groups, the custom objects, and the "Enable Group for Login Access" state that `loginAccess` sets.

3. **Behavioural check, as the delegated administrator.** Log in as one of the group's administrators and confirm (a) they can open user management for a user in one of the listed roles, (b) the profile picker offers only the listed profiles, and (c) a user in a role *outside* the listed branch is not reachable. Steps 1–8 of `references/llm-anti-patterns.md` anti-pattern 5 are the full script.

## Cross-references

| For | Read |
|---|---|
| What goes *in* the permission sets you list in `permissionSets` | `admin/permission-set-architecture` |
| Shaping the role branches that `roles` points at | `admin/role-hierarchy-design` |
| Provisioning, licensing, and deactivating the users being managed | `admin/user-management` |
| Governing standing administrative access and log-in-as generally | `security/privileged-access-management` |
