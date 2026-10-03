# Metadata Examples: OmniScript Design Patterns

How to keep OmniScripts under version control as metadata, with a reusable child script. Field names come from the OmniScript, OmniProcessElement, and OmniStudioSettings reference in the Industries Common Resources Developer Guide (Summer '26). The source-format folder and suffix (`omniScripts/`, `.os-meta.xml`) come from the Salesforce CLI metadata registry (source-deploy-retrieve 12.22.6); the guide lists the Metadata API suffix as `omniScript`.

## 1. Turn on Omnistudio metadata (one-way)

This sample is taken from the guide. `enableOmniStudioMetadata` can't be enabled while component unique names contain spaces or special characters, and it can't be disabled afterward.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/settings/OmniStudio.settings-meta.xml -->
<OmniStudioSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableOmniStudioMetadata>true</enableOmniStudioMetadata>
    <enableOmniStudioContentTest>false</enableOmniStudioContentTest>
    <enableStandardOmniStudioRuntime>false</enableStandardOmniStudioRuntime>
    <enableOmniStudioDrVersion>false</enableOmniStudioDrVersion>
    <enableOaForCore>false</enableOaForCore>
    <enableOaEventNotifications>false</enableOaEventNotifications>
    <enableOaEventInternalWrites>false</enableOaEventInternalWrites>
    <enableOmniGlobalAutoNumberPref>true</enableOmniGlobalAutoNumberPref>
    <disableRollbackFlagsPref>false</disableRollbackFlagsPref>
</OmniStudioSettings>
```

package.xml member form: `<members>OmniStudio</members>` under `<name>Settings</name>`.

## 2. A reusable, embeddable child OmniScript (skeleton)

Identity is Type `shared`, SubType `captureAddress`, Language `English`, so the unique name is `shared_captureAddress_English_1`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/omniScripts/shared_captureAddress_English_1.os-meta.xml -->
<OmniScript xmlns="http://soap.sforce.com/2006/04/metadata">
    <isActive>true</isActive>
    <isIntegrationProcedure>false</isIntegrationProcedure>
    <isMetadataCacheDisabled>false</isMetadataCacheDisabled>
    <isOmniScriptEmbeddable>true</isOmniScriptEmbeddable>
    <isTestProcedure>false</isTestProcedure>
    <isWebCompEnabled>true</isWebCompEnabled>
    <language>English</language>
    <name>Capture Address</name>
    <omniProcessElements>
        <childElements>
            <isActive>true</isActive>
            <isOmniScriptEmbeddable>false</isOmniScriptEmbeddable>
            <level>1.0</level>
            <name>MailingStreet</name>
            <omniProcessVersionNumber>1.0</omniProcessVersionNumber>
            <parentElementName>StepAddress</parentElementName>
            <parentElementType>Step</parentElementType>
            <propertySetConfig>{"label":"Street","required":true}</propertySetConfig>
            <sequenceNumber>0.0</sequenceNumber>
            <type>Text</type>
        </childElements>
        <isActive>true</isActive>
        <isOmniScriptEmbeddable>false</isOmniScriptEmbeddable>
        <level>0.0</level>
        <name>StepAddress</name>
        <omniProcessVersionNumber>1.0</omniProcessVersionNumber>
        <propertySetConfig>{"label":"Address"}</propertySetConfig>
        <sequenceNumber>0.0</sequenceNumber>
        <type>Step</type>
    </omniProcessElements>
    <omniProcessType>OmniScript</omniProcessType>
    <propertySetConfig>{}</propertySetConfig>
    <subType>captureAddress</subType>
    <type>shared</type>
    <uniqueName>shared_captureAddress_English_1</uniqueName>
    <versionNumber>1</versionNumber>
</OmniScript>
```

UNVERIFIED (2026-10-03): the guide documents every element used above, but its only sample is a Discovery Framework script, and it does not list the JSON keys inside `propertySetConfig`. The keys shown (`label`, `required`) are placeholders. Build the script in the designer, retrieve it, and keep the retrieved `propertySetConfig` values; use this file to check structure, identity fields, and the embeddable flag, not as a hand-written source of truth.

## 3. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/omniscripts.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>shared_captureAddress_English_1</members>
        <members>team_editAccount_English_2</members>
        <name>OmniScript</name>
    </types>
    <types>
        <members>OmniStudio</members>
        <name>Settings</name>
    </types>
    <version>67.0</version>
</Package>
```

UNVERIFIED (2026-10-03): the member name is assumed to equal `uniqueName`. Run `sf project retrieve start --metadata OmniScript` once and use the names the CLI writes.

## 4. Commands and checks

```bash
sf project retrieve start --metadata OmniScript --target-org dev
python3 skills/omnistudio/omniscript-design-patterns/scripts/check_omniscript_design_patterns.py --source-dir force-app
sf project deploy start --manifest manifest/omniscripts.xml --target-org uat --wait 30
```

| Check | Where |
|---|---|
| Only one active script per Type, SubType, Language | Checker output, then the OmniScripts list in the target org |
| Child scripts embeddable | `isOmniScriptEmbeddable` is `true` in each child file |
| Element names unique within a script | Checker output |
| Active version per environment | Designer header in each org after deployment |
