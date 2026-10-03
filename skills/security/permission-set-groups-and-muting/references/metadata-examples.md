# Metadata Examples: Permission Set Groups And Muting

A deployable "base bundle plus muting" design for two service personas. Senior agents get the full case bundle. Junior agents get the same permission sets through a second group whose muting permission set removes Case delete and edit on `Case.Priority`. Element names come from the Metadata API Developer Guide (Summer '26) samples for PermissionSet, PermissionSetGroup, and MutingPermissionSet. Paths are Salesforce DX source format.

## 1. The shared permission set

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/permissionsets/Case_Agent_Base.permissionset-meta.xml -->
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Case handling for all service agents. Owner: Service Ops.</description>
    <fieldPermissions>
        <editable>true</editable>
        <field>Case.Priority</field>
        <readable>true</readable>
    </fieldPermissions>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Case Agent Base</label>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>true</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Case</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
</PermissionSet>
```

This file is the complete definition of the permission set. Since API 40.0 a deployed permission set replaces its contents, so never deploy a trimmed copy.

## 2. Two groups over the same permission set

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/permissionsetgroups/Case_Agent_Senior.permissionsetgroup-meta.xml -->
<PermissionSetGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Senior service agents: full case bundle.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Case Agent Senior</label>
    <permissionSets>Case_Agent_Base</permissionSets>
</PermissionSetGroup>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/permissionsetgroups/Case_Agent_Junior.permissionsetgroup-meta.xml -->
<PermissionSetGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Junior service agents: case bundle without delete and without Priority edit.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Case Agent Junior</label>
    <mutingPermissionSets>Case_Agent_Junior_Muted</mutingPermissionSets>
    <permissionSets>Case_Agent_Base</permissionSets>
</PermissionSetGroup>
```

## 3. The muting permission set (enabled = muted)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/mutingpermissionsets/Case_Agent_Junior_Muted.mutingpermissionset-meta.xml -->
<MutingPermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Mutes Case delete and Case.Priority edit for the Case Agent Junior group.</description>
    <fieldPermissions>
        <editable>true</editable>
        <field>Case.Priority</field>
        <readable>false</readable>
    </fieldPermissions>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Case Agent Junior Muted</label>
    <objectPermissions>
        <allowCreate>false</allowCreate>
        <allowDelete>true</allowDelete>
        <allowEdit>false</allowEdit>
        <allowRead>false</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Case</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
</MutingPermissionSet>
```

`allowDelete=true` mutes delete. `editable=true` with `readable=false` mutes edit and keeps read on `Case.Priority`. Every `false` leaves the group's grant untouched.

## 4. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/case-agent-bundle.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case_Agent_Base</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>Case_Agent_Senior</members>
        <members>Case_Agent_Junior</members>
        <name>PermissionSetGroup</name>
    </types>
    <types>
        <members>Case_Agent_Junior_Muted</members>
        <name>MutingPermissionSet</name>
    </types>
    <version>67.0</version>
</Package>
```

## 5. Verification queries

```soql
-- Recalculation must reach Updated before testing
SELECT DeveloperName, Status FROM PermissionSetGroup WHERE DeveloperName IN ('Case_Agent_Senior', 'Case_Agent_Junior')

-- Every grant path for Case delete for one user (profile, permission sets, and group aggregates)
SELECT Parent.Name, Parent.Type, Parent.IsOwnedByProfile, Parent.PermissionSetGroup.DeveloperName, PermissionsDelete
FROM ObjectPermissions
WHERE SobjectType = 'Case' AND PermissionsDelete = true
  AND ParentId IN (SELECT PermissionSetId FROM PermissionSetAssignment WHERE AssigneeId = '005XXXXXXXXXXXXXXX')

-- Object permissions aggregated into a group (pattern from the Object Reference)
SELECT SObjectType, PermissionsDelete FROM ObjectPermissions WHERE Parent.PermissionSetGroup.DeveloperName = 'Case_Agent_Junior'
```

The fields `PermissionSet.IsOwnedByProfile`, `PermissionSet.PermissionSetGroupId`, and `PermissionSet.Type` are in the Object Reference. UNVERIFIED (2026-10-03): the second query assumes the profile-owned permission set and each group's aggregate permission set appear as `PermissionSetAssignment` rows for the user; check the result against Setup > User > View Summary before relying on it.

## 6. Deploy order and verification

```bash
sf project deploy start --manifest manifest/case-agent-bundle.xml --target-org uat --wait 30
python3 skills/security/permission-set-groups-and-muting/scripts/check_permission_set_groups_and_muting.py --manifest-dir force-app
```

| Order | Step | Verify |
|---|---|---|
| 1 | Deploy permission set, groups, and muting set together | Deploy succeeded |
| 2 | Wait for recalculation | Both groups show `Status = Updated` |
| 3 | Log in as a junior test user | Case Delete hidden; Priority read-only |
| 4 | Check other grant paths | The query in section 5 shows no profile or direct grant of Case delete |
