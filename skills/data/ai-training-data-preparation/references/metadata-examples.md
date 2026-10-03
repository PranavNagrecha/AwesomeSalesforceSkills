# Metadata Examples: Prediction Builder Data Definition With Explicit Exclusions

When a prediction is moved between orgs, the training scope travels in Metadata API types: AIApplication (the Prediction Builder instance), MLDataDefinition (which object, which fields, which records train and score), and MLPredictionDefinition (the prediction and the field scores are written to). Element names follow the Metadata API Developer Guide, Version 67.0. Writing `excludedFields` explicitly is how this skill's leakage audit becomes part of the deployed definition.

## File: `force-app/main/default/aiApplications/Case_Escalation.ai`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AIApplication xmlns="http://soap.sforce.com/2006/04/metadata">
    <developerName>Case_Escalation</developerName>
    <masterLabel>Case Escalation</masterLabel>
    <status>Draft</status>
    <type>PredictionBuilder</type>
</AIApplication>
```

## File: `force-app/main/default/mlDataDefinitions/Case_Escalation_Data.mlDataDefinition`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MLDataDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <developerName>Case_Escalation_Data</developerName>
    <entityDeveloperName>Case</entityDeveloperName>
    <excludedFields>Resolution_Time__c</excludedFields>
    <excludedFields>Escalation_Reason__c</excludedFields>
    <excludedFields>ClosedDate</excludedFields>
    <includedFields>Customer_Tier__c</includedFields>
    <includedFields>Product_Category__c</includedFields>
    <includedFields>Days_Without_Response__c</includedFields>
    <includedFields>Origin</includedFields>
    <trainingFilter>
        <filterName>Closed_Cases_Only</filterName>
        <lhPredictionField>IsClosed</lhPredictionField>
        <operation>Equals</operation>
        <rhType>Boolean</rhType>
        <rhValue>true</rhValue>
    </trainingFilter>
    <type>Prediction</type>
</MLDataDefinition>
```

## File: `force-app/main/default/mlPredictions/Case_Escalation_Prediction.mlPrediction`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MLPredictionDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <aiApplicationDeveloperName>Case_Escalation</aiApplicationDeveloperName>
    <developerName>Case_Escalation_Prediction</developerName>
    <masterLabel>Case Escalation Prediction</masterLabel>
    <predictionField>IsEscalated</predictionField>
    <pushbackField>Escalation_Score__c</pushbackField>
    <status>Draft</status>
    <type>BinaryClassification</type>
</MLPredictionDefinition>
```

UNVERIFIED (2026-10-03): the Metadata API guide lists these fields but gives no sample definitions for MLDataDefinition or MLPredictionDefinition. How a comparison is encoded in `trainingFilter` (whether `lhPredictionField` is the right left-hand element for an object field, and whether `lhType` is also required) is inferred from the MLFilter field list. Whether `includedFields` and `excludedFields` take bare field names or `Object.Field` is not stated. Retrieve an existing prediction from a sandbox and match its shape before deploying. Deploying with `status` Draft keeps the prediction from scoring until someone enables it.

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case_Escalation</members>
        <name>AIApplication</name>
    </types>
    <types>
        <members>Case_Escalation_Data</members>
        <name>MLDataDefinition</name>
    </types>
    <types>
        <members>Case_Escalation_Prediction</members>
        <name>MLPredictionDefinition</name>
    </types>
    <version>67.0</version>
</Package>
```

## Verify

1. Run the checker on the training extract first (Example 3 in `references/examples.md`) and resolve every ERROR.
2. Confirm each excluded field in the data definition matches a field the leakage review rejected.
3. Deploy to a sandbox with `status` Draft, review the prediction scorecard, then enable.
