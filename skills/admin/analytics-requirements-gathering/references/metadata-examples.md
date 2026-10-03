# Metadata Examples: Analytics Requirements Gathering

This file turns the audience matrix from `examples.md` Example 3 into the metadata a developer deploys, so the requirement and its configuration can be reviewed side by side.

Grounding: Metadata API Developer Guide, WaveApplication (`api_meta L138608-138650`), FolderShare access levels and shared-to types (`api_meta L74693-74745`), WaveRecipe `securityPredicate` (`api_meta L138986-139040`); Analytics Security Implementation Guide, predicates and sharing inheritance (`bi_admin_guide_security L253-301`); Analytics Platform Setup Guide, Security User and custom User fields (`bi_admin_guide_setup L98-104`).

## Audience matrix to configuration

| Requirement row | App access (WaveApplication share) | Row access (dataset predicate) |
|---|---|---|
| Finance analysts edit dashboards in their region | `EditAllContents` to group `Finance_Analysts` | `'Region__c' == "$User.Sales_Region__c"` |
| Regional sales managers view their region | `View` to role and subordinates `Regional_Sales_Manager` | same predicate |
| Analytics admins manage the app | `Manage` to group `Analytics_Admins` | not row-restricted by this predicate; decide explicitly |

App sharing and row-level security are separate layers. A share without a predicate shows every row to everyone who can open the app (gotcha 3).

## 1. App sharing

`force-app/main/default/wave/Finance_Analytics.wapp-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<WaveApplication xmlns="http://soap.sforce.com/2006/04/metadata">
    <assetIcon>/analytics/wave/web/proto/images/app/icons/11.png</assetIcon>
    <description>Revenue by region joined with billing data</description>
    <folder>Finance_Analytics</folder>
    <masterLabel>Finance Analytics</masterLabel>
    <shares>
        <accessLevel>EditAllContents</accessLevel>
        <sharedTo>Finance_Analysts</sharedTo>
        <sharedToType>Group</sharedToType>
    </shares>
    <shares>
        <accessLevel>View</accessLevel>
        <sharedTo>Regional_Sales_Manager</sharedTo>
        <sharedToType>RoleAndSubordinatesInternal</sharedToType>
    </shares>
    <shares>
        <accessLevel>Manage</accessLevel>
        <sharedTo>Analytics_Admins</sharedTo>
        <sharedToType>Group</sharedToType>
    </shares>
</WaveApplication>
```

| Element | Allowed values used here | Source |
|---|---|---|
| `accessLevel` | `View`, `EditAllContents`, `Manage` | FolderShare |
| `sharedToType` | `Group`, `RoleAndSubordinatesInternal` (also `Role`, `RoleAndSubordinates`, `Manager`, and others) | FolderShare |
| `sharedTo` | Developer name of the group or role | FolderShare |

UNVERIFIED (2026-10-03): FolderShare is documented for report and dashboard folders and is reused by `WaveApplication.shares`; confirm that every `sharedToType` value is accepted for Analytics apps in your org with a sandbox deploy.

## 2. Row-level security on the recipe that creates the dataset

`force-app/main/default/wave/Finance_Revenue.wdpr-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<WaveRecipe xmlns="http://soap.sforce.com/2006/04/metadata">
    <application>Finance_Analytics</application>
    <dataflow>02KB0000000c7d1MAA</dataflow>
    <format>R3</format>
    <masterLabel>Finance Revenue</masterLabel>
    <securityPredicate>'Region__c' == "$User.Sales_Region__c"</securityPredicate>
    <targetDatasetAlias>Finance_Revenue</targetDatasetAlias>
</WaveRecipe>
```

The predicate here applies when the dataset is first created. After that, change the predicate on the dataset, not in the recipe (`bi_admin_guide_security L274-275`). The `dataflow` value is an org-specific ID: retrieve it from the source org rather than typing it. Recipe design detail belongs to `admin/analytics-recipe-design`.

## 3. Let the Security User read the custom User field

The predicate references `User.Sales_Region__c`, a custom field, so the Security User needs read access to it (`bi_admin_guide_setup L98-104`). This is a numbered Setup procedure because the Security User is an internal user, not a deployable permission set target.

1. Setup, then Object Manager, then User, then Fields & Relationships, then Sales Region.
2. Set Field Accessibility (or Field-Level Security) and grant Read to the profile assigned to the Analytics Cloud Security User.
3. Save, then query the dataset as a regional manager and confirm no predicate error appears.

UNVERIFIED (2026-10-03): the exact name of the Security User's profile in Setup is not stated in the setup guide; locate it from the Analytics Cloud Security User record.

## 4. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Finance_Analytics</members>
        <name>WaveApplication</name>
    </types>
    <types>
        <members>Finance_Revenue</members>
        <name>WaveDataflow</name>
    </types>
    <types>
        <members>Finance_Revenue</members>
        <name>WaveRecipe</name>
    </types>
    <version>67.0</version>
</Package>
```

## Deploy order

1. Public groups `Finance_Analysts` and `Analytics_Admins` and the role `Regional_Sales_Manager` must already exist in the target org (deploy them separately if they do not).
2. `User.Sales_Region__c` field and its access for the Security User.
3. `WaveApplication`.
4. `WaveDataflow` and `WaveRecipe` together, then the first run so the dataset is created with its predicate.

## Verification

- A finance analyst in region West sees only West rows; a CFO account outside every predicate branch sees none until a decision is made for that role.
- Queries return no Security User field-access error.
- The dataset's security settings in Data Manager show the predicate from the recipe.
