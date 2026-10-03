# Metadata Examples: Clinical Data Requirements

The deployable prerequisite for every clinical data requirement: the org pref that switches on the FHIR-aligned clinical objects, plus a permission set that lets an integration user write them.

Grounding: Metadata API Developer Guide, IndustriesSettings (`api_meta L119169-119200` type definition, Health Cloud fields `L119538-119645`, `enableClinicalDataModel` `L119553-119555`, sample manifest `L120228-120240`) and PermissionSet object permissions; Health Cloud developer guide, org pref object list (`health_cloud_dev_guide L8345-8403`).

Licence gate: "Settings are specific to an industry vertical and are only available to customers with org editions where the vertical is enabled." The clinical data model is documented for Enterprise and Unlimited Editions.

## 1. Turn on the clinical data model

`force-app/main/default/settings/Industries.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<IndustriesSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableClinicalDataModel>true</enableClinicalDataModel>
</IndustriesSettings>
```

`enableClinicalDataModel` "indicates whether Clinical Data Model is enabled for your org", defaults to `false`, and is available from API 51.0. UNVERIFIED (2026-10-03): that this field is the same switch as the "FHIR-Aligned Clinical Data Model" org pref on the FHIR R4 Support Settings page is inferred from the description; confirm in Setup after deploying. Retrieve `Settings:Industries` first and merge, because the settings file holds every Industries setting and a deploy overwrites the fields it contains.

## 2. Integration user access to the clinical objects

`force-app/main/default/permissionsets/Clinical_Data_Integration.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Lets the clinical integration user create and update FHIR-aligned clinical records</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Clinical Data Integration</label>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>CodeSet</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>CodeSetBundle</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>HealthCondition</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
</PermissionSet>
```

Delete is off on purpose: clinical history should be corrected, not removed. UNVERIFIED (2026-10-03): the Health Cloud permission set license the integration user needs before this permission set can grant clinical object access is not named in the clinical data model chapter; assign the org's Health Cloud permission set license first, or the deploy or assignment fails.

## 3. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Clinical_Data_Integration</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>Industries</members>
        <name>Settings</name>
    </types>
    <version>67.0</version>
</Package>
```

## Deploy order

1. `Settings: Industries` (objects such as `HealthCondition` do not exist until the pref is on, so the permission set would fail first).
2. `PermissionSet`.
3. Assign the Health Cloud permission set license, then the permission set, to the integration user.

## Verification

- `SELECT Id FROM HealthCondition LIMIT 1` returns zero rows instead of an unknown-object error.
- A describe of `Contact` shows `Gender` and `DeceasedDate`, two of the fields the org pref adds.
- The integration user can insert a `CodeSet`, a `CodeSetBundle` referencing it in `CodeSet1Id`, and a `HealthCondition` referencing the bundle in `ConditionCodeId`.
