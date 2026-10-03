# Metadata Examples: Provider Policy and a Template Version Pinned to a Model

Two deployable pieces keep model choices reviewable: EinsteinGptSettings for provider policy and region fallback, and a GenAiPromptTemplate whose version names its model in `primaryModel`. Element names follow the Metadata API Developer Guide, Version 67.0.

## File: `force-app/main/default/settings/EinsteinGpt.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EinsteinGptSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <disableAIProvAWSBedrock>true</disableAIProvAWSBedrock>
    <disableAIProvAzureOpenAI>false</disableAIProvAzureOpenAI>
    <disableAIProvOpenAI>false</disableAIProvOpenAI>
    <disableAIProvVertexGemini>true</disableAIProvVertexGemini>
    <disableAIProviderRegionFallback>true</disableAIProviderRegionFallback>
    <enableAIModelBeta>false</enableAIModelBeta>
    <enableEinsteinGptPlatform>true</enableEinsteinGptPlatform>
</EinsteinGptSettings>
```

This policy allows Azure OpenAI and OpenAI, blocks Amazon Bedrock and Vertex AI, keeps beta models off, and stops Azure OpenAI fallback outside the endpoint region. Do not copy the guide's own EinsteinGptSettings sample, whose closing tags do not match.

## File: `force-app/main/default/genAiPromptTemplates/Thread_Summary.genAiPromptTemplate-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GenAiPromptTemplate xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Summarizes a customer email thread for the service rep.</description>
    <masterLabel>Thread Summary</masterLabel>
    <templateVersions>
        <content>Summarize the email thread on case {!$Input:Case.CaseNumber} in four bullet points.
Instructions:
"""
Use only the thread content. Do not invent dates or commitments.
"""</content>
        <inputs>
            <apiName>Case</apiName>
            <definition>SOBJECT://Case</definition>
            <referenceName>Input:Case</referenceName>
            <required>true</required>
        </inputs>
        <primaryModel>sfdc_ai__DefaultOpenAIGPT4</primaryModel>
        <status>Draft</status>
    </templateVersions>
    <type>einstein_gpt__flex</type>
    <visibility>Global</visibility>
</GenAiPromptTemplate>
```

`sfdc_ai__DefaultOpenAIGPT4` is the value used in the Metadata API's GenAiPromptTemplate sample. UNVERIFIED (2026-10-03): the API names for other Salesforce-managed models and for BYO model configurations are not listed in a fetched source. Select the model in Prompt Builder, retrieve the template, and copy the `primaryModel` value it writes.

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Thread_Summary</members>
        <name>GenAiPromptTemplate</name>
    </types>
    <types>
        <members>EinsteinGpt</members>
        <name>Settings</name>
    </types>
    <version>67.0</version>
</Package>
```

## Verify

1. `python3 skills/agentforce/model-builder-and-byollm/scripts/check_model_builder_and_byollm.py --manifest-dir force-app/main/default` reports no template on a blocked provider.
2. Deploy the settings first, then the template.
3. Preview the template in Prompt Builder and confirm the model shown in the configuration panel.
