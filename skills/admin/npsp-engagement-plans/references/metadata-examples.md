# Metadata and Data Examples: NPSP Engagement Plans

Two artifacts make an engagement plan cadence repeatable across orgs. The template is data. The automation that applies it is metadata. This file gives one complete, deployable example of each, built on the field names in the NPSP source (`SalesforceFoundation/NPSP`, `force-app/main/default/objects/`). In a subscriber org every NPSP object and field carries the `npsp__` prefix.

## 1. Template and template tasks as an `sf data import tree` plan

The Salesforce CLI reference says plan files are loaded in order, and records with lookups to records in another file must be listed after that file. The dependent task therefore lives in its own file after the independent tasks.

`data/engagement-plans/ep-plan.json`:

```json
[
  {
    "sobject": "npsp__Engagement_Plan_Template__c",
    "files": ["npsp__Engagement_Plan_Template__c.json"]
  },
  {
    "sobject": "npsp__Engagement_Plan_Task__c",
    "files": ["npsp__Engagement_Plan_Task__c-independent.json"]
  },
  {
    "sobject": "npsp__Engagement_Plan_Task__c",
    "files": ["npsp__Engagement_Plan_Task__c-dependent.json"]
  }
]
```

`data/engagement-plans/npsp__Engagement_Plan_Template__c.json`:

```json
{
  "records": [
    {
      "attributes": { "type": "npsp__Engagement_Plan_Template__c", "referenceId": "MajorGiftTemplate" },
      "Name": "Major Gift Stewardship 30-60-90",
      "npsp__Description__c": "Applied by Flow to Opportunities of 10,000 or more at Closed Won.",
      "npsp__Skip_Weekends__c": true,
      "npsp__Reschedule_To__c": "Monday",
      "npsp__Default_Assignee__c": "Owner of Object for Engagement Plan",
      "npsp__Automatically_Update_Child_Task_Due_Date__c": true
    }
  ]
}
```

`data/engagement-plans/npsp__Engagement_Plan_Task__c-independent.json`:

```json
{
  "records": [
    {
      "attributes": { "type": "npsp__Engagement_Plan_Task__c", "referenceId": "ThankYouCall" },
      "Name": "Thank-you call for major gift",
      "npsp__Engagement_Plan_Template__c": "@MajorGiftTemplate",
      "npsp__Days_After__c": 30,
      "npsp__Type__c": "Call",
      "npsp__Priority__c": "High",
      "npsp__Reminder__c": true,
      "npsp__Reminder_Time__c": "540"
    },
    {
      "attributes": { "type": "npsp__Engagement_Plan_Task__c", "referenceId": "ImpactReport" },
      "Name": "Send impact report for major gift",
      "npsp__Engagement_Plan_Template__c": "@MajorGiftTemplate",
      "npsp__Days_After__c": 60,
      "npsp__Type__c": "Email",
      "npsp__Priority__c": "Medium"
    }
  ]
}
```

`data/engagement-plans/npsp__Engagement_Plan_Task__c-dependent.json`:

```json
{
  "records": [
    {
      "attributes": { "type": "npsp__Engagement_Plan_Task__c", "referenceId": "CultivationMeeting" },
      "Name": "Cultivation meeting for major gift",
      "npsp__Engagement_Plan_Template__c": "@MajorGiftTemplate",
      "npsp__Parent_Task__c": "@ImpactReport",
      "npsp__Days_After__c": 30,
      "npsp__Type__c": "Meeting",
      "npsp__Priority__c": "High",
      "npsp__Send_Email__c": true
    }
  ]
}
```

Notes on the data:

- `Days_After__c` on a dependent task counts from the parent, per its field help text. The meeting is provisionally due at day 90 (60 + 30) and moves to "parent close date + 30" when the impact report Task closes.
- `Reminder_Time__c` is minutes after midnight on the due date; NPSP defaults to 720 (noon) when it is blank (`EP_Task_UTIL.setReminder`).
- `Assigned_To__c` is left out on purpose. It holds a User ID, which differs per org. The template's Default Assignee fills the gap.
- The JSON files above use `//` header comments for the file path only. Remove those lines before running the import, because JSON has no comment syntax.
- UNVERIFIED (2026-10-03): the `@referenceId` lookup syntax across plan files follows the sObject tree format produced by `sf data export tree --plan`; the CLI reference excerpt read for this skill describes file ordering but does not print the reference syntax.

Load it:

```bash
sf data import tree --plan data/engagement-plans/ep-plan.json --target-org prod
```

## 2. Record-triggered Flow that applies the template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/flows/Apply_Major_Gift_Stewardship_Plan.flow-meta.xml -->
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <customErrors>
        <name>Plan_Not_Created</name>
        <label>Plan Not Created</label>
        <locationX>440</locationX>
        <locationY>360</locationY>
        <customErrorMessages>
            <errorMessage>The stewardship plan could not be created, so this stage change was not saved. Detail: {!$Flow.FaultMessage}</errorMessage>
            <isFieldError>false</isFieldError>
        </customErrorMessages>
        <description>Fault target. NPSP inserts the plan's Tasks all-or-none, so one bad Task rolls back the plan; this surfaces the reason instead of failing silently.</description>
    </customErrors>
    <decisions>
        <name>Template_Found</name>
        <label>Template Found</label>
        <locationX>176</locationX>
        <locationY>240</locationY>
        <defaultConnectorLabel>No Template</defaultConnectorLabel>
        <rules>
            <name>Has_Template</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>Get_Stewardship_Template</leftValueReference>
                <operator>IsNull</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Create_Engagement_Plan</targetReference>
            </connector>
            <label>Has Template</label>
        </rules>
    </decisions>
    <description>Creates one npsp__Engagement_Plan__c on an Opportunity when it reaches Closed Won at 10,000 or more. NPSP then creates the Tasks.</description>
    <environments>Default</environments>
    <interviewLabel>Apply Major Gift Stewardship Plan {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Apply Major Gift Stewardship Plan</label>
    <processType>AutoLaunchedFlow</processType>
    <recordCreates>
        <name>Create_Engagement_Plan</name>
        <label>Create Engagement Plan</label>
        <locationX>176</locationX>
        <locationY>360</locationY>
        <faultConnector>
            <targetReference>Plan_Not_Created</targetReference>
        </faultConnector>
        <inputAssignments>
            <field>npsp__Engagement_Plan_Template__c</field>
            <value>
                <elementReference>Get_Stewardship_Template.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>npsp__Opportunity__c</field>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <object>npsp__Engagement_Plan__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
    <recordLookups>
        <name>Get_Stewardship_Template</name>
        <label>Get Stewardship Template</label>
        <locationX>176</locationX>
        <locationY>120</locationY>
        <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
        <connector>
            <targetReference>Template_Found</targetReference>
        </connector>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Name</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Major Gift Stewardship 30-60-90</stringValue>
            </value>
        </filters>
        <getFirstRecordOnly>true</getFirstRecordOnly>
        <object>npsp__Engagement_Plan_Template__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordLookups>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Get_Stewardship_Template</targetReference>
        </connector>
        <object>Opportunity</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
        <filterLogic>and</filterLogic>
        <filters>
            <field>StageName</field>
            <operator>EqualTo</operator>
            <value>
                <stringValue>Closed Won</stringValue>
            </value>
        </filters>
        <filters>
            <field>Amount</field>
            <operator>GreaterThanOrEqualTo</operator>
            <value>
                <numberValue>10000.0</numberValue>
            </value>
        </filters>
        <doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>
    </start>
    <status>Draft</status>
</Flow>
```

Design notes:

- Only one lookup is set on the plan (`npsp__Opportunity__c`). Setting a second target lookup makes NPSP reject the insert.
- `doesRequireRecordChangedToMeetCriteria` keeps the flow from creating a second plan every time a Closed Won opportunity is edited.
- The custom error blocks the stage change when the plan fails. If the business prefers the opportunity to save anyway, replace the fault target with the org's logging subflow from `templates/flow/FaultPath_Template.md`.
- UNVERIFIED (2026-10-03): the Metadata API guide marks `connector` as required on `FlowCustomError`; this example leaves the custom error as the last node with no connector. Validate with `sf project deploy validate` before relying on it.

## 3. package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Apply_Major_Gift_Stewardship_Plan</members>
        <name>Flow</name>
    </types>
    <version>67.0</version>
</Package>
```

The templates do not appear in `package.xml`. They are records of `npsp__Engagement_Plan_Template__c` and `npsp__Engagement_Plan_Task__c` and travel with the data plan in section 1.

## 4. Verification query after the first plan is applied

```sql
SELECT Id, Subject, Status, ActivityDate, IsReminderSet, OwnerId,
       npsp__Engagement_Plan__c, npsp__Engagement_Plan_Task__c
FROM Task
WHERE npsp__Engagement_Plan__r.npsp__Opportunity__c = :opportunityId
ORDER BY ActivityDate
```

Expect three rows. The meeting row shows `Waiting on Dependent Task` until the impact report Task is closed.
