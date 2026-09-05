# Metadata Examples — Custom Settings (and the CMT Contrast)

Deployable shapes for the **Custom Settings** half of this skill. The deep CustomMetadata / `__mdt` reference lives in `skills/admin/custom-metadata-types/references/metadata-examples.md` — this file shows one CMT block only as a contrast and does not repeat it.

Element names and enum values come from the Metadata API Developer Guide (v62 PDF), `CustomObject` section: `customSettingsType` (api_meta.txt:41967–41976), `customSettingsVisibility` (api_meta.txt:41977–41988), `visibility` (api_meta.txt:42277–42298). The worked example extends those field tables into a realistic per-profile alert configuration.

Validate what you produce with:

```bash
python3 skills/admin/custom-metadata-types-and-settings/scripts/check_custom_metadata_types_and_settings.py --manifest-dir force-app/main/default
```

## Where the files live

| Component | package.xml `<name>` | File in a DX project | Deploys? |
|---|---|---|---|
| The setting definition | `CustomObject`, member `Alert_Config__c` | `objects/Alert_Config__c/Alert_Config__c.object-meta.xml` | Yes |
| A field on the setting | `CustomField`, member `Alert_Config__c.Alert_Threshold__c` | `objects/Alert_Config__c/fields/Alert_Threshold__c.field-meta.xml` | Yes |
| Read access for non-admins | `PermissionSet`, member `Alert_Config_Reader` | `permissionsets/Alert_Config_Reader.permissionset-meta.xml` | Yes |
| Org-wide security switches | `Settings`, member `Schema` | `settings/Schema.settings-meta.xml` | Yes |
| **The records** (org default, profile rows, user rows) | — | — | **No — see "Data does not travel"** |

A custom setting is a `CustomObject` with a `__c` suffix, stored under `objects/` exactly like a normal custom object. The `customSettingsType` element is what turns it into a setting: "When this field is present, this component isn't a custom object, but a custom setting" (api_meta.txt:41967–41969).

## How to read the example

- **`customSettingsType` has exactly two values**: `List` — "static data stored in cache, accessed as part of your application, and available org-wide"; `Hierarchy` — "static data stored in cache, accessed as part of your application, and available based on a hierarchy of user, profile, or org. **This value is the default**" (api_meta.txt:41970–41976). Omitting the element on a setting therefore yields Hierarchy, not an error.
- **Write `visibility`, never `customSettingsVisibility`.** `customSettingsVisibility` "is available in API versions 17.0 through 33.0. In versions 34.0 and later, use the `visibility` field instead" (api_meta.txt:41986–41988).
- **`visibility` defaults to `Public`** and takes `Public` / `Protected` / `PackageProtected`, where `PackageProtected` is custom-metadata-type only (api_meta.txt:42279–42295). For a custom setting the practical choice is `Public` or `Protected`.
- **`Protected` only means something inside a managed package.** "Protection only applies to custom settings that are marked protected and installed to a subscriber organization as part of a managed package. Otherwise, they are treated as public custom settings and are readable for all profiles, including the guest user" (apexdev.txt:13508–13513).
- **Field XML is ordinary `CustomField` XML.** Geolocation is the one type the Object Reference rules out: "Geolocation fields aren't supported in custom settings" (object_reference.txt:2953).
- **Non-admin read access is a permission-set component.** `PermissionSetCustomSettingAccesses` — `enabled` "indicates whether the records for this custom setting are readable" — is available in API version 47.0 and later (api_meta.txt:94956–94964); the profile equivalent is `ProfileCustomSettingAccesses` (api_meta.txt:97974–97989).

## The setting: `Alert_Config__c` (Hierarchy)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <customSettingsType>Hierarchy</customSettingsType>
    <description>Case alert thresholds. Org default is the baseline; Profile and User rows override it. Records are org data and are created by the post-deploy script, not by this deployment.</description>
    <enableFeeds>false</enableFeeds>
    <label>Alert Config</label>
    <visibility>Protected</visibility>
</CustomObject>
```

The List variant differs in one element only, and changes which Apex methods are legal against it:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <customSettingsType>List</customSettingsType>
    <description>ISO country codes keyed by data set name. Org-wide; no per-user variation.</description>
    <enableFeeds>false</enableFeeds>
    <label>Foundation Countries</label>
    <visibility>Public</visibility>
</CustomObject>
```

## Field 1 — Number

`objects/Alert_Config__c/fields/Alert_Threshold__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Alert_Threshold__c</fullName>
    <externalId>false</externalId>
    <label>Alert Threshold</label>
    <precision>3</precision>
    <required>false</required>
    <scale>0</scale>
    <trackTrending>false</trackTrending>
    <type>Number</type>
    <unique>false</unique>
</CustomField>
```

Leave `required` false. A required field on a hierarchy setting forces every level you insert to carry a value, which defeats the merge behaviour described in `references/gotchas.md`.

## Field 2 — Checkbox

`objects/Alert_Config__c/fields/Suppress_Alerts__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Suppress_Alerts__c</fullName>
    <defaultValue>false</defaultValue>
    <externalId>false</externalId>
    <label>Suppress Alerts</label>
    <trackTrending>false</trackTrending>
    <type>Checkbox</type>
</CustomField>
```

## Read access for everyone who is not an admin

`permissionsets/Alert_Config_Reader.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Alert Config Reader</label>
    <customSettingAccesses>
        <enabled>true</enabled>
        <name>Alert_Config__c</name>
    </customSettingAccesses>
    <hasActivationRequired>false</hasActivationRequired>
</PermissionSet>
```

## Org-wide security switches you inherit by default

`settings/Schema.settings-meta.xml` — every field below "has a default value of false" (api_meta.txt:125511–125523), so an org that has never touched this file exposes custom setting values through the Enterprise WSDL and SOAP API to anyone who can read the object.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SchemaSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableAdvancedCMTSecurity>true</enableAdvancedCMTSecurity>
    <enableAdvancedCSSecurity>true</enableAdvancedCSSecurity>
    <enableListCustomSettingCreation>false</enableListCustomSettingCreation>
    <enableSOSLOnCustomSettings>false</enableSOSLOnCustomSettings>
</SchemaSettings>
```

Deploy this file only when you have decided each switch. `enableAdvancedCSSecurity` set to `true` restricts custom settings values to "Apex, flow, and formula operations" and cuts off SOAP API and WSDL readers — which is what you want for a `Protected` setting and what will break an integration that was quietly reading the values.

## The CMT contrast — one block, then go elsewhere

A Custom Metadata **record** is a separate component type in its own folder, and unlike a custom setting record it deploys:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <label>EMEA High</label>
    <protected>false</protected>
    <values>
        <field>Threshold__c</field>
        <value xsi:type="xsd:double">75.0</value>
    </values>
</CustomMetadata>
```

That is the whole of the CMT story in this file. For `xsi:type` mapping, `xsi:nil` clearing, `fieldManageability`, record-level `protected`, `MetadataRelationship`, and the 255-character truncation rule, read `skills/admin/custom-metadata-types/references/metadata-examples.md` — do not reconstruct them here.

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Alert_Config__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Alert_Config__c.Alert_Threshold__c</members>
        <members>Alert_Config__c.Suppress_Alerts__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Alert_Config_Reader</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>Schema</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

There is no `<name>` you can add to this manifest that carries the org default, the profile rows, or the user rows.

## Data does not travel

- **Packages:** "Only custom settings definitions are included in packages, not data. To include data, you must populate the custom settings using Apex code run by the subscribing organization after they've installed the package" (apexdev.txt:13561–13562).
- **Sandbox copies:** "custom settings data is included in sandbox copies" (apexdev.txt:13514) — so a refreshed full or partial sandbox does have the rows, and a brand-new scratch org does not.
- **Change sets:** UNVERIFIED (2026-09-05): the extracted Metadata API and Apex guides state the packaging rule above but do not make an equivalent statement about change sets. Treat the packaging rule as the safe assumption and verify in your own release before relying on it.

## Retrieve and deploy

```bash
# Retrieve an existing setting and the org's schema switches before editing either
sf project retrieve start \
  -m "CustomObject:Alert_Config__c" \
  -m "Settings:Schema" \
  -o my-sandbox

# Validate before you deploy
sf project deploy start -x manifest/package.xml -o my-sandbox --dry-run

# Deploy definition + fields + permission set
sf project deploy start -x manifest/package.xml -o my-sandbox
```

## Seed the records — the step the deployment cannot do

`scripts/apex/seed_alert_config.apex`, run with `sf apex run -f scripts/apex/seed_alert_config.apex` after every deploy to a new org:

```apex
// Org default: getOrgDefaults() returns an empty object (not null) when no row exists,
// so upsert is safe on a first run and idempotent afterwards.
Alert_Config__c orgDefault = Alert_Config__c.getOrgDefaults();
orgDefault.SetupOwnerId = UserInfo.getOrganizationId();
orgDefault.Alert_Threshold__c = 20;
orgDefault.Suppress_Alerts__c = false;
upsert orgDefault;

// Profile override, keyed by SetupOwnerId = the Profile Id
Profile salesRep = [SELECT Id FROM Profile WHERE Name = 'Sales Rep' LIMIT 1];
Alert_Config__c profileRow = Alert_Config__c.getValues(salesRep.Id);
if (profileRow == null) {
    profileRow = new Alert_Config__c(SetupOwnerId = salesRep.Id);
}
profileRow.Alert_Threshold__c = 5;
upsert profileRow;
```

`getValues(profileId)` is used deliberately here rather than `getInstance(profileId)`: it returns only the row defined at that level, so a null result proves the row is genuinely absent instead of handing back merged org-default values.

## Test-data pattern

Custom settings data "is treated as data for the purposes of Apex test isolation. Apex tests must use `SeeAllData=true` to see existing custom settings data in the organization. As a best practice, create the required custom settings data in your test setup" (apexdev.txt:13514–13516).

```apex
@IsTest
private class AlertConfigTest {
    // Insert once here. In API 42.0 and later, inserting a hierarchy custom setting
    // with the same SetupOwnerId again inside a test method throws DUPLICATE_VALUE.
    @TestSetup
    static void seed() {
        insert new Alert_Config__c(
            SetupOwnerId = UserInfo.getOrganizationId(),
            Alert_Threshold__c = 20
        );
    }

    @IsTest
    static void orgDefaultAppliesWhenNoUserRow() {
        Test.startTest();
        Alert_Config__c resolved = Alert_Config__c.getInstance();
        Test.stopTest();
        Assert.areEqual(20, (Integer) resolved.Alert_Threshold__c);
    }

    @IsTest
    static void userRowOverridesOrgDefault() {
        // A different SetupOwnerId, so no DUPLICATE_VALUE against @TestSetup
        insert new Alert_Config__c(
            SetupOwnerId = UserInfo.getUserId(),
            Alert_Threshold__c = 1
        );
        Alert_Config__c resolved = Alert_Config__c.getInstance();
        Assert.areEqual(1, (Integer) resolved.Alert_Threshold__c);
    }
}
```

## Verify

After the deploy and the seed script, confirm the rows exist and sit at the levels you intended. A direct SOQL query is correct here — this is a verification step, not runtime code, and the guide is explicit that SOQL against a custom setting bypasses the cache and behaves like a custom object query (apexrefguide.txt:204705–204709):

```sql
SELECT SetupOwnerId, SetupOwner.Name, SetupOwner.Type, Alert_Threshold__c, Suppress_Alerts__c
FROM Alert_Config__c
ORDER BY SetupOwner.Type
```

Expect exactly one row whose `SetupOwner.Type` is `Organization`. Then confirm the merge, in `sf apex run`:

```apex
System.debug(Alert_Config__c.getOrgDefaults().Alert_Threshold__c); // the baseline
System.debug(Alert_Config__c.getInstance().Alert_Threshold__c);    // what the running user gets
```

In Setup, the same check is **Custom Settings → Alert Config → Manage**, which lists the Default Organization Level Value plus every profile and user row.
