# Metadata Examples: Einstein Next Best Action

Deployable artifacts for a case-page recommendation setup. Sources: Object Reference (Recommendation fields), Metadata API Developer Guide (Flow `processType` `RecommendationStrategy`, `FlowRecordLookup` `limit`/`sortField`/`sortOrder`, RecordActionDeployment), and Trailhead "Set Up Salesforce Flow for Service". Recommendation records are data and load separately.

## 1. Custom fields the standard object does not have

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/objects/Recommendation/fields/Target_Object__c.field-meta.xml -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Target_Object__c</fullName>
    <description>Object page this recommendation belongs on. The standard Recommendation object has no object-type field.</description>
    <label>Target Object</label>
    <length>40</length>
    <required>false</required>
    <type>Text</type>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/objects/Recommendation/fields/Expiration_Date__c.field-meta.xml -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Expiration_Date__c</fullName>
    <description>Last day this recommendation may be offered. The standard Recommendation object has no expiration field.</description>
    <label>Expiration Date</label>
    <required>false</required>
    <type>Date</type>
</CustomField>
```

UNVERIFIED (2026-10-03): that custom fields can be added to the standard Recommendation object is assumed from the object being a standard sObject with create and update support; confirm in Object Manager before deploying.

## 2. Strategy flow

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/flows/Case_Recommendation_Strategy.flow-meta.xml -->
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <assignments>
        <name>Return_Recommendations</name>
        <label>Return Recommendations</label>
        <locationX>176</locationX>
        <locationY>240</locationY>
        <assignmentItems>
            <assignToReference>outputRecommendations</assignToReference>
            <operator>Assign</operator>
            <value>
                <elementReference>Get_Case_Recommendations</elementReference>
            </value>
        </assignmentItems>
    </assignments>
    <description>Returns up to four active, unexpired Case recommendations for the Actions &amp; Recommendations component.</description>
    <interviewLabel>Case Recommendation Strategy {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Case Recommendation Strategy</label>
    <processType>RecommendationStrategy</processType>
    <recordLookups>
        <name>Get_Case_Recommendations</name>
        <label>Get Case Recommendations</label>
        <locationX>176</locationX>
        <locationY>120</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Return_Recommendations</targetReference>
        </connector>
        <filterLogic>1 AND 2 AND (3 OR 4)</filterLogic>
        <filters>
            <field>IsActionActive</field>
            <operator>EqualTo</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </filters>
        <filters>
            <field>Target_Object__c</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Case</stringValue>
            </value>
        </filters>
        <filters>
            <field>Expiration_Date__c</field>
            <operator>IsNull</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </filters>
        <filters>
            <field>Expiration_Date__c</field>
            <operator>GreaterThanOrEqualTo</operator>
            <value>
                <elementReference>$Flow.CurrentDate</elementReference>
            </value>
        </filters>
        <getFirstRecordOnly>false</getFirstRecordOnly>
        <limit>
            <numberValue>4.0</numberValue>
        </limit>
        <object>Recommendation</object>
        <sortField>Name</sortField>
        <sortOrder>Asc</sortOrder>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Get_Case_Recommendations</targetReference>
        </connector>
    </start>
    <status>Draft</status>
    <variables>
        <name>recordId</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>outputRecommendations</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
        <objectType>Recommendation</objectType>
    </variables>
</Flow>
```

Design notes:

- `processType` `RecommendationStrategy` is the documented flow type for building recommendations (API 54.0+).
- `IsActionActive = true` keeps recommendations whose acceptance flow is inactive off the page.
- `limit` 4 matches the most the component can display; rank with `sortField` (replace `Name` with a custom priority field when one exists).
- UNVERIFIED (2026-10-03): the variable names `recordId` and `outputRecommendations` follow Salesforce Help search snippets for the template a new Recommendation Strategy flow starts with; no source read for this revision prints them. Create the flow from the template in Flow Builder and keep the names it generates.

## 3. Actions & Recommendations deployment

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/recordActionDeployments/Case_Service_Guidance.deployment-meta.xml -->
<RecordActionDeployment xmlns="http://soap.sforce.com/2006/04/metadata">
    <componentName>ActionsAndRecommendations</componentName>
    <deploymentContexts>
        <entityName>Case</entityName>
        <recommendationStrategy>Case_Recommendation_Strategy</recommendationStrategy>
    </deploymentContexts>
    <hasGuidedActions>false</hasGuidedActions>
    <hasRecommendations>true</hasRecommendations>
    <masterLabel>Case Service Guidance</masterLabel>
    <recommendation>
        <defaultStrategy>Case_Recommendation_Strategy</defaultStrategy>
        <hasDescription>true</hasDescription>
        <hasImage>false</hasImage>
        <hasRejectAction>true</hasRejectAction>
        <hasTitle>true</hasTitle>
        <maxDisplayRecommendations>4</maxDisplayRecommendations>
    </recommendation>
    <shouldLaunchActionOnReject>false</shouldLaunchActionOnReject>
</RecordActionDeployment>
```

Field rules from the Metadata API guide: `maxDisplayRecommendations` accepts 1–4; up to 10 `deploymentContexts`; `shouldLaunchActionOnReject` is required, and true launches the flow on reject. The guide stores these as `developer_name.deployment` files in `recordActionDeployments`. UNVERIFIED (2026-10-03): the `.deployment-meta.xml` source-format file name and whether `defaultStrategy` accepts a flow API name (the guide's description names the `RecommendationStrategy` metadata type) were not confirmed; retrieve one deployment built in Setup to check before relying on hand-written files. Select the deployment in the component properties on the Case page; with no deployment selected, reps see an empty list.

## 4. package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Recommendation.Target_Object__c</members>
        <members>Recommendation.Expiration_Date__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Case_Recommendation_Strategy</members>
        <members>Share_KB_Article_Flow</members>
        <members>Escalate_Case_Flow</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Case_Service_Guidance</members>
        <name>RecordActionDeployment</name>
    </types>
    <version>67.0</version>
</Package>
```

Deploy order: custom fields, acceptance flows, strategy flow (activate it), deployment, then load the Recommendation rows and check `IsActionActive` on each.
