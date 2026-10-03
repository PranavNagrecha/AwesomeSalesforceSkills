# Metadata Examples: Trust Layer Settings in Source Control

Two settings types carry the Trust Layer switches that can be deployed. Field names and descriptions come from the Metadata API Developer Guide, Version 67.0 (EinsteinAISettings, EinsteinGptSettings). Keep both files in source control so a sandbox refresh or a new org cannot quietly differ from production.

## File: `force-app/main/default/settings/EinsteinAI.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EinsteinAISettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableAIFeedbackWithDC>true</enableAIFeedbackWithDC>
    <enableTrustPIIMasking>true</enableTrustPIIMasking>
</EinsteinAISettings>
```

- `enableTrustPIIMasking`: "Indicates whether PII (Personally Identifiable Information) masking for AI trust features is enabled." API 60.0+.
- `enableAIFeedbackWithDC`: "Indicates whether AI feedback integration with Data 360 is enabled." API 60.0+.
- The guide marks `enableAITrustInputToxicityDetection` and `enableAITrustPromptInjectionDetection` as "Reserved for internal use." Do not set them.

UNVERIFIED (2026-10-03): the guide says the values live in "the EinsteinAISettings.settings file" but uses `EinsteinAI` as the package.xml member. The file name above follows the member-name convention of other settings types; retrieve once from a sandbox and keep whatever name the retrieve returns. Whether `enableAIFeedbackWithDC` is the same switch as "Einstein generative AI data collection and storage" in Setup is not stated.

## File: `force-app/main/default/settings/EinsteinGpt.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EinsteinGptSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <disableAIProvAWSBedrock>false</disableAIProvAWSBedrock>
    <disableAIProvAzureOpenAI>false</disableAIProvAzureOpenAI>
    <disableAIProvOpenAI>true</disableAIProvOpenAI>
    <disableAIProvVertexGemini>true</disableAIProvVertexGemini>
    <disableAIProviderRegionFallback>true</disableAIProviderRegionFallback>
    <enableEinsteinGptPlatform>true</enableEinsteinGptPlatform>
</EinsteinGptSettings>
```

- `enableEinsteinGptPlatform`: turns on generative AI features across Salesforce (default false). API 61.0+.
- `disableAIProv*`: each "Indicates whether [the provider] is turned off and access to its models are blocked." This example keeps Azure OpenAI and Amazon Bedrock and blocks OpenAI and Vertex AI, for an org whose policy approves only the first two.
- `disableAIProviderRegionFallback`: "Indicates whether the fallback of Azure OpenAI requests outside the model endpoint region for your org is turned off." Set to true when Azure OpenAI requests must stay in region. This does not stop geo-aware routing from sending requests to the US when a model is not available nearby; that "can't" be disabled (Generative AI guide, Geo-Aware LLM Request Routing).

Do not copy the guide's own EinsteinGptSettings sample: its closing tags do not match its opening tags (`<enableEinsteinGptPlatform>true</reRunAttributeBasedRules>`), so it does not parse.

UNVERIFIED (2026-10-03): which features stop working when a provider is blocked depends on which provider backs each feature's model; test in a sandbox before blocking a provider in production.

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>EinsteinAI</members>
        <members>EinsteinGpt</members>
        <name>Settings</name>
    </types>
    <version>67.0</version>
</Package>
```

## Verify

1. `python3 skills/agentforce/einstein-trust-layer/scripts/check_einstein_trust_layer.py --manifest-dir force-app/main/default` returns no ERROR.
2. After deploy, open Einstein Trust Layer in Setup and confirm masking shows on.
3. Preview a prompt template with a known test record and open View Your Data Masking Details.
4. Remember that agents are not masked regardless of these settings.
