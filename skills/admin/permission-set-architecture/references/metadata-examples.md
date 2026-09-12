# Metadata Examples — Permission Set Architecture

Deployable shapes taken from the Metadata API Developer Guide (`PermissionSet`, `PermissionSetGroup`, `MutingPermissionSet` types) and the Object Reference (`PermissionSet`, `PermissionSetAssignment`, `ObjectPermissions`, `FieldPermissions`, `PermissionSetGroup`). The three examples below are one persona end to end: an object-access set, a function set, and the PSG that composes them with a muting set.

## Where the files live

| Type | package.xml `<name>` | File in a DX project | API |
|---|---|---|---|
| `PermissionSet` | `PermissionSet` (wildcard `*` allowed) | `permissionsets/Obj_Case_Agent.permissionset-meta.xml` | 22.0+ |
| `PermissionSetGroup` | `PermissionSetGroup` (wildcard `*` allowed) | `permissionsetgroups/Persona_Service_Agent_T1.permissionsetgroup-meta.xml` | 45.0+ |
| `MutingPermissionSet` | `MutingPermissionSet` | `mutingpermissionsets/Mute_T1_Refund_Approval.mutingpermissionset-meta.xml` | 46.0+ |

The file name is the API name (`fullName`); `label` inside the file is what Setup shows.

---

## 1. Object-access permission set

One object, its CRUD level, the fields that level implies, the tab, and the record types the persona may pick.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Obj Case Agent</label>
    <description>Case CRUD for front-line agents. Object-access category; carries no system permissions.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Case</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
    <fieldPermissions>
        <editable>true</editable>
        <field>Case.Priority</field>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <editable>true</editable>
        <field>Case.Internal_Notes__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <editable>false</editable>
        <field>Case.Refund_Amount__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <tabSettings>
        <tab>standard-Case</tab>
        <visibility>Visible</visibility>
    </tabSettings>
    <recordTypeVisibilities>
        <recordType>Case.Support</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>
</PermissionSet>
```

How to read it:

- **`objectPermissions` is a dependency chain, not six independent switches.** The Object Reference states the requirements on `ObjectPermissions`: `PermissionsCreate` and `PermissionsEdit` require `PermissionsRead`; `PermissionsDelete` requires read and edit; `PermissionsViewAllRecords` requires read; `PermissionsModifyAllRecords` requires read, delete, edit, and `PermissionsViewAllRecords`. Deploying `allowEdit` with `allowRead` false fails.
- **`fieldPermissions` cannot outrun the object grant, and `readable` is the floor.** `PermissionsEdit` requires `PermissionsRead` on the same field, and a `FieldPermissions` record with `PermissionsRead` false "will be deleted" — an entry with `editable` true and `readable` false is either a deploy error or a silently discarded row. Required fields cannot be retrieved or deployed at all in API 30.0+; auto-number and formula fields accept `readable` only.
- **`viewAllFields`** (API 63.0+) is the fourth read-side object switch. When it is enabled, individual fields stop being returned under `fieldPermissions` on retrieve — the FLS is still in effect, it is just no longer visible in the file.
- **`tabSettings.visibility`** takes `Available`, `None`, or `Visible`. `Available` puts the tab on the All Tabs page only; `Visible` also puts it in the app.
- **`recordTypeVisibilities`** is never retrieved or deployed for inactive record types, so deactivating a record type silently drops it out of every permission set file on the next retrieve.
- **`hasActivationRequired`** stays `false` here on purpose. See the session-activation gotcha before setting it `true` on anything destined for a PSG.

---

## 2. Function permission set

System permissions, the code and flows that implement the capability, and the custom permission that gates it. No object rows — those belong in the object-access set.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Feat Case Escalation</label>
    <description>Escalate and transfer cases. Feature-access category; composed into agent and lead personas.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <license>Salesforce</license>
    <userPermissions>
        <enabled>true</enabled>
        <name>TransferAnyCase</name>
    </userPermissions>
    <userPermissions>
        <enabled>true</enabled>
        <name>ApiEnabled</name>
    </userPermissions>
    <classAccesses>
        <apexClass>CaseEscalationService</apexClass>
        <enabled>true</enabled>
    </classAccesses>
    <flowAccesses>
        <enabled>true</enabled>
        <flow>Escalate_Case_Screen</flow>
    </flowAccesses>
    <customPermissions>
        <enabled>true</enabled>
        <name>Escalate_Premium_Case</name>
    </customPermissions>
    <applicationVisibilities>
        <application>standard__Service</application>
        <visible>true</visible>
    </applicationVisibilities>
</PermissionSet>
```

How to read it:

- **`license` narrows who can hold the set.** The Object Reference's guidance on `PermissionSet.LicenseId`: "If you plan to assign a permission set to multiple users with different user and permission set licenses, leave `LicenseId` empty." Populating `license` with `Salesforce` here is a deliberate statement that no Platform-licensed user is in this persona. `userLicense` is the deprecated predecessor and is only available up to API 37.0.
- **`userPermissions` retrieves only what is enabled** (API 29.0+), and in API 40.0 and later a permission that is *not* listed in a deployment is disabled. A partial file is therefore a revocation, not a no-op.
- **Some system permissions drag object permissions with them.** The Object Reference calls this out for `TransferAnyLead`: a permission set holding it also has read and create on Lead. Audit queries over `ObjectPermissions` will show rows nobody wrote by hand. UNVERIFIED (2026-09-04): the API name `TransferAnyCase` used above does not appear in the extracted Metadata API or Object Reference text — the guide's worked permission-dependency example is `TransferAnyLead`. Confirm the exact name with `describeSObjects()` on `PermissionSet` (the guide's documented way to list available permission names) before deploying.
- **`classAccesses` grants the top-level class only** — methods in inner classes are covered by the top-level grant, not by separate entries.
- **`flowAccesses`** (API 47.0+) defaults to `false`; screen flows launched from a persona need an explicit entry. `customMetadataTypeAccesses` and `customSettingAccesses` (both 47.0+) follow the same `name` / `enabled` shape and grant read only.

---

## 3. Persona group plus its muting set

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MutingPermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Mute T1 Refund Approval</label>
    <description>Tier 1 must not approve refunds. Owner: Service Ops. Reviewed 2026-09-04.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <customPermissions>
        <enabled>true</enabled>
        <name>Escalate_Premium_Case</name>
    </customPermissions>
    <fieldPermissions>
        <editable>true</editable>
        <field>Case.Refund_Amount__c</field>
        <readable>false</readable>
    </fieldPermissions>
</MutingPermissionSet>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSetGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Persona_Service_Agent_T1</fullName>
    <label>Persona Service Agent T1</label>
    <description>Tier 1 service agent. Owner: Service Ops.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <permissionSets>Obj_Case_Agent</permissionSets>
    <permissionSets>Feat_Case_Escalation</permissionSets>
    <mutingPermissionSets>Mute_T1_Refund_Approval</mutingPermissionSets>
</PermissionSetGroup>
```

How to read it:

- **The group holds no permissions of its own.** The Metadata API guide is explicit: individual permissions are included in the referenced permission set, not in the group. A PSG file is a membership list plus a label.
- **A muting set reads inverted.** `MutingPermissionSet` has the same fields as `PermissionSet` plus `label`, but "settings enabled by MutingPermissionSet are turned off for the permission set group that it's a component of". The `customPermissions` entry above with `enabled` true *removes* `Escalate_Premium_Case` from this group. This is why muting files look like grants and must be read with the type name in mind.
- **`mutingPermissionSets` is API 46.0+ and `permissionSets` takes one element per member.** Both reference the member's API name, so every member must exist in the org or in the same deploy.
- **`hasActivationRequired` on the group** is API 53.0+. Do not confuse it with the same field on a member set: a session-based *member* stops requiring activation once it is in a group.

---

## 4. Assigning the group

`PermissionSetAssignment` carries either `PermissionSetId` or `PermissionSetGroupId` (API 45.0+), and `ExpirationDate` (API 52.0+) for time-boxed access.

```apex
PermissionSetGroup psg = [
    SELECT Id FROM PermissionSetGroup WHERE DeveloperName = 'Persona_Service_Agent_T1'
];

List<PermissionSetAssignment> toAssign = new List<PermissionSetAssignment>();
for (User u : [SELECT Id FROM User WHERE Profile.Name = 'Minimum Access - Salesforce' AND IsActive = true]) {
    toAssign.add(new PermissionSetAssignment(
        AssigneeId = u.Id,
        PermissionSetGroupId = psg.Id
    ));
}
insert toAssign;
```

For a time-limited elevation, populate `ExpirationDate` on the same object (design guidance in `admin/permission-set-expiration`):

```apex
insert new PermissionSetAssignment(
    AssigneeId = contractorId,
    PermissionSetId = tempSetId,
    ExpirationDate = System.now().addDays(30)
);
```

Via Data Loader, insert into `PermissionSetAssignment` with columns `AssigneeId`, `PermissionSetGroupId` (or `PermissionSetId`), and optionally `ExpirationDate`. There is no upsert key; re-running a load creates duplicate-assignment errors rather than updates.

---

## 5. package.xml and CLI

When you retrieve permission sets, retrieve the related components too. The Metadata API guide: "when retrieving object or field permissions, you must also retrieve the associated object", and for groups, "to retrieve PermissionSetGroup, you must also retrieve PermissionSet."

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Case.Support</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>Escalate_Premium_Case</members>
        <name>CustomPermission</name>
    </types>
    <types>
        <members>Obj_Case_Agent</members>
        <members>Feat_Case_Escalation</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>Mute_T1_Refund_Approval</members>
        <name>MutingPermissionSet</name>
    </types>
    <types>
        <members>Persona_Service_Agent_T1</members>
        <name>PermissionSetGroup</name>
    </types>
    <version>62.0</version>
</Package>
```

```bash
# Retrieve the whole tree, not just the sets — a partial retrieve produces a partial file.
sf project retrieve start --manifest manifest/package.xml --target-org my-sandbox

python3 skills/admin/permission-set-architecture/scripts/check_permission_set_architecture.py \
    --manifest-dir force-app/main/default

# Sets first, then groups and muting sets, so the group's members already exist.
sf project deploy start --source-dir force-app/main/default/permissionsets --target-org my-sandbox
sf project deploy start \
    --source-dir force-app/main/default/mutingpermissionsets \
    --source-dir force-app/main/default/permissionsetgroups \
    --target-org my-sandbox
```

---

## 6. Verify after deploy

Recalculation is asynchronous — check the status before testing access, and treat `Failed` as a deploy failure even though the deploy result was a success.

```sql
SELECT DeveloperName, Status FROM PermissionSetGroup WHERE DeveloperName = 'Persona_Service_Agent_T1'
```

`Status` is a restricted picklist: `Updated` (current), `Outdated` (needs recalculation), `Updating` (recalculating), `Failed`.

Who holds the persona, and until when:

```sql
SELECT Assignee.Username, PermissionSet.Name, PermissionSetGroup.DeveloperName, ExpirationDate
FROM PermissionSetAssignment
WHERE Assignee.Username = 'agent@acme.example.com'
```

What one set actually grants at the object level:

```sql
SELECT SobjectType, PermissionsRead, PermissionsCreate, PermissionsEdit, PermissionsDelete,
       PermissionsViewAllRecords, PermissionsModifyAllRecords
FROM ObjectPermissions
WHERE Parent.Name = 'Obj_Case_Agent'
```

Everything the group aggregates, member sets included — the Object Reference gives this pattern for PSGs:

```sql
SELECT SObjectType FROM ObjectPermissions
WHERE Parent.PermissionSetGroup.DeveloperName = 'Persona_Service_Agent_T1'
```

Sharing-bypass sweep across the org, excluding the profile-backed sets:

```sql
SELECT Parent.Name, SobjectType, PermissionsModifyAllRecords, PermissionsViewAllRecords
FROM ObjectPermissions
WHERE (PermissionsModifyAllRecords = true OR PermissionsViewAllRecords = true)
  AND Parent.IsOwnedByProfile = false
```

Note the limits of these queries: absence of an `ObjectPermissions` row means no access, so you cannot filter on `PermissionsRead = false` to find sets without access — the query returns nothing. And a set holding `Modify All Data` shows object rows whose Id begins with `000`, because that user permission grants full object access without storing real permission records.

---

## 7. Description length

`PermissionSet.description` and `Profile.description` are both capped at 255 characters — the Metadata API Developer Guide: "The permission set description. Limit: 255 characters" (`api_meta` L94788) and "The profile description. Limit: 255 characters" (`api_meta` L97678). `MutingPermissionSet` has the same fields as `PermissionSet`, so the same ceiling applies to its `description` too.

`PermissionSetGroup.description` carries no stated limit in the guide (`api_meta` L95328 — "The permission set group description provided by the permission set group creator", no `Limit:` clause). Treat it as 255 anyway — **UNVERIFIED (2026-09-11)**: no dry run has directly rejected an over-length PSG description, but `sf project deploy start --dry-run` against a Summer '26 developer org on 2026-09-11 rejected four over-length `PermissionSet` files, and the three `PermissionSetGroup` files that referenced them then failed as a cascade with `permission set names are invalid` (`examples/builds/case-onboarding/reports/MOCK-DEPLOY-M2.md`, once exported) — a PSG cannot deploy once a member set it depends on is rejected, regardless of the group's own description length.

**Where rationale goes instead.** A 300–450 character justification — who owns a set, why it exists, what it composes into, which open question it resolves — does not fit in `description` and should never be squeezed into it. Write that in the build's `deploy-order.md` or the configuration workbook, next to the component it explains, and keep `description` to what a Setup user reads at a glance: capability and owner, one line.

`scripts/check_permission_set_architecture.py` enforces this: `PSA-DESC-01` (ERROR) at 255+ characters on any `PermissionSet`, `MutingPermissionSet`, `PermissionSetGroup`, or `Profile` file; `PSA-DESC-02` (INFO) at 200+ characters as headroom — printed and counted, never affects the exit code.
