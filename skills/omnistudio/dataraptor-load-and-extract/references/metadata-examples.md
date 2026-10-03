# Metadata Examples: DataRaptor Load and Extract

Deployable `OmniDataTransform` components for the two examples in [examples.md](examples.md). Field names come from the `OmniDataTransform` and `OmniDataTransformItem` reference and sample in the Industries Common Resources Developer Guide (Summer '26). The source-format folder and suffix (`omniDataTransforms/`, `.rpt-meta.xml`) come from the Salesforce CLI metadata registry (source-deploy-retrieve 12.22.6).

Prerequisites: an Omnistudio license, and Omnistudio metadata enabled (`OmniStudioSettings.enableOmniStudioMetadata`, which can't be turned off once on).

## 1. Extract: Account with Contacts

The first item of each step defines the extract object, its filter, and its Extract Output Path. The remaining items map extract paths (`Account:Name`) to output fields. This mirrors the `COODMtest` sample in the guide.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/omniDataTransforms/AccountContactsExtract_1.rpt-meta.xml -->
<OmniDataTransform xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <assignmentRulesUsed>false</assignmentRulesUsed>
    <deletedOnSuccess>false</deletedOnSuccess>
    <description>Account plus Contacts for the Edit Account OmniScript</description>
    <errorIgnored>false</errorIgnored>
    <fieldLevelSecurityEnabled>true</fieldLevelSecurityEnabled>
    <inputType>JSON</inputType>
    <isManagedUsingStdDesigner>false</isManagedUsingStdDesigner>
    <name>AccountContactsExtract</name>
    <nullInputsIncludedInOutput>false</nullInputsIncludedInOutput>
    <omniDataTransformItem>
        <disabled>false</disabled>
        <filterGroup>0.0</filterGroup>
        <filterOperator>=</filterOperator>
        <filterValue>AccountId</filterValue>
        <globalKey>6f1c2a10-1a2b-4c3d-8e9f-000000000001</globalKey>
        <inputFieldName>Id</inputFieldName>
        <inputObjectName>Account</inputObjectName>
        <inputObjectQuerySequence>1.0</inputObjectQuerySequence>
        <linkedObjectSequence>0.0</linkedObjectSequence>
        <name>AccountContactsExtract</name>
        <outputCreationSequence>0.0</outputCreationSequence>
        <outputFieldName>Account</outputFieldName>
        <outputObjectName>json</outputObjectName>
        <requiredForUpsert>false</requiredForUpsert>
        <upsertKey>false</upsertKey>
    </omniDataTransformItem>
    <omniDataTransformItem>
        <disabled>false</disabled>
        <filterGroup>0.0</filterGroup>
        <filterOperator>=</filterOperator>
        <filterValue>Account:Id</filterValue>
        <globalKey>6f1c2a10-1a2b-4c3d-8e9f-000000000002</globalKey>
        <inputFieldName>AccountId</inputFieldName>
        <inputObjectName>Contact</inputObjectName>
        <inputObjectQuerySequence>2.0</inputObjectQuerySequence>
        <linkedObjectSequence>0.0</linkedObjectSequence>
        <name>AccountContactsExtract</name>
        <outputCreationSequence>0.0</outputCreationSequence>
        <outputFieldName>Contact</outputFieldName>
        <outputObjectName>json</outputObjectName>
        <requiredForUpsert>false</requiredForUpsert>
        <upsertKey>false</upsertKey>
    </omniDataTransformItem>
    <omniDataTransformItem>
        <disabled>false</disabled>
        <filterGroup>0.0</filterGroup>
        <globalKey>6f1c2a10-1a2b-4c3d-8e9f-000000000003</globalKey>
        <inputFieldName>Account:Name</inputFieldName>
        <inputObjectQuerySequence>0.0</inputObjectQuerySequence>
        <linkedObjectSequence>0.0</linkedObjectSequence>
        <name>AccountContactsExtract</name>
        <outputCreationSequence>1.0</outputCreationSequence>
        <outputFieldName>Account:Name</outputFieldName>
        <outputObjectName>json</outputObjectName>
        <requiredForUpsert>false</requiredForUpsert>
        <transformValuesMappings>{ }</transformValuesMappings>
        <upsertKey>false</upsertKey>
    </omniDataTransformItem>
    <omniDataTransformItem>
        <disabled>false</disabled>
        <filterGroup>0.0</filterGroup>
        <globalKey>6f1c2a10-1a2b-4c3d-8e9f-000000000004</globalKey>
        <inputFieldName>Contact:LastName</inputFieldName>
        <inputObjectQuerySequence>0.0</inputObjectQuerySequence>
        <linkedObjectSequence>0.0</linkedObjectSequence>
        <name>AccountContactsExtract</name>
        <outputCreationSequence>1.0</outputCreationSequence>
        <outputFieldName>Account:Contacts:LastName</outputFieldName>
        <outputObjectName>json</outputObjectName>
        <requiredForUpsert>false</requiredForUpsert>
        <transformValuesMappings>{ }</transformValuesMappings>
        <upsertKey>false</upsertKey>
    </omniDataTransformItem>
    <outputType>JSON</outputType>
    <processSuperBulk>false</processSuperBulk>
    <responseCacheTtlMinutes>5.0</responseCacheTtlMinutes>
    <responseCacheType>session</responseCacheType>
    <rollbackOnError>false</rollbackOnError>
    <sourceObjectDefault>false</sourceObjectDefault>
    <synchronousProcessThreshold>0.0</synchronousProcessThreshold>
    <type>Extract</type>
    <uniqueName>AccountContactsExtract_1</uniqueName>
    <versionNumber>1.0</versionNumber>
    <xmlDeclarationRemoved>false</xmlDeclarationRemoved>
</OmniDataTransform>
```

UNVERIFIED (2026-10-03): the guide's sample shows a quoted literal filter (`''`) and `Account:Type`-style input paths. The input-parameter filter value (`AccountId`), the cross-step filter value (`Account:Id`), the nested output path `Account:Contacts:LastName`, and the `session` spelling of `responseCacheType` follow the same conventions but are not shown verbatim. Build the Data Mapper in the designer once, retrieve it, and diff against this file before reusing it.

## 2. Load: Contact upsert by business key

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/omniDataTransforms/ContactFeedLoad_1.rpt-meta.xml -->
<OmniDataTransform xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <assignmentRulesUsed>false</assignmentRulesUsed>
    <deletedOnSuccess>false</deletedOnSuccess>
    <description>Upsert Contacts from the customer feed by External_Customer_ID__c</description>
    <errorIgnored>false</errorIgnored>
    <fieldLevelSecurityEnabled>true</fieldLevelSecurityEnabled>
    <inputType>JSON</inputType>
    <isManagedUsingStdDesigner>false</isManagedUsingStdDesigner>
    <name>ContactFeedLoad</name>
    <nullInputsIncludedInOutput>false</nullInputsIncludedInOutput>
    <omniDataTransformItem>
        <disabled>false</disabled>
        <filterGroup>0.0</filterGroup>
        <globalKey>7a2d3b20-2b3c-4d5e-9f00-000000000001</globalKey>
        <inputFieldName>customer:externalId</inputFieldName>
        <inputObjectQuerySequence>0.0</inputObjectQuerySequence>
        <linkedObjectSequence>0.0</linkedObjectSequence>
        <name>ContactFeedLoad</name>
        <outputCreationSequence>1.0</outputCreationSequence>
        <outputFieldName>External_Customer_ID__c</outputFieldName>
        <outputObjectName>Contact</outputObjectName>
        <requiredForUpsert>true</requiredForUpsert>
        <upsertKey>true</upsertKey>
    </omniDataTransformItem>
    <omniDataTransformItem>
        <disabled>false</disabled>
        <filterGroup>0.0</filterGroup>
        <globalKey>7a2d3b20-2b3c-4d5e-9f00-000000000002</globalKey>
        <inputFieldName>customer:lastName</inputFieldName>
        <inputObjectQuerySequence>0.0</inputObjectQuerySequence>
        <linkedObjectSequence>0.0</linkedObjectSequence>
        <name>ContactFeedLoad</name>
        <outputCreationSequence>1.0</outputCreationSequence>
        <outputFieldName>LastName</outputFieldName>
        <outputObjectName>Contact</outputObjectName>
        <requiredForUpsert>true</requiredForUpsert>
        <upsertKey>false</upsertKey>
    </omniDataTransformItem>
    <omniDataTransformItem>
        <disabled>false</disabled>
        <filterGroup>0.0</filterGroup>
        <globalKey>7a2d3b20-2b3c-4d5e-9f00-000000000003</globalKey>
        <inputFieldName>customer:email</inputFieldName>
        <inputObjectQuerySequence>0.0</inputObjectQuerySequence>
        <linkedObjectSequence>0.0</linkedObjectSequence>
        <name>ContactFeedLoad</name>
        <outputCreationSequence>1.0</outputCreationSequence>
        <outputFieldName>Email</outputFieldName>
        <outputObjectName>Contact</outputObjectName>
        <requiredForUpsert>false</requiredForUpsert>
        <upsertKey>false</upsertKey>
    </omniDataTransformItem>
    <outputType>SObject</outputType>
    <processSuperBulk>false</processSuperBulk>
    <responseCacheTtlMinutes>0.0</responseCacheTtlMinutes>
    <rollbackOnError>true</rollbackOnError>
    <sourceObjectDefault>false</sourceObjectDefault>
    <synchronousProcessThreshold>200.0</synchronousProcessThreshold>
    <type>Load</type>
    <uniqueName>ContactFeedLoad_1</uniqueName>
    <versionNumber>1.0</versionNumber>
    <xmlDeclarationRemoved>false</xmlDeclarationRemoved>
</OmniDataTransform>
```

UNVERIFIED (2026-10-03): the guide documents `upsertKey`, `requiredForUpsert`, `outputObjectName`, and `outputType` (listing "SObejct" among its values) but shows only an Extract sample. The Load item layout above (input path in `inputFieldName`, target object in `outputObjectName`, target field in `outputFieldName`) is inferred from those field descriptions; confirm it against a designer-built Load.

## 3. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/data-mappers.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>AccountContactsExtract_1</members>
        <members>ContactFeedLoad_1</members>
        <name>OmniDataTransform</name>
    </types>
    <version>67.0</version>
</Package>
```

UNVERIFIED (2026-10-03): the member name is assumed to be the `uniqueName`; the guide's own package.xml sample uses the `*` wildcard instead. Run `sf project retrieve start --metadata OmniDataTransform` once and use the names the CLI writes.

## 4. Commands and verification

```bash
sf project retrieve start --metadata OmniDataTransform --target-org dev --output-dir retrieved
python3 skills/omnistudio/dataraptor-load-and-extract/scripts/check_dataraptor_load_and_extract.py --source-dir force-app
sf project deploy start --manifest manifest/data-mappers.xml --target-org uat --wait 30
```

| Order | Step | Verify |
|---|---|---|
| 1 | Deploy both Data Mappers | Deploy succeeded; both active |
| 2 | Extract Preview in UAT with `AccountId` | Response nests Contacts under Account |
| 3 | Load Preview in a developer sandbox only | Existing key updates; new key creates; empty key skips |
| 4 | Integration Procedure test | The IP reports Load failures to the OmniScript |
