# Metadata Examples: Einstein Discovery Setup

The deployable shape of the Opportunity win prediction from `examples.md`: a prediction definition (`DiscoveryGoal`) with a segmented model and a catch-all model, its writeback field, terminal-state filters for accuracy monitoring, and the permission set that shows the score.

Grounding: Metadata API Developer Guide, DiscoveryAIModel (`api_meta L54449-54745`) and DiscoveryGoal including subtypes, sample, and manifest (`api_meta L54747-55190`). Element values marked UNVERIFIED are illustrative names for this org, not documented constants.

Licence gate: Einstein Discovery requires a CRM Analytics license (CRM Analytics Plus or an Einstein Predictions license; see the Analytics Platform Setup Guide licensing note).

## 1. Prediction definition with two segment models

`force-app/main/default/discovery/Opportunity_Win_Prediction.goal-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DiscoveryGoal xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <deployedModels>
        <active>true</active>
        <aiModel>Opportunity_Win_EMEA</aiModel>
        <fieldMappings>
            <mappedField>Opportunity.Amount</mappedField>
            <modelField>Amount</modelField>
            <sourceType>SalesforceField</sourceType>
        </fieldMappings>
        <fieldMappings>
            <mappedField>Opportunity.LeadSource</mappedField>
            <modelField>LeadSource</modelField>
            <sourceType>SalesforceField</sourceType>
        </fieldMappings>
        <filters>
            <field>Opportunity.Region__c</field>
            <operator>Equal</operator>
            <type>Text</type>
            <values>
                <type>Constant</type>
                <value>EMEA</value>
            </values>
        </filters>
        <label>Win model EMEA</label>
        <name>Opportunity_Win_EMEA</name>
    </deployedModels>
    <deployedModels>
        <active>true</active>
        <aiModel>Opportunity_Win_Global</aiModel>
        <fieldMappings>
            <mappedField>Opportunity.Amount</mappedField>
            <modelField>Amount</modelField>
            <sourceType>SalesforceField</sourceType>
        </fieldMappings>
        <fieldMappings>
            <mappedField>Opportunity.LeadSource</mappedField>
            <modelField>LeadSource</modelField>
            <sourceType>SalesforceField</sourceType>
        </fieldMappings>
        <label>Win model catch-all</label>
        <name>Opportunity_Win_Global</name>
    </deployedModels>
    <label>Opportunity Win Prediction</label>
    <outcome>
        <field>IsWon</field>
        <fieldLabel>Won</fieldLabel>
        <goal>Maximize</goal>
        <mappedField>Opportunity.IsWon</mappedField>
    </outcome>
    <predictionType>Classification</predictionType>
    <pushbackField>Win_Likelihood__c</pushbackField>
    <pushbackType>AiRecordInsight</pushbackType>
    <subscribedEntity>Opportunity</subscribedEntity>
    <terminalStateFilters>
        <field>Opportunity.IsClosed</field>
        <operator>Equal</operator>
        <type>Boolean</type>
        <values>
            <type>Constant</type>
            <value>true</value>
        </values>
    </terminalStateFilters>
</DiscoveryGoal>
```

| Element | Why it is set this way |
|---|---|
| `deployedModels` order | The EMEA model has a filter and comes first; the catch-all has no filter and comes last, because "the first model that has filters matching a specific input row will be used" |
| Number of models | Two of the maximum ten active models per prediction definition |
| `pushbackField` | Never remove it in a deploy; removing it deletes the field from Opportunity |
| `pushbackType` | Must be `AiRecordInsight`; `Direct` is reserved |
| `terminalStateFilters` | Closed opportunities are the observed outcomes used for accuracy monitoring |
| `predictionType` | `Classification` is binary; `MulticlassClassification` and `Regression` also exist |

UNVERIFIED (2026-10-03): `Region__c`, `Win_Likelihood__c`, and the model field names (`Amount`, `LeadSource`, `IsWon`) are illustrative; a real goal must use the model's actual variable names, so retrieve the goal after deploying from the story rather than writing it first. UNVERIFIED (2026-10-03): the guide's DiscoveryGoalOutcome table swaps the descriptions of `Minimize` and `Maximize`; `Maximize` is used here in its plain sense.

## 2. Models are retrieved, not written

The two `aiModel` values must exist as `DiscoveryAIModel` components (`discovery/<name>.model` plus `<name>.model-meta.xml`). "Write operations for DiscoveryAIModel objects are generally not supported," so retrieve them from the org where Einstein Discovery built them and deploy them unchanged.

## 3. Show the score to sales users

`force-app/main/default/permissionsets/Opportunity_Win_Score_Viewer.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Read access to the Einstein Discovery win likelihood on Opportunity</description>
    <fieldPermissions>
        <editable>false</editable>
        <field>Opportunity.Win_Likelihood__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Opportunity Win Score Viewer</label>
</PermissionSet>
```

`editable` stays `false`: the score is written by Einstein Discovery, not by users. UNVERIFIED (2026-10-03): whether the writeback field arrives with any default field-level security is help-only; this permission set makes access explicit either way.

## 4. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity_Win_EMEA</members>
        <members>Opportunity_Win_Global</members>
        <name>DiscoveryAIModel</name>
    </types>
    <types>
        <members>Opportunity_Win_Prediction</members>
        <name>DiscoveryGoal</name>
    </types>
    <types>
        <members>Opportunity_Win_Score_Viewer</members>
        <name>PermissionSet</name>
    </types>
    <version>67.0</version>
</Package>
```

## Deploy order

1. `DiscoveryAIModel` (retrieved, unchanged).
2. `DiscoveryGoal`, after a diff check that `pushbackField` is still present.
3. `PermissionSet`, then assign it to sales users and add the field to the Opportunity record page.

## Verification

- The prediction definition shows two active models, EMEA first.
- An EMEA opportunity is scored by the EMEA model; an APAC opportunity by the catch-all.
- Sales users with the permission set see `Win_Likelihood__c`; users without it do not.
- Model accuracy in Model Manager is computed only over closed opportunities.
