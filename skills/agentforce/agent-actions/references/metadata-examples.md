# Metadata Examples: Agent Actions

This file shows one side-effecting agent action built the way `SKILL.md` recommends: a narrow Apex reference action, a test, a `GenAiFunction` with confirmation turned on, and input and output schemas whose descriptions act as the action's instructions.

## Example 1: "Request Case Callback", a confirmation-gated write

**Context.** A service subagent lets a customer ask for a phone callback on an existing case. The action creates one Task on the case. Because it writes data on the customer's behalf, the agent must read the request back and get a yes before running it.

### 1. Apex reference action

**File path:** `force-app/main/default/classes/CaseCallbackRequestAction.cls`

```apex
public with sharing class CaseCallbackRequestAction {

    public class Request {
        @InvocableVariable(
            required=true
            label='Case Number'
            description='The case number the customer gave, for example 00001042. Ask the customer if it is missing.'
        )
        public String caseNumber;

        @InvocableVariable(
            required=true
            label='Preferred Callback Time'
            description='The date and time the customer wants the call, in the customer time zone. Confirm it back before running the action.'
        )
        public Datetime preferredCallbackTime;
    }

    public class Result {
        @InvocableVariable(label='Success' description='True when the callback request was saved.')
        public Boolean success;
        @InvocableVariable(label='Callback Task ID' description='The ID of the task that was created. Do not read it to the customer.')
        public String taskId;
        @InvocableVariable(label='Message' description='One sentence to tell the customer what happened.')
        public String message;
    }

    @InvocableMethod(
        label='Request Case Callback'
        description='Creates a callback request task on one existing case for the time the customer chose. Use only after the customer confirms the case number and time. Does not change the case itself.'
        category='Case Service'
    )
    public static List<Result> requestCallback(List<Request> requests) {
        Set<String> numbers = new Set<String>();
        for (Request req : requests) {
            if (req != null && String.isNotBlank(req.caseNumber)) {
                numbers.add(req.caseNumber.trim());
            }
        }
        Map<String, Id> caseIdByNumber = new Map<String, Id>();
        for (Case c : [SELECT Id, CaseNumber FROM Case WHERE CaseNumber IN :numbers WITH USER_MODE]) {
            caseIdByNumber.put(c.CaseNumber, c.Id);
        }

        List<Result> results = new List<Result>();
        List<Task> toInsert = new List<Task>();
        List<Integer> resultIndexForTask = new List<Integer>();
        for (Request req : requests) {
            Result res = new Result();
            res.success = false;
            Id caseId = (req == null || req.caseNumber == null) ? null : caseIdByNumber.get(req.caseNumber.trim());
            if (caseId == null) {
                res.message = 'I could not find that case. Please check the case number.';
            } else if (req.preferredCallbackTime == null || req.preferredCallbackTime < Datetime.now()) {
                res.message = 'Please choose a callback time in the future.';
            } else {
                toInsert.add(new Task(
                    WhatId = caseId,
                    Subject = 'Customer callback requested',
                    ActivityDate = req.preferredCallbackTime.date(),
                    ReminderDateTime = req.preferredCallbackTime,
                    IsReminderSet = true
                ));
                resultIndexForTask.add(results.size());
            }
            results.add(res);
        }

        if (!toInsert.isEmpty()) {
            Database.SaveResult[] saves = Database.insert(toInsert, false, AccessLevel.USER_MODE);
            for (Integer i = 0; i < saves.size(); i++) {
                Result res = results[resultIndexForTask[i]];
                if (saves[i].isSuccess()) {
                    res.success = true;
                    res.taskId = saves[i].getId();
                    res.message = 'Your callback request is saved.';
                } else {
                    res.message = 'I could not save the callback request. A service rep can help.';
                }
            }
        }
        return results;
    }
}
```

What the shape buys:

- One `List` parameter and one result per request, in the same order, with failures reported in the result instead of thrown (Apex Developer Guide, InvocableMethod Annotation).
- Primitive request fields only. Custom actions that reference Apex support only primitive data types (Generative AI guide, Considerations for Custom Actions).
- `WITH USER_MODE` and `AccessLevel.USER_MODE` apply the running agent user's object, field and sharing access to both the read and the write.
- The validation that the time is in the future lives in code. The Generative AI guide says to build sensitive or deterministic rules into the reference action, not into instructions.

### 2. Test class

**File path:** `force-app/main/default/classes/CaseCallbackRequestActionTest.cls`

```apex
@IsTest
private class CaseCallbackRequestActionTest {

    @TestSetup
    static void makeData() {
        insert new Case(Subject = 'Callback action test');
    }

    @IsTest
    static void createsTaskForKnownCaseAndReportsUnknownCase() {
        Case c = [SELECT CaseNumber FROM Case LIMIT 1];

        CaseCallbackRequestAction.Request good = new CaseCallbackRequestAction.Request();
        good.caseNumber = c.CaseNumber;
        good.preferredCallbackTime = Datetime.now().addDays(1);

        CaseCallbackRequestAction.Request unknown = new CaseCallbackRequestAction.Request();
        unknown.caseNumber = 'NOPE';
        unknown.preferredCallbackTime = Datetime.now().addDays(1);

        Test.startTest();
        List<CaseCallbackRequestAction.Result> results = CaseCallbackRequestAction.requestCallback(
            new List<CaseCallbackRequestAction.Request>{ good, unknown });
        Test.stopTest();

        Assert.areEqual(2, results.size(), 'One result per request');
        Assert.isTrue(results[0].success, 'Known case gets a task');
        Assert.isNotNull(results[0].taskId);
        Assert.isFalse(results[1].success, 'Unknown case is reported, not thrown');
        Assert.areEqual(1, [SELECT COUNT() FROM Task WHERE WhatId = :c.Id]);
    }

    @IsTest
    static void rejectsPastTime() {
        Case c = [SELECT CaseNumber FROM Case LIMIT 1];
        CaseCallbackRequestAction.Request past = new CaseCallbackRequestAction.Request();
        past.caseNumber = c.CaseNumber;
        past.preferredCallbackTime = Datetime.now().addDays(-1);

        List<CaseCallbackRequestAction.Result> results = CaseCallbackRequestAction.requestCallback(
            new List<CaseCallbackRequestAction.Request>{ past });

        Assert.isFalse(results[0].success);
        Assert.areEqual(0, [SELECT COUNT() FROM Task WHERE WhatId = :c.Id]);
    }
}
```

### 3. GenAiFunction with confirmation turned on

**File path:** `force-app/main/default/genAiFunctions/Request_Case_Callback/Request_Case_Callback.genAiFunction-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GenAiFunction xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Creates a callback request on one existing case for the date and time the customer chose. Use it when the customer asks to be called back about a case they already have. Do not use it to open a new case or to change the case.</description>
    <invocationTarget>CaseCallbackRequestAction</invocationTarget>
    <invocationTargetType>apex</invocationTargetType>
    <isConfirmationRequired>true</isConfirmationRequired>
    <isIncludeInProgressIndicator>true</isIncludeInProgressIndicator>
    <masterLabel>Request Case Callback</masterLabel>
    <progressIndicatorMessage>Saving your callback request</progressIndicatorMessage>
</GenAiFunction>
```

`isConfirmationRequired` is the metadata form of the "Require user confirmation" setting the Generative AI guide describes for actions that change a record. Turning it on adds a confirmation turn and an LLM call to every run, which is the intended cost of a write.

UNVERIFIED (2026-10-03): the source-format folder layout (component folder plus `input` and `output` schema folders) is inferred from the Metadata API description of the schema folders; confirm it by retrieving one action from your org.

**File path:** `force-app/main/default/genAiFunctions/Request_Case_Callback/input/schema.json`

```json
{
  "required": ["caseNumber", "preferredCallbackTime"],
  "properties": {
    "caseNumber": {
      "title": "Case Number",
      "description": "The case number the customer gave in this conversation. Ask for it if it is missing. Never guess it.",
      "lightning:type": "lightning__textType",
      "maxLength": 30,
      "lightning:isPII": false,
      "copilotAction:isUserInput": true
    },
    "preferredCallbackTime": {
      "title": "Preferred Callback Time",
      "description": "The date and time the customer wants to be called. Read it back to the customer before running the action.",
      "lightning:type": "lightning__dateTimeType",
      "lightning:isPII": false,
      "copilotAction:isUserInput": true
    }
  },
  "lightning:type": "lightning__objectType"
}
```

**File path:** `force-app/main/default/genAiFunctions/Request_Case_Callback/output/schema.json`

```json
{
  "properties": {
    "success": {
      "title": "Success",
      "description": "True when the callback request was saved. When false, tell the customer and offer a service rep.",
      "lightning:type": "lightning__booleanType",
      "lightning:isPII": false,
      "copilotAction:isDisplayable": false,
      "copilotAction:isUsedByPlanner": true
    },
    "message": {
      "title": "Message",
      "description": "One sentence to tell the customer what happened.",
      "lightning:type": "lightning__textType",
      "lightning:isPII": false,
      "copilotAction:isDisplayable": true,
      "copilotAction:isUsedByPlanner": true
    },
    "taskId": {
      "title": "Callback Task ID",
      "description": "The ID of the created task, for follow-up actions only. Do not show it to the customer.",
      "lightning:type": "lightning__recordIdType",
      "lightning:isPII": false,
      "copilotAction:isDisplayable": false,
      "copilotAction:isUsedByPlanner": true
    }
  },
  "lightning:type": "lightning__objectType"
}
```

`copilotAction:isUserInput` is the schema form of "Collect data from user", and `copilotAction:isDisplayable` is "Show in conversation". At least one output must have `copilotAction:isUsedByPlanner` set to `true`, or the planner returns random responses (Metadata API reference, GenAiFunction output folder).

## package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>CaseCallbackRequestAction</members>
        <members>CaseCallbackRequestActionTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Request_Case_Callback</members>
        <name>GenAiFunction</name>
    </types>
    <version>66.0</version>
</Package>
```

## Deploy order

1. The Apex class and its test. The agent user's permission set needs Apex class access to `CaseCallbackRequestAction`, plus read on Case and create on Task.
2. The `GenAiFunction`.
3. Add the action to a subagent. An action does nothing until it is assigned to a topic, and the guidance is no more than 15 actions per topic.
4. The agent must be deactivated, or a new version created, to add the action; deactivating interrupts live conversations.

## Verification

- Both test methods pass.
- `python3 skills/agentforce/agent-actions/scripts/check_agent_actions.py --manifest-dir force-app/main/default` and `python3 skills/agentforce/agentforce-tool-use-patterns/scripts/check_agentforce_tool_use_patterns.py --manifest-dir force-app/main/default` report no blocking findings.
- In Agentforce Builder preview, "please call me back about case 00001042 tomorrow at 10" produces a confirmation question that repeats the case number and time before the action runs. Answering "no" leaves no Task on the case.
