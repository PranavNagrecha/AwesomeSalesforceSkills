# Metadata Examples: Flow for Slack

Two deployable flows: a record-triggered flow that posts to Slack on an asynchronous path, and a Slack-enabled screen flow for Send Message to Launch Flow. Flow element names (`actionCalls`, `actionType`, `faultConnector`, `scheduledPaths`, `pathType`, `environments`) and the Slack `actionType` values come from the Metadata API Developer Guide (Summer '26, API 67.0).

## 1. Record-triggered flow: post to a channel when an Opportunity enters Negotiation

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/flows/Opportunity_Negotiation_Slack_Alert.flow-meta.xml -->
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <actionCalls>
        <name>Post_Negotiation_Alert</name>
        <label>Post Negotiation Alert</label>
        <locationX>176</locationX>
        <locationY>288</locationY>
        <actionName>slackPostMessage</actionName>
        <actionType>slackPostMessage</actionType>
        <faultConnector>
            <targetReference>Log_Slack_Failure</targetReference>
        </faultConnector>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>slackAppIdForToken</name>
            <value>
                <elementReference>$CustomMetadata.Slack_Config__mdt.Sales_Alerts.App_Id__c</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>slackWorkspaceIdForToken</name>
            <value>
                <elementReference>$CustomMetadata.Slack_Config__mdt.Sales_Alerts.Workspace_Id__c</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>slackConversationId</name>
            <value>
                <elementReference>$CustomMetadata.Slack_Config__mdt.Sales_Alerts.Channel_Id__c</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>slackMessage</name>
            <value>
                <elementReference>AlertText</elementReference>
            </value>
        </inputParameters>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </actionCalls>
    <apiVersion>67.0</apiVersion>
    <description>Posts to the deal-alerts Slack channel after an Opportunity moves to Negotiation. Slack action runs on the async path.</description>
    <environments>Default</environments>
    <interviewLabel>Opportunity Negotiation Slack Alert {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Opportunity Negotiation Slack Alert</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Log_Slack_Failure</name>
        <label>Log Slack Failure</label>
        <locationX>440</locationX>
        <locationY>288</locationY>
        <inputAssignments>
            <field>Subject</field>
            <value>
                <stringValue>Slack alert failed</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Description</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>WhatId</field>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>OwnerId</field>
            <value>
                <elementReference>$Record.OwnerId</elementReference>
            </value>
        </inputAssignments>
        <object>Task</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
        <filterLogic>and</filterLogic>
        <filters>
            <field>StageName</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Negotiation/Review</stringValue>
            </value>
        </filters>
        <object>Opportunity</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <scheduledPaths>
            <name>Post_After_Commit</name>
            <label>Post After Commit</label>
            <connector>
                <targetReference>Post_Negotiation_Alert</targetReference>
            </connector>
            <pathType>AsyncAfterCommit</pathType>
        </scheduledPaths>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Draft</status>
    <textTemplates>
        <name>AlertText</name>
        <isViewedAsPlainText>true</isViewedAsPlainText>
        <text>Negotiation: {!$Record.Name} for {!$Record.Account.Name}. Owner: {!$Record.Owner.Name}.</text>
    </textTemplates>
</Flow>
```

UNVERIFIED (2026-10-03): the four `inputParameters` names are not listed in the fetched Metadata API or Actions guides. Add the Send Slack Message action in Flow Builder once, retrieve the flow, and copy the parameter names it writes. `$CustomMetadata.Slack_Config__mdt...` assumes a custom metadata type you create with those three text fields; it keeps workspace and channel IDs out of the flow.

## 2. Screen flow launched from a Slack button

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/flows/Approve_Discount_In_Slack.flow-meta.xml -->
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <description>Screen flow launched by Send Message to Launch Flow. The Slack environment lets it run in Slack and in the default environment.</description>
    <environments>Slack</environments>
    <interviewLabel>Approve Discount In Slack {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Approve Discount In Slack</label>
    <processType>Flow</processType>
    <runInMode>DefaultMode</runInMode>
    <screens>
        <name>Review_Discount</name>
        <label>Review Discount</label>
        <locationX>176</locationX>
        <locationY>158</locationY>
        <allowBack>false</allowBack>
        <allowFinish>true</allowFinish>
        <allowPause>false</allowPause>
        <fields>
            <name>Discount_Summary</name>
            <fieldText>&lt;p&gt;Review the requested discount and confirm.&lt;/p&gt;</fieldText>
            <fieldType>DisplayText</fieldType>
        </fields>
        <showFooter>true</showFooter>
        <showHeader>true</showHeader>
    </screens>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Review_Discount</targetReference>
        </connector>
    </start>
    <status>Draft</status>
</Flow>
```

## 3. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/slack-flows.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity_Negotiation_Slack_Alert</members>
        <members>Approve_Discount_In_Slack</members>
        <name>Flow</name>
    </types>
    <version>67.0</version>
</Package>
```

## 4. Deploy and verify

```bash
python3 skills/flow/flow-for-slack/scripts/check_flow_for_slack.py --manifest-dir force-app
sf project deploy start --manifest manifest/slack-flows.xml --target-org uat --wait 30
```

| Order | Step | Verify |
|---|---|---|
| 1 | Create the `Slack_Config__mdt` record with sandbox workspace and channel IDs | Values point at the test workspace |
| 2 | Deploy both flows as Draft, then activate in the sandbox | Flows active |
| 3 | Move an Opportunity to Negotiation/Review | Message appears in the test channel; no Task named "Slack alert failed" |
| 4 | Remove the running user's Slack permission set and repeat | The fault path creates the Task with the fault message |
| 5 | Production: deploy, create the production config record, activate | First real alert posts to the production channel |

Production deploys flows inactive unless "Deploy processes and flows as active" is on, so step 5 includes manual activation.
