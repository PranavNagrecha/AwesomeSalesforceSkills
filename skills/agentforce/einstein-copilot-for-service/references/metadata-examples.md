# Metadata Examples: Einstein for Service Settings in Source Control

The switches that decide whether classification re-routes cases, and which reply features are on, are deployable settings. Element names follow the Metadata API Developer Guide, Version 67.0 (EinsteinAgentSettings, AIReplyRecommendationsSettings, ServiceAISetupDefinition, ServiceAISetupField, ExternalAIModel).

## File: `force-app/main/default/settings/EinsteinAgent.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EinsteinAgentSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <einsteinAgentRecommendations>true</einsteinAgentRecommendations>
    <reRunAttributeBasedRules>true</reRunAttributeBasedRules>
    <runAssignmentRules>false</runAssignmentRules>
</EinsteinAgentSettings>
```

- `einsteinAgentRecommendations`: "Indicates whether Einstein classification apps are enabled in your org." Default false.
- `reRunAttributeBasedRules`: "If true, skills-based routing rules are run after Einstein Case Classification automatically updates field values." Default false. This org routes by skills, so it is on.
- `runAssignmentRules`: "If true, assignment rules are run after Einstein Case Classification automatically updates field values." Default false. Left off here because routing is skills-based.

## File: `force-app/main/default/settings/AIReplyRecommendations.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AIReplyRecommendationsSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableAIReplyRecommendations>true</enableAIReplyRecommendations>
    <enableGenReplyRecommendations>true</enableGenReplyRecommendations>
    <enableServiceEinsteinGPTGrounding>true</enableServiceEinsteinGPTGrounding>
</AIReplyRecommendationsSettings>
```

- `enableAIReplyRecommendations`: Einstein Reply Recommendations (predictive replies from closed chats).
- `enableGenReplyRecommendations`: "Einstein Service Replies" (generative). API 58.0+.
- `enableServiceEinsteinGPTGrounding`: "Service AI Grounding." API 58.0+.

UNVERIFIED (2026-10-03): the guide says these three default to true "If true (default)," which suggests the settings file mostly records an existing state; confirm in a retrieve before deploying.

## File: `force-app/main/default/serviceAISetupDescriptions/Article_Recs_EN_FR.serviceAISetupDescription-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ServiceAISetupDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <appSourceType>ARTICLE_RECOMMENDATION</appSourceType>
    <name>Article_Recs_EN_FR</name>
    <setupStatus>FIELDS_SELECTED</setupStatus>
    <supportedLanguages>en,fr</supportedLanguages>
</ServiceAISetupDefinition>
```

## File: `force-app/main/default/serviceAiSetupFields/Article_Recs_Case_Subject.serviceAiSetupField-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ServiceAISetupField xmlns="http://soap.sforce.com/2006/04/metadata">
    <entity>Case</entity>
    <field>Subject</field>
    <fieldMappingType>CASE_SUBJ</fieldMappingType>
    <fieldPosition>1</fieldPosition>
    <name>Article_Recs_Case_Subject</name>
    <setupDefinition>Article_Recs_EN_FR</setupDefinition>
</ServiceAISetupField>
```

The folder and suffix follow the guide exactly, including its spelling `serviceAISetupDescriptions` / `.serviceAISetupDescription` for ServiceAISetupDefinition. UNVERIFIED (2026-10-03): the guide's sample sets `setupDefinition` to a record ID (`4hQRM0000004CDK`), not a name; retrieve from a sandbox and keep the value format the retrieve returns. Both types are available only when Einstein Article Recommendations is enabled and the Main Services Agreement is accepted.

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>AIReplyRecommendations</members>
        <members>EinsteinAgent</members>
        <name>Settings</name>
    </types>
    <types>
        <members>Article_Recs_EN_FR</members>
        <name>ServiceAISetupDefinition</name>
    </types>
    <types>
        <members>Article_Recs_Case_Subject</members>
        <name>ServiceAISetupField</name>
    </types>
    <version>67.0</version>
</Package>
```

ExternalAIModel (the Reply Recommendations model state) "doesn't support the wildcard character" in package.xml; add it by name after a retrieve shows the model's name.

## Verify

1. `python3 skills/agentforce/einstein-copilot-for-service/scripts/check_einstein_copilot_for_service.py --manifest-dir force-app/main/default`.
2. Deploy to a sandbox at API 52.0 or later (EinsteinAgentSettings did not exist before 52.0).
3. Create a test case that Einstein classifies and confirm skills-based routing re-runs after the field update.
