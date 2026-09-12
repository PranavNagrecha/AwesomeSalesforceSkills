# Metadata Examples — Profile vs Permission Set

Deployable shapes for the split this skill decides: a **base profile** carrying only what a profile can carry, and a **permission set** carrying everything else. Element names, enum values and the skeletons come from the Metadata API Developer Guide (v62 PDF, `Profile` and `PermissionSet` / `PermissionSetGroup` sections); the worked example extends the guide's own sample definitions into a realistic sales persona.

Validate the result with:

```bash
python3 skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py --manifest-dir force-app/main/default
```

## Where the files live

| Component | package.xml `<name>` | File in a DX project | API |
|---|---|---|---|
| Base profile | `Profile`, member `Minimum_Access_Base` | `profiles/Minimum_Access_Base.profile-meta.xml` | 10.0+ |
| Permission set | `PermissionSet`, member `Sales_Core_Access` | `permissionsets/Sales_Core_Access.permissionset-meta.xml` | 22.0+ |
| Permission set group | `PermissionSetGroup`, member `SalesRep_Bundle` | `permissionsetgroups/SalesRep_Bundle.permissionsetgroup-meta.xml` | 45.0+ |

The Metadata API suffixes are `.profile`, `.permissionset` and `.permissionsetgroup`; DX source format appends `-meta.xml`. All three types accept the `*` wildcard in package.xml.

## The element-level split — what only a Profile can hold

This is the table that decides the migration. Left column = present in the `Profile` field table and absent from the `PermissionSet` field table; there is no permission-set equivalent, so anything in this list is residue that stays on the profile.

| Profile-only element | What it does | Why it cannot move |
|---|---|---|
| `loginHours` | `<mondayStart>` / `<mondayEnd>` etc., minutes since midnight, divisible by 60 | No `loginHours` field on `PermissionSet` |
| `loginIpRanges` | `startAddress`, `endAddress`, `description` | No `loginIpRanges` field on `PermissionSet` |
| `layoutAssignments` | `layout` (+ optional `recordType`) — which page layout a user sees | No layout element on `PermissionSet` at all |
| `custom` | `true` = custom profile, `false` = standard profile (API 30.0+) | Profile-shape flag with no permission-set analogue |
| `categoryGroupVisibilities` | Data category group visibility (API 41.0+) | No equivalent field on `PermissionSet` |
| `loginFlows` | Login flow association | No equivalent field on `PermissionSet` |
| `profileActionOverrides` | Home-tab action override, API 39.0–44.0 only; moved to `CustomApplication` in 45.0+ | Was never a permission-set element |
| `<default>` inside `applicationVisibilities` | Marks the user's **default landing app**; only one app per profile may be `true` | `PermissionSetApplicationVisibility` has `application` and `visible` only — no `default` |
| `<default>` and `<personAccountDefault>` inside `recordTypeVisibilities` | Which record type is preselected when the user creates a record | `PermissionSetRecordTypeVisibility` has `recordType` and `visible` only |

The mirror image — present on `PermissionSet`, absent from `Profile`:

| PermissionSet-only element | What it does |
|---|---|
| `label` | Required display label, 80-character limit; a profile has no `label` element |
| `license` | The permission set license or user license it is scoped to (API 38.0+; replaces the deprecated `userLicense`) |
| `hasActivationRequired` | Makes it a session-based permission set (API 37.0+) |
| `emailRoutingAddressAccesses` | Email Routing Address permissions (API 62.0+) |
| `externalCredentialPrincipalAccesses` | External credential principals (API 59.0+) |
| `tabSettings` | Tab visibility — see the enum trap below |

**The tab enum trap.** Both types control tabs, but neither the element name nor the values match. `Profile` uses `tabVisibilities` with `DefaultOff` / `DefaultOn` / `Hidden`. `PermissionSet` uses `tabSettings` with `Available` / `None` / `Visible`. Copying a profile's `<tabVisibilities>` block into a permission set fails on both counts.

**The required-field trap.** In `PermissionSetObjectPermissions` the guide marks `allowCreate`, `allowDelete`, `allowEdit`, `allowRead`, `modifyAllRecords` and `viewAllRecords` **Required** — every permission set object block must state all six explicitly. The matching `ProfileObjectPermissions` fields are not marked required, and `objectPermissions` is only retrieved on a profile when `allowRead` is `true` (API 28.0+). So a profile block you copied across is usually short of what the permission set schema demands.

## How to read the examples

- **Everything the profile keeps is a *default* or a *login control*.** Record-type access and app access are grantable from a permission set; only the *default* record type and the *default* app are profile-bound. That distinction is why a migrated user keeps their access but lands on the wrong app.
- **`loginHours` times are minutes since midnight and must divide by 60.** The guide's own worked values: `300` is 5:00 AM, `1020` is 5:00 PM. Below, `480` is 8:00 AM and `1200` is 8:00 PM.
- **To delete login-hour restrictions, deploy an empty `<loginHours/>` tag.** The guide is explicit: an empty element with no start or end times is the only way to clear them; omitting the block leaves them in place.
- **`layout` uses `Object-Layout Name`.** Same form the guide uses in a `Layout` package.xml member (`Idea-Idea Layout`).
- **`recordType` uses `Object.RecordTypeName`**, e.g. `Account.Customer`, in both `recordTypeVisibilities` variants.
- **`field` uses `Object.Field__c`**, and for shared Activity fields specify `Event` or `Task` (e.g. `Event.Meeting__c`) — not `Activity`.
- **Required fields cannot be expressed in FLS.** In API 30.0 and later, permissions for required fields can be neither retrieved nor deployed in `fieldPermissions`.
- **`viewAllFields` suppresses the field list.** If `viewAllFields` is enabled for an object in a permission set, the individual fields are not returned under `fieldPermissions` at all; disabling it makes them reappear.
- **A permission set grants; it never denies.** The guide states it plainly: "You can use permission sets to grant access but not to deny access." Subtraction inside a group is a muting permission set — see `security/permission-set-groups-and-muting`.

## The base profile — only what a profile must hold

`profiles/Minimum_Access_Base.profile-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <custom>true</custom>
    <description>Base profile for all internal Salesforce-licence users. Login controls, default app, default record type and layout assignment only. All object, field and feature access is granted by permission set.</description>
    <userLicense>Salesforce</userLicense>

    <!-- Default landing app. Only one applicationVisibilities entry may set default=true. -->
    <applicationVisibilities>
        <application>Sales_Console</application>
        <default>true</default>
        <visible>true</visible>
    </applicationVisibilities>

    <!-- Default record type. The permission set grants VISIBILITY; only the profile can mark a DEFAULT. -->
    <recordTypeVisibilities>
        <default>true</default>
        <personAccountDefault>false</personAccountDefault>
        <recordType>Account.Customer</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>

    <!-- Page layout assignment. No permission-set equivalent exists. -->
    <layoutAssignments>
        <layout>Account-Account Sales Layout</layout>
        <recordType>Account.Customer</recordType>
    </layoutAssignments>

    <!-- Login window: 480 = 08:00, 1200 = 20:00, local to the org time zone. Values must divide by 60. -->
    <loginHours>
        <mondayStart>480</mondayStart>
        <mondayEnd>1200</mondayEnd>
        <tuesdayStart>480</tuesdayStart>
        <tuesdayEnd>1200</tuesdayEnd>
        <wednesdayStart>480</wednesdayStart>
        <wednesdayEnd>1200</wednesdayEnd>
        <thursdayStart>480</thursdayStart>
        <thursdayEnd>1200</thursdayEnd>
        <fridayStart>480</fridayStart>
        <fridayEnd>1200</fridayEnd>
    </loginHours>

    <loginIpRanges>
        <description>Head office egress</description>
        <startAddress>203.0.113.0</startAddress>
        <endAddress>203.0.113.255</endAddress>
    </loginIpRanges>
</Profile>
```

There is deliberately no `objectPermissions`, no `fieldPermissions`, no `userPermissions`, no `classAccesses` and no `tabVisibilities` block. That is the whole point of the split: everything absent here is present in the permission set below.

## The permission set — everything else

`permissionsets/Sales_Core_Access.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Sales Core Access</label>
    <description>Object, field, tab, app and feature access for the Sales Rep persona. Assigned through SalesRep_Bundle.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <license>Salesforce</license>

    <applicationVisibilities>
        <application>Sales_Console</application>
        <visible>true</visible>
    </applicationVisibilities>

    <objectPermissions>
        <object>Account</object>
        <allowCreate>true</allowCreate>
        <allowRead>true</allowRead>
        <allowEdit>true</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>false</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
        <viewAllFields>false</viewAllFields>
    </objectPermissions>
    <objectPermissions>
        <object>Credit_Application__c</object>
        <allowCreate>true</allowCreate>
        <allowRead>true</allowRead>
        <allowEdit>true</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>false</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
        <viewAllFields>false</viewAllFields>
    </objectPermissions>

    <fieldPermissions>
        <field>Credit_Application__c.Credit_Limit__c</field>
        <readable>true</readable>
        <editable>false</editable>
    </fieldPermissions>
    <fieldPermissions>
        <field>Credit_Application__c.Requested_Amount__c</field>
        <readable>true</readable>
        <editable>true</editable>
    </fieldPermissions>

    <!-- Record type ACCESS moves. The DEFAULT stayed on the profile above. -->
    <recordTypeVisibilities>
        <recordType>Account.Customer</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>

    <!-- Note the element name and enum: tabSettings / Visible, NOT tabVisibilities / DefaultOn. -->
    <tabSettings>
        <tab>Credit_Application__c</tab>
        <visibility>Visible</visibility>
    </tabSettings>

    <classAccesses>
        <apexClass>CreditApplicationService</apexClass>
        <enabled>true</enabled>
    </classAccesses>

    <customPermissions>
        <name>Submit_Credit_Application</name>
        <enabled>true</enabled>
    </customPermissions>

    <userPermissions>
        <enabled>true</enabled>
        <name>ViewRoles</name>
    </userPermissions>
</PermissionSet>
```

## The group that binds the persona

`permissionsetgroups/SalesRep_Bundle.permissionsetgroup-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSetGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Sales Rep Bundle</label>
    <description>Persona bundle for Sales Reps on the Minimum_Access_Base profile.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <permissionSets>Sales_Core_Access</permissionSets>
</PermissionSetGroup>
```

Individual permissions are never written in the group file — only the names of the permission sets it composes. Group-level subtraction uses `<mutingPermissionSets>`; the mechanics are in `admin/permission-set-group-composition`.

## package.xml

Retrieving a profile or permission set on its own returns almost nothing useful. The guide's rule: the returned `.profile` files include security settings **only for the other metadata types referenced in the same retrieve request**, with user permissions, IP address ranges and login hours as the always-retrieved exceptions. So the manifest must name every object, field, tab, app, record type, layout and class whose permissions you expect to see.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account</members>
        <members>Credit_Application__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Credit_Application__c.Credit_Limit__c</members>
        <members>Credit_Application__c.Requested_Amount__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Credit_Application__c</members>
        <name>CustomTab</name>
    </types>
    <types>
        <members>Sales_Console</members>
        <name>CustomApplication</name>
    </types>
    <types>
        <members>Account.Customer</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>Account-Account Sales Layout</members>
        <name>Layout</name>
    </types>
    <types>
        <members>CreditApplicationService</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Minimum_Access_Base</members>
        <name>Profile</name>
    </types>
    <types>
        <members>Sales_Core_Access</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>SalesRep_Bundle</members>
        <name>PermissionSetGroup</name>
    </types>
    <version>62.0</version>
</Package>
```

Two manifest rules worth stating explicitly, both from the guide:

- **`<members>*</members>` on `CustomObject` does not match standard objects.** The guide describes this as deliberate: it stops a Developer Edition retrieve from later overwriting production FLS on Account and every other standard object. To include a standard object you must name it as a member of `CustomObject` — `<members>Account</members>`, exactly as above.
- **Relationship fields drop the `Id`.** To retrieve field permissions for Contact's `AccountId`, the member is `Contact.Account`, not `Contact.AccountId`.

## Retrieve

```bash
# Retrieve using the manifest above — the only shape that returns complete profile permissions
sf project retrieve start --manifest manifest/package.xml --target-org myOrg

# Permission sets are self-contained from API 40.0 onward: all content exposed in
# Metadata API for the permission set is included in the retrieve.
sf project retrieve start --metadata "PermissionSet:Sales_Core_Access" --target-org myOrg

# This is the retrieve that produces a misleadingly empty profile. Use it only when
# you want login hours, IP ranges and system permissions and nothing else.
sf project retrieve start --metadata "Profile:Minimum_Access_Base" --target-org myOrg
```

## Deploy

```bash
# Validation-only run first. The profile deploy is the destructive half of the pair.
sf project deploy validate --manifest manifest/package.xml --target-org myOrg

# Order matters: the permission set and group must exist and be assigned before the
# profile is stripped, or users lose access in the window between the two deploys.
sf project deploy start --metadata "PermissionSet:Sales_Core_Access" --target-org myOrg
sf project deploy start --metadata "PermissionSetGroup:SalesRep_Bundle" --target-org myOrg
sf project deploy start --manifest manifest/package.xml --target-org myOrg
```

Profile deployment **overlays** the target profile rather than replacing it. The guide states that disabled permissions are not exported, so a deploy that is silent about a permission leaves whatever the target org already had. Removing a permission through metadata requires writing it out explicitly as `false`.

## Verify

Run these after the deploy, before declaring the migration done.

```soql
-- 1. Every profile in the org and its hidden permission set.
--    A profile's permissions are stored in a PermissionSet row with IsOwnedByProfile = true.
SELECT Id, Name, Label, IsOwnedByProfile, ProfileId, Profile.Name
FROM PermissionSet
WHERE IsOwnedByProfile = true
ORDER BY Profile.Name
```

The Object Reference is explicit that these rows are readable but not writable: "You can query permission sets that are owned by profiles but not modify them." It also warns not to key anything off their `Name` or `Label`, because those values can change.

```soql
-- 2. What object access does the base profile still grant? Should be empty after the strip.
--    Absence of a record means no access; you cannot query for "no access" directly.
SELECT ParentId, Parent.Profile.Name, SobjectType,
       PermissionsRead, PermissionsCreate, PermissionsEdit, PermissionsDelete,
       PermissionsViewAllRecords, PermissionsModifyAllRecords
FROM ObjectPermissions
WHERE Parent.IsOwnedByProfile = true
  AND Parent.Profile.Name = 'Minimum Access Base'
```

```soql
-- 3. Assignment counts per permission set — did the population actually land?
SELECT PermissionSet.Name, PermissionSet.Label, COUNT(Id) Assignments
FROM PermissionSetAssignment
WHERE PermissionSet.IsOwnedByProfile = false
  AND Assignee.IsActive = true
GROUP BY PermissionSet.Name, PermissionSet.Label
ORDER BY COUNT(Id) DESC
```

```soql
-- 4. Assignment counts per group, including expiring and revoked rows.
SELECT PermissionSetGroup.DeveloperName, Assignee.Name, ExpirationDate, IsActive
FROM PermissionSetAssignment
WHERE PermissionSetGroupId != null
  AND Assignee.IsActive = true
ORDER BY PermissionSetGroup.DeveloperName
```

```soql
-- 5. Grant attribution: for one object, which users got Read, and via profile or permission set?
SELECT Assignee.Name, PermissionSet.Id, PermissionSet.IsOwnedByProfile
FROM PermissionSetAssignment
WHERE PermissionSetId IN (
    SELECT ParentId FROM ObjectPermissions
    WHERE SObjectType = 'Credit_Application__c' AND PermissionsRead = true)
```

**Setup check.** Confirm the residue actually took effect on a real user: Setup → Users → the migrated user → **View Summary** shows combined effective access across the profile and every assigned permission set. If Read appears there and step 2 returned nothing, the grant came from the permission set — which is the intended end state.

## Description length

`Profile.description` and `PermissionSet.description` are both capped at 255 characters — the Metadata API Developer Guide: "The profile description. Limit: 255 characters" (`api_meta` L97678) and "The permission set description. Limit: 255 characters" (`api_meta` L94788).

`PermissionSetGroup.description` has no stated limit in the guide (`api_meta` L95328 — "The permission set group description provided by the permission set group creator", no `Limit:` clause). Treat it as 255 anyway — **UNVERIFIED (2026-09-11)**: no dry run has directly rejected an over-length PSG description, but `sf project deploy start --dry-run` against a Summer '26 developer org on 2026-09-11 rejected four over-length `PermissionSet` files and three over-length `Profile` files, and the `PermissionSetGroup` files that referenced the rejected sets then failed as a cascade with `permission set names are invalid` (`examples/builds/case-onboarding/reports/MOCK-DEPLOY-M2.md`, once exported).

**Where rationale goes instead.** Residue reasoning ("why this stays on the profile", "which persona this base is for", "what was deferred to a later phase") belongs in the build's `deploy-order.md` or `templates/permission-set-design-template.md`, not in `description`. Keep the metadata field to a one-line label a Setup user can scan.

`scripts/check_access_model.py` enforces this: `PSVP-DESC-01` (ERROR) at 255+ characters on any `Profile`, `PermissionSet`, or `PermissionSetGroup` file; `PSVP-DESC-02` (WARN) at 200+ characters as headroom.

## Also read

- `references/gotchas.md` — the platform behaviours that break this split in practice
- `admin/permission-set-architecture` — how to shape the permission sets before you write them
- `agents/profile-to-permset-migrator/AGENT.md` — the run-time agent that produces these stubs from a live org
